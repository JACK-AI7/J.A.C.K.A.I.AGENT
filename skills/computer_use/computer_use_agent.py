import os
import base64
import time
import requests
import json
from PIL import Image
from desktop_agent import desktop_agent
from mss import mss
import io
import re
from config import MODEL_PROFILES

class ComputerUseAgent:
    def __init__(self, model=MODEL_PROFILES["eyes"]["model"]):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.screen_width, self.screen_height = self._get_screen_res()

    def _get_screen_res(self):
        # Get actual screen size
        size_str = desktop_agent.get_screen_size()
        # "Screen size: 1920x1080 pixels"
        try:
            parts = size_str.split(":")[1].strip().split("x")
            return int(parts[0]), int(parts[1].split()[0])
        except:
            return 1920, 1080 # Fallback

    def capture_screen(self):
        """Capture screen and return base64 encoded string."""
        with mss() as sct:
            screenshot = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Ollama handles large images but reducing helps speed
            # Max dimension 1024 works well for Qwen2-VL
            img.thumbnail((1024, 1024))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85)
            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    def run_task(self, prompt):
        """Main loop for executing a task using local Ollama vision model."""
        print(f"TITAN Local-Compute: Initiating local brain ({self.model}) for: {prompt}")
        
        system_prompt = f"""You are the 'TITAN Eyes' Agent. You are monitoring the screen to assist the Manager.
Current Resolution: {self.screen_width}x{self.screen_height}.

PRECISION CONTROLS:
- click(x, y): Absolute pixel coordinates.
- type(text): Input text into highlighted field.
- move(x, y): Hover over element.
- scroll(direction, amount): 'up'/'down', amount 1-10.
- wait(seconds): Pause for UI loading.

STRATEGY:
Observe the visual state, identify interactive elements, and provide the NEXT logical action to fulfill the mission.

Output Format: ACTION: click(500, 250)
"""

        for i in range(10):  # Max 10 steps
            screenshot_b64 = self.capture_screen()
            
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\nTask: {prompt}\nWhat is the next action?",
                "images": [screenshot_b64],
                "stream": False
            }
            
            try:
                response = requests.post(self.ollama_url, json=payload)
                result = response.json()
                response_text = result.get("response", "")
                
                print(f"TITAN Brain Output: {response_text}")
                
                # Parse action (relaxed regex to handle brackets or extra spaces)
                action_match = re.search(r'ACTION:\s*\[?(\w+)\]?\s*\((.*)\)', response_text)
                if action_match:
                    action_type = action_match.group(1).lower()
                    params = [p.strip().strip("'").strip('"') for p in action_match.group(2).split(',')]
                    
                    if action_type == "click" and len(params) == 2:
                        desktop_agent.click_position(int(params[0]), int(params[1]))
                    elif action_type == "type" and len(params) == 1:
                        desktop_agent.type_text(params[0])
                    elif action_type == "move" and len(params) == 2:
                        # desktop_agent doesn't have move yet, we'll use click as placeholder
                        desktop_agent.click_position(int(params[0]), int(params[1]))
                    elif action_type == "scroll" and len(params) == 1:
                        desktop_agent.scroll(params[0])
                    elif action_type == "close":
                        desktop_agent.close_active_window()
                        
                    time.sleep(1) # Wait for UI to react
                else:
                    if "FINISH" in response_text or "COMPLETE" in response_text:
                        print("Task completed according to brain.")
                        break
                    print("No recognized action found. Retrying...")
                    
            except Exception as e:
                print(f"Local Brain Error: {e}")
                break

if __name__ == "__main__":
    # Test
    try:
        agent = ComputerUseAgent()
        # agent.run_task("Click the Start button")
    except Exception as e:
        print(f"Agent Init Failed: {e}")
