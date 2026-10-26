"""STARFALL FastAPI Serverless Application Entrypoint.

Provides validated tactical recommendations, health diagnostics, and post-game
performance analysis for the browser-based STARFALL arcade shooter.
Compatible with Vercel Python runtime and local ASGI servers.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
from pydantic import BaseModel, Field, field_validator

# Ensure repository root is on sys.path for local module resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Optional .env loading without overriding existing environment
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)
except Exception:
    pass

from ai.schemas import (
    ALLOWED_FORMATIONS,
    ALLOWED_OBSTACLES,
    FormationType,
    ObstacleType,
    TacticalStrategyResponse,
)
from ai.fallback import get_deterministic_strategy
from analytics.metrics import AggregatedMetrics
from analytics.player_profile import build_profile
from analytics.reports import generate_next_mission


# ==============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ==============================================================================

app = FastAPI(
    title="STARFALL Tactical Commander API",
    description="Adaptive AI Tactical Director and Post-Game Debrief Service for STARFALL",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Enable CORS for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# CONFIGURATION HELPERS
# ==============================================================================

def get_ollama_host() -> str:
    """Return configured Ollama host URL, stripping trailing slashes."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def get_configured_model() -> str:
    """Return configured AI model name."""
    return os.getenv("OLLAMA_MODEL", "gemma4:e4b")


def is_ai_enabled() -> bool:
    """Check whether AI inference is enabled."""
    return os.getenv("STARFALL_AI_ENABLED", "true").lower() in ("true", "1", "yes")


def get_timeout_seconds() -> float:
    """Return model inference timeout in seconds."""
    try:
        return float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "6.0"))
    except ValueError:
        return 6.0


