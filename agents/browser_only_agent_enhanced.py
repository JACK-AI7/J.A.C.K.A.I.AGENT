#!/usr/bin/env python
"""
Enhanced BrowserOnlyAgent - Ultimate Browser Automation
- Connects to existing Chrome (CDP) OR launches new session
- Shows real cursor movement (brings window to front)
- Auto-skips YouTube ads
- Can integrate antigravity-awesome-skills
- Humanized mouse, keyboard, scroll
- Full DOM control
"""

import sys, os, time, random, subprocess, json, importlib.util
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import pyautogui

try:
    from core.nexus_bridge import get_signals
    SIGNALS = get_signals()
except:
    SIGNALS = None

try:
    from agents.web_navigator import web_navigator
    WEB_NAV_AVAILABLE = True
except:
    WEB_NAV_AVAILABLE = False


class BrowserOnlyAgent:
    """Best browser-only agent: works with your logged-in Chrome, shows cursor, skips ads."""
    
    def __init__(self):
        self._page = None
        self._ready = False
        self._persistent = False
        self._using_cdp = False
        self.signals = SIGNALS
        self._skills = {}
        print("[BrowserOnlyAgent] Initialized")
    
    def _emit(self, status, msg):
        if self.signals:
            try: self.signals.emit_bridge("agent_status", "BrowserAgent", status, msg)
            except: pass
    
    def _action(self, act, detail):
        if self.signals:
            try: self.signals.emit_bridge("agent_action", "BrowserAgent", act, detail)
            except: pass
    
    # ==================== START / CONNECT ====================
    def start(self, use_existing_chrome=True):
        """
        Start browser session.
        - use_existing_chrome=True: attach to running Chrome via CDP (preserves your window)
        - False: launch new Playwright-controlled Chrome (may close existing profile)
        """
        if not WEB_NAV_AVAILABLE:
            return "ERROR: WebNavigator not available"
        
        try:
            wn = web_navigator
            wn.headless = False
            
            if use_existing_chrome:
                # Attempt CDP connect to already-running Chrome
                success = self._connect_via_cdp()
                if success:
                    self._page = wn.page
                    self._ready = True
                    self._using_cdp = True
                    self._emit("ACTIVE", "Connected to existing Chrome (CDP)")
                    return "Connected to existing Chrome (CDP)"
                else:
                    # Fallback to launch with persistent profile
                    print("[WARN] CDP connect failed, falling back to persistent launch")
                    wn.close()  # close any partial
                    wn._ensure_driver()  # this uses persistent context now
                    self._page = wn.page
                    self._ready = True
                    self._persistent = True
                    self._emit("ACTIVE", "Launched Chrome with profile")
                    return "Launched Chrome (profile-based)"
            else:
                wn.close()
                wn._ensure_driver()
                self._page = wn.page
                self._ready = True
                self._persistent = False
                self._emit("ACTIVE", "New Chrome session")
                return "New Chrome session started"
        except Exception as e:
            return f"Start failed: {e}"
    
    def _connect_via_cdp(self):
        """Attach to already-running Chrome via CDP (requires Chrome started with remote debugging)."""
        # Try default Chrome debugging port
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            # Connect to existing Chrome
            browser = pw.chromium.connect_over_cdp("http://localhost:9222")
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                if pages:
                    self._page = pages[0]
                    # Keep references to close later
                    self._pw = pw
                    self._browser = browser
                    self._context = context
                    return True
            # If no pages, close and fallback
            pw.stop()
        except Exception as e:
            print(f"CDP connect error: {e}")
        return False
    
    def stop(self):
        """Close browser (or disconnect CDP)."""
        try:
            if self._using_cdp:
                # CDP: just close context, keep Chrome running
                if hasattr(self, '_context') and self._context:
                    self._context.close()
                if hasattr(self, '_pw') and self._pw:
                    self._pw.stop()
                msg = "Disconnected from existing Chrome (Chrome still running)"
            else:
                web_navigator.close()
                msg = "Browser closed"
            self._ready = False
            self._emit("SHUTDOWN", "Browser stopped")
            return msg
        except Exception as e:
            return f"Stop error: {e}"
    
    # ==================== SCREEN VIEW ====================
    def view_screen(self):
        """Capture viewport as PIL Image."""
        if not self._ready:
            return None
        try:
            bytes_data = self._page.screenshot(full_page=False)
            return Image.open(BytesIO(bytes_data))
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def view_and_save(self, path="view.png"):
        img = self.view_screen()
        if img:
            img.save(path)
            return f"Saved {path}"
        return "Capture failed"
    
    # ==================== BRING TO FRONT (makes cursor visible) ====================
    def bring_to_front(self):
        """Bring browser window to foreground so mouse movements are visible."""
        if not self._ready:
            return "Not ready"
        try:
            # Use Playwright to bring page to front
            self._page.bring_to_front()
            # Also try to focus via OS-level window bring-to-front using pywinauto if available
            try:
                from pywinauto import Desktop
                # Find window by title (page title)
                title = self._page.title()[:50]
                for win in Desktop(backend="uia").windows():
                    if title in win.window_text():
                        win.set_focus()
                        break
            except: pass
            return "Browser brought to front"
        except Exception as e:
            return f"BringToFront error: {e}"
    
    # ==================== MOUSE CONTROL ====================
    def move_mouse(self, x, y, steps=25, bring_front=True):
        """Move mouse smoothly to (x,y). Brings browser to front for visibility."""
        if not self._ready:
            return "Not ready"
        try:
            if bring_front:
                self.bring_to_front()
                time.sleep(0.2)
            self._page.mouse.move(x, y, steps=steps)
            self._action("MOVE", f"({x},{y})")
            time.sleep(random.uniform(0.05, 0.12))
            return f"Moved to ({x},{y})"
        except Exception as e:
            return f"Move error: {e}"
    
    def click(self, x=None, y=None, button='left', double=False):
        """Click at coordinates. Moves mouse visibly."""
        if not self._ready:
            return "Not ready"
        try:
            if x is not None and y is not None:
                self.move_mouse(x, y)
                time.sleep(0.2)
            if double:
                self._page.mouse.dblclick(x, y)
                act = f"dblclick ({x},{y})"
            else:
                self._page.mouse.click(x, y, button=button)
                act = f"click {button} ({x},{y})"
            self._action("CLICK", act)
            return act
        except Exception as e:
            return f"Click error: {e}"
    
    def right_click(self, x=None, y=None):
        return self.click(x, y, button='right')
    
    def drag(self, start_x, start_y, end_x, end_y):
        """Drag from start to end (humanized)."""
        if not self._ready:
            return "Not ready"
        try:
            self.move_mouse(start_x, start_y)
            self._page.mouse.down()
            time.sleep(random.uniform(0.1, 0.3))
            self._page.mouse.move(end_x, end_y, steps=30)
            self._page.mouse.up()
            self._action("DRAG", f"({start_x},{start_y})->({end_x},{end_y})")
            return f"Dragged to ({end_x},{end_y})"
        except Exception as e:
            return f"Drag error: {e}"
    
    # ==================== SCROLL ====================
    def scroll(self, direction='down', amount=5):
        """Scroll using mouse wheel OR keyboard page up/down for smoother visible scrolling."""
        if not self._ready:
            return "Not ready"
        try:
            # First try to bring page to front so scroll is visible
            self.bring_to_front()
            time.sleep(0.1)
            if direction == 'down':
                key = 'PageDown' if random.random() < 0.5 else None
                delta = -120
            else:
                key = 'PageUp' if random.random() < 0.5 else None
                delta = 120
            # Mix: sometimes use mouse wheel, sometimes keyboard
            if key:
                for _ in range(amount):
                    self._page.keyboard.press(key)
                    time.sleep(random.uniform(0.1, 0.2))
            else:
                for _ in range(amount):
                    self._page.mouse.wheel(0, delta)
                    time.sleep(random.uniform(0.05, 0.12))
            self._action("SCROLL", f"{direction} x{amount}")
            return f"Scrolled {direction} x{amount}"
        except Exception as e:
            return f"Scroll error: {e}"
    
    # ==================== KEYBOARD ====================
    def type_text(self, text, humanized=True):
        """Type with human-like delays (50-150ms per char)."""
        if not self._ready:
            return "Not ready"
        try:
            self.bring_to_front()
            time.sleep(0.1)
            for char in text:
                delay = random.uniform(0.05, 0.12) if humanized else 0
                time.sleep(delay)
                self._page.keyboard.press(char)
            self._action("TYPE", text[:30])
            return f"Typed: {text[:50]}"
        except Exception as e:
            return f"Type error: {e}"
    
    def press_key(self, key):
        if not self._ready: return "Not ready"
        try:
            self._page.keyboard.press(key)
            self._action("KEY", key)
            return f"Pressed {key}"
        except Exception as e:
            return f"Key error: {e}"
    
    def hotkey(self, *keys):
        if not self._ready: return "Not ready"
        try:
            for k in keys:
                self._page.keyboard.down(k)
            time.sleep(0.1)
            for k in reversed(keys):
                self._page.keyboard.up(k)
            self._action("HOTKEY", '+'.join(keys))
            return f"Hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Hotkey error: {e}"
    
    # ==================== DOM HELPERS ====================
    def navigate(self, url):
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator unavailable"
        return web_navigator.navigate(url)
    
    def click_element(self, text=None, selector=None):
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator unavailable"
        return web_navigator.click_element(text=text, selector=selector)
    
    def fill_input(self, text, selector=None, name=None):
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator unavailable"
        return web_navigator.fill_input(text, selector=selector, name=name)
    
    def get_dom_map(self, max_elements=30):
        if not WEB_NAV_AVAILABLE:
            return "WebNavigator unavailable"
        return web_navigator.get_dom_elements(max_elements=max_elements)
    
    # ==================== YOUTUBE AD SKIP ====================
    def skip_youtube_ads(self):
        """
        Detect and skip YouTube ads.
        Looks for skip button, ad badge, or ad progress bar.
        Returns action taken.
        """
        if not self._ready:
            return "Not ready"
        try:
            # Check for skip button (text: "Skip Ad", "Skip")
            skip_selectors = [
                "button:has-text('Skip')",
                "button:has-text('Skip Ad')",
                "ytd-button-renderer:has-text('Skip')",
                "ytd-engagement-panel-section-list-renderer button",
            ]
            for sel in skip_selectors:
                try:
                    el = self._page.locator(sel).first
                    if el.is_visible():
                        el.click()
                        self._action("AD_SKIP", "Skipped YouTube ad")
                        return "Skipped ad via button"
                except: pass
            
            # Check for "Ad" badge on video player (often top-right)
            try:
                ad_badge = self._page.locator("text=Ad").first
                if ad_badge.is_visible():
                    # Sometimes pressing Escape or moving mouse away dismisses
                    self._page.keyboard.press("Escape")
                    time.sleep(0.5)
                    self._action("AD_SKIP", "Dismissed ad badge")
                    return "Dismissed ad via Escape"
            except: pass
            
            return "No ads detected"
        except Exception as e:
            return f"Ad skip error: {e}"
    
    # ==================== WORKFLOWS ====================
    def open_youtube(self):
        return self.navigate("youtube")
    
    def search_and_play(self, query, skip_ads=True):
        """
        Search YouTube and play first video.
        - skip_ads: periodically check and skip ads during playback
        Returns dict with steps and success.
        """
        steps = []
        # Ensure on YouTube
        if "youtube.com" not in self._page.url.lower():
            steps.append("Navigate to YouTube")
            self.navigate("https://www.youtube.com")
            time.sleep(3)
        
        # Focus search and type
        try:
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
        
        # Scroll a bit (to simulate human browsing)
        steps.append("Scroll down results")
        for _ in range(5):
            self._page.mouse.wheel(0, 120)
            time.sleep(0.15)
        time.sleep(1)
        
        # Find and click first video
        try:
            self._page.wait_for_selector("a[href*='/watch']", timeout=10000)
            first = self._page.locator("a[href*='/watch']").first
            try:
                first.scroll_into_view_if_needed(timeout=3000)
                time.sleep(0.5)
            except: pass
            box = first.bounding_box()
            if box and box.get('width',0)>0 and box.get('height',0)>0:
                cx = box['x'] + box['width']/2
                cy = box['y'] + box['height']/2
                steps.append(f"Video at ({cx:.0f},{cy:.0f})")
                self._page.mouse.move(cx, cy, steps=25)
                time.sleep(0.3)
                # Bring to front before click for visibility
                self.bring_to_front()
                time.sleep(0.1)
                self._page.mouse.click(cx, cy)
                steps.append("Clicked video")
                time.sleep(4)
            else:
                first.click()
                steps.append("Clicked via DOM")
                time.sleep(4)
        except Exception as e:
            return {'success': False, 'steps': steps + [f"Click error: {e}"]}
        
        # Ad skip loop (run a few times after navigation)
        if skip_ads:
            for _ in range(5):
                ad_res = self.skip_youtube_ads()
                if "Skipped" in ad_res or "Dismissed" in ad_res:
                    steps.append(f"Ad skip: {ad_res}")
                    time.sleep(1)
                else:
                    break
        
        # Verify playback
        try:
            t0 = self._page.evaluate("document.querySelector('#movie_player video').currentTime")
            if t0 < 1.0:
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
    
    # ==================== ANTIGRAVITY SKILLS ====================
    def install_antigravity_skills(self, skill_names=None, category="browser,web"):
        """
        Install and load skills from antigravity-awesome-skills repo.
        - skill_names: list of skill IDs/names to install; if None, installs all in category
        - category: comma-separated categories (browser,web,testing,etc.)
        Returns status string.
        """
        skills_dir = os.path.expanduser("~/.gemini/antigravity/skills")
        if not os.path.isdir(skills_dir):
            print("Installing antigravity-awesome-skills via npx...")
            subprocess.run(["npx", "antigravity-awesome-skills"], shell=True)
            time.sleep(3)
        if not os.path.isdir(skills_dir):
            return "Failed to install antigravity skills (dir missing)"
        
        index_path = os.path.join(skills_dir, "skills_index.json")
        if not os.path.exists(index_path):
            return "Skills index not found (install incomplete)"
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except Exception as e:
            return f"Failed to read skills index: {e}"
        
        selected = []
        for skill_id, info in index.get('skills', {}).items():
            cats = info.get('category', '').lower()
            if skill_names:
                if skill_id in skill_names or info.get('name') in skill_names:
                    selected.append((skill_id, info))
            else:
                if any(c.strip() in cats for c in category.split(',')):
                    selected.append((skill_id, info))
        
        # Register in agent
        for skill_id, info in selected:
            self._skills[skill_id] = info
        
        names = [s[0] for s in selected]
        return f"Loaded {len(selected)} antigravity skills. Categories: {category}"
    
    def use_skill(self, skill_id, *args, **kwargs):
        """Execute a loaded skill by ID."""
        if skill_id not in self._skills:
            return f"Skill {skill_id} not loaded. Install first."
        info = self._skills[skill_id]
        # For now: just indicate skill would be invoked
        # In full implementation, would import skill module and run its execute()
        return f"Skill '{skill_id}' invoked with args={args}, kwargs={kwargs}"
    
    # ==================== STATUS ====================
    def get_status(self):
        if not self._ready:
            return {'agent': 'BrowserOnlyAgent', 'status': 'OFFLINE'}
        return {
            'agent': 'BrowserOnlyAgent',
            'status': 'ACTIVE',
            'mode': 'CDP' if self._using_cdp else 'Playwright',
            'url': self._page.url,
            'title': self._page.title(),
            'viewport': self._page.viewport_size,
            'skills_loaded': len(self._skills)
        }


