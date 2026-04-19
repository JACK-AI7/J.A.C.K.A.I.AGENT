import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools import windows_ui_sniffer, os_control_interpreter, visual_click, open_application

def execute(task=None):
    """The entry point for specialized Windows Mastery missions."""
    if not task:
        return "Windows Master: I am ready to orchestrate your OS mission, Sir."
    
    print(f"Windows Master: Analyzing OS environment for task '{task}'...")
    
    # Logic: 
    # 1. Inspect the environment (UFO style)
    ui_map = windows_ui_sniffer()
    print(f"Environment Status:\n{ui_map}")
    
    # 2. Decide if we use Code or Vision
    # For this version, we provide a summarized response of how we'd proceed
    # In a real environment, this would feed back into the AI reasoning loop
    
    if any(app in task.lower() for app in ["excel", "ppt", "word", "powerpoint"]):
        return f"Windows Master: Detected cross-app request. I am engaging the Microsoft UFO-style UI Tree to navigate between your Office applications.\nStatus: Engaging TITAN Orchestrator."
    
    from tools import autonomous_desktop_mission
    print(f"Windows Master: Engaging Visual Orchestrator for task: {task}")
    return autonomous_desktop_mission(task)

if __name__ == "__main__":
    # Test
    print(execute("Copy data from Excel to a new Word document."))
