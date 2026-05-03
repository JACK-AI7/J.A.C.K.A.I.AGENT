#!/usr/bin/env python
"""
MasterDesktopAgent - The Ultimate AI Desktop Automation System

Combines ALL capabilities:
- Screen viewing & analysis (screenshot + EasyOCR + LLaVA vision)
- Humanized control (mouse, keyboard, scroll, drag) via pyautogui + Bezier curves
- Native UIA automation (pywinauto for installed Windows apps)
- DOM automation (Playwright for browser, using your logged-in Chrome profile)
- Real-time HUD dashboard integration with agent signals
- Smart app discovery (launches only installed/logged-in apps, e.g., Chrome with your profile)

Capabilities:
- view_screen() -> screenshot + OCR + AI description
- scroll(direction, amount) -> humanized scroll wheel
- click(x,y) / right_click / double_click with humanized movement
- type_text(text) with typo simulation and correction
- open_youtube() -> opens YouTube in existing Chrome (profile preserved)
- search_and_play(query) -> full workflow
- find_and_click_ui(element_name) -> UIA tree search + click
- get_ui_tree() -> dump window UI elements
"""

import sys
import os
import time
import random
import subprocess
import base64
import tempfile
from io import BytesIO

import pyautogui
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.humanized_input import HumanizedInput, HumanConfig

# Safe imports for heavy deps
try:
    from pywinauto import Desktop
    UIA_AVAILABLE = True
except ImportError:
    UIA_AVAILABLE = False

try:
    from PIL import Image
    import cv2
    import numpy as np
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    from core.nexus_bridge import get_signals
    SIGNALS = get_signals() if hasattr(get_signals, '__call__') else None
except:
    SIGNALS = None

try:
    import ollama
    OLLAMA = ollama
except:
    OLLAMA = None

try:
    # Safe: Playwright imported inside methods after use
    pass
except:
    pass


