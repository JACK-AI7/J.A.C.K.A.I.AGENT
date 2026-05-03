#!/usr/bin/env python
"""Precise replace of _ensure_driver and close in web_navigator.py"""

with open("agents/web_navigator.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 0-indexed
ensure_start = 37      # line 38
navigate_start = 83    # line 84 (method starts at line 83 index 82? let's double-check)
close_start = 279      # line 280

print(f"ensure_start index: {ensure_start}")
print(f"navigate_start index: {navigate_start}")
print(f"close_start index: {close_start}")

# Verify by printing those lines
print("ensure line:", lines[ensure_start].rstrip())
print("navigate line:", lines[navigate_start].rstrip())
print("close line:", lines[close_start].rstrip())

# new _ensure_driver lines
new_ensure = [
    "    def _ensure_driver(self):\n",
    "        \"\"\"Lazy load Playwright driver with user profile for logged-in sessions.\"\"\"\n",
    "        if not PLAYWRIGHT_AVAILABLE:\n",
    "            raise RuntimeError(\"Playwright not installed. Run: pip install playwright && python -m playwright install chromium\")\n",
    "        if self.page is None:\n",
    "            import os\n",
    "            print(\"Launching Playwright with Chrome profile...\")\n",
    "            self.playwright = sync_playwright().start()\n",
    "\n",
    "            user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\\\\Google\\\\Chrome\\\\User Data')\n",
    "            has_profile = os.path.isdir(user_data_dir) if user_data_dir else False\n",
    "\n",
    "            try:\n",
    "                if has_profile:\n",
    "                    self.context = self.playwright.chromium.launch_persistent_context(\n",
    "                        user_data_dir=user_data_dir,\n",
    "                        channel=\"chrome\",\n",
    "                        headless=self.headless,\n",
    "                        viewport={'width': 1920, 'height': 1080}\n",
    "                    )\n",
    "                    self._persistent = True\n",
    "                    print(f\"  Using logged-in Chrome profile: {user_data_dir}\")\n",
    "                else:\n",
    "                    self.browser = self.playwright.chromium.launch(channel=\"chrome\", headless=self.headless)\n",
    "                    self._persistent = False\n",
    "                    self.context = self.browser.new_context()\n",
    "                    print(\"  Using Chrome (no profile dir)\")\n",
    "            except Exception as e:\n",
    "                print(f\"  Chrome launch failed ({e}), using bundled Chromium\")\n",
    "                self.browser = self.playwright.chromium.launch(headless=self.headless)\n",
    "                self._persistent = False\n",
    "                self.context = self.browser.new_context()\n",
    "                print(\"  Using bundled Chromium\")\n",
    "\n",
    "            self.page = self.context.new_page()\n",
    "            self.page.set_viewport_size({\"width\": 1920, \"height\": 1080})\n",
]

# new close lines
new_close = [
    "    def close(self):\n",
    "        if self.playwright:\n",
    "            print(\"Closing browser session...\")\n",
    "            try:\n",
    "                if getattr(self, \"_persistent\", False):\n",
    "                    self.context.close()\n",
    "                else:\n",
    "                    self.browser.close()\n",
    "                self.playwright.stop()\n",
    "            except Exception:\n",
    "                pass\n",
    "            self.page = None\n",
    "            self.context = None\n",
    "            self.browser = None\n",
    "            self.playwright = None\n",
    "            try:\n",
    "                self.signals.emit_bridge(\"agent_status\", \"WebNavigator\", \"INITIALIZED\", \"Ready\")\n",
    "            except: pass\n",
    "            return \"Automation Engine closed.\"\n",
    "        return \"No engine running.\"\n",
]

# Build new file
new_lines = lines[:ensure_start]
new_lines.extend(new_ensure)
new_lines.append('\n')
new_lines.extend(lines[navigate_start:close_start])
new_lines.extend(new_close)
new_lines.append('\n')
new_lines.extend(lines[close_start+1:])

with open("agents/web_navigator.py", 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Replaced _ensure_driver and close successfully")
print(f"New file has {len(new_lines)} lines")
