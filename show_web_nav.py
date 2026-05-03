#!/usr/bin/env python
"""Show raw content of web_navigator._ensure_driver for exact replace"""
with open(r"agents/web_navigator.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Find _ensure_driver start and end
start = None
for i, l in enumerate(lines):
    if 'def _ensure_driver(self):' in l:
        start = i
        break
if start:
    # print until next method
    for i in range(start, min(start+40, len(lines))):
        print(f"{i+1}: {repr(lines[i])}")
    print("---")
    # show close() method
    close_start = None
    for i in range(start, len(lines)):
        if 'def close(self):' in lines[i]:
            close_start = i
            break
    if close_start:
        for i in range(close_start, min(close_start+20, len(lines))):
            print(f"{i+1}: {repr(lines[i])}")
