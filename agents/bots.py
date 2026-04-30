"""
JACK Specialized Bot System — Real, functional bot delegation.
Each bot maps to actual tools and executes real tasks.
"""
import asyncio
from core.logger import log_event


class BotDispatcher:
    """Routes bot delegation requests to the correct real tools."""
    
    def __init__(self, tool_router):
        self.tools = tool_router
        
        # Map bot names to their primary tools and capabilities
        self.bot_registry = {
            # --- BROWSING & WEB BOTS ---
            "browser_bot": {"tools": ["open_any_url", "dom_read", "dom_click", "dom_type"], "desc": "Web browsing and interaction"},
            "web_bot": {"tools": ["open_any_url", "dom_read", "dom_click", "dom_type"], "desc": "Web browsing"},
            "search_bot": {"tools": ["get_web_data", "live_web_search"], "desc": "Web search"},
            "research_bot": {"tools": ["get_web_data", "live_web_search", "get_wikipedia_summary"], "desc": "Deep research"},
            "youtube_bot": {"tools": ["open_youtube", "dom_read", "dom_click", "dom_type"], "desc": "YouTube interaction"},
            
            # --- SYSTEM BOTS ---
            "system_bot": {"tools": ["execute_terminal_command", "get_system_stats", "system_process_monitor"], "desc": "System administration"},
            "file_bot": {"tools": ["list_folder", "search_files", "read_file_content", "file_management"], "desc": "File operations"},
            "app_bot": {"tools": ["open_application", "native_click", "native_type"], "desc": "Application control"},
            "cleanup_bot": {"tools": ["clean_temp_files", "system_cleanup", "kill_process"], "desc": "System cleanup"},
            
            # --- UI AUTOMATION BOTS ---
            "click_bot": {"tools": ["native_click", "visual_click", "dom_click"], "desc": "UI clicking"},
            "type_bot": {"tools": ["native_type", "dom_type"], "desc": "Text input"},
            "scroll_bot": {"tools": ["scroll_screen"], "desc": "Scrolling"},
            "vision_bot": {"tools": ["analyze_screen_deep", "get_screen_context", "take_screenshot"], "desc": "Screen vision"},
            
            # --- COMMUNICATION BOTS ---
            "whatsapp_bot": {"tools": ["send_whatsapp_message"], "desc": "WhatsApp messaging"},
            "email_bot": {"tools": ["open_email_client"], "desc": "Email management"},
            "message_bot": {"tools": ["send_whatsapp_message"], "desc": "Messaging"},
            
            # --- UTILITY BOTS ---
            "math_bot": {"tools": ["simple_calculator"], "desc": "Calculations"},
            "weather_bot": {"tools": ["get_weather_for_location"], "desc": "Weather info"},
            "news_bot": {"tools": ["get_world_news"], "desc": "News updates"},
            "memory_bot": {"tools": ["manage_memory"], "desc": "Long-term memory"},
            "code_bot": {"tools": ["execute_system_code", "execute_terminal_command"], "desc": "Code execution"},
            "download_bot": {"tools": ["download_file"], "desc": "File downloads"},
            "clipboard_bot": {"tools": ["manage_clipboard"], "desc": "Clipboard management"},
            "security_bot": {"tools": ["virus_scan"], "desc": "Security scanning"},
        }
    
    async def dispatch(self, bot_name, task):
        """Route a bot delegation to the correct tool(s)."""
        bot_name_lower = bot_name.lower().strip().replace(" ", "_")
        
        # Try exact match first
        bot = self.bot_registry.get(bot_name_lower)
        
        # Fuzzy match: check if any bot name contains the input
        if not bot:
            for name, info in self.bot_registry.items():
                if bot_name_lower in name or name in bot_name_lower:
                    bot = info
                    bot_name_lower = name
                    break
        
        # Keyword match: check the description
        if not bot:
            for name, info in self.bot_registry.items():
                if any(word in bot_name_lower for word in info["desc"].lower().split()):
                    bot = info
                    bot_name_lower = name
                    break
        
        if not bot:
            log_event(f"Bot '{bot_name}' not found in registry. Available: {list(self.bot_registry.keys())}")
            return f"Bot '{bot_name}' not recognized. Available bots: {', '.join(self.bot_registry.keys())}"
        
        log_event(f"Bot Dispatch: {bot_name_lower} -> tools: {bot['tools']} for task: {task}")
        
        # Execute the primary tool with the task
        primary_tool = bot["tools"][0]
        
        # Build smart args based on the tool type
        args = self._build_args(primary_tool, task)
        
        result = await self.tools.execute(primary_tool, args)
        
        result_str = result.get("result", result.get("error", str(result))) if isinstance(result, dict) else str(result)
        return result_str
    
    def _build_args(self, tool_name, task):
        """Build the correct argument format for each tool."""
        # Tools that take a query/search parameter
        query_tools = ["get_web_data", "live_web_search", "get_wikipedia_summary", "search_files"]
        if tool_name in query_tools:
            return {"query": task}
        
        # Tools that take a command
        if tool_name == "execute_terminal_command":
            return {"command": task}
        
        # Tools that take app_name
        if tool_name == "open_application":
            return {"app_name": task}
        
        # Tools that take a URL
        if tool_name == "open_any_url":
            return {"url": task}
        
        # Tools that take expression
        if tool_name == "simple_calculator":
            return {"expression": task}
        
        # Tools that take text
        if tool_name in ["native_type", "dom_type"]:
            return {"text": task}
        
        # Tools that take element_name
        if tool_name in ["native_click"]:
            return {"element_name": task}
        
        # Tools that take target_description
        if tool_name == "visual_click":
            return {"target_description": task}
        
        # Tools that take direction
        if tool_name == "scroll_screen":
            return {"direction": task if task in ["up", "down"] else "down"}
        
        # Tools that take task
        if tool_name in ["open_youtube", "open_world_monitor"]:
            return {}
        
        # Tools with specific parameters
        if tool_name == "send_whatsapp_message":
            # Try to split "recipient: message" format
            if ":" in task:
                parts = task.split(":", 1)
                return {"recipient": parts[0].strip(), "message": parts[1].strip()}
            return {"recipient": task, "message": ""}
        
        if tool_name == "file_management":
            return {"action": "list", "path": task}
        
        if tool_name == "list_folder":
            return {"folder_path": task}
        
        if tool_name == "read_file_content":
            return {"file_path": task}
        
        if tool_name == "manage_memory":
            return {"action": "recall", "query": task}
        
        if tool_name == "manage_clipboard":
            return {"action": "read"}
        
        if tool_name == "download_file":
            return {"url": task}
        
        # Default: try with task as generic argument
        return {"task": task}


# Legacy bot classes preserved for backward compatibility
class CodeBot:
    """Specialized bot for system engineering and debugging."""
    def run(self, task):
        from core.tools import execute_system_code
        return execute_system_code(task)

class ResearchBot:
    """Specialized bot for deep web intelligence gathering."""
    def run(self, task):
        from core.tools import live_web_search
        return live_web_search(task)

class AutomationBot:
    """Specialized bot for UI orchestration and desktop control."""
    def run(self, task):
        from core.tools import autonomous_desktop_mission
        return autonomous_desktop_mission(task)
