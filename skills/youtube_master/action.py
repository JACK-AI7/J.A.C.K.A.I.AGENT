import asyncio
import os
import sys

# Add parent dir to path so we can find agent_browser etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agents.agent_browser import TitanBrowser

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
    if any(name in task.lower() for name in ["like", "sub", "comment"]):
        enhanced_task += "\n\nNote: If you need to like, subscribe, or comment, find the respective buttons. For 'Like', look for the thumb up icon. For 'Subscribe', ensure you don't unsubscribe if already joined."
    
    try:
        # Robust async execution
        try:
            loop = asyncio.get_running_loop()
            is_running = True
        except RuntimeError:
            is_running = False

        if is_running:
            # Run in a separate thread to avoid "loop already running" error
            import threading
            result_container = []
            def _run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result_container.append(new_loop.run_until_complete(TitanBrowser().run_task(enhanced_task)))
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=_run_in_thread)
            thread.start()
            thread.join()
            result = result_container[0] if result_container else "Mission failed in thread."
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(TitanBrowser().run_task(enhanced_task))
            finally:
                loop.close()
                
        return f"YouTube Mission Result: {result}"
    except Exception as e:
        return f"YouTube Master Error: {str(e)}"

if __name__ == "__main__":
    # Test
    print(execute())
