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
            result = await self.tools.execute(
                parsed["name"],
                parsed.get("args", {})
            )

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

        return {"type": "final", "status": "failed", "message": "Neural execution reached an undefined state."}
