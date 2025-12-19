import asyncio
import json
import os
import sys
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_agent.server.agent_service import AgentService
from voice_agent.server.state_manager import StateManager
from voice_agent.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Resolve paths relative to this file so it works no matter
# where you run the app from (project root or inside package)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

# Mount Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Agent Service
agent_service = AgentService()
state_manager = StateManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Agent Service...")
    await agent_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping Agent Service...")
    await agent_service.stop()

@app.get("/")
async def get():
    # Serve the dashboard HTML
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state_manager.websockets.append(websocket)
    try:
        # Send initial state
        await websocket.send_json({"type": "status", "payload": state_manager.status})
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue

            msg_type = data.get("type")
            if msg_type == "listen_start":
                # UI asked to start continuous listening
                await state_manager.set_listening_active(True)
            elif msg_type == "listen_stop":
                # UI asked to stop listening
                await state_manager.set_listening_active(False)
            elif msg_type == "text":
                text = (data.get("payload") or "").strip()
                if text:
                    await state_manager.add_text_input(text)
    except WebSocketDisconnect:
        state_manager.websockets.remove(websocket)

def start():
    logger.info("Starting Web Server at http://localhost:8001")
    uvicorn.run("voice_agent.app:app", host="0.0.0.0", port=8001, reload=False)

if __name__ == "__main__":
    start()
