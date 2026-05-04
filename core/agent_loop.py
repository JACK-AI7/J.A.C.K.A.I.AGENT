from core.logger import log_event

class AgentLoop:
    """Autonomous loop for JACK missions."""
    def __init__(self, executor, max_steps=10):
        self.executor = executor
        self.max_steps = max_steps
        self.interrupt = False
        try:
            from core.skill_learner import SkillLearner
            self.learner = SkillLearner(executor.ai)
        except Exception:
            self.learner = None

    async def run(self, task):
        log_event(f"Starting Mission: {task}")
        
        # Reset executor for new mission
        if hasattr(self.executor, "reset"):
            self.executor.reset()
            
        context = task
        self.interrupt = False

        for step in range(self.max_steps):
            if self.interrupt:
                log_event("MISSION INTERRUPTED by neural override.")
                return {"type": "final", "status": "failed", "message": "Mission interrupted, Sir. I have ceased all current work."}
            
            log_event(f"Mission Step {step+1}/{self.max_steps}")
            
            try:
                # Step the execution
                result = await self.executor.step(context)
            except Exception as e:
                log_event(f"Error during mission step: {e}")
                result = f"CRITICAL_STEP_ERROR: {str(e)}. Sir, I encountered an error during this step. I will reflect and attempt to correct my course."

            # If result is the 'final' dict, mission is done
            if isinstance(result, dict) and result.get("type") == "final":
                log_event(f"Mission Finalized: {result.get('message')}")
                
                # --- SELF-IMPROVEMENT REFLECTION ---
                if result.get("status") == "success" and self.learner:
                    try:
                        # Extract trace from executor state
                        trace = self.executor.state.get_history()
                        import asyncio
                        # Run reflection in background so it doesn't block response
                        asyncio.create_task(self.learner.reflect_on_mission(task, trace))
                    except Exception as e:
                        log_event(f"Post-mission reflection failed: {e}")
                
                return result

            # Otherwise, feed the result back as context for the next action
            context = result

        log_event("Mission Aborted: Maximum autonomous depth reached.")
        return {
            "type": "final",
            "status": "partial",
            "message": "I've reached my maximum mission depth, Sir. I was able to complete some steps, but the task might be incomplete."
        }
