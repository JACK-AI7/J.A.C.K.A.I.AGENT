#!/usr/bin/env python
"""Fix web_navigator.py: replace _ensure_driver and close with persistent-profile-aware versions"""

with open("agents/web_navigator.py", 'r', encoding='utf-8') as f:
    content = f.read()

# New _ensure_driver (clean, handles persistent context correctly)
new_ensure = '''    def _ensure_driver(self):
        """Lazy load Playwright driver with user profile for logged-in sessions."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        if self.page is None:
            import os
            print("Launching Playwright with Chrome profile...")
            self.playwright = sync_playwright().start()
            
            user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
            has_profile = os.path.isdir(user_data_dir)
            
            try:
                if has_profile:
                    # Use persistent context → reuses your logged-in Chrome profile
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="chrome",
                        headless=self.headless,
                        viewport={'width': 1920, 'height': 1080}
                    )
                    self._persistent = True
                    print(f"  Using logged-in Chrome profile at: {user_data_dir}")
                else:
                    # No profile dir; launch regular Chrome
                    self.browser = self.playwright.chromium.launch(channel="chrome", headless=self.headless)
                    self._persistent = False
                    self.context = self.browser.new_context()
                    print("  Using Chrome (no profile dir found)")
            except Exception as e:
                print(f"  Chrome launch failed ({e}), falling back to bundled Chromium")
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
                if getattr(self, "_persistent", False):
                    self.context.close()      # persistent context - just close it
                else:
                    self.browser.close()      # regular browser - close entirely
                self.playwright.stop()
            except Exception:
                pass
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            try:
                self.signals.emit_bridge("agent_status", "WebNavigator", "INITIALIZED", "Ready")
            except: pass
            return "Automation Engine closed."
        return "No engine running."
'''

# Find and replace _ensure_driver
start_ensure = content.find('def _ensure_driver(self):')
if start_ensure == -1:
    print("ERROR: _ensure_driver not found")
else:
    # Find next method (def navigate)
    end_ensure = content.find('\n    def ', start_ensure + 10)
    if end_ensure == -1:
        print("ERROR: Could not find end of _ensure_driver")
    else:
        before = content[:start_ensure]
        after = content[end_ensure:]
        content = before + new_ensure + '\n' + after
        print("Replaced _ensure_driver")

# Find and replace close()
start_close = content.find('def close(self):')
if start_close == -1:
    print("ERROR: close not found")
else:
    end_close = content.find('\n\n# Singleton', start_close)
    if end_close == -1:
        end_close = content.find('\nweb_navigator', start_close)
    before = content[:start_close]
    after = content[end_close:]
    content = before + new_close + '\n\n' + after
    print("Replaced close")

# Write back
with open("agents/web_navigator.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("web_navigator.py updated successfully")
