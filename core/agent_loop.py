from core.logger import log_event

class AgentLoop:
    """Autonomous loop for JACK missions."""
    def __init__(self, executor, max_steps=10):
        self.executor = executor
        self.max_steps = max_steps

    async def run(self, task):
        log_event(f"Starting Mission: {task}")
        
        # Reset executor for new mission
        if hasattr(self.executor, "reset"):
            self.executor.reset()
            
        context = task

        for step in range(self.max_steps):
            log_event(f"Mission Step {step+1}/{self.max_steps}")
            
            try:
                # Step the execution
                result = await self.executor.step(context)
            except Exception as e:
                log_event(f"Error during mission step: {e}")
                result = {
                    "type": "final",
                    "status": "failed",
                    "message": f"I encountered an unexpected error during execution: {str(e)}"
                }

            # If result is the 'final' dict, mission is done
            if isinstance(result, dict) and result.get("type") == "final":
                log_event(f"Mission Finalized: {result.get('message')}")
                return result

            # Otherwise, feed the result back as context for the next action
            context = result

        log_event("Mission Aborted: Maximum autonomous depth reached.")
        return {
            "type": "final",
            "status": "partial",
            "message": "I've reached my maximum mission depth, Sir. I was able to complete some steps, but the task might be incomplete."
        }
