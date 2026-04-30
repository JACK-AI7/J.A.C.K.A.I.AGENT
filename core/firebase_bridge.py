import requests
import json
import threading
import time
try:
    from nexus_bridge import register_forwarder
except ImportError:
    def register_forwarder(func):
        pass

class FirebaseBridge:
    """
    A robust cloud-based bridge using Firebase Realtime Database.
    This bypasses all local network issues by using the internet.
    """
    def __init__(self, agent, firebase_url):
        self.agent = agent
        self.firebase_url = firebase_url.rstrip('/')
        self.is_running = False
        self.last_command_id = None
        
        # Register for telemetry
        register_forwarder(self.forward_telemetry)

    def start(self):
        self.is_running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        print(f"FIREBASE_BRIDGE: Online (Syncing with {self.firebase_url})")

    def _listen_loop(self):
        """Poll Firebase for new commands."""
        while self.is_running:
            try:
                # We check the 'command' node
                response = requests.get(f"{self.firebase_url}/command.json")
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        cmd_text = data.get("text")
                        cmd_id = data.get("id")
                        
                        if cmd_text and cmd_id != self.last_command_id:
                            print(f"FIREBASE_BRIDGE: Received Cloud Command: {cmd_text}")
                            self.last_command_id = cmd_id
                            if self.agent:
                                threading.Thread(target=self.agent.process_text_command, args=(cmd_text,), daemon=True).start()
                                
                # Update presence
                requests.patch(f"{self.firebase_url}/status.json", json={
                    "pc_online": True,
                    "last_seen": time.time()
                })
                
            except Exception as e:
                print(f"FIREBASE_BRIDGE: Error: {e}")
            
            time.sleep(2) # Poll every 2 seconds

    def forward_telemetry(self, signal_name, *args):
        """Push telemetry to Firebase."""
        if not self.is_running:
            return

        try:
            if signal_name == "telemetry_pulsed" and args:
                stats = args[0]
                requests.patch(f"{self.firebase_url}/telemetry.json", json={
                    "cpu": stats.get("cpu", 0),
                    "ram": stats.get("ram", 0),
                    "timestamp": time.time()
                })
            elif signal_name == "chat_received" and len(args) >= 2:
                requests.put(f"{self.firebase_url}/last_msg.json", json={
                    "speaker": args[0],
                    "text": args[1],
                    "timestamp": time.time()
                })
        except:
            pass
