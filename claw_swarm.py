import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import logging

class ClawSwarm:
    """The parallel execution engine for JACK's multi-agent bots (Claws)."""

    def __init__(self, max_bots=5):
        self.max_bots = max_bots
        self.executor = ThreadPoolExecutor(max_workers=max_bots)
        self.active_bots = {}
        self.mission_history = []

    def deploy_swarm(self, tasks, hud=None):
        """Deploy a swarm of bots to handle multiple tasks in parallel."""
        print(f"TITAN Swarm: Deploying {len(tasks)} bots across the system...")
        results = {}
        
        if hud:
            hud.signals.status_changed.emit(f"Swarm Active ({len(tasks)} Bots)", "pulsing")

        # Nexus Integration: Add nodes for each bot
        from nexus_bridge import get_signals
        signals = get_signals()
        
        for task in tasks:
            bot_name = task.get('name', 'GenericBot')
            signals.node_added.emit(f"bot_{bot_name}", bot_name, "code", "ROOT")
            signals.thought_received.emit(f"Claw Bot '{bot_name}' deployed for task: {task.get('tool', 'Unknown')}", "decision")
            try: signals.bot_status.emit(bot_name, "DEPLOYED", f"Task: {task.get('tool', 'Unknown')}")
            except: pass

        # Submit tasks to the thread pool
        futures = {self.executor.submit(self._run_bot, t): t for t in tasks}
        
        for future in futures:
            task_info = futures[future]
            try:
                result = future.result()
                results[task_info['name']] = result
            except Exception as e:
                results[task_info['name']] = f"Bot Error: {str(e)}"
        
        if hud:
            hud.signals.status_changed.emit("Swarm Dispersed", "idle")
            
        return results

    def _run_bot(self, task):
        """Internal execution loop for a single Claw Bot."""
        name = task.get('name', 'GenericBot')
        func = task.get('func')
        args = task.get('args', [])
        
        print(f"  [Bot: {name}] Started...")
        start_time = time.time()
        
        from nexus_bridge import get_signals
        signals = get_signals()
        
        try:
            if callable(func):
                signals.bot_status.emit(name, "RUNNING", f"Executing...")
                result = func(*args)
            else:
                result = f"Error: '{name}' function is not callable."
            signals.thought_received.emit(f"Bot '{name}' mission SUCCESS: {str(result)[:50]}...", "thought")
            try: signals.bot_status.emit(name, "SUCCESS", str(result)[:50])
            except: pass
        except Exception as e:
            result = f"Crash: {str(e)}"
            signals.thought_received.emit(f"Bot '{name}' mission FAILED: {str(e)}", "decision")
            try: signals.bot_status.emit(name, "FAILED", str(e)[:50])
            except: pass
        
        end_time = time.time()
        print(f"  [Bot: {name}] Mission complete in {end_time - start_time:.2f}s")
        return result

def spawn_claw_swarm(mission_manifest):
    """Bridge function to spawn a swarm from a manifest dictionary."""
    # Example manifest: [{"name": "SearchBot", "func": get_web_data, "args": ["weather"]}, ...]
    swarm = ClawSwarm()
    return swarm.deploy_swarm(mission_manifest)

if __name__ == "__main__":
    # Test
    def mock_task(n):
        time.sleep(n)
        return f"Slept for {n}s"
    
    swarm = ClawSwarm()
    manifest = [
        {"name": "Bot1", "func": mock_task, "args": [1]},
        {"name": "Bot2", "func": mock_task, "args": [2]}
    ]
    print(swarm.deploy_swarm(manifest))
