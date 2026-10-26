"""STARFALL Post-Game Analytics Report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from analytics.metrics import AggregatedMetrics
from analytics.player_profile import PlayerProfile
from analytics.strategy_evaluation import StrategyOutcome


@dataclass
class NextRunMission:
    title: str
    target_metric: str
    target_value: float
    current_value: float
    rationale: str
    measurement_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "target_metric": self.target_metric,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "rationale": self.rationale,
            "measurement_description": self.measurement_description,
        }


@dataclass
class PostGameReport:
    match_id: str
    total_score: int
    waves_completed: int
    survival_seconds: float
    enemies_destroyed: int
    shots_fired: int
    shots_hit: int
    accuracy: float
    dodges: int
    lives_lost: int
    metrics: AggregatedMetrics
    profile: PlayerProfile
    adaptation_history: List[StrategyOutcome]
    next_mission: NextRunMission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "total_score": self.total_score,
            "waves_completed": self.waves_completed,
            "survival_seconds": round(self.survival_seconds, 1),
            "enemies_destroyed": self.enemies_destroyed,
            "shots_fired": self.shots_fired,
            "shots_hit": self.shots_hit,
            "accuracy": round(self.accuracy, 4),
            "dodges": self.dodges,
            "lives_lost": self.lives_lost,
            "metrics": self.metrics.to_dict(),
            "profile": self.profile.to_dict(),
            "adaptation_history": [o.to_dict() for o in self.adaptation_history],
            "next_mission": self.next_mission.to_dict(),
        }


def generate_next_mission(metrics: AggregatedMetrics, profile: PlayerProfile) -> NextRunMission:
    """Generate a measurable next-run training mission based on observed weaknesses."""
    if metrics.accuracy < 0.30:
        target_acc = round(min(0.50, metrics.accuracy + 0.12), 2)
        return NextRunMission(
            title="Precision Calisthenics",
            target_metric="accuracy",
            target_value=target_acc,
            current_value=round(metrics.accuracy, 2),
            rationale="Firing accuracy was below 30%. Controlled shot bursts will conserve energy and increase score.",
            measurement_description=f"Achieve at least {target_acc:.0%} accuracy across at least 2 waves.",
        )
    elif metrics.left_zone_ratio > 0.55:
        return NextRunMission(
            title="Lateral Breakout",
            target_metric="right_zone_ratio",
            target_value=0.35,
            current_value=round(metrics.right_zone_ratio, 2),
            rationale="Player spent over 55% of the match pinned to the left lane.",
            measurement_description="Spend at least 35% of flight time in the right and center quadrants.",
        )
    elif metrics.camping_ratio > 0.45:
        return NextRunMission(
            title="Dynamic Repositioning",
            target_metric="camping_ratio",
            target_value=0.25,
            current_value=round(metrics.camping_ratio, 2),
            rationale="High stationary ratio allowed enemy formations to converge with focused fire.",
            measurement_description="Reduce stationary camping ratio below 25% by actively cycling flight lanes.",
        )
    else:
        target_dodges = metrics.dodges_successful + 4
        return NextRunMission(
            title="Acrobatic Threat Evasion",
            target_metric="dodges_successful",
            target_value=float(target_dodges),
            current_value=float(metrics.dodges_successful),
            rationale="Strong fundamentals detected. Next milestone tests close-quarters projectile evasion.",
            measurement_description=f"Successfully execute at least {target_dodges} close-proximity threat dodges.",
        )
