import asyncio
import json
import logging
import threading
import websockets
import psutil
from core.nexus_bridge import register_forwarder

class RelayClient:
    """Bridging the PC Agent to the Mobile Relay via WebSockets."""
    
    def __init__(self, agent, relay_url="ws://localhost:8001/ws/jack_secure_neural_link_2026"):
        self.agent = agent
        self.relay_url = relay_url
        self.websocket = None
        self.loop = None
        self.is_running = False
        
        # Register as forwarder to capture telemetry
        register_forwarder(self.forward_telemetry)

    def start(self):
        """Start the relay client in a background thread."""
        self.is_running = True
        threading.Thread(target=self._run_event_loop, daemon=True).start()
        print("TITAN_MOBILE_BRIDGE: Initializing...")

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._listen())

    async def _listen(self):
        """Maintain WebSocket connection and listen for remote commands."""
        while self.is_running:
            try:
                async with websockets.connect(self.relay_url) as ws:
                    self.websocket = ws
                    print(f"TITAN_MOBILE_BRIDGE: Connected to {self.relay_url}")
                    
                    # Send initial online status
                    await self.send_to_relay({"status": "ONLINE", "message": "PC Agent Connected"})
                    
                    # Start keep-alive ping loop
                    async def _ping():
                        while self.websocket == ws:
                            try:
                                await ws.ping()
                                await asyncio.sleep(20)
                            except: break
                    
                    asyncio.create_task(_ping())

                    async for message in ws:
                        try:
                            # If it's a raw string command (from mobile)
                            print(f"TITAN_MOBILE_BRIDGE: Received Command: {message}")
                            # Execute on agent
                            if self.agent:
                                threading.Thread(target=self.agent.process_text_command, args=(message,), daemon=True).start()
                        except Exception as e:
                            print(f"TITAN_MOBILE_BRIDGE: Command Error: {e}")
                            
            except Exception as e:
                self.websocket = None
                print(f"TITAN_MOBILE_BRIDGE: Connection failed ({e}). Retrying in 5s...")
                await asyncio.sleep(5)

    def forward_telemetry(self, signal_name, *args):
        """Forward internal signals to the mobile app."""
        if not self.websocket or not self.loop:
            return

        payload = {"type": signal_name}
        
        if signal_name == "telemetry_pulsed" and args:
            stats = args[0]
            payload.update({
                "cpu": stats.get("cpu", 0),
                "ram": stats.get("ram", 0),
                "gpu": stats.get("gpu", 0)
            })
        elif signal_name == "pipeline_stage" and len(args) >= 2:
            payload["stage"] = args[0]
            payload["detail"] = args[1]
        elif signal_name == "chat_received" and len(args) >= 2:
            payload["speaker"] = args[0]
            payload["text"] = args[1]
        else:
            # Generic payload for other signals
            payload["args"] = list(args)

        # Schedule sending in the event loop
        asyncio.run_coroutine_threadsafe(self.send_to_relay(payload), self.loop)

    async def send_to_relay(self, data):
        """Send a JSON payload to the relay server."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(data))
            except:
                self.websocket = None
