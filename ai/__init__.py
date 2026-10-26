"""STARFALL AI Package."""

from ai.schemas import (
    ALLOWED_FORMATIONS,
    ALLOWED_OBSTACLES,
    TacticalStrategyResponse,
    PostGameAnalysisResponse,
)
from ai.ollama_client import OllamaClientWrapper
from ai.model_registry import get_model_info, list_supported_models
from ai.prompts import (
    TACTICAL_DIRECTOR_SYSTEM_PROMPT,
    POST_GAME_ANALYST_SYSTEM_PROMPT,
    build_wave_prompt,
    build_post_game_prompt,
)
from ai.validator import validate_tactical_strategy
from ai.fallback import get_deterministic_strategy
from ai.strategy_graph import (
    create_strategy_graph,
    AIStrategyOrchestrator,
    GraphState,
)

__all__ = [
    "ALLOWED_FORMATIONS",
    "ALLOWED_OBSTACLES",
    "TacticalStrategyResponse",
    "PostGameAnalysisResponse",
    "OllamaClientWrapper",
    "get_model_info",
    "list_supported_models",
    "TACTICAL_DIRECTOR_SYSTEM_PROMPT",
    "POST_GAME_ANALYST_SYSTEM_PROMPT",
    "build_wave_prompt",
    "build_post_game_prompt",
    "validate_tactical_strategy",
    "get_deterministic_strategy",
    "create_strategy_graph",
    "AIStrategyOrchestrator",
    "GraphState",
]
