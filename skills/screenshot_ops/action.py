import os
import time
from agents.desktop_agent import desktop_agent

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
        
        # Use desktop_agent's humanized screenshot
        desktop_agent.take_screenshot(filepath)
        
        return f"Screenshot captured successfully: {filepath}"
    
    except Exception as e:
        return f"Screenshot Error: {str(e)}"
