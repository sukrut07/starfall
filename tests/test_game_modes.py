"""Tests for STARFALL Game Modes, Simulation Lifecycle, and Headless Runs."""

import pytest
from game.engine import GameEngine
from game.state import GameStatus, InputCommand
from game.waves import WavePlan
from renderers.terminal_renderer import TerminalRenderer
from analytics.telemetry import TelemetryCollector
from analytics.metrics import compute_metrics
from analytics.player_profile import build_profile
from analytics.reports import PostGameReport, generate_next_mission
from ai.strategy_graph import AIStrategyOrchestrator


def test_headless_game_simulation_lifecycle():
    engine = GameEngine(width=800.0, height=700.0)
    engine.start_game()
    assert engine.status == GameStatus.PLAYING
    assert engine.player.lives == 3

    # Fast forward through initial 1.5s wave intermission
    engine.update(1.6, InputCommand())
    assert engine.wave_manager.current_wave_num == 1
    assert len(engine.enemies) > 0

    initial_enemy_count = len(engine.enemies)

    # Simulate player moving and firing
    cmd_fire = InputCommand(move_x=0.0, move_y=0.0, fire=True)
    engine.update(0.05, cmd_fire)

    assert len(engine.projectiles) > 0
    assert engine.score_keeper.shots_fired > 0

    # Test clamping: player cannot move outside game area
    cmd_left = InputCommand(move_x=-50.0, move_y=0.0)
    for _ in range(30):
        engine.update(0.05, cmd_left)
    assert engine.player.x >= engine.player.radius

    cmd_right = InputCommand(move_x=50.0, move_y=0.0)
    for _ in range(30):
        engine.update(0.05, cmd_right)
    assert engine.player.x <= (800.0 - engine.player.radius)


def test_terminal_renderer_snapshot_generation():
    engine = GameEngine(width=800.0, height=700.0)
    engine.start_game()
    engine.update(1.6, InputCommand())

    snapshot = engine.get_snapshot()
    renderer = TerminalRenderer(cols=72, rows=22)
    # Ensure snapshot holds all required attributes for terminal rendering
    assert snapshot.score >= 0
    assert snapshot.current_wave == 1
    assert len(snapshot.enemies) > 0
    assert snapshot.player_x > 0
    assert snapshot.player_y > 0


def test_strategy_queue_at_wave_boundary():
    engine = GameEngine(width=800.0, height=700.0)
    engine.start_game()

    custom_plan = WavePlan(
        formation="left_flank",
        obstacle="slow_moving_barriers",
        difficulty=3,
        spawn_count=6,
        projectile_speed=250.0,
        reason="Testing wave queue.",
        evidence=["test_run"],
        confidence=0.9,
    )
    # Queue plan
    engine.queue_strategy_plan(custom_plan)
    assert engine.wave_manager.next_queued_plan == custom_plan

    # Advance wave intermission
    engine.update(2.0, InputCommand())
    # Should apply the queued plan at the wave boundary
    assert engine.wave_manager.active_plan.formation == "left_flank"
    assert engine.wave_manager.active_plan.difficulty == 3
    assert engine.wave_manager.next_queued_plan is None


def test_complete_match_report_generation():
    collector = TelemetryCollector(match_id="test_run_1")
    engine = GameEngine()
    engine.set_telemetry_callback(lambda t, d: collector.record(t, d))
    engine.start_game()

    # Advance simulation
    engine.update(1.6, InputCommand(fire=True))
    # Record hit and kill
    collector.record("player_fired", {"shots_count": 2})
    collector.record("enemy_hit", {})
    collector.record("enemy_destroyed", {"points": 100})
    collector.record("dodge_successful", {"points": 25})

    metrics = compute_metrics(collector.events, total_duration=10.0)
    profile = build_profile(metrics)
    next_mission = generate_next_mission(metrics, profile)

    report = PostGameReport(
        match_id="test_run_1",
        total_score=125,
        waves_completed=1,
        survival_seconds=10.0,
        enemies_destroyed=1,
        shots_fired=2,
        shots_hit=1,
        accuracy=0.5,
        dodges=1,
        lives_lost=0,
        metrics=metrics,
        profile=profile,
        adaptation_history=[],
        next_mission=next_mission,
    )

    d = report.to_dict()
    assert d["total_score"] == 125
    assert d["accuracy"] == 0.5
    assert "metrics" in d
    assert "profile" in d
    assert "next_mission" in d
