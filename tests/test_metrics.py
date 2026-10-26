"""Tests for STARFALL Metrics and Player Profiling."""

import pytest
from analytics.telemetry import TelemetryCollector
from analytics.metrics import compute_metrics
from analytics.player_profile import build_profile


def test_metrics_empty_events():
    collector = TelemetryCollector()
    metrics = compute_metrics(collector.events)
    assert metrics.shots_fired == 0
    assert metrics.accuracy == 0.0
    assert metrics.dodge_rate == 0.0
    assert metrics.position_samples == 0


def test_metrics_and_profile_with_events():
    collector = TelemetryCollector()
    # 4 shots, 2 hits -> 50% accuracy
    collector.record("player_fired", {"shots_count": 2})
    collector.record("enemy_hit", {})
    collector.record("player_fired", {"shots_count": 2})
    collector.record("enemy_hit", {})
    collector.record("enemy_destroyed", {})

    # Add position samples in left lane
    for _ in range(12):
        collector.record("player_position", {"x": 120.0, "norm_x": 0.20})

    metrics = compute_metrics(collector.events, total_duration=10.0)
    assert metrics.shots_fired == 4
    assert metrics.shots_hit == 2
    assert metrics.accuracy == 0.50
    assert metrics.left_zone_ratio == 1.0

    profile = build_profile(metrics)
    assert profile.is_sufficient_data is True
    assert profile.aim_rating == "Sharpshooter"
    assert "Left" in profile.primary_bias or "Port-Wing" in profile.playstyle_tag
