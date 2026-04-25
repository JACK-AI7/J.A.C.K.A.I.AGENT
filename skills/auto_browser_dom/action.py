import os
import asyncio
from agents.agent_browser import TitanBrowser

def execute(url=None, task=None):
    """
    TITAN Action: Performs an automatic DOM analysis of a website.
    Extracted from the 'Fullstack Hightech' suite.
    """
    if not url and not task:
        return "Skill Error: Provide either a URL or a task for DOM analysis."

    mission = task if task else f"Go to {url} and analyze the interactive DOM elements."
    
    try:
        # We reuse the TitanBrowser logic which uses browser-use (Playwright based)
        from agents.agent_browser import browse_titan
        result = browse_titan(mission)
        return f"Automatic DOM Analysis Complete:\n{result}"
    except Exception as e:
        return f"DOM Analysis Failure: {str(e)}"
