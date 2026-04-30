import asyncio
import json
import os
import socket
import websockets
import logging
from zeroconf import IPVersion, ServiceInfo, Zeroconf

# --- CONFIGURATION ---
SECRET_TOKEN = os.getenv("JACK_RELAY_TOKEN", "jack_secure_neural_link_2026")
PORT = 8001
LOG_FILE = os.path.join("logs", "relay.log")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TITAN_RELAY")

class ConnectionManager:
    """Manages neural links between Mobile Controller and PC Agent."""
    def __init__(self):
        self.active_links = set()

    async def handle_connection(self, websocket, path=None):
        try:
            # Handle path for newer websockets versions where it's not passed as an argument
            if path is None:
                path = getattr(websocket, 'path', '/')
                
            parts = path.strip("/").split("/")
            if len(parts) < 2 or parts[0] != "ws" or parts[1] != SECRET_TOKEN:
                logger.warning(f"Unauthorized connection attempt from {websocket.remote_address} on path {path}")
                await websocket.close(code=4003)
                return

            self.active_links.add(websocket)
            logger.info(f"Neural Link Established: {websocket.remote_address}. Total Active: {len(self.active_links)}")
            
            try:
                async for message in websocket:
                    await self.broadcast(message, websocket)
            except websockets.exceptions.ConnectionClosed:
                logger.debug(f"Connection closed: {websocket.remote_address}")
            finally:
                if websocket in self.active_links:
                    self.active_links.remove(websocket)
                logger.info(f"Neural Link Severed: {websocket.remote_address}. Remaining: {len(self.active_links)}")
        except Exception as e:
            logger.error(f"Connection Error: {e}")

    async def broadcast(self, message, sender):
        if not self.active_links:
            return
            
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

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def main():
    if is_port_in_use(PORT):
        logger.error(f"Port {PORT} is already in use. Is another instance running?")
        return

    # --- M-DNS ADVERTISING ---
    zeroconf = None
    try:
        hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except:
            local_ip = socket.gethostbyname(hostname)
        finally:
            s.close()
        
        logger.info(f"Relay IP Detected: {local_ip}")
        
        desc = {'version': '1.0.0', 'id': 'jack_agent_primary', 'token_hint': SECRET_TOKEN[:4] + "****"}
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
        logger.info(f"M-DNS: Advertising JACK Service on {local_ip}:{PORT}")
    except Exception as e:
        logger.error(f"M-DNS ERROR: {e}")

    # Start WebSocket Server
    logger.info(f"Starting WebSocket Relay on 0.0.0.0:{PORT}...")
    try:
        async with websockets.serve(manager.handle_connection, "0.0.0.0", PORT):
            await asyncio.Future()
    except Exception as e:
        logger.critical(f"RELAY SERVER FATAL ERROR: {e}")
    finally:
        if zeroconf:
            zeroconf.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Relay shutting down.")
