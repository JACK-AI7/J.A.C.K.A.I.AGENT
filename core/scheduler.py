import asyncio
import datetime
import json
import logging
from typing import List, Dict, Any
from core.logger import log_event

class NLTask:
    """A task scheduled via natural language."""
    def __init__(self, task_id: str, description: str, cron_expr: str, next_run: datetime.datetime):
        self.task_id = task_id
        self.description = description
        self.cron_expr = cron_expr
        self.next_run = next_run

class NLScheduler:
    """Natural Language Scheduler inspired by Hermes Agent."""
    
    def __init__(self, agent_loop):
        self.agent_loop = agent_loop
        self.tasks: List[NLTask] = []
        self.is_running = False

    def schedule_task(self, description: str, cron_expr: str):
        """Schedule a task using a simple cron-like format or NL (to be parsed)."""
        # For simplicity, we assume the LLM provides a next_run or simple timing
        # In a full impl, we'd use a cron parser.
        # Example: "Every minute" or "2026-05-04 21:00:00"
        task_id = f"task_{len(self.tasks) + 1}"
        
        # Simple parser for demo/initial impl
        now = datetime.datetime.now()
        if "minute" in cron_expr:
            next_run = now + datetime.timedelta(minutes=1)
        elif "hour" in cron_expr:
            next_run = now + datetime.timedelta(hours=1)
        elif "day" in cron_expr:
            next_run = now + datetime.timedelta(days=1)
        else:
            try:
                next_run = datetime.datetime.fromisoformat(cron_expr)
            except:
                next_run = now + datetime.timedelta(minutes=5) # Default
        
        task = NLTask(task_id, description, cron_expr, next_run)
        self.tasks.append(task)
        log_event(f"SCHEDULER: Task '{description}' scheduled for {next_run}")
        return f"Task scheduled, Sir. Next run at {next_run}."

    async def start(self):
        """Main loop to check and run tasks."""
        self.is_running = True
        log_event("SCHEDULER: Background engine online.")
        while self.is_running:
            now = datetime.datetime.now()
            for task in self.tasks:
                if now >= task.next_run:
                    log_event(f"SCHEDULER: Executing scheduled task: {task.description}")
                    # Run the mission loop
                    asyncio.create_task(self.agent_loop.run(task.description))
                    
                    # Update next run if recurring
                    if "minute" in task.cron_expr:
                        task.next_run = now + datetime.timedelta(minutes=1)
                    elif "hour" in task.cron_expr:
                        task.next_run = now + datetime.timedelta(hours=1)
                    elif "day" in task.cron_expr:
                        task.next_run = now + datetime.timedelta(days=1)
                    else:
                        # Non-recurring, remove
                        self.tasks.remove(task)
            
            await asyncio.sleep(30) # Check every 30 seconds

# Bridge tool for the agent
def schedule_automation(task_description: str, timing: str):
    """Tool for JACK to schedule tasks autonomously."""
    # This will be called via the ToolRouter
    from core.jack_ai_agent import global_agent
    if hasattr(global_agent, "scheduler"):
        return global_agent.scheduler.schedule_task(task_description, timing)
    return "Scheduler not initialized."
