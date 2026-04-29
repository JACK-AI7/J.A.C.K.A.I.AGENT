import os
import sys
import asyncio

# Root path alignment for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent_browser import TitanBrowser

def execute(task=None):
    """
    Executes an autonomous web mission using the TITAN Browser Engine.
    """
    if not task:
        return "Please provide a web mission, Sir."
    
    print(f"Auto-Navigator: Starting high-fidelity mission - {task}")
    
    try:
        # Wrap the async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(TitanBrowser().run_task(task))
        return f"Web Mission Result: {result}"
    except Exception as e:
        return f"Auto-Navigator Error: {str(e)}"

if __name__ == "__main__":
    print(execute("Search for the latest space news and summarize the top headline."))
