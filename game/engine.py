"""STARFALL Core Game Engine."""

from __future__ import annotations

import math
import random
from typing import Callable, List, Optional, Tuple, Any

from game.entities import (
    Enemy,
    EnemyType,
    LaserLane,
    Obstacle,
    Particle,
    PlayerShip,
    PowerUp,
    PowerUpType,
    Projectile,
    ProjectileOwner,
)
from game.collisions import (
    check_circle_collision,
    check_point_in_laser_lane,
    check_projectile_dodge,
)
from game.projectiles import (
    create_player_projectiles,
    create_enemy_projectile,
)
from game.scoring import ScoreKeeper
from game.waves import WaveManager, WavePlan
from game.state import GameStatus, InputCommand, GameStateSnapshot


class GameEngine:
    """Authoritative game simulation engine decoupled from rendering."""

    def __init__(
        self,
        width: float = 800.0,
        height: float = 700.0,
        starting_lives: int = 3,
        invuln_duration: float = 2.0,
        fire_cooldown: float = 0.18,
    ):
        self.width = width
        self.height = height
        self.starting_lives = starting_lives
        self.invuln_duration = invuln_duration
        self.fire_cooldown = fire_cooldown

        self.player = PlayerShip(
            x=width * 0.5,
            y=height - 75.0,
            radius=14.0,
            lives=starting_lives,
            speed=420.0,
        )
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.obstacles: List[Obstacle] = []
        self.laser_lanes: List[LaserLane] = []
        self.powerups: List[PowerUp] = []
        self.particles: List[Particle] = []

        self.wave_manager = WaveManager(play_width=width, play_height=height)
        self.score_keeper = ScoreKeeper()
        self.status = GameStatus.START_SCREEN

        self.match_time: float = 0.0
        self._next_id: int = 5000

        # Telemetry callback hook: fn(event_type: str, data: dict)
        self.telemetry_callback: Optional[Callable[[str, dict], None]] = None

    def set_telemetry_callback(self, cb: Callable[[str, dict], None]) -> None:
        self.telemetry_callback = cb

    def _emit_event(self, event_type: str, data: dict) -> None:
        if self.telemetry_callback:
            data["match_time"] = self.match_time
            data["current_wave"] = self.wave_manager.current_wave_num
            self.telemetry_callback(event_type, data)

    def start_game(self) -> None:
        """Start or restart a match."""
        self.reset()
        self.status = GameStatus.PLAYING
        self.wave_manager.start_intermission(duration=1.5)
        self._emit_event("game_started", {"starting_lives": self.starting_lives})

    def reset(self) -> None:
        self.player = PlayerShip(
            x=self.width * 0.5,
            y=self.height - 75.0,
            radius=14.0,
            lives=self.starting_lives,
            speed=420.0,
        )
        self.enemies.clear()
        self.projectiles.clear()
        self.obstacles.clear()
        self.laser_lanes.clear()
        self.powerups.clear()
        self.particles.clear()
        self.wave_manager.reset()
        self.score_keeper.reset()
        self.match_time = 0.0
        self.status = GameStatus.PLAYING

    def queue_strategy_plan(self, plan: WavePlan) -> None:
        """Queue validated strategy plan to be applied at wave boundary."""
        self.wave_manager.queue_next_plan(plan)

    def update(self, dt: float, cmd: InputCommand) -> None:
        """Main simulation update step."""
        # Handle state changes from input
        if cmd.quit:
            return

        if cmd.pause and self.status in (GameStatus.PLAYING, GameStatus.PAUSED):
            self.status = GameStatus.PAUSED if self.status == GameStatus.PLAYING else GameStatus.PLAYING
            return

        if self.status == GameStatus.START_SCREEN:
            if cmd.fire or cmd.restart:
                self.start_game()
            return

        if self.status == GameStatus.GAME_OVER:
            if cmd.restart:
                self.start_game()
            return

        if self.status == GameStatus.PAUSED:
            return

        # Status is PLAYING or WAVE_TRANSITION
        self.match_time += dt

        # 1. Update Player Input & Movement
        self._update_player_movement(dt, cmd)

        # 2. Player Firing
        self._update_player_firing(cmd)

        # 3. Update Player Entity
        self.player.update(dt)

        # 4. Update Wave Transitions & Spawning
        self._update_waves(dt)

        # 5. Update Enemies
        self._update_enemies(dt)

        # 6. Update Obstacles & Laser Lanes
        self._update_obstacles(dt)

        # 7. Update Projectiles
        self._update_projectiles(dt)

        # 8. Update Powerups
        self._update_powerups(dt)

        # 9. Update Particles
        self._update_particles(dt)

        # 10. Check Collisions
        self._resolve_collisions()

        # 11. Check Player Death / Game Over
        if self.player.lives <= 0:
            self.status = GameStatus.GAME_OVER
            self._emit_event("game_over", {
                "score": self.score_keeper.total_score,
                "waves_cleared": self.score_keeper.waves_completed,
                "match_time": self.match_time,
                "accuracy": self.score_keeper.accuracy,
            })

    def _update_player_movement(self, dt: float, cmd: InputCommand) -> None:
        if cmd.absolute_pos and cmd.target_x is not None and cmd.target_y is not None:
            # Direct position assignment from calibrated gestures
            self.player.x = cmd.target_x
            self.player.y = cmd.target_y
        else:
            # Relative movement from keyboard or relative gestures
            self.player.x += cmd.move_x * self.player.speed * dt
            self.player.y += cmd.move_y * self.player.speed * dt

        # Clamp strictly inside boundaries
        pad = self.player.radius + 4.0
        self.player.x = max(pad, min(self.width - pad, self.player.x))
        # Keep player in bottom 45% of screen
        min_y = self.height * 0.55
        max_y = self.height - pad
        self.player.y = max(min_y, min(max_y, self.player.y))

        # Periodic player position telemetry
        if int(self.match_time * 10) % 2 == 0:  # ~5Hz
            self._emit_event("player_position", {
                "x": self.player.x,
                "y": self.player.y,
                "norm_x": self.player.x / self.width,
            })

    def _update_player_firing(self, cmd: InputCommand) -> None:
        if cmd.fire and self.player.fire_cooldown_timer <= 0.0:
            cooldown = self.fire_cooldown * (0.6 if self.player.rapid_fire_timer > 0.0 else 1.0)
            self.player.fire_cooldown_timer = cooldown

            new_bullets = create_player_projectiles(self.player, base_speed=-640.0, current_id=self._get_id())
            self.projectiles.extend(new_bullets)
            self.score_keeper.record_shot()
            self._emit_event("player_fired", {"shots_count": len(new_bullets)})

    def _update_waves(self, dt: float) -> None:
        spawned, new_enemies, new_obstacles, new_lasers = self.wave_manager.update(dt)
        if spawned and new_enemies:
            self.enemies = new_enemies
            if new_obstacles:
                self.obstacles.extend(new_obstacles)
            if new_lasers:
                self.laser_lanes.extend(new_lasers)

            self._emit_event("wave_started", {
                "wave": self.wave_manager.current_wave_num,
                "formation": self.wave_manager.active_plan.formation,
                "enemy_count": len(new_enemies),
                "obstacle": self.wave_manager.active_plan.obstacle,
                "difficulty": self.wave_manager.active_plan.difficulty,
                "is_fallback": self.wave_manager.active_plan.is_fallback,
            })

        # Check wave completion
        if self.wave_manager.wave_in_progress and len(self.enemies) == 0:
            self.wave_manager.start_intermission(duration=2.5)
            self.score_keeper.record_wave_completed()
            # Clear expired lasers and obstacles for next wave
            self.obstacles.clear()
            self.laser_lanes.clear()

            self._emit_event("wave_completed", {
                "wave": self.wave_manager.current_wave_num,
                "score": self.score_keeper.total_score,
                "accuracy": self.score_keeper.accuracy,
                "lives_remaining": self.player.lives,
            })

    def _update_enemies(self, dt: float) -> None:
        p_speed = self.wave_manager.active_plan.projectile_speed
        for enemy in self.enemies:
            enemy.update(dt)

            # Enemy shooting
            if enemy.entry_completed and enemy.shoot_timer <= 0.0:
                enemy.shoot_timer = enemy.shoot_cooldown + random.uniform(-0.2, 0.4)
                eb = create_enemy_projectile(enemy, self.player, speed=p_speed, current_id=self._get_id())
                self.projectiles.extend(eb)
                self._emit_event("enemy_fired", {"enemy_type": enemy.enemy_type.value})

    def _update_obstacles(self, dt: float) -> None:
        for obs in self.obstacles:
            obs.update(dt)
            # Bounce barriers horizontally off edges
            if obs.obstacle_type == "barrier":
                if obs.x - obs.radius < 10.0 or obs.x + obs.radius > self.width - 10.0:
                    obs.vx = -obs.vx

        # Remove asteroids off screen
        self.obstacles = [o for o in self.obstacles if o.active and o.y < self.height + 50.0]

        # Update laser lanes
        for lane in self.laser_lanes:
            lane.update(dt)
        self.laser_lanes = [l for l in self.laser_lanes if l.state != "expired"]

    def _update_projectiles(self, dt: float) -> None:
        for p in self.projectiles:
            p.update(dt)

            # Check dodge for enemy projectiles
            if p.owner == ProjectileOwner.ENEMY:
                if check_projectile_dodge(p, self.player, self.height):
                    pts = self.score_keeper.record_dodge()
                    self._emit_event("dodge_successful", {"points": pts})

        # Remove out of bounds projectiles
        self.projectiles = [
            p for p in self.projectiles
            if p.active and -30.0 <= p.y <= self.height + 30.0 and -30.0 <= p.x <= self.width + 30.0
        ]

    def _update_powerups(self, dt: float) -> None:
        for p in self.powerups:
            p.update(dt)
        self.powerups = [p for p in self.powerups if p.active and p.y < self.height + 40.0]

    def _update_particles(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def _spawn_explosion(self, x: float, y: float, count: int = 14, color: Tuple[int, int, int] = (255, 180, 50)) -> None:
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(30.0, 160.0)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd,
                    lifetime=random.uniform(0.2, 0.55),
                    max_lifetime=0.55,
                    color=color,
                    size=random.uniform(2.0, 4.5),
                )
            )

    def _resolve_collisions(self) -> None:
        """Resolve all collision interactions deterministically."""
        # 1. Player bullets vs Enemies
        for bullet in self.projectiles:
            if not bullet.active or bullet.owner != ProjectileOwner.PLAYER:
                continue

            for enemy in self.enemies:
                if not enemy.active:
                    continue

                if check_circle_collision(bullet, enemy):
                    bullet.active = False
                    enemy.hp -= bullet.damage
                    self.score_keeper.record_hit()
                    self._emit_event("enemy_hit", {"enemy_type": enemy.enemy_type.value, "remaining_hp": enemy.hp})

                    if enemy.hp <= 0:
                        enemy.active = False
                        is_tough = enemy.enemy_type == EnemyType.DREADNOUGHT
                        pts = self.score_keeper.record_enemy_kill(is_tough=is_tough)
                        self._spawn_explosion(enemy.x, enemy.y, count=18, color=(255, 120, 30) if is_tough else (255, 210, 60))
                        self._emit_event("enemy_destroyed", {"enemy_type": enemy.enemy_type.value, "points": pts})

                        # 15% chance to drop powerup
                        if random.random() < 0.18:
                            ptype = random.choice([PowerUpType.SHIELD, PowerUpType.RAPID_FIRE, PowerUpType.SPREAD_SHOT])
                            self.powerups.append(
                                PowerUp(
                                    id=self._get_id(),
                                    x=enemy.x,
                                    y=enemy.y,
                                    powerup_type=ptype,
                                )
                            )
                    else:
                        self._spawn_explosion(bullet.x, bullet.y, count=4, color=(255, 255, 255))
                    break

        # 2. Player bullets vs Obstacles
        for bullet in self.projectiles:
            if not bullet.active or bullet.owner != ProjectileOwner.PLAYER:
                continue

            for obs in self.obstacles:
                if not obs.active:
                    continue
                if check_circle_collision(bullet, obs):
                    bullet.active = False
                    obs.hp -= bullet.damage
                    self._spawn_explosion(bullet.x, bullet.y, count=5, color=(160, 160, 180))
                    if obs.hp <= 0:
                        obs.active = False
                        self._spawn_explosion(obs.x, obs.y, count=15, color=(200, 200, 220))
                    break

        # 3. Enemy bullets vs Player
        for bullet in self.projectiles:
            if not bullet.active or bullet.owner != ProjectileOwner.ENEMY:
                continue

            if check_circle_collision(bullet, self.player):
                bullet.active = False
                life_lost = self.player.take_damage(self.invuln_duration)
                self._spawn_explosion(self.player.x, self.player.y, count=16, color=(255, 50, 50))

                if life_lost:
                    self.score_keeper.record_life_lost()
                    self._emit_event("player_hit", {"damage": 1, "lives_remaining": self.player.lives})
                else:
                    self._emit_event("player_shield_absorbed", {})

        # 4. Obstacles vs Player
        for obs in self.obstacles:
            if not obs.active:
                continue
            if check_circle_collision(obs, self.player):
                life_lost = self.player.take_damage(self.invuln_duration)
                if life_lost:
                    self.score_keeper.record_life_lost()
                    self._emit_event("player_hit_obstacle", {"lives_remaining": self.player.lives})

        # 5. Laser lanes vs Player
        for lane in self.laser_lanes:
            if check_point_in_laser_lane(self.player.x, self.player.y, self.player.radius, lane):
                life_lost = self.player.take_damage(self.invuln_duration)
                if life_lost:
                    self.score_keeper.record_life_lost()
                    self._emit_event("player_hit_laser", {"lives_remaining": self.player.lives})

        # 6. Enemies vs Player (body ramming)
        for enemy in self.enemies:
            if not enemy.active:
                continue
            if check_circle_collision(enemy, self.player):
                enemy.active = False
                life_lost = self.player.take_damage(self.invuln_duration)
                self._spawn_explosion(enemy.x, enemy.y, count=15)
                if life_lost:
                    self.score_keeper.record_life_lost()
                    self._emit_event("player_rammed", {"lives_remaining": self.player.lives})

        # 7. Powerups vs Player
        for pup in self.powerups:
            if not pup.active:
                continue
            if check_circle_collision(pup, self.player):
                pup.active = False
                self.score_keeper.record_bonus()
                if pup.powerup_type == PowerUpType.SHIELD:
                    self.player.shield_active = True
                elif pup.powerup_type == PowerUpType.RAPID_FIRE:
                    self.player.rapid_fire_timer = 8.0
                elif pup.powerup_type == PowerUpType.SPREAD_SHOT:
                    self.player.spread_shot_timer = 8.0
                self._emit_event("powerup_collected", {"type": pup.powerup_type.value})

        # Cleanup inactive entities safely
        self.enemies = [e for e in self.enemies if e.active]
        self.projectiles = [p for p in self.projectiles if p.active]
        self.obstacles = [o for o in self.obstacles if o.active]
        self.powerups = [p for p in self.powerups if p.active]

    def _get_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def get_snapshot(self) -> GameStateSnapshot:
        """Create a clean decoupled state snapshot for renderers."""
        return GameStateSnapshot(
            status=self.status,
            player_x=self.player.x,
            player_y=self.player.y,
            player_radius=self.player.radius,
            player_lives=self.player.lives,
            player_invulnerable=self.player.is_invulnerable(),
            player_shield=self.player.shield_active,
            score=self.score_keeper.total_score,
            high_score=self.score_keeper.high_score,
            enemies_destroyed=self.score_keeper.enemies_destroyed,
            shots_fired=self.score_keeper.shots_fired,
            shots_hit=self.score_keeper.shots_hit,
            accuracy=self.score_keeper.accuracy,
            dodges=self.score_keeper.successful_dodges,
            current_wave=self.wave_manager.current_wave_num,
            in_intermission=self.wave_manager.in_intermission,
            intermission_time_left=max(0.0, self.wave_manager.intermission_timer),
            active_plan=self.wave_manager.active_plan,
            enemies=[(e.x, e.y, e.enemy_type.value, e.hp, e.max_hp) for e in self.enemies],
            player_bullets=[(p.x, p.y) for p in self.projectiles if p.owner == ProjectileOwner.PLAYER],
            enemy_bullets=[(p.x, p.y) for p in self.projectiles if p.owner == ProjectileOwner.ENEMY],
            obstacles=[(o.x, o.y, o.radius, o.obstacle_type, o.hp) for o in self.obstacles],
            laser_lanes=[(l.x, l.width, l.state, l.timer) for l in self.laser_lanes],
            powerups=[(p.x, p.y, p.powerup_type.value) for p in self.powerups],
            particles=[(p.x, p.y, p.color, p.size) for p in self.particles],
            match_time=self.match_time,
        )
