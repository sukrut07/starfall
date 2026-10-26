"""Tests for STARFALL Deterministic Fallback Strategy."""

import pytest
from ai.fallback import get_deterministic_strategy
from ai.schemas import ALLOWED_FORMATIONS, ALLOWED_OBSTACLES


def test_deterministic_fallback_no_metrics():
    strat = get_deterministic_strategy(wave=1)
    assert strat.formation in ALLOWED_FORMATIONS
    assert strat.obstacle in ALLOWED_OBSTACLES
    assert 1 <= strat.difficulty <= 5
    assert 3 <= strat.spawn_count <= 18
    assert 140.0 <= strat.projectile_speed <= 500.0
    assert strat.confidence >= 0.5


def test_fallback_adapts_to_left_bias():
    metrics = {"left_zone_ratio": 0.70, "right_zone_ratio": 0.10, "camping_ratio": 0.1}
    strat = get_deterministic_strategy(wave=3, metrics=metrics)
    assert strat.formation == "right_flank"
    assert any("left_zone_ratio" in ev for ev in strat.evidence)


def test_fallback_adapts_to_camping():
    metrics = {"camping_ratio": 0.65}
    strat = get_deterministic_strategy(wave=2, metrics=metrics)
    assert strat.formation == "converging_pincer"
    assert strat.obstacle == "slow_moving_barriers"
    assert any("camping_ratio" in ev for ev in strat.evidence)


def test_fallback_scales_with_wave():
    strat_w1 = get_deterministic_strategy(wave=1)
    strat_w5 = get_deterministic_strategy(wave=5)
    assert strat_w5.difficulty >= strat_w1.difficulty
    assert strat_w5.spawn_count >= strat_w1.spawn_count
