import asyncio
from core.safety import is_safe
from core.logger import log_event

class ToolRouter:
    """Safe execution layer for JACK tools with built-in stability guards."""
    def __init__(self, tool_map):
        self.tool_map = tool_map
        self.default_timeout = 30 # Seconds

    async def execute(self, name, args):
        if name not in self.tool_map:
            log_event(f"Error: Tool '{name}' not found.")
            return {"status": "error", "error": f"Tool '{name}' not found"}

        # Safety Check for shell commands
        if name in ["run_command", "execute_terminal_command"]:
            cmd = args.get("cmd") or args.get("command")
            if cmd and not is_safe(cmd):
                log_event(f"SECURITY ALERT: Blocked destructive command: {cmd}")
                return {"status": "error", "error": "Blocked destructive command for system safety."}

        try:
            log_event(f"Executing Tool: {name} with args: {args}")
            
            # --- STABILITY: ASYNC TIMEOUT GUARD ---
            async def _run():
                return await asyncio.to_thread(self.tool_map[name], **args)

            try:
                result = await asyncio.wait_for(_run(), timeout=self.default_timeout)
                return {"status": "success", "result": str(result)}
            except asyncio.TimeoutError:
                log_event(f"Stability Warning: Tool '{name}' timed out after {self.default_timeout}s.")
                return {"status": "error", "error": f"Mission timed out - Tool '{name}' failed to respond."}
            
        except Exception as e:
            log_event(f"Tool Execution Error ({name}): {str(e)}")
            return {"status": "error", "error": str(e)}
