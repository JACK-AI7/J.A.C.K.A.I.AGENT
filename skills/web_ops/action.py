import webbrowser
import requests
from tools import get_web_data, open_any_url

def execute(task=None):
    """
    Executes web operations based on the task description.
    Task formats:
    - 'search: [query]'
    - 'open: [url]'
    """
    if not task:
        return "Web Ops Error: No task provided."
    
    if task.startswith("search:"):
        query = task.replace("search:", "").strip()
        return get_web_data(query)
    elif task.startswith("open:"):
        url = task.replace("open:", "").strip()
        return open_any_url(url)
    else:
        # Default to search if no prefix
        return get_web_data(task)
