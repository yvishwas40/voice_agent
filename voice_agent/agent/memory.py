from typing import List, Dict, Any, Optional
import json
from ..utils.logger import logger

class MemoryManager:
    def __init__(self):
        self.profile: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []

    def update_profile(self, key: str, value: Any):
        """Updates user profile with conflict detection."""
        existing = self.profile.get(key)
        
        # Simple conflict check
        if existing and existing != value:
            # Ignore minor type diffs if values similar (e.g. 5 vs 5.0)
            if str(existing).lower() != str(value).lower():
                logger.warning(f"Conflict detected for {key}: {existing} vs {value}")
                self.conflicts.append({
                    "field": key,
                    "old": existing,
                    "new": value
                })
                # For now, overwrite but log. 
                # Ideally, we pause and ask, but logic here is simple.
        
        self.profile[key] = value
        logger.debug(f"Profile Updated: {key}={value}")

    def add_turn(self, role: str, text: str):
        self.history.append({"role": role, "text": text})

    def get_context_block(self) -> str:
        """Returns specific context for the LLM"""
        return json.dumps({
            "profile": self.profile,
            "recent_history": self.history[-5:], # Last 5 turns
            "known_conflicts": self.conflicts
        }, indent=2)

    def clear(self):
        self.profile = {}
        self.history = []
        self.conflicts = []
