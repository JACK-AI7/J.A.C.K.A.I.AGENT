#!/usr/bin/env python
"""
BrowserOnlyAgent - The Ultimate Browser Automation Agent

Operates EXCLUSIVELY within your signed-in Chrome browser.
- Uses Playwright with Chrome user profile (preserves cookies/logins)
- Full screen viewing (screenshot → PIL Image)
- Humanized mouse movement, clicking, scrolling, typing
- Full DOM access (selectors, fills, clicks)
- Real-time HUD dashboard signals
- Built-in workflows: YouTube search+play, Gmail open, etc.

No desktop app interference. Only web.
"""

import sys
import os
import time
import random
import base64
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import pyautogui  # for screen size only; control via Playwright

try:
    from core.nexus_bridge import get_signals
    SIGNALS = get_signals()
except:
    SIGNALS = None

try:
    # Use the WebNavigator singleton (already configured for Chrome profile)
    from agents.web_navigator import web_navigator
    WEB_NAV_AVAILABLE = True
except ImportError:
    WEB_NAV_AVAILABLE = False


class BrowserOnlyAgent:
    """Agent that controls only the Chrome browser with full humanized interaction."""
    
    def __init__(self):
        self.headless = False
        self._page = None
        self._ready = False
        
        # Signals for HUD
        self.signals = SIGNALS
        
        print("BrowserOnlyAgent initialized. Use Chrome (logged-in).")
    
    def _emit_status(self, status, msg):
        if self.signals:
            try:
                self.signals.emit_bridge("agent_status", "BrowserAgent", status, msg)
            except: pass
    
    def _emit_action(self, action, detail):
        if self.signals:
            try:
                self.signals.emit_bridge("agent_action", "BrowserAgent", action, detail)
            except: pass
    
    # ==================== INITIALIZATION ====================
    def start(self):
        """Start/connect to the browser session."""
        if not WEB_NAV_AVAILABLE:
            return "ERROR: WebNavigator not available"
        
        # Reset WebNavigator if needed
        try:
            web_navigator.headless = self.headless
            # Force fresh connection
            if web_navigator.page is None:
                web_navigator._ensure_driver()
            self._page = web_navigator.page
            self._ready = True
            self._emit_status("ACTIVE", "Browser session active")
            return "Browser session started (logged-in Chrome)"
        except Exception as e:
            return f"Failed to start browser: {e}"
    
    def stop(self):
        """Close browser session."""
        try:
            web_navigator.close()
            self._ready = False
            self._emit_status("SHUTDOWN", "Browser closed")
            return "Browser closed"
        except Exception as e:
            return f"Close error: {e}"
    
    # ==================== SCREEN VIEWING ====================
    def view_screen(self, as_image=True):
        """
        Capture current browser viewport.
        Returns: PIL Image if as_image=True, else raw bytes
        """
        if not self._ready or not self._page:
            return None
        
        try:
            # Screenshot as bytes
            screenshot_bytes = self._page.screenshot(full_page=False)
            if as_image:
                img = Image.open(BytesIO(screenshot_bytes))
                return img
            return screenshot_bytes
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def view_and_save(self, path="browser_view.png"):
        """Save viewport screenshot to file."""
        img = self.view_screen()
        if img:
            img.save(path)
            return f"Saved: {path}"
        return "Screenshot failed"
    
    # ==================== MOUSE CONTROL ====================
    def move_mouse(self, x, y, steps=20):
        """
        Move mouse to (x,y) within viewport using humanized curve.
        x,y are viewport coordinates (0-1920, 0-1080)
        """
        if not self._ready:
            return "Browser not started"
        try:
            self._page.mouse.move(x, y, steps=steps)
            self._emit_action("MOVE", f"({x},{y})")
            time.sleep(random.uniform(0.05, 0.15))
            return f"Moved to ({x},{y})"
        except Exception as e:
            return f"Move failed: {e}"
    
    def click(self, x=None, y=None, button='left', double=False):
        """
        Click at coordinates. If no coords: click current position.
        Uses Playwright's mouse with smooth movement.
        """
        if not self._ready:
            return "Browser not started"
        try:
            if x is not None and y is not None:
                self.move_mouse(x, y)
                time.sleep(0.2)
            
            if double:
                self._page.mouse.dblclick(x, y)
                act = f"Double-click at ({x},{y})"
            else:
                self._page.mouse.click(x, y, button=button)
                act = f"Click {button} at ({x},{y})"
            
            self._emit_action("CLICK", act)
            return act
        except Exception as e:
            return f"Click error: {e}"
    
    def right_click(self, x=None, y=None):
        return self.click(x, y, button='right')
    
    def drag(self, start_x, start_y, end_x, end_y, button='left'):
        """Drag from start to end."""
        if not self._ready:
            return "Not started"
        try:
            self.move_mouse(start_x, start_y)
            self._page.mouse.down(button=button)
            time.sleep(random.uniform(0.1, 0.3))
            self._page.mouse.move(end_x, end_y, steps=30)
            self._page.mouse.up(button=button)
            self._emit_action("DRAG", f"({start_x},{start_y}) -> ({end_x},{end_y})")
            return f"Dragged to ({end_x},{end_y})"
        except Exception as e:
            return f"Drag error: {e}"
    
    # ==================== SCROLL ====================
    def scroll(self, direction='down', amount=5):
        """
        Scroll viewport using mouse wheel.
        direction: 'up' | 'down'
        amount: number of notches
        """
        if not self._ready:
            return "Browser not started"
        try:
            delta = 120 * (1 if direction == 'up' else -1)
            for _ in range(amount):
                self._page.mouse.wheel(0, delta)
                time.sleep(random.uniform(0.05, 0.12))
            self._emit_action("SCROLL", f"{direction} x{amount}")
            return f"Scrolled {direction} x{amount}"
        except Exception as e:
            return f"Scroll error: {e}"
    
    # ==================== KEYBOARD ====================
    def type_text(self, text, humanized=True):
        """
        Type text into focused element.
        Uses humanized delay: 50-150ms per character.
        """
        if not self._ready:
            return "Browser not started"
        try:
            if humanized:
                for char in text:
                    # Random small delay
                    time.sleep(random.uniform(0.05, 0.12))
                    self._page.keyboard.press(char)
            else:
                self._page.keyboard.type(text)
            self._emit_action("TYPE", text[:30])
            return f"Typed: {text[:50]}"
        except Exception as e:
            return f"Type error: {e}"
    
    def press_key(self, key):
        """Press a single key (Enter, Space, Tab, Escape, etc.)."""
        if not self._ready:
            return "Browser not started"
        try:
            self._page.keyboard.press(key)
            self._emit_action("KEY", key)
            return f"Pressed {key}"
        except Exception as e:
            return f"Key press error: {e}"
    
    def hotkey(self, *keys):
        """Press hotkey combination (Ctrl, Alt, Shift, Meta)."""
        if not self._ready:
            return "Browser not started"
        try:
            for k in keys:
                self._page.keyboard.down(k)
            time.sleep(0.1)
            for k in reversed(keys):
                self._page.keyboard.up(k)
            self._emit_action("HOTKEY", '+'.join(keys))
            return f"Hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Hotkey error: {e}"
    
    # ==================== DOM AUTOMATION ====================
    def navigate(self, url):
        """Navigate browser to URL (uses WebNavigator)."""
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator not available"
        return web_navigator.navigate(url)
    
    def click_element(self, text=None, selector=None):
        """Click an element by visible text or CSS selector."""
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator not available"
        return web_navigator.click_element(text=text, selector=selector)
    
    def fill_input(self, text, selector=None, name=None):
        """Fill an input field."""
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator not available"
        return web_navigator.fill_input(text, selector=selector, name=name)
    
    def get_dom_map(self, max_elements=30):
        """Get a summary of interactive elements on current page."""
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator not available"
        return web_navigator.get_dom_elements(max_elements=max_elements)
    
    # ==================== WORKFLOWS ====================
    def open_youtube(self):
        """Open YouTube (reuses logged-in session)."""
        return self.navigate("youtube")
    
    def search_and_play(self, query):
        """
        Search YouTube for query and play first video.
        Returns dict with status and steps.
        """
        steps = []
        
        # 1. Ensure on YouTube
        if "youtube.com" not in self._page.url.lower():
            steps.append("Navigating to YouTube...")
            self.navigate("https://www.youtube.com")
            time.sleep(3)
        
        # 2. Focus search box and type query with humanized delays
        try:
            # Clear any existing? focus first
            self._page.click("input[name='search_query']")
            time.sleep(0.3)
            steps.append(f"Typing: '{query}'")
            for char in query:
                self._page.keyboard.press(char)
                time.sleep(random.uniform(0.08, 0.15))
            self._page.keyboard.press("Enter")
            steps.append("Search executed")
            time.sleep(3)
        except Exception as e:
            return {'success': False, 'steps': steps + [f"Search error: {e}"]}
        
        # 3. Scroll down a bit (optional scroll demo)
        steps.append("Scrolling down results...")
        for _ in range(5):
            self._page.mouse.wheel(0, 120)
            time.sleep(0.15)
        time.sleep(1)
        
        # 4. Find & click first video
        try:
            # Wait for video links
            self._page.wait_for_selector("a[href*='/watch']", timeout=10000)
            first = self._page.locator("a[href*='/watch']").first
            
            # Ensure element is in view
            try:
                first.scroll_into_view_if_needed(timeout=3000)
                time.sleep(0.5)
            except: pass
            
            box = first.bounding_box()
            if box and box.get('width',0)>0 and box.get('height',0)>0:
                cx = box['x'] + box['width']/2
                cy = box['y'] + box['height']/2
                steps.append(f"First video at viewport ({cx:.0f},{cy:.0f})")
                self._page.mouse.move(cx, cy, steps=25)
                time.sleep(0.3)
                self._page.mouse.click(cx, cy)
                steps.append("Clicked first video via mouse")
                time.sleep(4)
            else:
                # Fallback: direct click
                first.click()
                steps.append("Clicked first video via DOM click")
                time.sleep(4)
        except Exception as e:
            return {'success': False, 'steps': steps + [f"Click error: {e}"]}
        
        # 5. Verify playback
        try:
            t0 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            if t0 < 1.0:
                # Maybe paused - try space
                self._page.keyboard.press("Space")
                time.sleep(2)
                t0 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            time.sleep(3)
            t1 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            advancing = t1 > t0 + 2.0
            steps.append(f"Time: {t0:.1f}s -> {t1:.1f}s")
        except Exception as e:
            steps.append(f"Verify error: {e}")
            advancing = False
        
        steps.append(f"Result: {'SUCCESS' if advancing else 'FAIL'}")
        return {'success': advancing, 'steps': steps}
    
    def open_gmail(self):
        """Open Gmail in new tab."""
        return self.navigate("gmail")
    
    def compose_email(self, to_addr, subject, body):
        """
        Open Gmail compose window with fields filled.
        Assumes Gmail is already open.
        """
        try:
            # Click compose
            self._page.click("div.T-I.T-I-KE.L3", timeout=5000)
            time.sleep(1)
            # Fill fields
            self._page.fill("input[aria-label='To field']", to_addr)
            self._page.fill("input[aria-label='Subject']", subject)
            # Body: switch to iframe?
            # For simplicity: just type after focusing body
            body_frame = self._page.frame_locator("iframe[aria-label='Rich Text Editor']")
            body_frame.locator("div[role='textbox']").click()
            self.type_text(body)
            return "Compose window filled"
        except Exception as e:
            return f"Compose error: {e}"
    
    # ==================== STATUS ====================
    def get_status(self):
        if not self._ready:
            return {'agent': 'BrowserOnlyAgent', 'status': 'OFFLINE', 'url': None}
        return {
            'agent': 'BrowserOnlyAgent',
            'status': 'ACTIVE',
            'url': self._page.url,
            'title': self._page.title(),
            'viewport': f"{self._page.viewport_size}"
        }


