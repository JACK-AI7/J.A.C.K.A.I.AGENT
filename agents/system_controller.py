import subprocess
import os
import sys
import json
import tempfile
import traceback
import time
import re
import shutil
try:
    from core.nexus_bridge import get_signals
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

from utils.humanized_input import HumanizedInput, HumanConfig


class SystemController:
    """Handles advanced system control, dynamic code execution, and visual GUI automation."""

    def __init__(self):
        from core.config import DESKTOP_SETTINGS
        self.workspace = os.getcwd()
        
        # Humanized input system for realistic automation
        human_config = HumanConfig(
            mouse_precision=0.88,
            typing_speed_base=0.08,
            typo_chance=0.01
        )
        self.human = HumanizedInput(human_config)
        
        # Get signals for agent status
        try:
            from core.nexus_bridge import get_signals
            self.signals = get_signals()
            self.signals.emit_bridge("agent_status", "SystemController", "INITIALIZED", "Vision & Control ready")
        except Exception as e:
            print(f"SystemController signals init failed: {e}")
        
        # Initialize OCR Reader
        self.reader = None
        if easyocr is not None:
            try:
                self.reader = easyocr.Reader(["en"])
                print("Visual Engine: EasyOCR Initialization Successful.")
                try:
                    self.signals.emit_bridge("agent_status", "SystemController", "ACTIVE", "OCR engine online")
                except: pass
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
            # Take screenshot using human module (consistent)
            screenshot = self.human.capture_screen()
            screenshot_np = np.array(screenshot)
            # Convert RGB to BGR for OpenCV
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            # Perform OCR
            results = self.reader.readtext(screenshot_bgr)

            # Search for matches
            for bbox, text, prob in results:
                if target_description.lower() in text.lower():
                    # Calculate center of bounding box
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
            self.human.capture_screen_to_file(temp_path)

            print("Visual Engine: Engaging LLaVA for deep analysis...")
            response = ollama.chat(
                model="llava",
                messages=[
                    {
                        "role": "user",
                        "content": "What is currently on this computer screen? Describe the apps, windows, text, and overall context in detail.",
                        "images": [temp_path],
                    }
                ],
            )

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return response["message"]["content"]
        except Exception as e:
            if "does not support image input" in str(e) or "image" in str(e).lower():
                return "Visual Engine Error: The current AI model does not support image input. Please switch to a multimodal model like LLaVA."
            else:
                return f"Deep Vision Error: {str(e)}"

    def locate_and_click(self, x, y, verify=True):
        """Execute a precision click at specific coordinates with optional verification."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "SystemController", "CLICK", f"Clicking at ({x}, {y})")
            except: pass
            
            # Capture state before click for verification
            before_path = None
            after_path = None
            if verify:
                before_path = os.path.join(tempfile.gettempdir(), "click_before.png")
                self.human.capture_screen_to_file(before_path)
            
            # Use humanized click with smooth movement
            self.human.click(x, y)
            
            if verify:
                time.sleep(0.5)  # Wait for UI to react
                after_path = os.path.join(tempfile.gettempdir(), "click_after.png")
                self.human.capture_screen_to_file(after_path)
                # Cleanup
                for p in [before_path, after_path]:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except:
                            pass

            result = f"Clicked at ({x}, {y})"
            
            try:
                self.signals.emit_bridge("agent_action", "SystemController", "CLICK", result)
                self.signals.emit_bridge("agent_status", "SystemController", "ACTIVE", "Click executed")
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "SystemController", "CLICK", f"Error: {str(e)}")
            except: pass
            return f"Control Error: {str(e)}"

    def ai_vision_click(self, target_description):
        """Use LLaVA vision AI to find and click UI elements."""
        if ollama is None:
            return "Vision Error: Ollama not available for AI vision click."
        try:
            print(f"Visual Engine: Analyzing screen to find '{target_description}'...")
            temp_path = os.path.join(tempfile.gettempdir(), "vision_search.png")
            self.human.capture_screen_to_file(temp_path)

            prompt = f"Find the UI element for '{target_description}' on this screen. Return ONLY the JSON coordinates like {{'x': 500, 'y': 300}}. If not found, return {{'x': -1, 'y': -1}}"

            response = ollama.chat(
                model="llava",
                messages=[{"role": "user", "content": prompt, "images": [temp_path]}],
            )

            if os.path.exists(temp_path):
                os.remove(temp_path)

            match = re.search(r"\{.*\}", response["message"]["content"])
            if match:
                coords = json.loads(match.group().replace("'", '"'))
                if coords["x"] != -1:
                    return self.locate_and_click(coords["x"], coords["y"], verify=True)

            # Fallback to OCR
            print("Visual Engine: Coordinate prediction failed, falling back to OCR...")
            res = self.visual_locate(target_description)
            if isinstance(res, dict):
                return self.locate_and_click(res["x"], res["y"], verify=True)

            return f"Immortal Error: Could not locate '{target_description}' visually."
        except Exception as e:
            return f"Vision Mission Error: {str(e)}"

    def manage_files(self, action, path, destination=None, confirmed=False):
        """High-level file management (move, copy, delete)."""
        from config import PRIVACY_SETTINGS
        
        # Privacy Check
        if not confirmed:
            path_lower = path.lower()
            if any(kw in path_lower for kw in PRIVACY_SETTINGS.get("protected_keywords", [])):
                return f"PRIVACY_ALERT: The path '{path}' appears to be sensitive. Boss, I need your explicit confirmation to perform this '{action}' operation. Should I proceed?"

        signals = get_signals()
        try:
            if action == "move":
                signals.thought_received.emit(f"Moving: {os.path.basename(path)} -> {destination}", "decision")
                shutil.move(path, destination)
                return f"Moved {path} to {destination}"
            elif action == "copy":
                signals.thought_received.emit(f"Cloning: {os.path.basename(path)} -> {destination}", "thought")
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
