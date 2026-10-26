"""STARFALL Analytics Package."""

from analytics.telemetry import TelemetryCollector, TelemetryEvent
from analytics.metrics import AggregatedMetrics, compute_metrics
from analytics.player_profile import PlayerProfile, build_profile
from analytics.strategy_evaluation import StrategyOutcome, evaluate_strategy_outcome
from analytics.reports import PostGameReport, NextRunMission, generate_next_mission

__all__ = [
    "TelemetryCollector",
    "TelemetryEvent",
    "AggregatedMetrics",
    "compute_metrics",
    "PlayerProfile",
    "build_profile",
    "StrategyOutcome",
    "evaluate_strategy_outcome",
    "PostGameReport",
    "NextRunMission",
    "generate_next_mission",
]
