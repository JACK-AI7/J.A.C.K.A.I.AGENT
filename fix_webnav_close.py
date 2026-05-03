#!/usr/bin/env python
"""Fix web_navigator dupe - replace entire close method cleanly"""

with open("agents/web_navigator.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find indices
close_start = None
singleton_start = None
for i, line in enumerate(lines):
    if line.strip() == 'def close(self):' and close_start is None:
        close_start = i
    elif line.startswith('web_navigator = ') and singleton_start is None:
        singleton_start = i
        break

if close_start is None or singleton_start is None:
    print(f"ERROR: close_start={close_start}, singleton_start={singleton_start}")
else:
    print(f"close_start index: {close_start} (line {close_start+1})")
    print(f"singleton_start index: {singleton_start} (line {singleton_start+1})")
    print(f"Lines to replace: {close_start} to {singleton_start-1} inclusive")
    
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
        "\n",
    ]
    
    # Rebuild file: before close + new_close + singleton line + rest
    new_lines = lines[:close_start] + new_close + lines[singleton_start:]
    
    with open("agents/web_navigator.py", 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Replaced close method ({singleton_start - close_start} lines -> {len(new_close)} lines)")
    print("File fixed - no more duplicate")
