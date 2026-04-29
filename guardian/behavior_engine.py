import json
import os
from collections import defaultdict

class BehaviorEngine:
    """The 'Subconscious' of JACK: Learns and predicts user patterns."""
    def __init__(self, storage_path="vault/behavior.json"):
        self.storage_path = storage_path
        self.patterns = defaultdict(int)
        self.load_memory()

    def log_action(self, action_name: str):
        """Track an action to learn user habits."""
        self.patterns[action_name] += 1
        self.save_memory()

    def get_recommendations(self, limit: int = 3):
        """Suggest actions based on learned behavior."""
        sorted_patterns = sorted(self.patterns.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in sorted_patterns[:limit]]

    def load_memory(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.patterns.update(data)
            except:
                pass

    def save_memory(self):
        # Ensure vault exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "w") as f:
                json.dump(dict(self.patterns), f)
        except:
            pass

behavior_engine = BehaviorEngine()
