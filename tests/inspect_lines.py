#!/usr/bin/env python
"""Show problematic lines in communication test"""
with open(r"tests/communication_automation_test.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show lines around suspected areas
ranges = [(149, 162), (185, 198), (221, 237), (265, 285)]
for start, end in ranges:
    print(f"\n=== Lines {start+1}-{end} ===")
    for i in range(start, min(end, len(lines))):
        # Show line number, repr to see whitespace
        print(f"{i+1:4d}: {repr(lines[i])}")
