from core.parser import parse_llm_output
from core.logger import log_event
import json

class Executor:
    """Core brain of JACK: Coordinates AI, Parser, Router, and State."""
    def __init__(self, ai_handler, tool_router, state):
        self.ai = ai_handler
        self.tools = tool_router
        self.state = state
        self.mission_history = []
        self._action_counts = {} # For stuck detection

    def reset(self):
        """Reset mission context."""
        self.mission_history = []
        self._action_counts = {}

    async def step(self, user_input):
        # Initialize history if empty
        if not self.mission_history:
            self.mission_history = []
            
        # 0. Append user input/result to history
        self.mission_history.append({"role": "user", "content": user_input})
        
        # 1. Generate response from AI using full history
        raw = self.ai.generate(self.mission_history)
        
        # 2. Parse JSON
        parsed = parse_llm_output(raw)
        log_event(f"AI Decision: {parsed}")
        
        # Append AI response to history
        self.mission_history.append({"role": "assistant", "content": json.dumps(parsed)})

        # 3. Stuck Detection
        action_key = f"{parsed.get('type')}:{parsed.get('name')}:{json.dumps(parsed.get('args'))}"
        self._action_counts[action_key] = self._action_counts.get(action_key, 0) + 1
        
        if self._action_counts[action_key] >= 3:
            log_event(f"STUCK DETECTION: Repetitive action detected: {action_key}")
            return {
                "type": "final",
                "status": "failed",
                "message": "I noticed I'm repeating the same action, Sir. I'm aborting this mission to avoid a loop. Can we try a different approach?"
            }

        # 4. Handle Tool Execution
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

        # 5. Handle Bot Delegation
        elif parsed["type"] == "bot":
            bot_name = parsed.get("name")
            bot_task = parsed.get("task")
            log_event(f"Delegating mission to specialized bot: {bot_name}")
            
            # --- ACTUAL BOT EXECUTION ---
            try:
                from core.skill_manager import execute_titan_skill
                result = execute_titan_skill(bot_name, bot_task)
                
                # If skill not found, try to execute as a tool just in case
                if "not found in the library" in str(result):
                    result = await self.tools.execute(bot_name, {"task": bot_task})
                
                return f"BOT_RESULT ({bot_name}): {result}"
            except Exception as e:
                return f"BOT_ERROR ({bot_name}): Failed to initialize - {str(e)}"

        # 6. Handle Finalization
        elif parsed["type"] == "final":
            return parsed

        # 7. Handle Common Hallucinated Types
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

        # 8. Last Resort Fallback
        log_event(f"Undefined State: Parsed data was {parsed}")
        return {
            "type": "final", 
            "status": "success", 
            "message": parsed.get("message") or str(parsed)
        }
