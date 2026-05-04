from core.parser import parse_llm_output
from core.logger import log_event
from core.aimp_bridge import AIMPBridge
from memory.persistent_memory import persistent_memory
import json

class Executor:
    """Core brain of JACK: Coordinates AI, Parser, Router, and State."""
    def __init__(self, ai_handler, tool_router, state):
        self.ai = ai_handler
        self.tools = tool_router
        self.state = state
        self.mission_history = []
        self._action_counts = {}  # For stuck detection

    def reset(self):
        """Reset mission context."""
        self.mission_history = []
        self._action_counts = {}

    async def step(self, user_input):
        # Initialize history if empty
        if not self.mission_history:
            self.mission_history = []
            
        # 0. Query Long-Term Memory for Context
        memories = persistent_memory.search(str(user_input), limit=2)
        if memories:
            mem_context = "\nRelevant Memories:\n" + "\n".join([f"- {m['content']}" for m in memories])
            self.mission_history.append({"role": "system", "content": mem_context})

        # 1. Append user input/result to history
        self.mission_history.append({"role": "user", "content": str(user_input)})
        
        # 1. Generate response from AI using full history
        raw = self.ai.generate(self.mission_history)
        
        # 2. Parse JSON
        parsed = parse_llm_output(raw)
        log_event(f"AI Decision: {parsed}")
        
        # Append AI response to history
        self.mission_history.append({"role": "assistant", "content": json.dumps(parsed)})

        # --- EMIT THOUGHT FOR VISUALIZATION ---
        thought = parsed.get("thought")
        if thought:
            try:
                from core.nexus_bridge import get_signals
                get_signals().emit_bridge("thought_received", thought, "thought")
                get_signals().emit_bridge("agent_thought", "JACK", thought, 0.95)
            except: pass

        # 3. Stuck Detection
        action_key = f"{parsed.get('type')}:{parsed.get('name')}:{json.dumps(parsed.get('args', {}), sort_keys=True)}"
        self._action_counts[action_key] = self._action_counts.get(action_key, 0) + 1
        
        if self._action_counts[action_key] >= 3:
            log_event(f"STUCK DETECTION: Repetitive action detected: {action_key}")
            return {
                "type": "final",
                "status": "failed",
                "message": "I noticed I'm repeating the same action, Sir. I'm aborting this mission to avoid a loop. Can we try a different approach?"
            }

        res_type = parsed.get("type", "unknown")

        # 4. Handle Tool Execution
        if res_type == "tool":
            tool_name = parsed.get("name", "")
            tool_args = parsed.get("args") or {}
            
            # Normalize string args to dict
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except (json.JSONDecodeError, ValueError):
                    # If it's a simple string, wrap it as the first expected arg
                    tool_args = {"task": tool_args}
            
            # --- PRIVACY GUARD ---
            from core.privacy_guard import check_privacy
            if check_privacy(tool_name, tool_args):
                return {
                    "type": "final",
                    "status": "failed",
                    "message": "SECURITY ALERT: I've blocked this action because it contains potentially sensitive information (passwords, keys, or credentials) that shouldn't be sent online. Your safety is my priority, Sir."
                }

            # Wrap in AIMP format for internal standardization
            aimp_req = AIMPBridge.wrap_tool_call(tool_name, tool_args)
            log_event(f"AIMP Request: {json.dumps(aimp_req)}")
            
            result = await self.tools.execute(tool_name, tool_args)
            
            # Wrap result in AIMP
            aimp_res = AIMPBridge.wrap_tool_result(tool_name, result)
            log_event(f"AIMP Response: {json.dumps(aimp_res)}")
            
            # --- EMIT OBSERVATION FOR VISUALIZATION ---
            result_summary = str(result)[:200] + ("..." if len(str(result)) > 200 else "")
            try:
                from core.nexus_bridge import get_signals
                signals = get_signals()
                signals.emit_bridge("thought_received", f"Observation ({tool_name}): {result_summary}", "log")
                signals.emit_bridge("agent_action", "JACK", "OBSERVATION", tool_name, result_summary)
                # Streaming Output for TUI/Dashboard
                signals.emit_bridge("tool_output", tool_name, str(result))
            except: pass
            
            # --- BEHAVIOR LEARNING ---
            try:
                from guardian.behavior_engine import behavior_engine
                behavior_engine.log_action(tool_name)
            except Exception:
                pass

            self.state.log({
                "type": "tool_execution",
                "name": tool_name,
                "args": tool_args,
                "result": result
            })

            # Format result for the AI to process
            result_str = result.get("result", result.get("error", str(result))) if isinstance(result, dict) else str(result)
            return f"TOOL_RESULT ({tool_name}): {result_str}"

        # 5. Handle Bot Delegation (route to real tools)
        elif res_type == "bot":
            bot_name = parsed.get("name", "")
            bot_task = parsed.get("task", parsed.get("args", {}).get("task", ""))
            log_event(f"Delegating mission to specialized bot: {bot_name}")
            
            try:
                from agents.bots import BotDispatcher
                dispatcher = BotDispatcher(self.tools)
                result = await dispatcher.dispatch(bot_name, bot_task)
                return f"BOT_RESULT ({bot_name}): {result}"
            except Exception as e:
                log_event(f"Bot dispatch failed: {e}")
                # Fallback: try as skill
                try:
                    from core.skill_manager import execute_titan_skill
                    result = execute_titan_skill(bot_name, bot_task)
                    if "not found" not in str(result).lower():
                        return f"BOT_RESULT ({bot_name}): {result}"
                except Exception:
                    pass
                return f"BOT_ERROR ({bot_name}): Could not dispatch bot - {str(e)}"

        # 6. Handle Finalization & Common Response Types
        if res_type in ["final", "chat", "response", "answer", "message", "thought"]:
            # Standardize on 'final' type
            parsed["type"] = "final"
            if "status" not in parsed: parsed["status"] = "success"
            
            # Ensure 'message' key exists
            if not parsed.get("message"):
                parsed["message"] = parsed.get("response") or parsed.get("answer") or parsed.get("thought") or str(parsed)
            
            # Log to Persistent Memory if it's a significant summary
            if parsed.get("status") == "success":
                persistent_memory.add_memory(
                    content=parsed["message"],
                    memory_type="mission_result",
                    metadata={"status": "success", "mission": str(user_input)}
                )

            return parsed

            
        elif res_type == "action":
            # Treat "action" as tool
            tool_name = parsed.get("name") or parsed.get("action", "")
            tool_args = parsed.get("args", {})
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except:
                    tool_args = {"task": tool_args}
            
            # Wrap in AIMP format
            aimp_req = AIMPBridge.wrap_tool_call(tool_name, tool_args)
            log_event(f"AIMP Request (Action): {json.dumps(aimp_req)}")

            result = await self.tools.execute(tool_name, tool_args)
            
            # Wrap result in AIMP
            aimp_res = AIMPBridge.wrap_tool_result(tool_name, result)
            log_event(f"AIMP Response (Action): {json.dumps(aimp_res)}")
            result_str = result.get("result", result.get("error", str(result))) if isinstance(result, dict) else str(result)
            return f"TOOL_RESULT ({tool_name}): {result_str}"

        # 8. Last Resort Fallback
        log_event(f"Undefined State: Parsed data was {parsed}")
        return {
            "type": "final", 
            "status": "success", 
            "message": parsed.get("message") or str(parsed)
        }
