class StateManager:
    """Tracks context and mission history for JACK."""
    def __init__(self):
        self.state = {
            "last_tool": None,
            "app_open": {},
            "history": [],
            "mission_start_time": None,
            "user_profile": {
                "name": "Boss",
                "preferences": {},
                "learned_facts": []
            }
        }

    def update(self, key, value):
        self.state[key] = value

    def get(self, key):
        return self.state.get(key)

    def log(self, step):
        self.state["history"].append(step)
        # Also log to file if needed
        from core.logger import log_event
        log_event(f"State Update: {step}")
