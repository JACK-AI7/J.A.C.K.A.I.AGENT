from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
import json
import os

app = FastAPI(title="JACK Neural Relay", version="1.0.0")

# SECURITY: Secret Token for authentication
# In production, use environment variables
SECRET_TOKEN = os.getenv("JACK_RELAY_TOKEN", "jack_secure_neural_link_2026")

class ConnectionManager:
    """Manages neural links between Mobile Controller and PC Agent."""
    def __init__(self):
        self.active_links: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, token: str):
        if token != SECRET_TOKEN:
            await websocket.close(code=4003) # Forbidden
            return False
            
        await websocket.accept()
        self.active_links.append(websocket)
        print(f"RELAY: Neural Link Established. Active Links: {len(self.active_links)}")
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_links:
            self.active_links.remove(websocket)
            print("RELAY: Neural Link Severed.")

    async def broadcast(self, message: str, sender: WebSocket):
        """Bridge data between the Mobile App and the PC Agent."""
        for connection in self.active_links:
            if connection != sender:
                try:
                    await connection.send_text(message)
                except:
                    self.active_links.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    success = await manager.connect(websocket, token)
    if not success: return

    try:
        while True:
            data = await websocket.receive_text()
            # Bridge the command/telemetry to all other linked nodes
            await manager.broadcast(data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"RELAY ERROR: {str(e)}")
        manager.disconnect(websocket)

@app.get("/health")
def health():
    return {"status": "RELAY_OPERATIONAL", "nodes": len(manager.active_links)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
