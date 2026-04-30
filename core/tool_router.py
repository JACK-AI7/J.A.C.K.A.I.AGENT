import asyncio
import inspect
from core.safety import is_safe
from core.logger import log_event

class ToolRouter:
    """Safe execution layer for JACK tools with built-in stability guards."""
    def __init__(self, tool_map):
        self.tool_map = tool_map
        self.default_timeout = 60  # Seconds (increased for complex tools)

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
            
            func = self.tool_map[name]
            
            # --- SMART ASYNC/SYNC DETECTION ---
            async def _run():
                if inspect.iscoroutinefunction(func):
                    # Tool is async — call it directly with await
                    if isinstance(args, dict):
                        return await func(**args)
                    elif args:
                        return await func(args)
                    else:
                        return await func()
                else:
                    # Tool is sync — run in thread pool to avoid blocking
                    if isinstance(args, dict):
                        return await asyncio.to_thread(func, **args)
                    elif args:
                        return await asyncio.to_thread(func, args)
                    else:
                        return await asyncio.to_thread(func)

            try:
                result = await asyncio.wait_for(_run(), timeout=self.default_timeout)
                
                # Handle case where sync function accidentally returns a coroutine
                if inspect.iscoroutine(result):
                    result = await asyncio.wait_for(result, timeout=self.default_timeout)
                
                return {"status": "success", "result": str(result)}
            except asyncio.TimeoutError:
                log_event(f"Stability Warning: Tool '{name}' timed out after {self.default_timeout}s.")
                return {"status": "error", "error": f"Mission timed out - Tool '{name}' failed to respond."}
            
        except TypeError as e:
            # Handle argument mismatch — try without args
            try:
                log_event(f"Tool '{name}' arg mismatch, retrying without args: {e}")
                if inspect.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = await asyncio.to_thread(func)
                return {"status": "success", "result": str(result)}
            except Exception as e2:
                log_event(f"Tool Execution Retry Error ({name}): {str(e2)}")
                return {"status": "error", "error": str(e2)}
        except Exception as e:
            log_event(f"Tool Execution Error ({name}): {str(e)}")
            return {"status": "error", "error": str(e)}
