from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ToolInput(BaseModel):
    """Base class for tool inputs"""
    pass

class ToolOutput(BaseModel):
    """Standardized output for all tools"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

class EligibilityInput(ToolInput):
    age: Optional[int] = None
    income: Optional[int] = None
    occupation: Optional[str] = None
    land_acres: Optional[float] = None
    caste: Optional[str] = None
    # Add other fields as needed

class SchemeLookupInput(ToolInput):
    scheme_id: Optional[str] = None
    keywords: Optional[Any] = None # Relaxed type to handle str input

    @property
    def keywords_list(self) -> List[str]:
        if isinstance(self.keywords, str):
            return [self.keywords]
        if isinstance(self.keywords, list):
            return [str(k) for k in self.keywords]
        return []
