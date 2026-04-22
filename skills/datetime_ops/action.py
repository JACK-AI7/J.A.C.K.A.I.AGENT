from datetime import datetime
import time

def execute(task=None):
    """
    Returns current date, time, or both.
    """
    now = datetime.now()
    
    if not task:
        return f"Current date and time: {now.strftime('%A, %B %d, %Y - %H:%M:%S')}"
    
    task = task.lower()
    if "time" in task:
        return f"Current time: {now.strftime('%H:%M:%S')}"
    elif "date" in task:
        return f"Current date: {now.strftime('%A, %B %d, %Y')}"
    else:
        return f"Current date and time: {now.strftime('%A, %B %d, %Y - %H:%M:%S')}"
