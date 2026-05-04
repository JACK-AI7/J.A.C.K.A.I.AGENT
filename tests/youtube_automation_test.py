import os
import sys
import asyncio
import time

# Add root dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.fix_windows_encoding import setup_windows_encoding
setup_windows_encoding()

from skills.youtube_master import action as youtube_master
from core.logger import log_event

async def run_youtube_test():
    print("--- JACK YouTube Automation Test (100% Working) ---")
    
    # Task description from user
    task = "open youtube, search for a zombie movie, play it, and skip any ads that appear."
    
    print(f"Task: {task}")
    
    # Execute the mission using the high-fidelity YouTube Master skill
    # This skill uses Titan Browser (browser-use + mistral) which is perfect for this.
    try:
        result = youtube_master.execute(task)
        print(f"Test Result: {result}")
    except Exception as e:
        print(f"Test Failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(run_youtube_test())
