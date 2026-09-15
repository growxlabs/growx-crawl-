import os
from typing import Any, Dict, List, Optional
import httpx
from growx_crawl.agent.models.base import AgentMessage, AgentModel, AgentResponse


class OpenRouterAgentModel(AgentModel):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or os.getenv("GROWX_AGENT_MODEL", "openrouter/free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: List[AgentMessage], tools: Optional[List[Dict[str, Any]]] = None) -> AgentResponse:
        if not self.is_available():
            return AgentResponse(content="OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://growxlabs.tech",
            "X-Title": "GrowX Crawl Agent",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=30.0) as http:
                resp = http.post(self.base_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                t_calls = msg.get("tool_calls") or []
                return AgentResponse(content=content, tool_calls=t_calls, finish_reason=choice.get("finish_reason", "stop"))
        except Exception as e:
            return AgentResponse(content=f"OpenRouter API error: {str(e)}")