# ==================== DEMO ====================
def demo():
    print("\n" + "="*70)
    print("ENHANCED BrowserOnlyAgent DEMO")
    print(" - Connect to existing Chrome (CDP) with visible cursor")
    print(" -Skip YouTube ads")
    print(" - Antigravity skills ready")
    print("="*70)
    
    agent = BrowserOnlyAgent()
    
    # 1. Connect to existing Chrome
    print("\n[1] Connecting to existing Chrome (CDP)...")
    print(agent.start(use_existing_chrome=True))
    time.sleep(2)
    
    # 2. Bring to front and move mouse visibly
    print("\n[2] Moving mouse to center (bring to front)...")
    print(agent.move_mouse(960, 540, steps=30))
    time.sleep(0.5)
    
    # 3. Screenshot
    print("\n[3] Capturing viewport...")
    print(agent.view_and_save("enhanced_view.png"))
    
    # 4. Open YouTube and search
    print("\n[4] YouTube search & play 'munna bhaai gaming' with ad skip...")
    result = agent.search_and_play("munna bhaai gaming", skip_ads=True)
    print(f"  Success: {result['success']}")
    for s in result['steps'][-8:]:  # last few steps
        print(f"    {s}")
    
    # 5. Show antigravity skills (if installed)
    print("\n[5] Loading Antigravity Awesome Skills...")
    # Load a small set
    load_res = agent.install_antigravity_skill
    print(f"  {load_res}")
    
    # 6. Status
    print("\n[6] Agent status:")
    st = agent.get_status()
    for k, v in st.items():
        print(f"  {k}: {v}")
    
    # 7. Clean close (disconnect only)
    print("\n[7] Stopping agent...")
    print(agent.stop())
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    return result['success']


if __name__ == "__main__":
    ok = demo()
    sys.exit(0 if ok else 1)
