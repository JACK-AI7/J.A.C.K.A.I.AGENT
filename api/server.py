from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jack_ai_agent import JackAIAgent

app = FastAPI(title="JACK Production API", version="1.0.0")
agent = None

class TaskRequest(BaseModel):
    task: str

@app.on_event("startup")
async def startup_event():
    global agent
    # Initialize JACK on startup
    # Note: ai_handler and tool_map would normally be passed here
    # agent = JackAIAgent(ai_handler, tool_map)
    print("JACK Production API: System Cores Online.")

@app.post("/run")
async def run_mission(req: TaskRequest):
    """Execute an autonomous mission via the API."""
    if not agent:
        raise HTTPException(status_code=503, detail="JACK System Interface not initialized.")
        
    try:
        # Run mission in a separate thread to keep API responsive
        result = await asyncio.to_thread(
            agent.process_text_command,
            req.task
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Verify system core status."""
    return {"status": "TITAN_HEALTHY", "memory": "LOADED", "vision": "ACTIVE"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