# ==================== QUICK DEMO ====================
def demo_browser_agent():
    print("\n" + "="*70)
    print("BROWSER-ONLY AGENT DEMO")
    print("Operates exclusively within your signed-in Chrome")
    print("="*70)
    
    agent = BrowserOnlyAgent()
    
    print("\n[1] Starting browser session...")
    print(agent.start())
    time.sleep(2)
    
    print("\n[2] Viewing screen...")
    img = agent.view_screen()
    if img:
        print(f"  Screenshot: {img.size} {img.mode}")
        agent.view_and_save("demo_view.png")
        print("  Saved: demo_view.png")
    else:
        print("  No screenshot")
    
    print("\n[3] Testing mouse movement...")
    print(agent.move_mouse(960, 540, steps=15))
    
    print("\n[4] Testing scroll...")
    print(agent.scroll('down', 5))
    
    print("\n[5] YouTube search & play 'munna bhaai gaming'...")
    result = agent.search_and_play("munna bhaai gaming")
    print(f"  Success: {result['success']}")
    for step in result['steps']:
        print(f"    {step}")
    
    print("\n[6] Agent status:")
    st = agent.get_status()
    # Safe ASCII-only print
    print(f"  agent={st['agent']} status={st['status']} viewport={st['viewport']}")
    
    print("\n[7] Closing browser...")
    print(agent.stop())
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    return result['success']


if __name__ == "__main__":
    ok = demo_browser_agent()
    sys.exit(0 if ok else 1)
