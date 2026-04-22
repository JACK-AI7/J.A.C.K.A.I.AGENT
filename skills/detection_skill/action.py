import os
import sys
import cv2
import time
from ultralytics import YOLO
import torch

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

class VisionSystem:
    def __init__(self):
        self.model_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), "assets", "yolov8n.pt")
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        if not self.model:
            print(f"Vision System: Loading Neural Weights from {self.model_path}...")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)

    def detect(self):
        try:
            self._load_model()
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Vision Error: Physical optics (Camera) not responding."

            ret, frame = cap.read()
            cap.release()

            if not ret:
                return "Vision Error: Failed to capture live frame."

            results = self.model(frame)
            
            detections = []
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = self.model.names[cls]
                    if conf > 0.3: # Threshold
                        detections.append(f"{label} ({int(conf*100)}%)")

            if not detections:
                return "Vision Analysis: Analysis complete. No significant objects identified in the current sector."

            # Save annotated image for HUD
            assets_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), "assets")
            os.makedirs(assets_dir, exist_ok=True)
            output_path = os.path.join(assets_dir, "last_detection.jpg")
            
            annotated_frame = results[0].plot()
            cv2.imwrite(output_path, annotated_frame)

            return f"Vision Analysis: Targeted identification successful. Detected: {', '.join(detections)}. Frame archived to assets."
        except Exception as e:
            return f"Vision Critical Failure: {str(e)}"

def execute(task=None):
    # For detection, we usually ignore the task as it's just 'look'
    vs = VisionSystem()
    return vs.detect()

if __name__ == "__main__":
    # Test
    # print(execute())
    pass
