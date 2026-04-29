def run_agent_mission(agent, task_input):
    """Background task to execute a full JACK mission."""
    # This is intended to be run by the Redis worker
    return agent.process_text_command(task_input)
