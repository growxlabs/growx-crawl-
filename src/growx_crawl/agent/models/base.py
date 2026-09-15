from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class AgentResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    finish_reason: str = "stop"
    usage: Dict[str, int] = Field(default_factory=dict)


class AgentModel(ABC):
    @abstractmethod
    def generate(self, messages: List[AgentMessage], tools: Optional[List[Dict[str, Any]]] = None) -> AgentResponse:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
