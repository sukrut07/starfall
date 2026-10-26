"""STARFALL Strategy Output Validator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from ai.schemas import (
    ALLOWED_FORMATIONS,
    ALLOWED_OBSTACLES,
    TacticalStrategyResponse,
)


def validate_tactical_strategy(
    raw_data: Any,
    current_difficulty: int = 2,
    max_difficulty_delta: int = 1,
    max_difficulty_cap: int = 5,
) -> Tuple[bool, Optional[TacticalStrategyResponse], List[str]]:
    """
    Validate raw model response against schema and safety bounds.
    Returns (is_valid, validated_strategy, error_messages).
    """
    errors: List[str] = []

    if not isinstance(raw_data, dict):
        return False, None, ["Model output was not a valid dictionary/JSON object."]

    # 1. Pydantic schema validation
    try:
        strategy = TacticalStrategyResponse(**raw_data)
    except Exception as e:
        return False, None, [f"Schema validation error: {str(e)}"]

    # 2. Strict independent boundary checks
    if strategy.formation not in ALLOWED_FORMATIONS:
        errors.append(f"Formation '{strategy.formation}' not in allowed list: {ALLOWED_FORMATIONS}")

    if strategy.obstacle not in ALLOWED_OBSTACLES:
        errors.append(f"Obstacle '{strategy.obstacle}' not in allowed list: {ALLOWED_OBSTACLES}")

    # Clamp or enforce difficulty delta
    if abs(strategy.difficulty - current_difficulty) > max_difficulty_delta:
        # Enforce difficulty ceiling / gradual ramp
        clamped_diff = max(
            1,
            min(
                max_difficulty_cap,
                current_difficulty + (max_difficulty_delta if strategy.difficulty > current_difficulty else -max_difficulty_delta),
            ),
        )
        strategy.difficulty = clamped_diff

    # Independent projectile speed bounds
    if strategy.projectile_speed > 520.0:
        strategy.projectile_speed = 520.0
    elif strategy.projectile_speed < 140.0:
        strategy.projectile_speed = 140.0

    # Independent spawn count bounds
    if strategy.spawn_count > 18:
        strategy.spawn_count = 18
    elif strategy.spawn_count < 3:
        strategy.spawn_count = 3

    if errors:
        return False, None, errors

    return True, strategy, []
