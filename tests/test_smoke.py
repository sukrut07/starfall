"""Smoke test verifying end-to-end match execution with simulated input."""

import time
from game.engine import GameEngine
from game.state import InputCommand
from renderers.terminal_renderer import TerminalRenderer
from analytics.telemetry import TelemetryCollector
from analytics.metrics import compute_metrics
from analytics.player_profile import build_profile
from analytics.reports import PostGameReport, generate_next_mission
from persistence.database import init_database
from persistence.repositories import MatchRepository


def test_full_match_smoke_simulation():
    db = init_database(":memory:")
    repo = MatchRepository(db)

    collector = TelemetryCollector(match_id="smoke_test_run")
    engine = GameEngine(width=800.0, height=700.0)
    engine.set_telemetry_callback(lambda t, d: collector.record(t, d))
    engine.start_game()

    renderer = TerminalRenderer(cols=72, rows=22)

    # Simulate 50 frames of real gameplay
    for f in range(50):
        # Fire on every 5th frame, alternate movement
        move_x = 1.0 if f % 10 < 5 else -1.0
        fire = (f % 5 == 0)
        cmd = InputCommand(move_x=move_x, move_y=0.0, fire=fire)
        engine.update(0.04, cmd)

        # Get snapshot and test rendering logic
        snap = engine.get_snapshot()
        assert snap is not None

    # End simulation and save match
    metrics = compute_metrics(collector.events, total_duration=engine.match_time)
    profile = build_profile(metrics)
    next_mission = generate_next_mission(metrics, profile)

    report = PostGameReport(
        match_id="smoke_test_run",
        total_score=engine.score_keeper.total_score,
        waves_completed=engine.score_keeper.waves_completed,
        survival_seconds=engine.match_time,
        enemies_destroyed=engine.score_keeper.enemies_destroyed,
        shots_fired=engine.score_keeper.shots_fired,
        shots_hit=engine.score_keeper.shots_hit,
        accuracy=engine.score_keeper.accuracy,
        dodges=engine.score_keeper.successful_dodges,
        lives_lost=engine.score_keeper.lives_lost,
        metrics=metrics,
        profile=profile,
        adaptation_history=[],
        next_mission=next_mission,
    )

    repo.save_match(report)
    recent = repo.get_recent_matches(limit=1)
    assert len(recent) == 1
    assert recent[0]["match_id"] == "smoke_test_run"

    last_rep = repo.get_last_match_report()
    assert last_rep is not None
    assert last_rep["match_id"] == "smoke_test_run"
    db.close()