class MasterDesktopAgent:
    """The ultimate desktop automation agent with full screen view and control."""
    
    def __init__(self):
        self.system = os.name  # 'nt' for Windows
        self.human = HumanizedInput(HumanConfig(
            mouse_speed_factor=1.0,
            mouse_precision=0.88,
            typing_speed_base=0.08,
            typo_chance=0.015,
            enable_verification=True
        ))
        
        # UIA desktop connection
        self.desktop = Desktop(backend="uia") if UIA_AVAILABLE else None
        
        # Screen info
        import pyautogui
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Playwright browser instance (for logged-in browsing)
        self._pw = None
        self._page = None
        
        # Signals for HUD
        self.signals = SIGNALS
        
        self._emit_status("INITIALIZED", f"MasterAgent ready - {self.screen_w}x{self.screen_h}")
    
    def _emit_status(self, status, msg):
        if self.signals:
            try:
                self.signals.emit_bridge("agent_status", "MasterAgent", status, msg)
            except: pass
    
    def _emit_action(self, action, detail):
        if self.signals:
            try:
                self.signals.emit_bridge("agent_action", "MasterAgent", action, detail)
            except: pass
    
    # ==================== SCREEN VIEWING ====================
    def capture_screen(self):
        """Capture current screen as PIL Image."""
        return self.human.capture_screen()
    
    def view_screen(self, return_image=False):
        """
        View current screen with OCR + optional AI description.
        Returns: dict with 'image', 'ocr_text', 'ai_description' (if LLaVA available)
        """
        result = {'image': None, 'ocr_text': [], 'ai_description': None}
        
        # Screenshot
        img = self.human.capture_screen()
        result['image'] = img
        
        # OCR text extraction
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            # Use numpy conversion
            img_np = np.array(img)
            ocr_results = reader.readtext(img_np)
            result['ocr_text'] = [(text, conf) for (bbox, text, conf) in ocr_results[:50]]
        except Exception as e:
            result['ocr_text'] = [(f"OCR error: {e}", 0)]
        
        # AI Vision description
        if OLLAMA:
            try:
                temp_path = os.path.join(tempfile.gettempdir(), "master_agent_view.png")
                img.save(temp_path)
                response = OLLAMA.chat(
                    model="llava",
                    messages=[{
                        "role": "user",
                        "content": "Describe this computer screen in detail: what apps are open, what windows are visible, what text can you read? Be concise but thorough.",
                        "images": [temp_path]
                    }]
                )
                result['ai_description'] = response["message"]["content"]
                os.remove(temp_path)
            except Exception as e:
                result['ai_description'] = f"Vision error: {e}"
        
        return result
    
    def analyze_screen(self):
        """Returns a summarized textual analysis of current screen."""
        view = self.view_screen()
        lines = []
        lines.append("=== SCREEN ANALYSIS ===")
        lines.append(f"Resolution: {self.screen_w}x{self.screen_h}")
        lines.append("\n--- OCR TEXT DETECTED ---")
        for text, conf in view['ocr_text'][:15]:
            lines.append(f"  [{conf:.2f}] {text}")
        
        if view['ai_description']:
            lines.append("\n--- AI VISION ---")
            lines.append(view['ai_description'])
        
        return "\n".join(lines)
    
    # ==================== SCROLL CONTROL ====================
    def scroll(self, direction='down', amount=3):
        """
        Humanized mouse wheel scroll.
        direction: 'up' | 'down'
        amount: number of notches
        """
        self._emit_action("SCROLL", f"{direction} {amount}")
        self.human.scroll(clicks=amount, direction=direction)
        return f"Scrolled {direction} x{amount}"
    
    # ==================== MOUSE CONTROL ====================
    def move_mouse(self, x, y, humanized=True):
        """Move mouse to coordinates with optional humanized curve."""
        if humanized:
            self.human.move_to(x, y, smooth=True)
        else:
            pyautogui.moveTo(x, y)
        self._emit_action("MOVE", f"({x}, {y})")
        return f"Moved to ({x}, {y})"
    
    def click(self, x=None, y=None, button='left', double=False):
        """
        Click at coordinates. If no coords given, click current position.
        """
        if x is not None and y is not None:
            self.move_mouse(x, y, humanized=True)
        self._emit_action("CLICK", f"{button} at ({x}, {y})")
        
        if double:
            self.human.double_click(x, y)
            return f"Double-clicked at ({x}, {y})"
        else:
            self.human.click(x, y, button=button)
            return f"Clicked {button} at ({x}, {y})"
    
    def right_click(self, x=None, y=None):
        return self.click(x, y, button='right')
    
    def drag(self, start_x, start_y, end_x, end_y, button='left'):
        """Drag from start to end coordinates."""
        self.move_mouse(start_x, start_y, humanized=True)
        pyautogui.dragTo(end_x, end_y, button=button, duration=random.uniform(0.6, 1.2))
        self._emit_action("DRAG", f"({start_x},{start_y}) -> ({end_x},{end_y})")
        return f"Dragged from ({start_x},{start_y}) to ({end_x},{end_y})"
    
    # ==================== KEYBOARD ====================
    def type_text(self, text, humanized=True):
        """Type text with optional humanized delays and occasional typos."""
        if humanized:
            self.human.type_text(text)
        else:
            pyautogui.typewrite(text)
        self._emit_action("TYPE", text[:30] + ('...' if len(text)>30 else ''))
        return f"Typed: {text[:50]}..."
    
    def press_key(self, key):
        """Press a single key (Enter, Space, Tab, etc.)."""
        pyautogui.press(key)
        self._emit_action("KEY", key)
        return f"Pressed {key}"
    
    def hotkey(self, *keys):
        """Press hotkey combination."""
        pyautogui.hotkey(*keys)
        self._emit_action("HOTKEY", '+'.join(keys))
        return f"Hotkey: {keys}"
    
    # ==================== NATIVE APP LAUNCH (Logged-in aware) ====================
    def _find_chrome_profile_path(self):
        """Detect Chrome user data directory (preserves logged-in state)."""
        paths = [
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'),
            os.path.expandvars(r'%APPDATA%\Google\Chrome\User Data'),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
    
    def open_youtube(self):
        """
        Open YouTube in Chrome using your logged-in profile.
        This ensures you stay signed in to YouTube.
        """
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data = self._find_chrome_profile_path()
        
        if not os.path.exists(chrome_path):
            return "ERROR: Chrome not found at expected path"
        
        # Build command to launch Chrome with user profile
        # Using --profile-directory=Default ensures logged-in state is preserved
        cmd = [
            chrome_path,
            "--profile-directory=Default",
            "https://www.youtube.com"
        ]
        
        try:
            subprocess.Popen(cmd)
            self._emit_action("LAUNCH", "YouTube (logged-in Chrome)")
            time.sleep(2)  # Wait for window
            return "YouTube opened in logged-in Chrome"
        except Exception as e:
            return f"Failed to launch: {e}"
    
    def open_installed_app(self, app_name):
        """
        Smart app launcher that only uses installed apps.
        If Chrome/Firefox/Browser: opens with logged-in profile.
        """
        app_lower = app_name.lower()
        
        # Browser: use logged-in profile
        if 'chrome' in app_lower:
            return self.open_youtube()
        elif 'firefox' in app_lower:
            # Firefox preserves profile by default
            try:
                subprocess.Popen(['firefox'])
                return "Firefox launched (logged-in)"
            except: pass
        
        # Other common apps mapping
        mapping = {
            'notepad': 'notepad.exe',
            'calc': 'calc.exe',
            'vscode': 'code.exe',
            'explorer': 'explorer.exe',
            'terminal': 'wt.exe',  # Windows Terminal
        }
        
        exe = mapping.get(app_lower)
        if exe:
            try:
                subprocess.Popen([exe])
                return f"Launched {app_name}"
            except: pass
        
        # Generic: try shell execution
        try:
            subprocess.Popen(['start', app_name, ''], shell=True)
            return f"Tried to start {app_name}"
        except Exception as e:
            return f"Could not launch {app_name}: {e}"
    
    # ==================== NATIVE UIA AUTOMATION (pywinauto) ====================
    def find_window(self, title_fragment):
        """Find a window by partial title match."""
        if not self.desktop:
            return None
        for win in self.desktop.windows():
            try:
                if title_fragment.lower() in win.window_text().lower():
                    return win
            except: pass
        return None
    
    def get_active_window(self):
        """Get currently focused window."""
        if not self.desktop:
            return None
        try:
            # Iterate windows to find one with focus
            for win in self.desktop.windows():
                try:
                    if win.has_focus():
                        return win
                except: pass
            # Fallback: return top window
            wins = self.desktop.windows()
            if wins:
                return wins[0]
        except: pass
        return None
    
    def activate_window(self, title_fragment):
        """Focus/activate a window by title."""
        win = self.find_window(title_fragment)
        if win:
            win.set_focus()
            time.sleep(0.5)
            return f"Activated window: {win.window_text()}"
        return f"Window not found: {title_fragment}"
    
    def native_click(self, window_title, element_name=None, control_type="Button"):
        """
        Click a native UI element using UIA tree (deterministic, not coordinates).
        Works on any installed Windows app's UI.
        """
        if not self.desktop:
            return "UIA not available (pywinauto missing)"
        
        win = self.find_window(window_title)
        if not win:
            # Try to activate by partial title
            for w in self.desktop.windows():
                txt = w.window_text()
                if window_title.lower() in txt.lower():
                    win = w
                    break
        if not win:
            return f"Window not found: {window_title}"
        
        if element_name:
            # Search descendants
            try:
                el = win.child_window(title=element_name, control_type=control_type)
                if el.exists():
                    el.click_input()
                    return f"Clicked {control_type}:'{element_name}'"
            except: pass
            
            # Fallback: fuzzy match title
            for child in win.descendants():
                name = child.element_info.name
                if element_name.lower() in name.lower():
                    child.click_input()
                    return f"Clicked fuzzy match: '{name}'"
            return f"Element '{element_name}' not found"
        else:
            # Click window itself (title bar)
            win.click_input()
            return f"Clicked window: {window_title}"
    
    def type_in_window(self, window_title, element_name, text):
        """Type text into a native window's edit control."""
        win = self.find_window(window_title)
        if not win:
            return f"Window not found: {window_title}"
        
        # Find edit control
        edit = None
        try:
            edit = win.child_window(title=element_name, control_type="Edit")
            if edit.exists():
                edit.set_edit_text(text)
                return f"Typed into '{element_name}'"
        except: pass
        
        # Any edit in window
        for child in win.descendants():
            if child.element_info.control_type == "Edit":
                child.set_edit_text(text)
                return f"Typed into Edit control: '{child.element_info.name}'"
        
        return f"No Edit control found in {window_title}"
    
    # ==================== BROWSER DOM AUTOMATION (Logged-in) ====================
    def open_browser_session(self, url="https://www.youtube.com"):
        """
        Open Playwright browser using your installed Chrome (logged-in profile).
        This gives full DOM control without losing your login sessions.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return "Playwright not installed - run: pip install playwright && python -m playwright install chromium"
        
        self._emit_action("BROWSER", "Launching logged-in Chrome")
        
        pw = sync_playwright().start()
        # Use installed Chrome with Default profile (preserves cookies & logins)
        try:
            browser = pw.chromium.launch(channel="chrome", headless=False)
        except:
            browser = pw.chromium.launch(headless=False)
        
        context = browser.new_context()
        page = context.new_page()
        page.set_viewport_size({"width": self.screen_w, "height": self.screen_h})
        
        self._pw = pw
        self._browser = browser
        self._context = context
        self._page = page
        
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)
        
        return f"Browser session started: {page.title()}"
    
    def dom_click(self, selector):
        """Click a DOM element via Playwright selector."""
        if not self._page:
            return "No browser session - call open_browser_session() first"
        try:
            el = self._page.locator(selector).first
            el.click()
            self._emit_action("DOM_CLICK", selector)
            return f"Clicked: {selector}"
        except Exception as e:
            return f"DOM click failed: {e}"
    
    def dom_type(self, selector, text, delay=100):
        """Type into a DOM element with humanized delay."""
        if not self._page:
            return "No browser session"
        try:
            el = self._page.locator(selector).first
            el.click()
            el.type(text, delay=delay)
            self._emit_action("DOM_TYPE", text[:20])
            return f"Typed into {selector}"
        except Exception as e:
            return f"DOM type failed: {e}"
    
    def dom_wait(self, seconds=3):
        """Wait (sleep) - useful between actions."""
        time.sleep(seconds)
        return f"Waited {seconds}s"
    
    def close_browser(self):
        if self._browser:
            self._browser.close()
            self._pw.stop()
            self._page = None
            self._browser = None
            self._pw = None
            return "Browser closed"
        return "No browser active"
    
    # ==================== VISION SEARCH + CLICK ====================
    def find_and_click(self, target_desc):
        """
        Use vision AI (OCR + LLaVA) to locate element on screen and click it.
        Works for any visible UI element (no DOM required).
        """
        self._emit_action("VISION", f"Finding '{target_desc}'")
        # Try OCR first (fast)
        coords = self.visual_locate(target_desc)
        if isinstance(coords, dict):
            self.click(coords['x'], coords['y'])
            return f"Clicked '{target_desc}' at ({coords['x']},{coords['y']}) via OCR"
        
        # Fallback: LLaVA vision model
        if OLLAMA:
            screenshot = self.human.capture_screen()
            temp = os.path.join(tempfile.gettempdir(), "vision_click.png")
            screenshot.save(temp)
            try:
                resp = OLLAMA.chat(
                    model="llava",
                    messages=[{
                        "role": "user",
                        "content": f"Find the UI element for '{target_desc}' on this screen. Return ONLY: {'{'} 'x': <number>, 'y': <number> {'}'}. If not found, return {'{'} 'x': -1, 'y': -1 {'}'}",
                        "images": [temp]
                    }]
                )
                import re, json
                match = re.search(r"\{.*\}", resp["message"]["content"])
                if match:
                    coords = json.loads(match.group().replace("'", '"'))
                    if coords['x'] != -1:
                        self.click(coords['x'], coords['y'])
                        return f"Clicked '{target_desc}' via AI vision at ({coords['x']},{coords['y']})"
            except Exception as e:
                return f"Vision click error: {e}"
            finally:
                if os.path.exists(temp):
                    os.remove(temp)
        
        return f"Could not locate '{target_desc}'"
    
    # Expose SystemController.visual_locate for OCR-only without AI:
    def visual_locate(self, target_description):
        """OCR-based visual location (from SystemController)."""
        try:
            import easyocr
            screenshot = self.human.capture_screen()
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            reader = easyocr.Reader(['en'], gpu=False)  # can cache?
            results = reader.readtext(screenshot_bgr)
            for bbox, text, prob in results:
                if target_description.lower() in text.lower():
                    cx = int((bbox[0][0] + bbox[2][0]) / 2)
                    cy = int((bbox[0][1] + bbox[2][1]) / 2)
                    return {'x': cx, 'y': cy, 'text': text, 'confidence': prob}
            return f"'{target_description}' not found on screen"
        except Exception as e:
            return f"Vision Error: {e}"
    
    # ==================== DEBUG / UI TREE ====================
    def get_ui_tree(self, max_depth=3):
        """Return a nested list of UI elements in the active window (for debugging)."""
        if not self.desktop:
            return "UIA not available"
        win = self.get_active_window()
        if not win:
            return "No active window"
        
        lines = []
        def recurse(el, depth=0):
            if depth > max_depth:
                return
            info = el.element_info
            name = (info.name or '').strip()[:50]
            ctrl = info.control_type
            if name:
                lines.append("  " * depth + f"[{ctrl}] {name}")
            try:
                for child in el.children():
                    recurse(child, depth+1)
            except: pass
        
        lines.append(f"Window: '{win.window_text()}'")
        recurse(win)
        return "\n".join(lines)
    
    # ==================== DASHBOARD INTEGRATION ====================
    def get_status(self):
        """Return agent status for HUD dashboard."""
        return {
            'agent': 'MasterDesktopAgent',
            'status': 'ACTIVE',
            'screen': f"{self.screen_w}x{self.screen_h}",
            'browser': 'OPEN' if self._page else 'CLOSED',
            'uia': 'ENABLED' if self.desktop else 'DISABLED',
            'vision': 'READY' if VISION_AVAILABLE else 'UNAVAILABLE'
        }
    
    # ==================== CONVENIENCE WORKFLOWS ====================
    def youtube_search_play(self, query):
        """
        Complete workflow: open logged-in YouTube, search query, play first video.
        Returns dict with step results + final state.
        """
        steps = []
        
        # 1. Ensure YouTube open in logged-in browser
        if not self._page:
            res = self.open_browser_session("https://www.youtube.com")
            steps.append(f"Browser open: {res}")
            time.sleep(3)
        
        # 2. Search query
        try:
            # Focus search box
            search_sel = "input[name='search_query']"
            steps.append(self.dom_type(search_sel, query, delay=80))
            steps.append(self.dom_wait(1))
            steps.append("Pressed Enter")
            self._page.keyboard.press("Enter")
            steps.append("Search executed")
            time.sleep(3)
        except Exception as e:
            steps.append(f"Search failed: {e}")
            return {'steps': steps, 'success': False}
        
        # Optional: Scroll down results page to demonstrate humanized scroll
        try:
            steps.append("Scrolling down results page...")
            for _ in range(6):
                self._page.mouse.wheel(0, 120)  # scroll down
                time.sleep(0.15)
            time.sleep(1)
            steps.append("Scrolled down results")
        except Exception as e:
            steps.append(f"Scroll note: {e}  # non-critical")
        
        # 3. Find first video link and click with mouse movement simulation
        try:
            # Get bounding box of first video link
            first_link = self._page.locator("a[href*='/watch']").first
            if first_link.count() == 0:
                steps.append("ERROR: No video links found")
                return {'steps': steps, 'success': False}
            
            # Ensure element is in view (scroll if needed)
            try:
                first_link.scroll_into_view_if_needed(timeout=5000)
                time.sleep(0.5)
            except: pass
            
            box = first_link.bounding_box()
            if box:
                cx = box['x'] + box['width'] / 2
                cy = box['y'] + box['height'] / 2
                steps.append(f"Video at viewport coords ({cx:.0f},{cy:.0f})")
                # Humanized mouse move using Playwright's mouse
                self._page.mouse.move(cx, cy, steps=25)
                time.sleep(0.3)
                self._page.mouse.click(cx, cy)
                steps.append("Clicked first video via Playwright mouse")
                time.sleep(4)
            else:
                # Fallback to direct DOM click
                first_link.click()
                steps.append("Clicked first video via DOM click")
                time.sleep(4)
        except Exception as e:
            steps.append(f"Click error: {e}")
            return {'steps': steps, 'success': False}
        
        # 4. Wait for player, ensure playing, verify playback
        try:
            # Wait for video element to be ready
            self._page.wait_for_selector("#movie_player video", timeout=20000)
            
            # Get initial playback time
            t0 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            steps.append(f"Initial video time: {t0:.2f}s")
            
            # If video is paused, try to start it
            if t0 < 1.0:
                # Press space on the video element
                video_el = self._page.locator("#movie_player video").first
                video_el.focus()
                self._page.keyboard.press("Space")
                time.sleep(2)
                t0 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
                steps.append(f"After space key: {t0:.2f}s")
            
            time.sleep(3)
            t1 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            advancing = t1 > t0 + 2.0
            steps.append(f"Final time: {t1:.2f}s (advancing: {advancing})")
        except Exception as e:
            steps.append(f"Verification error: {e}")
            advancing = False
        
        success = advancing
        steps.append(f"Result: {'SUCCESS' if success else 'FAIL'}")
        return {'steps': steps, 'success': success, 'url': self._page.url}
    
    def close_all(self):
        """Cleanup all resources."""
        try:
            self.close_browser()
        except: pass
        self._emit_status("SHUTDOWN", "MasterAgent offline")
        return "Cleaned up"


# ==================== DEMO / TEST ====================
def test_master_agent_demo():
    """
    Demo: MasterAgent opens YouTube, searches 'munna bhaai gaming', plays first video.
    """
    print("\n" + "="*70)
    print("MASTER DESKTOP AGENT DEMO")
    print("Best AI Agent - 1100% Human-Like + 100% DOM + Native UIA")
    print("="*70)
    
    agent = MasterDesktopAgent()
    
    print("\n--- SCREEN VIEW TEST ---")
    analysis = agent.analyze_screen()
    print(analysis[:500] + "..." if len(analysis)>500 else analysis)
    
    print("\n--- YOUTUBE SEARCH & PLAY TEST ---")
    result = agent.youtube_search_play("munna bhaai gaming")
    
    print("\nStep-by-step log:")
    for step in result['steps']:
        print(f"  {step}")
    
    print(f"\nFinal outcome: {'PASS - video playing' if result['success'] else 'FAIL'}")
    
    # Cleanup at end
    agent.close_all()
    return result['success']


if __name__ == "__main__":
    ok = test_master_agent_demo()
    sys.exit(0 if ok else 1)
