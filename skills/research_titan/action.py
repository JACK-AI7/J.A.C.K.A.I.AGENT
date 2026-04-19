import os
import sys
import asyncio

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent_search import deep_search_mission

def execute(task=None):
    """The entry point for TITAN Research."""
    if not task:
        return "Please provide a research topic, Sir."
    
    print(f"Research Titan: Deploying crawling swarm for '{task}'...")
    
    # We use our Deep Search agent to perform the heavy lifting
    try:
        # Wrap the async call in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(deep_search_mission(task))
        return result
    except Exception as e:
        return f"Research Titan: Swarm encounter an anomaly - {str(e)}"

if __name__ == "__main__":
    # Test if called directly
    print(execute("The history of quantum computing and its future prospects"))