async def check_ollama_reachability(host: str, timeout: float = 1.5) -> tuple[bool, List[str]]:
    """
    Perform a non-blocking health check against the configured Ollama host.
    Returns (is_reachable, installed_models). Never raises.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{host}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return True, models
    except Exception:
        pass
    return False, []


# ==============================================================================
# PYDANTIC REQUEST & RESPONSE MODELS
# ==============================================================================

class StrategyRequest(BaseModel):
    """Telemetry payload submitted by the browser game between waves."""
    wave: int = Field(default=1, ge=1, le=100, description="Upcoming wave number")
    shots_fired: int = Field(default=0, ge=0, description="Total player shots fired")
    shots_hit: int = Field(default=0, ge=0, description="Total player shots on target")
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Player accuracy ratio")
    movement_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"left": 0.33, "center": 0.34, "right": 0.33},
        description="Player quadrant position distribution",
    )
    camping_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Stationary time ratio")
    dodges: int = Field(default=0, ge=0, description="Count of close projectile dodges")
    lives_lost: int = Field(default=0, ge=0, le=20, description="Lives lost this match")
    current_difficulty: int = Field(default=2, ge=1, le=5, description="Current difficulty tier")
    supported_formations: Optional[List[str]] = None
    supported_obstacles: Optional[List[str]] = None
    previous_strategy_outcome: Optional[Dict[str, Any]] = None


class StrategyResponse(BaseModel):
    """Bounded, validated tactical plan returned to the client game."""
    formation: FormationType
    obstacle: ObstacleType
    difficulty: int = Field(ge=1, le=5)
    spawn_count: int = Field(ge=3, le=24)
    projectile_speed: float = Field(ge=140.0, le=500.0)
    reason: str
    evidence: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    mission: Optional[str] = None
    is_fallback: bool = False
    source: str = "deterministic_fallback"
    latency_ms: float = 0.0


class AnalyzeRequest(BaseModel):
    """Final match summary payload submitted on Game Over."""
    match_id: str = Field(default="browser-match")
    total_score: int = Field(default=0, ge=0)
    waves_completed: int = Field(default=0, ge=0)
    survival_seconds: float = Field(default=0.0, ge=0.0)
    enemies_destroyed: int = Field(default=0, ge=0)
    shots_fired: int = Field(default=0, ge=0)
    shots_hit: int = Field(default=0, ge=0)
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    dodges: int = Field(default=0, ge=0)
    lives_lost: int = Field(default=0, ge=0)
    movement_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"left": 0.33, "center": 0.34, "right": 0.33}
    )
    camping_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    strategies_applied: List[Any] = Field(default_factory=list)


# ==============================================================================
# API ROUTE HANDLERS
# ==============================================================================

@app.get("/api/health", summary="Service and Model Health Diagnostics")
@app.get("/health", summary="Service and Model Health Diagnostics (Bare Path)")
async def health_check() -> Dict[str, Any]:
    """
    Check the health of the STARFALL service and probe reachability of the
    configured AI inference endpoint without exposing secrets or filesystem paths.
    """
    host = get_ollama_host()
    configured_model = get_configured_model()
    ai_enabled = is_ai_enabled()

    reachable, installed_models = await check_ollama_reachability(host, timeout=1.5)

    return {
        "app": "STARFALL",
        "version": "1.0.0",
        "status": "healthy",
        "ai_enabled": ai_enabled,
        "configured_model": configured_model,
        "inference_reachable": reachable,
        "installed_models_count": len(installed_models),
        "fallback_available": True,
        "timestamp": time.time(),
    }


@app.get("/api/config", summary="Safe Client Game Configuration")
@app.get("/config", summary="Safe Client Game Configuration (Bare Path)")
async def get_client_config() -> Dict[str, Any]:
    """
    Provide public, safe configuration data for the browser arcade game.
    Never exposes internal tokens, passwords, or filesystem paths.
    """
    host = get_ollama_host()
    reachable, _ = await check_ollama_reachability(host, timeout=1.0)

    return {
        "app_title": "STARFALL // Textmode Tactical Display & AI Commander",
        "version": "1.0.0",
        "control_modes": ["keyboard", "gesture", "mixed"],
        "game_settings": {
            "target_fps": 60,
            "canvas_width": 800,
            "canvas_height": 480,
            "default_lives": 3,
            "invulnerability_duration": 2.0,
            "player_speed": 420.0,
            "laser_speed": 600.0,
        },
        "supported_formations": ALLOWED_FORMATIONS,
        "allowed_obstacles": ALLOWED_OBSTACLES,
        "gesture_enabled": True,
        "ai_service": {
            "provider": "ollama",
            "configured_model": get_configured_model(),
            "inference_reachable": reachable,
            "deterministic_fallback_active": not reachable,
        },
    }


@app.post("/api/strategy", response_model=StrategyResponse, summary="Request Bounded Wave Strategy")
@app.post("/strategy", response_model=StrategyResponse, summary="Request Bounded Wave Strategy (Bare Path)")
async def request_strategy(payload: StrategyRequest) -> StrategyResponse:
    """
    Evaluate player telemetry and return a validated, bounded tactical plan.
    If the remote AI model is reachable, calls it with a strict timeout;
    otherwise seamlessly returns the deterministic fallback plan.
    """
    start_time = time.perf_counter()
    host = get_ollama_host()
    model = get_configured_model()
    timeout = get_timeout_seconds()

    # Metrics dictionary for deterministic evaluation and inference grounding
    metrics_summary = {
        "left_zone_ratio": payload.movement_distribution.get("left", 0.33),
        "right_zone_ratio": payload.movement_distribution.get("right", 0.33),
        "center_zone_ratio": payload.movement_distribution.get("center", 0.34),
        "camping_ratio": payload.camping_ratio,
        "accuracy": payload.accuracy,
        "damage_taken": payload.lives_lost,
        "dodges_successful": payload.dodges,
        "shots_fired": payload.shots_fired,
        "shots_hit": payload.shots_hit,
    }

    # Attempt model inference if AI enabled and host looks reachable
    if is_ai_enabled():
        try:
            prompt = (
                f"You are the STARFALL Tactical Director. Formulate a strategy for wave {payload.wave}.\n"
                f"Player Telemetry: Accuracy={payload.accuracy:.1%}, LeftZone={metrics_summary['left_zone_ratio']:.1%}, "
                f"RightZone={metrics_summary['right_zone_ratio']:.1%}, Camping={payload.camping_ratio:.1%}, "
                f"Dodges={payload.dodges}, LivesLost={payload.lives_lost}.\n"
                f"Allowed Formations: {ALLOWED_FORMATIONS}\n"
                f"Allowed Obstacles: {ALLOWED_OBSTACLES}\n"
                f"Respond ONLY with valid JSON matching:\n"
                f'{{"formation": "<formation>", "obstacle": "<obstacle>", "difficulty": <1-5>, '
                f'"spawn_count": <4-16>, "projectile_speed": <180-380>, "reason": "<evidence-based rationale>", '
                f'"evidence": ["<metric1>", "<metric2>"], "confidence": <0.0-1.0>}}'
            )

            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.2, "num_predict": 256},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "{}")
                    import json
                    parsed = json.loads(raw_text)

                    # Validate with Pydantic
                    val_strat = TacticalStrategyResponse(**parsed)
                    latency = (time.perf_counter() - start_time) * 1000.0

                    return StrategyResponse(
                        formation=val_strat.formation,
                        obstacle=val_strat.obstacle,
                        difficulty=val_strat.difficulty,
                        spawn_count=val_strat.spawn_count,
                        projectile_speed=val_strat.projectile_speed,
                        reason=val_strat.reason,
                        evidence=val_strat.evidence,
                        confidence=val_strat.confidence,
                        mission=val_strat.mission or f"Survive wave {payload.wave} against {val_strat.formation}.",
                        is_fallback=False,
                        source=f"ollama_{model}",
                        latency_ms=round(latency, 1),
                    )
        except Exception:
            # Clean fallback on any inference error, timeout, or schema mismatch
            pass

    # Deterministic tactical fallback
    fallback_plan = get_deterministic_strategy(
        wave=payload.wave,
        metrics=metrics_summary,
        difficulty_cap=5,
    )
    latency = (time.perf_counter() - start_time) * 1000.0

    return StrategyResponse(
        formation=fallback_plan.formation,
        obstacle=fallback_plan.obstacle,
        difficulty=fallback_plan.difficulty,
        spawn_count=fallback_plan.spawn_count,
        projectile_speed=fallback_plan.projectile_speed,
        reason=fallback_plan.reason,
        evidence=fallback_plan.evidence,
        confidence=fallback_plan.confidence,
        mission=fallback_plan.mission,
        is_fallback=True,
        source="deterministic_fallback",
        latency_ms=round(latency, 1),
    )


async def generate_gemma_debrief(
    payload: AnalyzeRequest,
    metrics: AggregatedMetrics,
    profile: Any,
    next_mission: Any,
) -> Dict[str, Any]:
    """
    Synthesize an intelligent post-mission evaluation of what the gameplay was
    and how the pilot performed using Gemma 4 via Ollama, with high-fidelity fallback.
    """
    host = get_ollama_host()
    model = get_configured_model()
    timeout = min(15.0, max(10.0, get_timeout_seconds() * 2.5))

    acc_pct = payload.accuracy * 100.0
    dodges = payload.dodges
    waves = payload.waves_completed
    camping = payload.camping_ratio * 100.0

    if waves >= 4 or (acc_pct >= 75.0 and dodges >= 6):
        default_grade = "S-Tier Ace"
    elif waves >= 2 or (acc_pct >= 55.0 and dodges >= 3):
        default_grade = "A-Tier Veteran"
    elif waves >= 1 or acc_pct >= 35.0:
        default_grade = "B-Tier Pilot"
    else:
        default_grade = "C-Tier Cadet"

    movement_desc = "balanced lateral quadrant coverage"
    left_r = payload.movement_distribution.get("left", 0.33)
    right_r = payload.movement_distribution.get("right", 0.33)
    if left_r > 0.45:
        movement_desc = "heavy port-side (left) drift bias"
    elif right_r > 0.45:
        movement_desc = "heavy starboard (right) drift bias"
    elif payload.camping_ratio > 0.35:
        movement_desc = "high stationary camping in mid-channel"

    fallback_analysis = {
        "combat_grade": default_grade,
        "performance_summary": (
            f"Pilot sustained combat operations for {payload.survival_seconds:.1f}s with {acc_pct:.1f}% firing accuracy and {dodges} threat evasions. "
            f"Maneuvering exhibited {movement_desc}, surviving across {payload.waves_completed} hostile wave deployments."
        ),
        "tactical_breakdown": (
            f"Telemetry records {payload.shots_hit}/{max(1, payload.shots_fired)} weapon hits with a camping quotient of {camping:.0f}%. "
            f"Pincer and spread wave adaptations forced lateral evasion, highlighting {movement_desc} under combat stress."
        ),
        "key_strength": (
            f"Exceptional close-range projectile evasion ({dodges} clean dodges)"
            if dodges >= 3
            else f"Consistent cannon fire accuracy ({acc_pct:.1f}%)"
        ),
        "fatal_flaw": (
            f"Stationary camping quotient ({camping:.0f}%) limited rapid interceptor repositioning"
            if payload.camping_ratio > 0.25
            else "Delayed lateral reaction against converging projectile waves"
        ),
        "next_mission_directive": next_mission.measurement_description if hasattr(next_mission, "measurement_description") else f"Achieve >60% accuracy and clear wave {payload.waves_completed + 1}.",
        "source": "deterministic_analysis",
        "is_ai_generated": False,
    }

    if not is_ai_enabled():
        return fallback_analysis

    try:
        if payload.strategies_applied:
            formations_list = []
            for item in payload.strategies_applied:
                if isinstance(item, dict):
                    formations_list.append(str(item.get("formation", "wave")))
                else:
                    formations_list.append(str(item))
            formations_str = ", ".join(formations_list)
        else:
            formations_str = "standard tactical waves"

        prompt = (
            f"You are the STARFALL Tactical Fleet Commander AI running Gemma 4.\n"
            f"Analyze this combat mission debrief based on measured pilot telemetry:\n"
            f"- Total Score: {payload.total_score:,} pts\n"
            f"- Waves Cleared: {payload.waves_completed}\n"
            f"- Combat Survival Time: {payload.survival_seconds:.1f}s\n"
            f"- Firing Precision (Accuracy): {payload.accuracy:.1%}\n"
            f"- Shots Fired / Hit: {payload.shots_fired} / {payload.shots_hit}\n"
            f"- Close-Range Dodges: {payload.dodges}\n"
            f"- Spatial Movement Distribution: Left={left_r:.0%}, Center={payload.movement_distribution.get('center', 0.34):.0%}, Right={right_r:.0%}\n"
            f"- Stationary Camping Ratio: {camping:.0f}%\n"
            f"- Enemy Formations Encountered: {formations_str}\n\n"
            f"Evaluate what the gameplay was like and how the pilot performed. "
            f"Respond ONLY with valid JSON with these keys:\n"
            f"{{\n"
            f'  "combat_grade": "<S-Tier Ace | A-Tier Veteran | B-Tier Pilot | C-Tier Cadet>",\n'
            f'  "performance_summary": "<2-3 sentence engaging analysis of what the gameplay was like and how the pilot handled threats>",\n'
            f'  "tactical_breakdown": "<detailed observation of pilot habits, spatial positioning bias, and combat rhythm>",\n'
            f'  "key_strength": "<the pilot\'s greatest asset in this run>",\n'
            f'  "fatal_flaw": "<the vulnerability or tendency that led to hull compromise>",\n'
            f'  "next_mission_directive": "<actionable tactical challenge for their next flight>"\n'
            f"}}"
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.3, "num_predict": 384},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data.get("response", "{}")
                import json
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "combat_grade" in parsed and "performance_summary" in parsed:
                    return {
                        "combat_grade": str(parsed.get("combat_grade", default_grade)),
                        "performance_summary": str(parsed.get("performance_summary", fallback_analysis["performance_summary"])),
                        "tactical_breakdown": str(parsed.get("tactical_breakdown", fallback_analysis["tactical_breakdown"])),
                        "key_strength": str(parsed.get("key_strength", fallback_analysis["key_strength"])),
                        "fatal_flaw": str(parsed.get("fatal_flaw", fallback_analysis["fatal_flaw"])),
                        "next_mission_directive": str(parsed.get("next_mission_directive", fallback_analysis["next_mission_directive"])),
                        "source": f"gemma4_{model}",
                        "is_ai_generated": True,
                    }
    except Exception as exc:
        print(f"[STARFALL] Gemma debrief generation error: {exc}")

    return fallback_analysis


@app.post("/api/analyze", summary="Generate Post-Match Flight Debrief")
@app.post("/analyze", summary="Generate Post-Match Flight Debrief (Bare Path)")
async def analyze_match(payload: AnalyzeRequest) -> Dict[str, Any]:
    """
    Produce a structured post-game flight debrief with measured facts,
    Gemma-powered combat narrative, playstyle classification, and a concrete next-run mission.
    """
    # Build AggregatedMetrics from client payload
    metrics = AggregatedMetrics(
        shots_fired=payload.shots_fired,
        shots_hit=payload.shots_hit,
        accuracy=payload.accuracy,
        enemies_destroyed=payload.enemies_destroyed,
        dodges_successful=payload.dodges,
        threats_encountered=max(payload.dodges, payload.enemies_destroyed * 2),
        dodge_rate=round(payload.dodges / max(1, payload.dodges + payload.lives_lost), 2),
        lives_lost=payload.lives_lost,
        damage_taken=payload.lives_lost,
        survival_seconds=payload.survival_seconds,
        waves_completed=payload.waves_completed,
        position_samples=max(10, int(payload.survival_seconds * 10)),
        left_zone_ratio=payload.movement_distribution.get("left", 0.33),
        center_zone_ratio=payload.movement_distribution.get("center", 0.34),
        right_zone_ratio=payload.movement_distribution.get("right", 0.33),
        camping_ratio=payload.camping_ratio,
        total_movement_distance=payload.survival_seconds * 140.0,
        average_speed=140.0,
    )

    # Generate Profile and Next Mission Directive
    profile = build_profile(metrics)
    next_mission = generate_next_mission(metrics, profile)

    # Generate Gemma 4 Intelligent Debrief
    gemma_eval = await generate_gemma_debrief(payload, metrics, profile, next_mission)

    return {
        "match_id": payload.match_id,
        "total_score": payload.total_score,
        "waves_completed": payload.waves_completed,
        "survival_seconds": round(payload.survival_seconds, 1),
        "enemies_destroyed": payload.enemies_destroyed,
        "shots_fired": payload.shots_fired,
        "shots_hit": payload.shots_hit,
        "accuracy": round(payload.accuracy, 4),
        "dodges": payload.dodges,
        "lives_lost": payload.lives_lost,
        "metrics": metrics.to_dict(),
        "profile": profile.to_dict(),
        "adaptation_history": payload.strategies_applied,
        "next_mission": next_mission.to_dict(),
        "gemma_analysis": gemma_eval,
    }


@app.get("/api/status", summary="Companion Model Status")
@app.get("/status", summary="Companion Model Status (Bare Path)")
async def get_companion_status() -> Dict[str, Any]:
    host = get_ollama_host()
    configured_model = get_configured_model()
    reachable, installed = await check_ollama_reachability(host, timeout=1.5)
    return {
        "ai": {
            "endpoint": host,
            "ollama_online": reachable,
            "primary_model": configured_model,
            "installed_models": installed,
            "ollama_message": "Ollama service operational" if reachable else "Ollama offline; fallback active",
        }
    }


@app.get("/api/matches", summary="Recent Matches")
@app.get("/matches", summary="Recent Matches (Bare Path)")
async def get_recent_matches() -> Dict[str, Any]:
    return {"matches": []}


@app.get("/api/match/last", summary="Last Match Report")
@app.get("/match/last", summary="Last Match Report (Bare Path)")
async def get_last_match() -> Dict[str, Any]:
    return {"report": None}


# ==============================================================================
# STATIC ASSETS MOUNT (FOR LOCAL TESTING & ASGI EXECUTION)
# ==============================================================================

PUBLIC_DIR = ROOT_DIR / "public"
if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")

