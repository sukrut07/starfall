"""STARFALL Game State and Input Command definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
from game.entities import PlayerShip, Enemy, Projectile, Obstacle, LaserLane, PowerUp, Particle
from game.scoring import ScoreKeeper
from game.waves import WavePlan


class GameStatus(Enum):
    START_SCREEN = "start_screen"
    PLAYING = "playing"
    PAUSED = "paused"
    WAVE_TRANSITION = "wave_transition"
    GAME_OVER = "game_over"
    RESULTS = "results"


@dataclass
class InputCommand:
    """Normalized input command from either keyboard or gesture."""
    move_x: float = 0.0   # -1.0 to +1.0 for relative, or absolute coordinate if absolute_pos is True
    move_y: float = 0.0   # -1.0 to +1.0
    fire: bool = False
    pause: bool = False
    restart: bool = False
    quit: bool = False
    absolute_pos: bool = False
    target_x: Optional[float] = None
    target_y: Optional[float] = None


@dataclass
class GameStateSnapshot:
    """Read-only snapshot of current game state for rendering."""
    status: GameStatus
    player_x: float
    player_y: float
    player_radius: float
    player_lives: int
    player_invulnerable: bool
    player_shield: bool
    score: int
    high_score: int
    enemies_destroyed: int
    shots_fired: int
    shots_hit: int
    accuracy: float
    dodges: int
    current_wave: int
    in_intermission: bool
    intermission_time_left: float
    active_plan: WavePlan
    enemies: List[Tuple[float, float, str, int, int]]  # x, y, type, hp, max_hp
    player_bullets: List[Tuple[float, float]]          # x, y
    enemy_bullets: List[Tuple[float, float]]           # x, y
    obstacles: List[Tuple[float, float, float, str, int]] # x, y, radius, type, hp
    laser_lanes: List[Tuple[float, float, str, float]] # x, width, state, timer
    powerups: List[Tuple[float, float, str]]           # x, y, type
    particles: List[Tuple[float, float, Tuple[int, int, int], float]] # x, y, color, size
    match_time: float
