"""STARFALL HUD and Tactical Formatter."""

from __future__ import annotations

from typing import Any, Dict, List
from game.state import GameStateSnapshot


def format_hud_header(snapshot: GameStateSnapshot) -> str:
    """Format single-line concise HUD header."""
    lives_str = "♥" * max(0, snapshot.player_lives)
    shield_str = " [SHIELD]" if snapshot.player_shield else ""
    return (
        f"SCORE: {snapshot.score:06d} | "
        f"WAVE: {snapshot.current_wave} | "
        f"LIVES: {lives_str}{shield_str} | "
        f"ACC: {snapshot.accuracy:.1%} | "
        f"DODGES: {snapshot.dodges}"
    )


def format_tactical_panel(snapshot: GameStateSnapshot, ai_status: str) -> List[str]:
    """Format multi-line AI Commander tactical briefing."""
    plan = snapshot.active_plan
    fallback_badge = "[FALLBACK]" if plan.is_fallback else "[GEMMA 4 ADAPTED]"
    evidence_str = ", ".join(plan.evidence) if plan.evidence else "baseline"

    lines = [
        f"─── AI COMMANDER {fallback_badge} ───",
        f"FORMATION : {plan.formation.upper()} (Diff: {plan.difficulty}, Enemies: {plan.spawn_count})",
        f"OBSTACLE  : {plan.obstacle.upper()}",
        f"REASONING : {plan.reason}",
        f"EVIDENCE  : {evidence_str} (Confidence: {plan.confidence:.0%})",
        f"STATUS    : {ai_status}",
    ]
    if plan.mission:
        lines.append(f"MISSION   : {plan.mission}")
    return lines
