"""STARFALL Deterministic Strategy Fallback Engine."""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from ai.schemas import TacticalStrategyResponse


def get_deterministic_strategy(
    wave: int,
    metrics: Optional[Dict[str, Any]] = None,
    difficulty_cap: int = 4,
) -> TacticalStrategyResponse:
    """
    Deterministic offline fallback policy that selects from known, tested patterns.
    Never crashes, never depends on Ollama or network.
    """
    metrics = metrics or {}
    left_ratio = metrics.get("left_zone_ratio", 0.33)
    right_ratio = metrics.get("right_zone_ratio", 0.33)
    camping_ratio = metrics.get("camping_ratio", 0.0)
    accuracy = metrics.get("accuracy", 0.0)
    damage = metrics.get("damage_taken", 0)

    # Base difficulty escalation
    diff = min(difficulty_cap, max(1, 1 + (wave // 2)))
    # Reduce difficulty if player took heavy damage
    if damage >= 2:
        diff = max(1, diff - 1)

    spawn_count = min(16, 6 + (diff * 2))
    p_speed = min(400.0, 190.0 + (diff * 35.0))

    # Evidence-grounded deterministic choices
    if camping_ratio >= 0.50:
        formation = "converging_pincer"
        obstacle = "slow_moving_barriers"
        reason = f"Player showed high stationary ratio ({camping_ratio:.0%}). Deployed converging pincer to encourage movement."
        evidence = [f"camping_ratio={camping_ratio:.2f}"]
    elif left_ratio >= 0.55:
        formation = "right_flank"
        obstacle = "telegraphed_laser_lane"
        reason = f"Player favored the left lane ({left_ratio:.0%}). Deployed right-flank formation to test lateral repositioning."
        evidence = [f"left_zone_ratio={left_ratio:.2f}"]
    elif right_ratio >= 0.55:
        formation = "left_flank"
        obstacle = "telegraphed_laser_lane"
        reason = f"Player favored the right lane ({right_ratio:.0%}). Deployed left-flank pressure."
        evidence = [f"right_zone_ratio={right_ratio:.2f}"]
    elif accuracy >= 0.40:
        formation = "split_formation"
        obstacle = "drifting_asteroids"
        reason = f"Player demonstrated high firing accuracy ({accuracy:.0%}). Splitting targets to test cross-screen tracking."
        evidence = [f"accuracy={accuracy:.2f}"]
    else:
        # Default balanced escalation
        cycle = ["v_formation", "center_sweep", "staggered_assault"]
        formation = cycle[(wave - 1) % len(cycle)]
        obstacle = "none" if wave <= 2 else "slow_moving_barriers"
        reason = f"Standard balanced tactical wave {wave} matching baseline skill."
        evidence = [f"wave={wave}", "balanced_progression"]

    return TacticalStrategyResponse(
        formation=formation,
        obstacle=obstacle,
        difficulty=diff,
        spawn_count=spawn_count,
        projectile_speed=p_speed,
        reason=reason,
        evidence=evidence,
        confidence=0.55,
        mission=f"Clear wave {wave} against {formation.replace('_', ' ')}.",
    )
