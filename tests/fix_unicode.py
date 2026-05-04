#!/usr/bin/env python
"""Fix Unicode symbols in communication test to ASCII"""
import re

filepath = r"tests/communication_automation_test.py"

# Read as UTF-8
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '[OK]': '[OK]',
    '[ERROR]': '[FAIL]',
    '✕': '[FAIL]',
    '✖': '[FAIL]',
    '⚠': '[INFO]',
    '✔': '[OK]',
    '✘': '[FAIL]',
}

for orig, repl in replacements.items():
    content = content.replace(orig, repl)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Unicode symbols replaced successfully.")
