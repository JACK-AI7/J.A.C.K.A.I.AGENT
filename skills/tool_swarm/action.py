import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

def execute(task=None):
    """The entry point for the Universal Tool Swarm."""
    if not task:
        return "Universal Swarm: Awaiting instructions for bridge deployment, Sir."
    
    # Priority: Tavily Search (If available and task is search-related)
    if TAVILY_AVAILABLE and any(word in task.lower() for word in ["search", "find", "lookup"]):
        try:
            # We look for a TAVILY_API_KEY in the environment
            api_key = os.environ.get("TAVILY_API_KEY")
            if api_key:
                client = TavilyClient(api_key=api_key)
                print(f"Tool Swarm: Deploying Tavily Deep Search for '{task}'...")
                result = client.search(task, search_depth="advanced")
                return f"Tavily Deep Search Result: {result}"
            else:
                return "Tool Swarm: Tavily Search is ready, but I need a TAVILY_API_KEY in your .env to launch the sensors."
        except Exception as e:
            return f"Tavily Search Error: {str(e)}"

    # General Swarm Messaging
    return f"Tool Swarm: I am primed to handle '{task}'. Once you connect your Composio account, I can execute this across 100+ apps."

if __name__ == "__main__":
    # Test
    print(execute("Deep search for the future of AI agents in 2026"))
