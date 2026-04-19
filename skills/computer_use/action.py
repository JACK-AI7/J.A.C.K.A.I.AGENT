import os
from skills.computer_use.computer_use_agent import ComputerUseAgent

def execute(task=None):
    """
    TITAN Action: Initiates the Anthropic Computer Use loop to fulfill a task.
    """
    if not task:
        return "Skill Error: No task provided for Computer Use."
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Skill Error: ANTHROPIC_API_KEY environment variable is missing."
        
    try:
        agent = ComputerUseAgent(api_key=api_key)
        # Note: run_task currently has placeholder logic for the loop
        result = agent.run_task(task)
        return f"Computer Use execution initiated for: {task}. {result}"
    except Exception as e:
        return f"Computer Use Critical Failure: {str(e)}"
