#!/usr/bin/env python
"""Replace _ensure_driver and close methods in web_navigator.py with clean versions"""

new_ensure_driver = '''    def _ensure_driver(self):
        """Lazy load the Playwright driver with user profile for logged-in state."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed. Run: pip install playwright && python -m playwright install chromium")
        if self.page is None:
            print(f"Launching Playwright with logged-in Chrome...")
            self.playwright = sync_playwright().start()
            
            # Locate Chrome user data directory (preserves login)
            import os
            user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data')
            has_profile = os.path.exists(user_data_dir) if user_data_dir else False
            
            try:
                if has_profile:
                    # Persistent context reuses your logged-in Chrome profile
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="chrome",
                        headless=self.headless,
                        viewport={'width': 1920, 'height': 1080}
                    )
                    self._persistent = True
                    print(f"  Using logged-in Chrome profile: {user_data_dir}")
                else:
                    # Fallback: launch regular Chrome
                    self.browser = self.playwright.chromium.launch(
                        channel="chrome",
                        headless=self.headless
                    )
                    self._persistent = False
                    self.context = self.browser.new_context()
                    print("  Using Chrome (no profile detected)")
            except Exception as e:
                print(f"  Chrome launch failed ({e}), using bundled Chromium")
                self.browser = self.playwright.chromium.launch(headless=self.headless)
                self._persistent = False
                self.context = self.browser.new_context()
                print("  Using bundled Chromium")
            
            self.page = self.context.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
'''

new_close = '''    def close(self):
        if self.playwright:
            print("Closing browser session...")
            try:
                if hasattr(self, '_persistent') and self._persistent:
                    # Persistent context: just close context (browser stays)
                    self.context.close()
                else:
                    # Regular browser: close browser
                    self.browser.close()
                self.playwright.stop()
            except Exception:
                pass
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            try:
                self.signals.emit_bridge("agent_status", "WebNavigator", "INITIALIZED", "Ready for next session")
            except: pass
            return "Automation Engine closed."
        return "No engine running."
'''

with open(r"agents/web_navigator.py", 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _ensure_driver method
old_ensure_start = content.find('def _ensure_driver(self):')
old_close_start = content.find('def close(self):')

if old_ensure_start == -1 or old_close_start == -1:
    print("ERROR: Could not find methods")
else:
    # Find method bodies by finding next 'def ' after start
    def_next_ensure = content.find('\n    def ', old_ensure_start + 10)
    def_next_close = content.find('\n    def ', old_close_start + 10)
    
    before_ensure = content[:old_ensure_start]
    after_ensure = content[def_next_ensure:]
    
    before_close = content[def_next_ensure:def_next_close]
    after_close = content[def_next_close:]
    
    # Insert new ensure
    new_content_before = before_ensure + new_ensure_driver + '\n' + before_close
    # Replace close
    new_content = new_content_before[:new_content_before.find('def close(self):')] + new_close + after_close
    
    with open("agents/web_navigator.py", 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced _ensure_driver and close methods successfully")
