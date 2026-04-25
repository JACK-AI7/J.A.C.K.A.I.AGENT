
import sys
import os

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from agents.web_navigator import WebNavigator
    print("WebNavigator imported successfully.")
    nav = WebNavigator(headless=False)
    print("Navigating to youtube.com...")
    res = nav.navigate("youtube")
    print(res)
    if "Failed" not in res:
        print("Waiting 5 seconds...")
        import time
        time.sleep(5)
    nav.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
