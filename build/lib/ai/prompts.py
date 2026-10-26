"""STARFALL Gemma 4 Versioned System Prompts and Prompt Builders."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from ai.schemas import ALLOWED_FORMATIONS, ALLOWED_OBSTACLES


TACTICAL_DIRECTOR_SYSTEM_PROMPT = """You are the tactical director of STARFALL, a fair adaptive arcade space shooter.

Analyze only the structured telemetry and previous strategy outcomes supplied by the application.
Identify measured facts and distinguish them from hypotheses. Never invent gameplay events.
Select only supported enemy formations, obstacles, and difficulty configuration from the supplied allowlists.

Rules:
1. Do not modify player controls, score, collisions, lives, or game rules.
2. Do not create unsupported attack types.
3. Respect every spawn, speed, projectile, and difficulty limit.
4. Prefer a small number of meaningful tactical changes over arbitrary difficulty increases.
5. If evidence is insufficient, choose a balanced fallback strategy and report low confidence.
6. Explain the tactical decision in concise language (1-2 sentences) and cite relevant metric identifiers and values.
7. Do not claim that a strategy worked until the next wave has been evaluated.
8. Return only a valid JSON object matching the requested schema.
"""

POST_GAME_ANALYST_SYSTEM_PROMPT = """You are the post-game flight instructor and tactical analyst of STARFALL.

Review the completed match summary, player profiling metrics, and AI adaptation history.
Provide an honest, evidence-backed evaluation:
1. What the player did well (citing specific stats like accuracy, dodges, or movement balance).
2. Main opportunities for improvement.
3. Summary of how the enemy AI adapted to the player's habits across waves.
4. Recommend one specific, measurable training mission for their next run.

Return only a valid JSON object matching the requested schema.
"""


def build_wave_prompt(
    wave: int,
    metrics: Dict[str, Any],
    profile: Dict[str, Any],
    previous_strategy: Dict[str, Any],
    recent_outcomes: List[Dict[str, Any]],
    current_difficulty: int = 2,
    max_difficulty: int = 5,
) -> str:
    """Format user message containing structured gameplay telemetry."""
    payload = {
        "wave": wave,
        "current_difficulty": current_difficulty,
        "max_difficulty": max_difficulty,
        "allowed_formations": ALLOWED_FORMATIONS,
        "allowed_obstacles": ALLOWED_OBSTACLES,
        "player_metrics": {
            "accuracy": metrics.get("accuracy", 0.0),
            "shots_fired": metrics.get("shots_fired", 0),
            "shots_hit": metrics.get("shots_hit", 0),
            "left_zone_time_ratio": metrics.get("left_zone_ratio", 0.33),
            "center_zone_time_ratio": metrics.get("center_zone_ratio", 0.34),
            "right_zone_time_ratio": metrics.get("right_zone_ratio", 0.33),
            "camping_ratio": metrics.get("camping_ratio", 0.0),
            "average_speed": metrics.get("average_speed", 0.0),
            "successful_dodges": metrics.get("dodges_successful", 0),
            "damage_taken": metrics.get("damage_taken", 0),
            "lives_lost": metrics.get("lives_lost", 0),
        },
        "player_profile": {
            "playstyle": profile.get("playstyle_tag", "Unknown"),
            "aim_rating": profile.get("aim_rating", "Unknown"),
            "evasion_rating": profile.get("evasion_rating", "Unknown"),
            "primary_bias": profile.get("primary_bias", "None"),
            "is_sufficient_data": profile.get("is_sufficient_data", False),
        },
        "previous_strategy": previous_strategy,
        "recent_outcomes": recent_outcomes[-3:] if recent_outcomes else [],
    }
    return (
        "Tactical Telemetry Input:\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```\n"
        "Generate the next wave strategy conforming to TacticalStrategyResponse schema."
    )


def build_post_game_prompt(
    total_score: int,
    waves_completed: int,
    survival_seconds: float,
    metrics: Dict[str, Any],
    profile: Dict[str, Any],
    adaptation_history: List[Dict[str, Any]],
) -> str:
    """Format prompt for post-game flight debrief."""
    payload = {
        "match_summary": {
            "total_score": total_score,
            "waves_completed": waves_completed,
            "survival_seconds": survival_seconds,
            "accuracy": metrics.get("accuracy", 0.0),
            "dodges": metrics.get("dodges_successful", 0),
            "lives_lost": metrics.get("lives_lost", 0),
            "camping_ratio": metrics.get("camping_ratio", 0.0),
            "left_ratio": metrics.get("left_zone_ratio", 0.33),
            "right_ratio": metrics.get("right_zone_ratio", 0.33),
        },
        "player_profile": profile,
        "adaptation_history": adaptation_history,
    }
    return (
        "Match Performance Log:\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```\n"
        "Generate post-game flight debrief conforming to PostGameAnalysisResponse schema."
    )
