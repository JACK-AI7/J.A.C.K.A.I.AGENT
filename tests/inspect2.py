#!/usr/bin/env python
"""Print raw representations of specific line ranges"""
with open(r"tests/communication_automation_test.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

ranges = [(262, 285), (288, 296), (300, 312)]
for start, end in ranges:
    print(f"\n=== Lines {start+1}-{end} ===")
    for i in range(start-1, min(end, len(lines))):
        print(repr(lines[i]))
