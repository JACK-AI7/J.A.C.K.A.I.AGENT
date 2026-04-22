import cv2
import os
import time

def execute(task=None):
    """
    Captures a frame from the default camera and saves it.
    """
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Camera Skill Error: Could not open camera."
        
        # Give camera time to warm up
        time.sleep(2)
        
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return "Camera Skill Error: Could not read frame."
        
        # Create output directory
        out_dir = os.path.join(os.getcwd(), "assets", "captures")
        os.makedirs(out_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"capture_{timestamp}.jpg"
        filepath = os.path.join(out_dir, filename)
        
        cv2.imwrite(filepath, frame)
        cap.release()
        
        # Also show the frame briefly if possible (not needed for autonomous)
        return f"Photo captured successfully and saved to: {filepath}"
    
    except Exception as e:
        return f"Camera Skill Error: {str(e)}"
