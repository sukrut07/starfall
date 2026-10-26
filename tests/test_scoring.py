"""Tests for STARFALL Authoritative Scoring System."""

import pytest
from game.scoring import ScoreKeeper


def test_initial_scoring_state():
    sk = ScoreKeeper()
    assert sk.total_score == 0
    assert sk.enemies_destroyed == 0
    assert sk.shots_fired == 0
    assert sk.shots_hit == 0
    assert sk.accuracy == 0.0  # Division by zero safety
    assert sk.successful_dodges == 0
    assert sk.high_score == 0


def test_score_kills_and_accuracy():
    sk = ScoreKeeper()
    sk.record_shot()
    sk.record_shot()
    assert sk.accuracy == 0.0

    sk.record_hit()
    assert sk.accuracy == 0.5

    pts = sk.record_enemy_kill(is_tough=False)
    assert pts == 100
    assert sk.total_score == 100
    assert sk.high_score == 100

    pts_tough = sk.record_enemy_kill(is_tough=True)
    assert pts_tough == 500
    assert sk.total_score == 600
    assert sk.high_score == 600


def test_dodge_and_wave_scoring():
    sk = ScoreKeeper()
    d_pts = sk.record_dodge()
    assert d_pts == 25
    assert sk.successful_dodges == 1

    w_pts = sk.record_wave_completed()
    assert w_pts == 250
    assert sk.waves_completed == 1
    assert sk.total_score == 275


def test_no_negative_score_on_reset():
    sk = ScoreKeeper()
    sk.record_enemy_kill()
    assert sk.high_score == 100
    sk.reset()
    assert sk.total_score == 0
    assert sk.high_score == 100  # High score preserved
