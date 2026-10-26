"""STARFALL AI Strategy Evaluation and Outcome Tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from analytics.metrics import AggregatedMetrics


@dataclass
class StrategyOutcome:
    wave: int
    formation: str
    obstacle: str
    difficulty: int
    reason: str
    evidence_cited: List[str]
    outcome_label: str = "inconclusive"  # helpful, harmful, inconclusive
    summary: str = "Evaluating..."
    accuracy_delta: float = 0.0
    damage_taken_in_wave: int = 0
    dodges_in_wave: int = 0
    was_applied: bool = True
    is_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave": self.wave,
            "formation": self.formation,
            "obstacle": self.obstacle,
            "difficulty": self.difficulty,
            "reason": self.reason,
            "evidence_cited": self.evidence_cited,
            "outcome_label": self.outcome_label,
            "summary": self.summary,
            "accuracy_delta": round(self.accuracy_delta, 3),
            "damage_taken_in_wave": self.damage_taken_in_wave,
            "dodges_in_wave": self.dodges_in_wave,
            "was_applied": self.was_applied,
            "is_fallback": self.is_fallback,
        }


def evaluate_strategy_outcome(
    wave: int,
    formation: str,
    obstacle: str,
    difficulty: int,
    reason: str,
    evidence: List[str],
    metrics_before: Optional[AggregatedMetrics],
    metrics_wave: AggregatedMetrics,
    is_fallback: bool = False,
) -> StrategyOutcome:
    """Evaluate whether an applied wave strategy achieved its intended tactical adaptation."""
    acc_before = metrics_before.accuracy if metrics_before else 0.0
    acc_delta = metrics_wave.accuracy - acc_before
    damage = metrics_wave.damage_taken
    dodges = metrics_wave.dodges_successful

    outcome = StrategyOutcome(
        wave=wave,
        formation=formation,
        obstacle=obstacle,
        difficulty=difficulty,
        reason=reason,
        evidence_cited=evidence,
        accuracy_delta=acc_delta,
        damage_taken_in_wave=damage,
        dodges_in_wave=dodges,
        is_fallback=is_fallback,
    )

    if metrics_wave.shots_fired < 3 and metrics_wave.position_samples < 5:
        outcome.outcome_label = "inconclusive"
        outcome.summary = "Insufficient engagement duration to evaluate adaptation."
        return outcome

    # Evaluate outcomes objectively
    if damage > 2:
        # Rapid damage / unfair difficulty spike
        outcome.outcome_label = "harmful"
        outcome.summary = f"Difficulty spike caused severe damage ({damage} hits). Counter-measures recommended."
    elif damage == 0 and dodges >= 2:
        # Player overcame challenge effectively
        outcome.outcome_label = "helpful"
        outcome.summary = f"Player adapted cleanly, successfully dodging threats with {metrics_wave.accuracy:.1%} accuracy."
    elif acc_delta > 0.08:
        outcome.outcome_label = "helpful"
        outcome.summary = f"Formation focused player aim (accuracy rose by {acc_delta:+.1%})."
    elif acc_delta < -0.15:
        outcome.outcome_label = "inconclusive"
        outcome.summary = f"Player accuracy dropped ({acc_delta:+.1%}), indicating heavy evasive pressure."
    else:
        outcome.outcome_label = "helpful"
        outcome.summary = "Balanced engagement maintained consistent pressure without excessive damage."

    return outcome
