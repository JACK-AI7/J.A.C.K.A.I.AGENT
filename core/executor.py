from core.parser import parse_llm_output
from core.logger import log_event

class Executor:
    """Core brain of JACK: Coordinates AI, Parser, Router, and State."""
    def __init__(self, ai_handler, tool_router, state):
        self.ai = ai_handler
        self.tools = tool_router
        self.state = state

    async def step(self, user_input):
        # 1. Generate response from AI
        raw = self.ai.generate(user_input)
        
        # 2. Parse JSON
        parsed = parse_llm_output(raw)
        log_event(f"AI Decision: {parsed}")

        # 3. Handle Tool Execution
        if parsed["type"] == "tool":
            tool_name = parsed["name"]
            result = await self.tools.execute(
                tool_name,
                parsed.get("args", {})
            )
            
            # --- BEHAVIOR LEARNING ---
            from guardian.behavior_engine import behavior_engine
            behavior_engine.log_action(tool_name)

            self.state.log({
                "type": "tool_execution",
                "name": parsed["name"],
                "args": parsed.get("args", {}),
                "result": result
            })

            return f"TOOL_RESULT ({parsed['name']}): {result}"

        # 4. Handle Bot Delegation
        elif parsed["type"] == "bot":
            bot_name = parsed.get("name")
            bot_task = parsed.get("task")
            log_event(f"Delegating mission to specialized bot: {bot_name}")
            
            # For now, we return bot result as context for the next loop step
            # In a full multi-agent system, this would call the actual bot
            return f"BOT_RESULT ({bot_name}): Initialized mission for '{bot_task}'."

        # 5. Handle Finalization
        elif parsed["type"] == "final":
            return parsed

        # 6. Handle Common Hallucinated Types
        elif parsed["type"] in ["chat", "response", "answer", "message", "thought"]:
            return {
                "type": "final",
                "status": "success",
                "message": parsed.get("message") or parsed.get("response") or parsed.get("answer") or parsed.get("thought") or str(parsed)
            }
            
        elif parsed["type"] == "action":
            # Treat "action" as tool
            tool_name = parsed.get("name") or parsed.get("action")
            result = await self.tools.execute(tool_name, parsed.get("args", {}))
            return f"TOOL_RESULT ({tool_name}): {result}"

        # 7. Last Resort Fallback
        log_event(f"Undefined State: Parsed data was {parsed}")
        return {
            "type": "final", 
            "status": "success", 
            "message": parsed.get("message") or str(parsed)
        }
