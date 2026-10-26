"""STARFALL Gameplay Metrics Calculation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Any
from analytics.telemetry import TelemetryCollector, TelemetryEvent


@dataclass
class AggregatedMetrics:
    shots_fired: int = 0
    shots_hit: int = 0
    accuracy: float = 0.0
    enemies_destroyed: int = 0
    dodges_successful: int = 0
    threats_encountered: int = 0
    dodge_rate: float = 0.0
    lives_lost: int = 0
    damage_taken: int = 0
    survival_seconds: float = 0.0
    waves_completed: int = 0

    # Spatial behavior
    position_samples: int = 0
    left_zone_ratio: float = 0.33
    center_zone_ratio: float = 0.34
    right_zone_ratio: float = 0.33
    camping_ratio: float = 0.0
    total_movement_distance: float = 0.0
    average_speed: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shots_fired": self.shots_fired,
            "shots_hit": self.shots_hit,
            "accuracy": round(self.accuracy, 4),
            "enemies_destroyed": self.enemies_destroyed,
            "dodges_successful": self.dodges_successful,
            "threats_encountered": self.threats_encountered,
            "dodge_rate": round(self.dodge_rate, 4),
            "lives_lost": self.lives_lost,
            "damage_taken": self.damage_taken,
            "survival_seconds": round(self.survival_seconds, 2),
            "waves_completed": self.waves_completed,
            "position_samples": self.position_samples,
            "left_zone_ratio": round(self.left_zone_ratio, 3),
            "center_zone_ratio": round(self.center_zone_ratio, 3),
            "right_zone_ratio": round(self.right_zone_ratio, 3),
            "camping_ratio": round(self.camping_ratio, 3),
            "total_movement_distance": round(self.total_movement_distance, 1),
            "average_speed": round(self.average_speed, 1),
        }


def compute_metrics(events: List[TelemetryEvent], total_duration: float = 0.0) -> AggregatedMetrics:
    """Compute measurable metrics from a list of telemetry events."""
    m = AggregatedMetrics()
    if not events:
        return m

    m.survival_seconds = total_duration if total_duration > 0.0 else (events[-1].timestamp - events[0].timestamp if len(events) > 1 else 0.0)

    # Count events
    shots_fired = 0
    shots_hit = 0
    enemies_destroyed = 0
    dodges = 0
    threats = 0
    lives_lost = 0
    damage_taken = 0
    waves_completed = 0

    pos_samples: List[tuple[float, float, float]] = []  # timestamp, x, norm_x

    for ev in events:
        t = ev.event_type
        d = ev.data

        if t == "player_fired":
            shots_fired += d.get("shots_count", 1)
        elif t == "enemy_hit":
            shots_hit += 1
        elif t == "enemy_destroyed":
            enemies_destroyed += 1
        elif t == "dodge_successful":
            dodges += 1
            threats += 1
        elif t == "player_hit" or t == "player_rammed" or t == "player_hit_obstacle" or t == "player_hit_laser":
            lives_lost += 1
            damage_taken += 1
            threats += 1
        elif t == "player_shield_absorbed":
            damage_taken += 1
            threats += 1
        elif t == "wave_completed":
            waves_completed += 1
        elif t == "player_position":
            x = d.get("x", 400.0)
            norm_x = d.get("norm_x", 0.5)
            pos_samples.append((ev.timestamp, x, norm_x))

    m.shots_fired = shots_fired
    m.shots_hit = shots_hit
    m.accuracy = min(1.0, shots_hit / shots_fired) if shots_fired > 0 else 0.0
    m.enemies_destroyed = enemies_destroyed
    m.dodges_successful = dodges
    m.threats_encountered = max(threats, dodges)
    m.dodge_rate = (dodges / m.threats_encountered) if m.threats_encountered > 0 else 0.0
    m.lives_lost = lives_lost
    m.damage_taken = damage_taken
    m.waves_completed = waves_completed

    # Analyze position distribution
    m.position_samples = len(pos_samples)
    if pos_samples:
        left_count = sum(1 for _, _, nx in pos_samples if nx < 0.35)
        center_count = sum(1 for _, _, nx in pos_samples if 0.35 <= nx <= 0.65)
        right_count = sum(1 for _, _, nx in pos_samples if nx > 0.65)
        total_p = len(pos_samples)
        m.left_zone_ratio = left_count / total_p
        m.center_zone_ratio = center_count / total_p
        m.right_zone_ratio = right_count / total_p

        # Compute movement distance and camping
        dist = 0.0
        stationary_samples = 0
        for i in range(1, len(pos_samples)):
            dx = abs(pos_samples[i][1] - pos_samples[i - 1][1])
            dist += dx
            if dx < 3.0:  # Moved less than 3 pixels between samples
                stationary_samples += 1

        m.total_movement_distance = dist
        m.camping_ratio = (stationary_samples / max(1, len(pos_samples) - 1))
        duration = max(0.1, m.survival_seconds)
        m.average_speed = dist / duration

    return m
