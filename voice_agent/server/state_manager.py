import asyncio
from typing import List, Dict, Any
from ..utils.logger import logger

class StateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.status = "IDLE" # IDLE, LISTENING, THINKING, SPEAKING
            cls._instance.transcript = []
            cls._instance.thoughts = []
            cls._instance.websockets = []
            # whether continuous listening is active (controlled from UI)
            cls._instance.listening_active = False
            # queue of typed text inputs from UI
            cls._instance._text_queue: List[str] = []
        return cls._instance

    async def broadcast(self, message: Dict[str, Any]):
        """Sends updates to all connected websocket clients"""
        if not self.websockets:
            return
            
        disconnected = []
        for ws in self.websockets:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            self.websockets.remove(ws)

    async def set_status(self, status: str):
        if self.status != status:
            self.status = status
            await self.broadcast({"type": "status", "payload": status})

    async def set_listening_active(self, active: bool):
        """Enables or disables continuous listening, as requested by UI."""
        self.listening_active = active
        await self.broadcast(
            {"type": "control", "payload": "listening_on" if active else "listening_off"}
        )

    async def add_text_input(self, text: str):
        """Add a typed user message from UI into the processing queue."""
        if not text:
            return
        # Only add to queue - don't broadcast yet, let agent_service handle it after processing
        # This prevents duplicate messages
        self._text_queue.append(text)

    async def consume_text_input(self) -> str | None:
        """Retrieve the next typed user message if available."""
        if not self._text_queue:
            return None
        return self._text_queue.pop(0)

    async def add_transcript(self, role: str, text: str):
        entry = {"role": role, "text": text}
        self.transcript.append(entry)
        await self.broadcast({"type": "transcript", "payload": entry})

    async def add_thought(self, log_entry: str):
        self.thoughts.append(log_entry)
        await self.broadcast({"type": "thought", "payload": log_entry})
