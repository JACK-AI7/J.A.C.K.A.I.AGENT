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
    # We add a strong instruction to ensure it finds the buttons.
    enhanced_task = f"""
    Go to youtube.com if not already there.
    {task}
    Specifically:
    1. Click the first video thumbnail.
    2. Wait 3 seconds for it to start.
    3. Find the 'Like' button (thumb up icon) and click it.
    4. Find the 'Subscribe' button and if it doesn't say 'Subscribed', click it.
    5. Be careful not to click the 'Unsubscribe' button if already subscribed.
    """
    
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
