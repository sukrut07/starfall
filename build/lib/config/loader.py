"""STARFALL Configuration Loader and Models."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import yaml

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    load_dotenv = None
    DOTENV_AVAILABLE = False
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    title: str = "STARFALL: Adaptive AI Arcade Shooter"
    version: str = "1.0.0"
    debug: bool = False
    database_path: str = "starfall.db"


class DisplayConfig(BaseModel):
    pygame_width: int = 800
    pygame_height: int = 700
    terminal_width: int = 80
    terminal_height: int = 28
    target_fps: int = 60
    terminal_fps: int = 25


class ControlsConfig(BaseModel):
    default_mode: str = "keyboard"  # keyboard, gesture, mixed
    move_speed: float = 400.0
    fire_cooldown: float = 0.18


class VisionConfig(BaseModel):
    camera_index: int = 0
    preview_enabled: bool = True
    preview_width: int = 160
    preview_height: int = 120
    model_path: str = "assets/models/hand_landmarker.task"
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    smoothing_alpha: float = 0.28
    deadzone: float = 0.02
    pinch_engage_thresh: float = 0.055
    pinch_release_thresh: float = 0.085
    debounce_frames: int = 2


class GameplayConfig(BaseModel):
    starting_lives: int = 3
    invulnerability_duration: float = 2.0
    starting_difficulty: int = 2
    max_difficulty: int = 5
    max_enemies_per_wave: int = 18
    max_projectile_speed: float = 550.0
    player_hitbox_radius: float = 14.0
    star_count: int = 75


class ScoringConfig(BaseModel):
    enemy_kill: int = 100
    boss_kill: int = 500
    successful_dodge: int = 25
    wave_completed: int = 250
    bonus_target: int = 150
    life_lost_penalty: int = 0


class AIConfig(BaseModel):
    enabled: bool = True
    ollama_endpoint: str = "http://localhost:11434"
    primary_model: str = "gemma4:e2b"
    alternative_model: str = "gemma4:e4b"
    api_key: Optional[str] = None
    timeout_seconds: float = 30.0
    retry_limit: int = 2
    max_difficulty_delta: int = 1
    min_observations_for_profile: int = 10
    allowed_formations: List[str] = Field(
        default_factory=lambda: [
            "v_formation",
            "center_sweep",
            "left_flank",
            "right_flank",
            "split_formation",
            "staggered_assault",
            "converging_pincer",
        ]
    )
    allowed_obstacles: List[str] = Field(
        default_factory=lambda: [
            "none",
            "slow_moving_barriers",
            "telegraphed_laser_lane",
            "drifting_asteroids",
        ]
    )


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    controls: ControlsConfig = Field(default_factory=ControlsConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    gameplay: GameplayConfig = Field(default_factory=GameplayConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load YAML defaults, then .env values, then explicit OS environment overrides."""
    if DOTENV_AVAILABLE and load_dotenv is not None:
        load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

    data = {}
    if config_path is None:
        default_yaml = Path(__file__).parent / "settings.yaml"
        if default_yaml.exists():
            config_path = str(default_yaml)

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                data = loaded

    settings = Settings(**data)

    # Environment variable overrides
    if "OLLAMA_HOST" in os.environ:
        settings.ai.ollama_endpoint = os.environ["OLLAMA_HOST"]
    if "OLLAMA_MODEL" in os.environ:
        settings.ai.primary_model = os.environ["OLLAMA_MODEL"]
    if "GEMMA_API_KEY" in os.environ:
        settings.ai.api_key = os.environ["GEMMA_API_KEY"]
    elif "OLLAMA_API_KEY" in os.environ:
        settings.ai.api_key = os.environ["OLLAMA_API_KEY"]
    if "STARFALL_CAMERA_INDEX" in os.environ:
        try:
            settings.vision.camera_index = int(os.environ["STARFALL_CAMERA_INDEX"])
        except ValueError:
            pass
    if "STARFALL_DEBUG" in os.environ:
        settings.app.debug = os.environ["STARFALL_DEBUG"].lower() in ("true", "1", "yes")
    if "STARFALL_DB_PATH" in os.environ:
        settings.app.database_path = os.environ["STARFALL_DB_PATH"]

    return settings

