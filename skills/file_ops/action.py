import os
import shutil
import glob
from tools import file_management

def execute(task=None):
    """
    Handles advanced file operations.
    Supports JSON-like formatting or natural language strings passed to tools.
    """
    if not task:
        return "File Ops Error: No task provided."
    
    # Delegate to the refined file_management tool in tools.py
    # or handle natural language mapping here
    return file_management("auto", task) # Assume 'auto' is a smart dispatcher
