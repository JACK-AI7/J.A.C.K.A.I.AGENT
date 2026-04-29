import asyncio
import os
import sys

# Add parent dir to path so we can find agent_browser etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent_browser import TitanBrowser

def execute(task=None):
    """The entry point for YouTube Mastery."""
    if not task:
        task = "Play the first video on the screen, like it, and subscribe to the channel."
    
    print(f"YouTube Master: Initiating High-Fidelity mission - '{task}'")
    
    # We use our Titan Browser to reason about the YouTube UI
    # We ensure we're on YouTube and then let the model follow the specific instructions.
    if "youtube.com" not in task.lower():
        enhanced_task = f"Go to youtube.com. {task}"
    else:
        enhanced_task = task

    # If it's a generic "interact" request, add the standard sub/like advice
    if any(word in task.lower() for name in ["like", "sub", "comment"]):
        enhanced_task += "\n\nNote: If you need to like, subscribe, or comment, find the respective buttons. For 'Like', look for the thumb up icon. For 'Subscribe', ensure you don't unsubscribe if already joined."
    
    try:
        # Wrap the async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(TitanBrowser().run_task(enhanced_task))
        return f"YouTube Mission Result: {result}"
    except Exception as e:
        return f"YouTube Master Error: {str(e)}"

if __name__ == "__main__":
    # Test
    print(execute())
