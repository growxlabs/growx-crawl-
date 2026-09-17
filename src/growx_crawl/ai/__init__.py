"""
GrowX AI Platform Boundary.
Unified access point for all LLM and AI models across the system.
"""

from growx_crawl.ai.models import (
    AIRequest,
    AIResponse,
    ClassificationRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    QualityTier,
    RunStatus,
    StructuredAIRequest,
    SummaryRequest,
)
from growx_crawl.ai.cost import MODEL_RATES, calculate_ai_cost, enforce_cost_guard
from growx_crawl.ai.errors import (
    AIBudgetExceeded,
    AICircuitBreakerOpen,
    AIConfigurationError,
    AIError,
    AIInvalidResponse,
    AIRateLimited,
    AISchemaValidationError,
    AITimeout,
    AIProviderUnavailable,
)
from growx_crawl.ai.gateway import AIGateway, ai_gateway
from growx_crawl.ai.prompt_registry import prompt_registry, wrap_untrusted_input
from growx_crawl.ai.prompts import PROMPT_REGISTRY, get_prompt_template
from growx_crawl.ai.repository import InMemoryAIRepository, SqliteAIRepository, ai_repository
from growx_crawl.ai.router import provider_router, route_request
from growx_crawl.ai.tasks import AITask, TaskDefinition, get_task_definition
from growx_crawl.ai.telemetry import AITelemetry, ai_telemetry

__all__ = [
    # Gateway
    "AIGateway",
    "ai_gateway",
    # Models
    "AIRequest",
    "AIResponse",
    "StructuredAIRequest",
    "ClassificationRequest",
    "SummaryRequest",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "QualityTier",
    "RunStatus",
    # Tasks
    "AITask",
    "TaskDefinition",
    "get_task_definition",
    # Cost
    "calculate_ai_cost",
    "enforce_cost_guard",
    "MODEL_RATES",
    # Prompts
    "PROMPT_REGISTRY",
    "get_prompt_template",
    "prompt_registry",
    "wrap_untrusted_input",
    # Telemetry
    "AITelemetry",
    "ai_telemetry",
    # Routing
    "route_request",
    "provider_router",
    # Persistence
    "ai_repository",
    "InMemoryAIRepository",
    "SqliteAIRepository",
    # Errors
    "AIError",
    "AITimeout",
    "AIRateLimited",
    "AIProviderUnavailable",
    "AICircuitBreakerOpen",
    "AIInvalidResponse",
    "AISchemaValidationError",
    "AIBudgetExceeded",
    "AIConfigurationError",
]
