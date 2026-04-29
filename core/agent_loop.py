from core.logger import log_event

class AgentLoop:
    """Autonomous loop for JACK missions."""
    def __init__(self, executor, max_steps=10):
        self.executor = executor
        self.max_steps = max_steps

    async def run(self, task):
        log_event(f"Starting Mission: {task}")
        context = task

        for step in range(self.max_steps):
            log_event(f"Mission Step {step+1}/{self.max_steps}")
            
            # Step the execution
            result = await self.executor.step(context)

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
            "message": "Max mission steps reached without finalization."
        }
