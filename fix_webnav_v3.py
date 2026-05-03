#!/usr/bin/env python
"""Clean fix: replace _ensure_driver and close in web_navigator.py via precise slicing"""

with open("agents/web_navigator.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find _ensure_driver line
ensure_start = None
close_start = None
navigate_start = None
for i, line in enumerate(lines):
    if 'def _ensure_driver(self):' in line:
        ensure_start = i
    elif 'def close(self):' in line:
        close_start = i
    elif ensure_start and close_start and navigate_start is None:
        if 'def navigate(' in line:
            navigate_start = i
            break

print(f"ensure_start={ensure_start}, close_start={close_start}, navigate_start={navigate_start}")

if not all(x is not None for x in [ensure_start, close_start, navigate_start]):
    print("ERROR: could not find method boundaries")
else:
    # Build replacement _ensure_driver block
    new_ensure_lines = [
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
    
    new_close_lines = [
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
    
    # Construct new file
    before_ensure = lines[:ensure_start]
    between_ensure_close = lines[navigate_start:close_start]  # from navigate up to close
    after_close = lines[close_start+1:]  # after close line we'll insert new close
    
    # Actually, we need to replace from ensure_start to navigate_start (exclusive) with new_ensure_lines
    # and replace from close_start to just before web_navigator singleton with new_close_lines
    
    # Build new file step by step
    new_file = []
    new_file.extend(lines[:ensure_start])
    new_file.extend(new_ensure_lines)
    new_file.append('\n')  # blank line after method
    new_file.extend(lines[navigate_start:close_start])
    new_file.extend(new_close_lines)
    new_file.append('\n')
    # Find singleton line: should be after old close
    singleton_idx = close_start + 1
    while singleton_idx < len(lines) and not lines[singleton_idx].startswith('web_navigator'):
        singleton_idx += 1
    if singleton_idx < len(lines):
        new_file.extend(lines[singleton_idx:])
    
    with open("agents/web_navigator.py", 'w', encoding='utf-8') as f:
        f.writelines(new_file)
    
    print(f"Replaced _ensure_driver (lines {ensure_start+1}->{navigate_start}) and close (lines {close_start+1}->{singleton_idx})")
    print("File updated successfully")
