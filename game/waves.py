"""STARFALL Wave Progression and Spawn Scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from game.entities import Enemy, Obstacle, LaserLane
from game.enemies import spawn_formation
from game.obstacles import spawn_obstacles


@dataclass
class WavePlan:
    """Strategy plan for an upcoming enemy wave."""
    formation: str = "v_formation"
    obstacle: str = "none"
    difficulty: int = 2
    spawn_count: int = 8
    projectile_speed: float = 240.0
    reason: str = "Standard tactical sweep formation."
    evidence: List[str] = field(default_factory=lambda: ["baseline_opening"])
    confidence: float = 0.5
    mission: Optional[str] = "Eliminate all hostiles while maintaining high accuracy."
    is_fallback: bool = False


class WaveManager:
    """Manages wave transitions, countdowns, and entity spawning."""

    def __init__(self, play_width: float = 800.0, play_height: float = 700.0):
        self.play_width = play_width
        self.play_height = play_height
        self.current_wave_num: int = 0
        self.active_plan: WavePlan = WavePlan()
        self.next_queued_plan: Optional[WavePlan] = None
        self.intermission_timer: float = 2.0
        self.in_intermission: bool = True
        self.wave_in_progress: bool = False
        self.total_waves_cleared: int = 0
        self._entity_id_seq: int = 100

    def get_next_entity_id(self) -> int:
        self._entity_id_seq += 1
        return self._entity_id_seq

    def queue_next_plan(self, plan: WavePlan) -> None:
        """Queue a validated strategy to be applied strictly at next wave boundary."""
        self.next_queued_plan = plan

    def start_intermission(self, duration: float = 2.5) -> None:
        """Begin transition to the next wave."""
        self.in_intermission = True
        self.intermission_timer = duration
        self.wave_in_progress = False

    def update(self, dt: float) -> Tuple[bool, Optional[List[Enemy]], Optional[List[Obstacle]], Optional[List[LaserLane]]]:
        """
        Update intermission timers.
        Returns (wave_started, spawned_enemies, spawned_obstacles, spawned_laser_lanes).
        """
        if self.in_intermission:
            self.intermission_timer -= dt
            if self.intermission_timer <= 0.0:
                self.in_intermission = False
                self.wave_in_progress = True
                self.current_wave_num += 1

                # Apply queued plan if present, else fallback/scaled progression
                if self.next_queued_plan is not None:
                    self.active_plan = self.next_queued_plan
                    self.next_queued_plan = None
                else:
                    self.active_plan = self._generate_default_plan(self.current_wave_num)

                # Spawn entities
                enemies = spawn_formation(
                    formation_name=self.active_plan.formation,
                    count=self.active_plan.spawn_count,
                    difficulty=self.active_plan.difficulty,
                    play_width=self.play_width,
                    play_height=self.play_height,
                    start_id=self.get_next_entity_id(),
                )
                obstacles, lasers = spawn_obstacles(
                    obstacle_type=self.active_plan.obstacle,
                    difficulty=self.active_plan.difficulty,
                    play_width=self.play_width,
                    play_height=self.play_height,
                    start_id=self.get_next_entity_id(),
                )
                return True, enemies, obstacles, lasers

        return False, None, None, None

    def _generate_default_plan(self, wave_num: int) -> WavePlan:
        """Deterministic scalable fallback progression if no AI plan is ready."""
        formations = ["v_formation", "center_sweep", "split_formation", "staggered_assault", "converging_pincer"]
        obstacles = ["none", "slow_moving_barriers", "drifting_asteroids", "telegraphed_laser_lane"]

        formation = formations[(wave_num - 1) % len(formations)]
        obstacle = obstacles[(wave_num // 2) % len(obstacles)]
        difficulty = min(5, 1 + (wave_num // 2))
        count = min(18, 6 + wave_num * 2)
        speed = min(420.0, 200.0 + (wave_num * 25.0))

        return WavePlan(
            formation=formation,
            obstacle=obstacle,
            difficulty=difficulty,
            spawn_count=count,
            projectile_speed=speed,
            reason=f"Standard tactical escalation for Wave {wave_num}.",
            evidence=[f"wave={wave_num}", "default_progression"],
            confidence=0.5,
            mission=f"Survive wave {wave_num} against {formation}.",
            is_fallback=True,
        )

    def reset(self) -> None:
        self.current_wave_num = 0
        self.active_plan = WavePlan()
        self.next_queued_plan = None
        self.intermission_timer = 2.0
        self.in_intermission = True
        self.wave_in_progress = False
        self.total_waves_cleared = 0
