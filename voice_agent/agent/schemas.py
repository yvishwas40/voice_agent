from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentState(str, Enum):
    START = "START"
    IDLE = "IDLE" 
    LISTENING = "LISTENING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    EVALUATING = "EVALUATING" 
    SPEAKING = "SPEAKING"
    CLARIFYING = "CLARIFYING"
    FAILURE_RECOVERY = "FAILURE_RECOVERY"

class PlanStep(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class PlannerOutput(BaseModel):
    reasoning: str
    intent: str
    next_state: AgentState
    tool_calls: List[PlanStep] = []
    missing_info: List[str] = []
    response_text_if_any: Optional[str] = None # For chit-chat or direct answers

class EvaluatorOutput(BaseModel):
    action: str  # SPEAK, ASK_USER, REPLAN, RETRY
    reason: str
    clean_response: str = "" # Final text to speak
