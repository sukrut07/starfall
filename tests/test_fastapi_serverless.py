"""Tests for STARFALL FastAPI Serverless Backend and Telemetry Contracts."""

import pytest
from fastapi.testclient import TestClient
from api.index import app
from ai.schemas import ALLOWED_FORMATIONS, ALLOWED_OBSTACLES


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    """GET /api/health returns valid JSON without exposing secrets."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["app"] == "STARFALL"
    assert data["status"] == "healthy"
    assert "version" in data
    assert "configured_model" in data
    assert "inference_reachable" in data
    assert data["fallback_available"] is True
    # Ensure no secrets, keys, or internal file paths leaked
    assert "api_key" not in data
    assert "password" not in data
    assert "secret" not in data
    assert "/" not in data.get("app_title", "")


def test_config_endpoint(client):
    """GET /api/config returns safe public client configuration."""
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()

    assert "control_modes" in data
    assert "keyboard" in data["control_modes"]
    assert "gesture" in data["control_modes"]

    assert "game_settings" in data
    assert data["game_settings"]["canvas_width"] == 800
    assert data["game_settings"]["canvas_height"] == 480

    assert data["supported_formations"] == ALLOWED_FORMATIONS
    assert data["allowed_obstacles"] == ALLOWED_OBSTACLES
    assert data["gesture_enabled"] is True

    # Check safe AI service status
    assert "ai_service" in data
    assert "provider" in data["ai_service"]
    assert "configured_model" in data["ai_service"]


def test_strategy_endpoint_valid_request(client):
    """POST /api/strategy accepts telemetry and returns a bounded tactical plan."""
    payload = {
        "wave": 3,
        "shots_fired": 40,
        "shots_hit": 28,
        "accuracy": 0.70,
        "movement_distribution": {"left": 0.65, "center": 0.20, "right": 0.15},
        "camping_ratio": 0.10,
        "dodges": 5,
        "lives_lost": 0,
        "current_difficulty": 2,
    }
    resp = client.post("/api/strategy", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["formation"] in ALLOWED_FORMATIONS
    assert data["obstacle"] in ALLOWED_OBSTACLES
    assert 1 <= data["difficulty"] <= 5
    assert 3 <= data["spawn_count"] <= 24
    assert 140.0 <= data["projectile_speed"] <= 500.0
    assert len(data["reason"]) > 0
    assert isinstance(data["evidence"], list)
    assert 0.0 <= data["confidence"] <= 1.0


def test_strategy_endpoint_fallback_adaptation(client):
    """POST /api/strategy adapts correctly to high left lane bias with deterministic fallback."""
    payload = {
        "wave": 2,
        "shots_fired": 20,
        "shots_hit": 10,
        "accuracy": 0.50,
        "movement_distribution": {"left": 0.80, "center": 0.10, "right": 0.10},
        "camping_ratio": 0.05,
        "dodges": 2,
        "lives_lost": 0,
        "current_difficulty": 2,
    }
    resp = client.post("/api/strategy", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # High left lane ratio (80%) triggers right_flank deployment
    if data["is_fallback"]:
        assert data["formation"] == "right_flank"
        assert any("left_zone_ratio" in e for e in data["evidence"])


def test_strategy_endpoint_invalid_payload_rejected(client):
    """POST /api/strategy rejects invalid numeric bounds (e.g. negative wave or accuracy > 1)."""
    # Negative wave
    resp = client.post("/api/strategy", json={"wave": -1, "accuracy": 0.5})
    assert resp.status_code == 422

    # Accuracy over 1.0
    resp = client.post("/api/strategy", json={"wave": 2, "accuracy": 1.5})
    assert resp.status_code == 422


def test_analyze_endpoint(client):
    """POST /api/analyze produces a structured flight debrief with measurable next mission."""
    payload = {
        "match_id": "stf-test-01",
        "total_score": 14500,
        "waves_completed": 4,
        "survival_seconds": 124.5,
        "enemies_destroyed": 24,
        "shots_fired": 80,
        "shots_hit": 36,
        "accuracy": 0.45,
        "dodges": 8,
        "lives_lost": 2,
        "movement_distribution": {"left": 0.30, "center": 0.40, "right": 0.30},
        "camping_ratio": 0.15,
        "strategies_applied": [{"wave": 2, "formation": "v_formation"}],
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["match_id"] == "stf-test-01"
    assert data["total_score"] == 14500
    assert data["waves_completed"] == 4
    assert data["accuracy"] == 0.45
    assert data["dodges"] == 8

    # Profile assertions
    assert "profile" in data
    assert "playstyle_tag" in data["profile"]
    assert "observed_weakness" in data["profile"]

    # Next mission objective assertions
    assert "next_mission" in data
    mission = data["next_mission"]
    assert "title" in mission
    assert "target_metric" in mission
    assert "measurement_description" in mission
    assert len(mission["rationale"]) > 0

    # Gemma analysis assertions
    assert "gemma_analysis" in data
    gemma = data["gemma_analysis"]
    assert "combat_grade" in gemma
    assert "performance_summary" in gemma
    assert "tactical_breakdown" in gemma
    assert "key_strength" in gemma
    assert "fatal_flaw" in gemma
    assert "next_mission_directive" in gemma


def test_static_assets_serving(client):
    """Verify static assets in public/ are served."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "STARFALL" in resp.text

    resp_css = client.get("/styles.css")
    assert resp_css.status_code == 200
    assert "--bg-color" in resp_css.text

    resp_js = client.get("/app.js")
    assert resp_js.status_code == 200
    assert "SoundFX" in resp_js.text
