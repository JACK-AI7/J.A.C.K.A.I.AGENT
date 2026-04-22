import os
import json
import sys
from typing import List, Dict, Any

# Ensure we can import from root if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

class MemoryManager:
    def __init__(self):
        # Use a hidden file in the user's home directory for persistence
        self.memory_file = os.path.expanduser("~/.jack_ltm_memory.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load(self):
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _save(self, data):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def remember(self, key: str, value: str):
        data = self._load()
        data[key.lower().strip()] = value
        self._save(data)
        return f"Neural Archive: Information stored. I will remember that '{key}' is '{value}'."

    def retrieve(self, key: str):
        data = self._load()
        key_clean = key.lower().strip()
        if key_clean in data:
            return f"Neural Retrieval: Match found. '{key}' is '{data[key_clean]}'."
        # Try fuzzy match?
        for k in data:
            if key_clean in k or k in key_clean:
                return f"Neural Retrieval: Closest match found. '{k}' is '{data[k]}'."
        return f"Neural Retrieval: No records found for '{key}'."

    def list_all(self):
        data = self._load()
        if not data:
            return "Neural Archive: All memory sectors are currently empty."
        lines = [f"- {k}: {v}" for k, v in data.items()]
        return "Neural Archive Content:\n" + "\n".join(lines)

    def forget(self, key: str):
        data = self._load()
        key_clean = key.lower().strip()
        if key_clean in data:
            del data[key_clean]
            self._save(data)
            return f"Neural Archive: Deleted record for '{key}'."
        return f"Neural Archive: No record found for '{key}' to delete."

def execute(task=None):
    if not task:
        return "Memory Error: No command provided."

    mm = MemoryManager()
    task_lower = task.lower().strip()

    if task_lower.startswith("remember"):
        # Pattern: remember [key] is [value] or remember [key]:[value]
        content = task[8:].strip()
        if " is " in content:
            key, value = content.split(" is ", 1)
        elif ":" in content:
            key, value = content.split(":", 1)
        else:
            # Assume the whole thing is a fact to be parsed as key=fact, value=context?
            # Or just use the whole thing as a key-value pair if simple
            return mm.remember("fact", content)
        return mm.remember(key, value)

    elif task_lower.startswith("retrieve") or task_lower.startswith("get"):
        key = task_lower.replace("retrieve", "").replace("get", "").strip()
        return mm.retrieve(key)

    elif "list" in task_lower:
        return mm.list_all()

    elif task_lower.startswith("forget") or task_lower.startswith("delete"):
        key = task_lower.replace("forget", "").replace("delete", "").strip()
        return mm.forget(key)

    else:
        # Generic query - try to see if it's a retrieval
        return mm.retrieve(task)

if __name__ == "__main__":
    # Test
    print(execute("remember favorite food is pizza"))
    print(execute("retrieve favorite food"))
    print(execute("list"))
    print(execute("forget favorite food"))
