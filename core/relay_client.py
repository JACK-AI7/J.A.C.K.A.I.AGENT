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
        self._mobile_controller = None  # Will be set by main.py
        
        # Register as forwarder to capture telemetry
        register_forwarder(self.forward_telemetry)

    def set_mobile_controller(self, controller):
        """Inject the MobileController instance for ADB command execution."""
        self._mobile_controller = controller

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
                    
                    await self.send_to_relay({"status": "ONLINE", "message": "PC Agent Connected"})
                    
                    async def _ping():
                        while self.websocket == ws:
                            try:
                                await ws.ping()
                                await asyncio.sleep(20)
                            except:
                                break
                    asyncio.create_task(_ping())

                    async for message in ws:
                        try:
                            data = json.loads(message)
                            
                            # ADB command from mobile app
                            if data.get("type") == "adb_command":
                                action = data.get("action")
                                params = data.get("params", {})
                                result = await self._execute_adb_action(action, params)
                                response = {"type": "command_result", "action": action, "result": result}
                                await ws.send(json.dumps(response))
                                await self.broadcast(json.dumps(response), ws)
                            
                            # Legacy: raw string command
                            elif "command" in data:
                                command = data["command"]
                                print(f"TITAN_MOBILE_BRIDGE: Received Command: {command}")
                                if self.agent:
                                    threading.Thread(target=self.agent.process_text_command, args=(command,), daemon=True).start()
                            else:
                                print(f"TITAN_MOBILE_BRIDGE: Unknown message type: {data}")
                                
                        except Exception as e:
                            print(f"TITAN_MOBILE_BRIDGE: Command Error: {e}")
                            
            except Exception as e:
                self.websocket = None
                print(f"TITAN_MOBILE_BRIDGE: Connection failed ({e}). Retrying in 5s...")
                await asyncio.sleep(5)

    async def _execute_adb_action(self, action, params):
        """Execute ADB command using the injected controller."""
        if not self._mobile_controller:
            return "ERROR: Mobile ADB controller not attached"
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_adb_action_sync, action, params)
    
    def _run_adb_action_sync(self, action, params):
        """Synchronous ADB action runner."""
        try:
            ctrl = self._mobile_controller
            if action == "tap":
                return ctrl.adb_input_tap(params.get("x", 0), params.get("y", 0))
            elif action == "swipe":
                return ctrl.adb_input_swipe(
                    params.get("x1", 0), params.get("y1", 0),
                    params.get("x2", 0), params.get("y2", 0),
                    params.get("duration", 300))
            elif action == "text":
                return ctrl.adb_input_text(params.get("text", ""))
            elif action == "key":
                return ctrl.adb_press_key(params.get("key", ""))
            elif action == "launch":
                return ctrl.adb_start_app(params.get("package", ""))
            elif action == "screencap":
                img = ctrl.adb_screencap()
                if img:
                    import base64
                    from io import BytesIO
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    screenshot_msg = {
                        "type": "screenshot_update",
                        "data": b64,
                        "timestamp": time.time()
                    }
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast(json.dumps(screenshot_msg), None),
                        self.loop
                    )
                    return "Screenshot sent"
                return "Screenshot failed"
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"ADB error: {e}"

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
            payload["args"] = list(args)

        asyncio.run_coroutine_threadsafe(self.send_to_relay(payload), self.loop)

    async def send_to_relay(self, data):
        """Send a JSON payload to the relay server."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(data))
            except:
                self.websocket = None
