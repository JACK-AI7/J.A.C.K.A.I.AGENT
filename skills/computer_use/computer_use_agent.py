import os
import base64
import time
import random
import requests
import json
from PIL import Image
from desktop_agent import desktop_agent
from mss import mss
import io
import re
from core.config import MODEL_PROFILES
from utils.humanized_input import HumanizedInput

class ComputerUseAgent:
    def __init__(self, model=MODEL_PROFILES["eyes"]["model"]):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.screen_width, self.screen_height = self._get_screen_res()
        # Humanized input for realistic actions
        self.human = HumanizedInput()

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
                "stream": False,
                "options": {
                    "temperature": 0.1,  # More deterministic
                    "num_predict": 256,
                }
            }
            
            try:
                print(f"  [Thinking] Step {i+1}: Querying vision model...")
                response = requests.post(self.ollama_url, json=payload, timeout=30)
                
                if response.status_code != 200:
                    print(f"  [ERROR] Ollama API returned {response.status_code}: {response.text}")
                    # Fallback: try without image? Better to abort
                    break
                    
                result = response.json()
                response_text = result.get("response", "").strip()
                
                if not response_text:
                    print("  [WARNING] Empty response from model, retrying...")
                    time.sleep(1)
                    continue
                    
                print(f"  [Thought] {response_text}")
                
                # Parse action (relaxed regex to handle brackets or extra spaces)
                action_match = re.search(r'ACTION:\s*\[?(\w+)\]?\s*\((.*)\)', response_text, re.IGNORECASE)
                if action_match:
                    action_type = action_match.group(1).lower()
                    params = [p.strip().strip("'").strip('"') for p in action_match.group(2).split(',') if p.strip()]
                    
                    print(f"  [Action] Executing: {action_type}({params})")
                    
                    # Execute with verification and retry
                    success = self._execute_action_with_retry(action_type, params)
                    if not success:
                        print(f"  [WARNING] Action failed after retries: {action_type}({params})")
                    
                    # Human think time between actions
                    time.sleep(random.uniform(0.8, 1.5))
                else:
                    if "FINISH" in response_text or "COMPLETE" in response_text or "DONE" in response_text:
                        print("Task completed according to brain.")
                        break
                    print(f"  [WARNING] No ACTION found in response. Full response: {response_text[:200]}")
                    # Continue to next iteration to retry
                    
            except requests.exceptions.RequestException as e:
                print(f"  [NETWORK ERROR] Ollama request failed: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"  [PARSE ERROR] Invalid JSON response: {e}")
                break
            except Exception as e:
                print(f"  [UNEXPECTED ERROR] {type(e).__name__}: {e}")
                break
                    
                result = response.json()
                response_text = result.get("response", "").strip()
                
                if not response_text:
                    print("  [WARNING] Empty response from model, retrying...")
                    time.sleep(1)
                    continue
                    
                print(f"  [Thought] {response_text}")
                
                # Parse action (relaxed regex to handle brackets or extra spaces)
                action_match = re.search(r'ACTION:\s*\[?(\w+)\]?\s*\((.*)\)', response_text, re.IGNORECASE)
                if action_match:
                    action_type = action_match.group(1).lower()
                    params = [p.strip().strip("'").strip('"') for p in action_match.group(2).split(',') if p.strip()]
                    
                    print(f"  [Action] Executing: {action_type}({params})")
                    
                    # Execute with verification and retry
                    success = self._execute_action_with_retry(action_type, params)
                    if not success:
                        print(f"  [WARNING] Action failed after retries: {action_type}({params})")
                    
                    # Human think time between actions
                    time.sleep(random.uniform(0.8, 1.5))
                else:
                    if "FINISH" in response_text or "COMPLETE" in response_text or "DONE" in response_text:
                        print("Task completed according to brain.")
                        break
                    print(f"  [WARNING] No ACTION found in response. Full response: {response_text[:200]}")
                    # Continue to next iteration to retry
                    
            except requests.exceptions.RequestException as e:
                print(f"  [NETWORK ERROR] Ollama request failed: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"  [PARSE ERROR] Invalid JSON response: {e}")
                break
            except Exception as e:
                print(f"  [UNEXPECTED ERROR] {type(e).__name__}: {e}")
                break
    
    def _execute_action_with_retry(self, action_type: str, params: list) -> bool:
        """Execute action with retry logic and verification."""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                result = self._perform_action(action_type, params)
                print(f"  Action result: {result}")
                
                # For certain actions, verify success
                if action_type in ['click', 'type']:
                    # Wait for UI to update
                    time.sleep(0.5)
                    # Simple verification: if no exception, assume success
                    # Could enhance with visual verification here
                    return True
                else:
                    return True
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = 0.5 * (2 ** attempt)  # exponential backoff
                    time.sleep(delay + random.uniform(0, 0.3))
                else:
                    print(f"  [ERROR] Action failed: {e}")
                    return False
        return False
        
    def _perform_action(self, action_type: str, params: list):
        """Perform a single action."""
        if action_type == "click" and len(params) == 2:
            x, y = int(params[0]), int(params[1])
            desktop_agent.click_position(x, y)
        elif action_type == "type" and len(params) == 1:
            desktop_agent.type_text(params[0])
        elif action_type == "move" and len(params) == 2:
            # desktop_agent doesn't have move, use click as placeholder
            x, y = int(params[0]), int(params[1])
            self.human.move_to(x, y, smooth=True)
        elif action_type == "scroll" and len(params) >= 1:
            direction = params[0]
            amount = int(params[1]) if len(params) > 1 else 3
            desktop_agent.scroll(direction, amount)
        elif action_type == "wait" and len(params) == 1:
            time.sleep(float(params[0]))
        elif action_type == "close":
            desktop_agent.close_active_window()
        else:
            print(f"  Unknown action: {action_type} with params {params}")

if __name__ == "__main__":
    # Test
    try:
        agent = ComputerUseAgent()
        # agent.run_task("Click the Start button")
    except Exception as e:
        print(f"Agent Init Failed: {e}")
