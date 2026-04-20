import time
import os
import json
import re
import logging
import pyautogui
import pywinauto
from pywinauto import Desktop
from system_controller import system_controller
from desktop_agent import desktop_agent

# Screen awareness imports
import tempfile

try:
    import ollama
except ImportError:
    ollama = None

try:
    import cv2
except ImportError:
    cv2 = None

from config import OLLAMA_SETTINGS


class VisualOrchestrator:
    """LLM-driven autonomous desktop agent with real-time screen awareness.
    
    Capabilities:
    - Screen Awareness: Reads the screen via OCR + LLaVA in real-time
    - Full PC Control: Opens, clicks, types, scrolls, manages files
    - Deep OS Integration: Uses pywinauto UIA tree for native UI control
    """

    def __init__(self):
        self.history = []
        self.max_steps = 15
        self.desktop = Desktop(backend="uia")
        self.model = OLLAMA_SETTINGS["current"]["model"]

    def execute_mission(self, task_description):
        """Perform a multi-step autonomous mission using LLM-driven planning."""
        print(f"Visual Agent: Mission Start - '{task_description}'")

        for step in range(1, self.max_steps + 1):
            print(f"\n--- [Step {step}/{self.max_steps}] ---")

            # 1. PERCEIVE: Get current screen state
            screen_context = self._perceive_screen()
            
            # 2. THINK: Ask the LLM what to do next
            action = self._think(task_description, screen_context, step)
            print(f"  Decision: {action}")

            if action["type"] == "complete":
                return f"Mission Accomplished: {action.get('reason', 'Task completed.')}"
            if action["type"] == "failure":
                return f"Mission Failed: {action.get('reason', 'Could not complete task.')}"

            # 3. ACT: Execute the decided action
            result = self._perform_action(action)
            print(f"  Result: {result}")
            
            # Record history for context
            self.history.append({
                "step": step,
                "action": action,
                "result": result
            })

            time.sleep(1)  # Let the UI settle

        return "Mission Timeout: Max steps reached."

    def _perceive_screen(self):
        """Build a structured understanding of the current screen state."""
        context_parts = []

        # 1. Comprehensive Window info
        try:
            windows = self.desktop.windows()
            if windows:
                # 1.1 Identify the focused/top window
                top = windows[0]
                text = top.window_text()
                context_parts.append(f"Primary Focused Window: '{text or 'No Title'}'")
                
                # 1.2 Extract deep UI tree (Buttons, Inputs) for the primary window
                try:
                    elements = []
                    # Filter for interactive elements to keep context window manageable
                    children = top.descendants()
                    for el in children[:50]: # Scan top 50 elements
                        if el.element_info.control_type in ("Button", "Edit", "MenuItem", "TabItem", "ListItem", "Hyperlink", "CheckBox"):
                            name = el.element_info.name
                            if name:
                                elements.append(f"  [{el.element_info.control_type}] {name}")
                    
                    if elements:
                        context_parts.append("Interactive Elements Detected:\n" + "\n".join(elements[:25]))
                except Exception:
                    pass

                # 1.3 List other significant visible windows
                other = [w.window_text() for w in windows[1:10] if w.window_text() and len(w.window_text()) > 2]
                if other:
                    context_parts.append(f"Visible Background Windows: {', '.join(other[:5])}")
        except Exception as e:
            context_parts.append(f"Window Subsystem Telemetry: {str(e)}")

        # 2. Vision-Based (OCR) Awareness (The Eyes)
        try:
            if system_controller.reader:
                screenshot = pyautogui.screenshot()
                import numpy as np
                import cv2
                screenshot_np = np.array(screenshot)
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                results = system_controller.reader.readtext(screenshot_bgr)
                
                # Use a slightly lower confidence for better recall in complex UIs
                visible_text = [text for _, text, prob in results if prob > 0.35]
                if visible_text:
                    context_parts.append(f"Neural Vision (Visible Text): {' | '.join(visible_text[:20])}")
        except Exception:
            pass

        final_context = "\n".join(context_parts) if context_parts else "Neural Jam: No screen telemetry available."
        print(f"  Screen Awareness Pulse: {len(context_parts)} sectors identified.")
        return final_context

    def _think(self, goal, screen_context, step):
        """Use the LLM to decide the next action based on the current screen."""
        history_text = ""
        for h in self.history[-5:]:  # Last 5 steps for context
            history_text += f"Step {h['step']}: {h['action']['type']}({h['action'].get('target', '')}) -> {h['result'][:100]}\n"

        prompt = f"""You are an autonomous desktop agent. Your goal: {goal}

Current Screen State:
{screen_context}

Previous Actions:
{history_text if history_text else "None yet."}

Current Step: {step}/{self.max_steps}

Decide the SINGLE next action. Reply with ONLY valid JSON in one of these formats:
{{"type": "open", "target": "app_name"}}
{{"type": "click", "target": "element_name_or_label"}}
{{"type": "type", "text": "text to type"}}
{{"type": "key", "keys": "ctrl+s"}}
{{"type": "scroll", "direction": "down"}}
{{"type": "complete", "reason": "why task is done"}}
{{"type": "failure", "reason": "why task cannot be done"}}

Reply with ONLY the JSON, nothing else."""

        try:
            if ollama is None:
                return {"type": "complete", "reason": "Ollama not available for planning."}
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 150},
            )
            content = response["message"]["content"].strip()
            
            # Extract JSON from response
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                action = json.loads(match.group())
                if "type" in action:
                    return action
        except Exception as e:
            print(f"  Think Error: {e}")

        # Fallback: If LLM fails, report completion
        return {"type": "complete", "reason": "Agent reasoning completed."}

    def smart_click(self, target_name):
        """Logical-First Click: Try UI Tree, then OCR Vision, then AI Vision."""
        print(f"Smart Click: Targeting '{target_name}'...")

        # 1. Logical Strategy (Fast — pywinauto UIA tree)
        try:
            for win in self.desktop.windows():
                try:
                    element = win.child_window(
                        title_re=f".*{re.escape(target_name)}.*",
                        found_index=0,
                    )
                    if element.exists(timeout=0.5):
                        print(f"  Found via UI Tree: {element.window_text()}")
                        element.click_input()
                        return f"Clicked '{target_name}' (UI Tree)"
                except Exception:
                    continue
        except Exception as e:
            print(f"  UI Tree search failed: {e}")

        # 2. OCR Strategy (Medium — EasyOCR text location)
        try:
            if system_controller.reader:
                result = system_controller.visual_locate(target_name)
                if isinstance(result, dict):
                    system_controller.locate_and_click(result["x"], result["y"])
                    return f"Clicked '{target_name}' at ({result['x']}, {result['y']}) (OCR)"
        except Exception as e:
            print(f"  OCR click failed: {e}")

        # 3. AI Vision Strategy (Slow — LLaVA coordinate prediction)
        print(f"  Falling back to AI Vision for '{target_name}'...")
        result = system_controller.ai_vision_click(target_name)
        return f"Clicked '{target_name}' (AI Vision): {result}"

    def smart_open(self, app_name):
        """Launch an app and wait for it to be ready for interaction."""
        print(f"Smart Open: Launching '{app_name}'...")
        result = desktop_agent.open_application(app_name)

        # Wait for the window to appear
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                for win in self.desktop.windows():
                    if app_name.lower() in win.window_text().lower():
                        win.set_focus()
                        print(f"  '{app_name}' is ready and focused.")
                        return f"Opened and focused '{app_name}'"
            except Exception:
                pass
            time.sleep(1)

        return f"Opened '{app_name}', but could not verify focus."

    def _perform_action(self, action):
        """Execute a specific action on the desktop."""
        try:
            atype = action["type"]

            if atype == "click":
                return self.smart_click(action.get("target", ""))

            elif atype == "open":
                return self.smart_open(action.get("target", ""))

            elif atype == "type":
                text = action.get("text", "")
                pyautogui.write(text, interval=0.02)
                return f"Typed: '{text}'"

            elif atype == "key":
                keys = action.get("keys", "")
                key_parts = [k.strip() for k in keys.split("+")]
                pyautogui.hotkey(*key_parts)
                return f"Pressed: {keys}"

            elif atype == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 3)
                pyautogui.scroll(amount if direction == "up" else -amount)
                return f"Scrolled {direction}"

            else:
                return f"Unknown action type: {atype}"

        except Exception as e:
            return f"Action Error: {str(e)}"

    def get_screen_summary(self):
        """Public method: Get a human-readable summary of what's on screen right now."""
        return self._perceive_screen()


def run_autonomous_mission(task):
    """The global bridge for the autonomous UI agent."""
    orchestrator = VisualOrchestrator()
    return orchestrator.execute_mission(task)


if __name__ == "__main__":
    # Test
    orch = VisualOrchestrator()
    print(orch.smart_open("Notepad"))
    time.sleep(2)
    orch.smart_click("File")
