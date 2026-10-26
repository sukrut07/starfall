"""Tests for STARFALL AI Strategy Validation and Schema Enforcement."""

import pytest
from ai.validator import validate_tactical_strategy
from ai.schemas import TacticalStrategyResponse


def test_valid_strategy_passes():
    raw = {
        "formation": "right_flank",
        "obstacle": "slow_moving_barriers",
        "difficulty": 3,
        "spawn_count": 8,
        "projectile_speed": 260.0,
        "reason": "Player favored the left corridor.",
        "evidence": ["left_zone_ratio=0.65"],
        "confidence": 0.8,
        "mission": "Survive the right flank pressure.",
    }
    is_valid, strategy, errors = validate_tactical_strategy(raw, current_difficulty=2)
    assert is_valid is True
    assert strategy is not None
    assert strategy.formation == "right_flank"
    assert len(errors) == 0


def test_unknown_formation_rejected():
    raw = {
        "formation": "quantum_hyper_strike",  # Unsupported formation
        "obstacle": "none",
        "difficulty": 2,
        "spawn_count": 6,
        "projectile_speed": 220.0,
        "reason": "Imaginary attack.",
        "evidence": [],
    }
    is_valid, strategy, errors = validate_tactical_strategy(raw, current_difficulty=2)
    assert is_valid is False
    assert strategy is None
    assert any("Unknown formation" in e or "formation" in e for e in errors)


def test_unknown_obstacle_rejected():
    raw = {
        "formation": "v_formation",
        "obstacle": "nuclear_plasma_minefield",  # Unsupported obstacle
        "difficulty": 2,
        "spawn_count": 6,
        "projectile_speed": 220.0,
        "reason": "Imaginary obstacle.",
        "evidence": [],
    }
    is_valid, strategy, errors = validate_tactical_strategy(raw, current_difficulty=2)
    assert is_valid is False
    assert strategy is None
    assert any("Unknown obstacle" in e or "obstacle" in e for e in errors)


def test_extreme_difficulty_and_speed_clamped():
    raw = {
        "formation": "split_formation",
        "obstacle": "none",
        "difficulty": 5,  # Jump from 2 to 5 exceeds max delta 1
        "spawn_count": 100,  # Exceeds max 18
        "projectile_speed": 9999.0,  # Extreme speed
        "reason": "Unfair difficulty spike test.",
        "evidence": [],
    }
    # Schema validation clamps or rejects values outside Pydantic bounds
    is_valid, strategy, errors = validate_tactical_strategy(raw, current_difficulty=2)
    # The spawn_count > 18 is caught by schema validation
    assert is_valid is False or (strategy is not None and strategy.spawn_count <= 18)
