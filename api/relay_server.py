import asyncio
import json
import os
import socket
import websockets
from zeroconf import IPVersion, ServiceInfo, Zeroconf

# SECURITY: Secret Token for authentication
SECRET_TOKEN = os.getenv("JACK_RELAY_TOKEN", "jack_secure_neural_link_2026")
PORT = 8001

class ConnectionManager:
    """Manages neural links between Mobile Controller and PC Agent."""
    def __init__(self):
        self.active_links = set()

    async def handle_connection(self, websocket, path):
        # Path is expected to be /ws/{token}
        try:
            parts = path.strip("/").split("/")
            if len(parts) < 2 or parts[0] != "ws" or parts[1] != SECRET_TOKEN:
                print(f"RELAY: Unauthorized connection attempt from {websocket.remote_address} on path {path}")
                await websocket.close(code=4003) # Forbidden
                return

            self.active_links.add(websocket)
            print(f"RELAY: Neural Link Established from {websocket.remote_address}. Active Links: {len(self.active_links)}")
            
            try:
                async for message in websocket:
                    # Bridge the command/telemetry to all other linked nodes
                    await self.broadcast(message, websocket)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.active_links.remove(websocket)
                print(f"RELAY: Neural Link Severed for {websocket.remote_address}. Remaining: {len(self.active_links)}")
        except Exception as e:
            print(f"RELAY ERROR: {str(e)}")

    async def broadcast(self, message, sender):
        """Bridge data between the Mobile App and the PC Agent."""
        if not self.active_links:
            return
            
        # Create a list of tasks for parallel sending
        websockets_to_remove = []
        for connection in self.active_links:
            if connection != sender:
                try:
                    await connection.send(message)
                except:
                    websockets_to_remove.append(connection)
        
        for ws in websockets_to_remove:
            if ws in self.active_links:
                self.active_links.remove(ws)

manager = ConnectionManager()

async def main():
    # --- M-DNS ADVERTISING ---
    zeroconf = None
    try:
        desc = {'version': '1.0.0', 'id': 'jack_agent_primary'}
        hostname = socket.gethostname()
        # Get actual local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except:
            local_ip = socket.gethostbyname(hostname)
        finally:
            s.close()
        
        info = ServiceInfo(
            "_jack-relay._tcp.local.",
            "JACK_AGENT._jack-relay._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=PORT,
            properties=desc,
            server=f"{hostname}.local.",
        )
        
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(info)
        print(f"RELAY_DNS: Advertising JACK Service at {local_ip}:{PORT}")
    except Exception as e:
        print(f"RELAY_DNS_ERROR: {e}")

    # Start WebSocket Server
    print(f"TITAN RELAY: Starting on 0.0.0.0:{PORT}...")
    async with websockets.serve(manager.handle_connection, "0.0.0.0", PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("TITAN RELAY: Shutting down.")
