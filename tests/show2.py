#!/usr/bin/env python
with open(r"tests/communication_automation_test.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(381, 395):
    print(f"{i+1}: {repr(lines[i])}")
