import pyautogui
import os
import time

def execute(task=None):
    """
    Captures a screenshot of the entire screen.
    """
    try:
        # Create output directory
        out_dir = os.path.join(os.getcwd(), "assets", "screenshots")
        os.makedirs(out_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(out_dir, filename)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        return f"Screenshot captured successfully: {filepath}"
    
    except Exception as e:
        return f"Screenshot Error: {str(e)}"
