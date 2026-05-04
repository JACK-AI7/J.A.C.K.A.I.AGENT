import re
import json
from core.logger import log_event
from core.config import PRIVACY_SETTINGS

class PrivacyGuard:
    """The Shield of JACK: Prevents sensitive data from leaking to the internet."""
    
    def __init__(self):
        self.keywords = PRIVACY_SETTINGS.get("protected_keywords", [
            "password", "passwd", "secret", "ssh", "key", "token", "credential", 
            "bank", "credit card", "pin", "cvv", "api_key", "bearer"
        ])
        # Regex for common sensitive patterns
        self.patterns = [
            r'[a-zA-Z0-9]{32,}', # Potential API keys/hashes
            r'(?i)password\s*[:=]\s*\S+',
            r'(?i)api_key\s*[:=]\s*\S+',
            r'(\d{4}-){3}\d{4}', # Potential credit card
        ]

    def scan_for_leak(self, tool_name: str, args: dict) -> bool:
        """Scan tool arguments for potential privacy leaks."""
        # Only scan 'online' tools
        online_tools = [
            "web_search", "get_web_data", "open_any_url", "deep_research", 
            "browse_titan", "precision_search", "navigate_browser"
        ]
        
        if tool_name not in online_tools:
            return False # Local tools are safe

        args_str = json.dumps(args).lower()
        
        # 1. Keyword Check
        for kw in self.keywords:
            if kw.lower() in args_str:
                log_event(f"PRIVACY_GUARD: Blocked {tool_name} due to keyword match: '{kw}'")
                return True
        
        # 2. Pattern Check
        for pattern in self.patterns:
            if re.search(pattern, args_str):
                log_event(f"PRIVACY_GUARD: Blocked {tool_name} due to pattern match.")
                return True
                
        return False

# Singleton instance
privacy_guard = PrivacyGuard()

def check_privacy(tool_name: str, args: dict):
    """Bridge for the executor."""
    return privacy_guard.scan_for_leak(tool_name, args)
