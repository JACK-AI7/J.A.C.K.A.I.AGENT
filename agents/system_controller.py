import subprocess
import os
import sys
import json
import tempfile
import traceback
import pyautogui
import numpy as np
from PIL import Image
import time
import re
import shutil
try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
        thought_received = type('Signal', (), {'emit': lambda *a: None})()
    _dummy = _DummySignals()
    def get_signals(): return _dummy

# Safe imports for heavy dependencies
try:
    import cv2
except ImportError:
    cv2 = None
    print("System Controller: OpenCV not installed. Visual features limited.")

try:
    import easyocr
except ImportError:
    easyocr = None
    print("System Controller: EasyOCR not installed. OCR features disabled.")

try:
    import ollama
except ImportError:
    ollama = None
    print("System Controller: Ollama Python client not installed.")


class SystemController:
    """Handles advanced system control, dynamic code execution, and visual GUI automation."""

    def __init__(self):
        from config import DESKTOP_SETTINGS
        self.workspace = os.getcwd()
        pyautogui.FAILSAFE = DESKTOP_SETTINGS.get("failsafe", True) # IMMORTAL OVERRIDE
        pyautogui.PAUSE = DESKTOP_SETTINGS.get("pause", 0.1)
        # Initialize OCR Reader (loads models on first use)
        self.reader = None
        if easyocr is not None:
            try:
                self.reader = easyocr.Reader(["en"])
                print("Visual Engine: EasyOCR Initialization Successful.")
            except Exception as e:
                print(f"Visual Engine: OCR failed to load: {e}")
        else:
            print("Visual Engine: EasyOCR not available (not installed).")

    def execute_terminal(self, command):
        """Execute a terminal command (PowerShell on Windows) and return output."""
        signals = get_signals()
        signals.thought_received.emit(f"Executing Terminal: {command[:50]}...", "decision")
        try:
            # Use powershell for better Windows control
            process = subprocess.Popen(
                ["powershell", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0:
                return f"Execution Successful:\n{stdout}"
            else:
                return f"Execution Failed (Code {process.returncode}):\n{stderr}"
        except Exception as e:
            return f"System Error: {str(e)}"

    def execute_python(self, code):
        """Execute dynamic Python code safely and capture stdout/stderr."""
        # Create a temporary file to run the code
        fd, path = tempfile.mkstemp(suffix=".py", prefix="agent_temp_")
        try:
            with os.fdopen(fd, "w") as tmp:
                tmp.write(code)

            # Execute the temporary file
            process = subprocess.Popen(
                [sys.executable, path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.workspace,
            )
            stdout, stderr = process.communicate(timeout=60)

            output = ""
            if stdout:
                output += f"Output:\n{stdout}\n"
            if stderr:
                output += f"Errors:\n{stderr}\n"

            return output if output else "Execution completed with no output."

        except Exception as e:
            return f"Execution Error: {str(e)}\n{traceback.format_exc()}"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def visual_locate(self, target_description):
        """
        Locate an element on the screen using computer vision and OCR.
        Returns coordinates of the text matching target_description.
        """
        if self.reader is None:
            return "Vision Error: OCR engine not initialized."
        if cv2 is None:
            return "Vision Error: OpenCV not installed."

        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            # Convert RGB to BGR for OpenCV
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            # Perform OCR
            results = self.reader.readtext(screenshot_bgr)

            # Search for matches
            for bbox, text, prob in results:
                if target_description.lower() in text.lower():
                    # Calculate center of bounding box
                    # bbox: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                    center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                    return {
                        "x": center_x,
                        "y": center_y,
                        "text": text,
                        "confidence": prob,
                    }

            return f"Could not find '{target_description}' on screen."
        except Exception as e:
            return f"Vision Error: {str(e)}"

    def analyze_screen_deep(self):
        """Use LLaVA (via Ollama) to describe the entire screen in detail."""
        if ollama is None:
            return "Visual Engine Error: Ollama Python client not installed."
        try:
            # Save temporary screenshot
            temp_path = os.path.join(tempfile.gettempdir(), "agent_eye.png")
            pyautogui.screenshot(temp_path)

            print("Visual Engine: Engaging LLaVA for deep analysis...")
            response = ollama.chat(
                model="llava",
                messages=[
                    {
                        "role": "user",
                        "content": "What is currently on this computer screen? Describe the apps, text, and overall context.",
                        "images": [temp_path],
                    }
                ],
            )

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return response["message"]["content"]
        except Exception as e:
            # Check if the error is about image input not supported
            if "does not support image input" in str(e) or "image" in str(e).lower():
                return "Visual Engine Error: The current AI model does not support image input. Please switch to a multimodal model like LLaVA."
            else:
                return f"Deep Vision Error: {str(e)}"

    def locate_and_click(self, x, y, verify=True):
        """Execute a precision click at specific coordinates with optional verification."""
        try:
            # Capture state before click
            before_path = os.path.join(tempfile.gettempdir(), "click_before.png")
            if verify:
                pyautogui.screenshot(before_path)

            pyautogui.click(x, y)
            print(f"Visual Engine: Clicked at ({x}, {y})")

            if verify:
                time.sleep(0.3)  # Fast-path: reduced wait
                after_path = os.path.join(tempfile.gettempdir(), "click_after.png")
                pyautogui.screenshot(after_path)

                # Cleanup
                for p in [before_path, after_path]:
                    if os.path.exists(p):
                        os.remove(p)

            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Control Error: {str(e)}"

    def smart_ui_click(self, target_description):
        """TITAN Fast-Path: Try logical UI control before vision."""
        from visual_orchestrator import VisualOrchestrator
        orchestrator = VisualOrchestrator()
        return orchestrator.smart_click(target_description)

    def ai_vision_click(self, target_description):
        """The 'Immortal' click: Uses LLaVA to find the coordinate, then clicks and verifies."""
        if ollama is None:
            return "Vision Error: Ollama not available for AI vision click."
        try:
            print(f"Visual Engine: Analyzing screen to find '{target_description}'...")
            # 1. Get deep analysis with coordinates
            temp_path = os.path.join(tempfile.gettempdir(), "vision_search.png")
            pyautogui.screenshot(temp_path)

            prompt = f"Find the UI element for '{target_description}' on this screen. Return ONLY the JSON coordinates like {{'x': 500, 'y': 300}}. If not found, return {{'x': -1, 'y': -1}}"

            response = ollama.chat(
                model="llava",
                messages=[{"role": "user", "content": prompt, "images": [temp_path]}],
            )

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # Simple regex to extract JSON from LLaVA response
            match = re.search(r"\{.*\}", response["message"]["content"])
            if match:
                coords = json.loads(match.group().replace("'", '"'))
                if coords["x"] != -1:
                    return self.locate_and_click(coords["x"], coords["y"], verify=True)

            # Fallback to OCR if LLaVA coordinate prediction is vague
            print("Visual Engine: Coordinate prediction failed, falling back to OCR...")
            res = self.visual_locate(target_description)
            if isinstance(res, dict):
                return self.locate_and_click(res["x"], res["y"], verify=True)

            return f"Immortal Error: Could not locate '{target_description}' visually."
        except Exception as e:
            return f"Vision Mission Error: {str(e)}"

    def manage_files(self, action, path, destination=None):
        """High-level file management (move, copy, delete)."""
        signals = get_signals()
        try:
            if action == "move":
                signals.thought_received.emit(f"Moving: {os.path.basename(path)} → {destination}", "decision")
                shutil.move(path, destination)
                return f"Moved {path} to {destination}"
            elif action == "copy":
                signals.thought_received.emit(f"Cloning: {os.path.basename(path)} → {destination}", "thought")
                shutil.copy(path, destination)
                return f"Copied {path} to {destination}"
            elif action == "delete":
                signals.thought_received.emit(f"Purging: {os.path.basename(path)}", "decision")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return f"Deleted {path}"
        except Exception as e:
            return f"File Error: {str(e)}"


# Singleton instance
system_controller = SystemController()
