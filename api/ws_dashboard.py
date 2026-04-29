from fastapi import WebSocket
import json

class DashboardManager:
    """Manages real-time WebSocket connections for the TITAN Dashboard."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("TITAN Dashboard: Neural Link Established.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("TITAN Dashboard: Neural Link Severed.")

    async def broadcast(self, data: dict):
        """Send system telemetry to all connected dashboards."""
        message = json.dumps(data)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

dashboard_manager = DashboardManager()
