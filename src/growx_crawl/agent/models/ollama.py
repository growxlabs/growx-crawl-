import os
from typing import Any, Dict, List, Optional
import httpx
from growx_crawl.agent.models.base import AgentMessage, AgentModel, AgentResponse


class OllamaAgentModel(AgentModel):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("GROWX_AGENT_MODEL", "llama3.2")

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as http:
                res = http.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def generate(self, messages: List[AgentMessage], tools: Optional[List[Dict[str, Any]]] = None) -> AgentResponse:
        if not self.is_available():
            return AgentResponse(content="Local Ollama instance not reachable at " + self.base_url)

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "stream": False,
        }

        try:
            with httpx.Client(timeout=45.0) as http:
                resp = http.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                msg = data.get("message", {})
                return AgentResponse(content=msg.get("content") or "")
        except Exception as e:
            return AgentResponse(content=f"Ollama API error: {str(e)}")
