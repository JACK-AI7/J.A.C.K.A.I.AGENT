import sys
import os
import json

# Add necessary paths
script_dir = os.getcwd()
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
for folder in ["core", "agents", "gui", "utils", "setup"]:
    folder_path = os.path.join(script_dir, folder)
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)

from core.ai_handler import AIHandler

def test():
    handler = AIHandler()
    
    # Test 1: Open YouTube (should trigger open_youtube tool)
    print("\n--- Test 1: Open YouTube ---")
    query = "Open YouTube"
    response = handler.process_query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    
    # Test 3: Auto-Navigator (should trigger auto_navigator tool)
    print("\n--- Test 3: Auto-Navigator ---")
    query = "Search for the latest space news and summarize the top headline."
    response = handler.process_query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")

if __name__ == "__main__":
    test()
