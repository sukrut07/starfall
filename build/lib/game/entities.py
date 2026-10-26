"""STARFALL core entities for game simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class EntityType(Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    PROJECTILE = "projectile"
    OBSTACLE = "obstacle"
    POWERUP = "powerup"


class EnemyType(Enum):
    SCOUT = "scout"          # Fast, low HP, basic shots
    RAIDER = "raider"        # Sweeping arc, medium HP
    INTERCEPTOR = "interceptor" # Aims at player position
    DREADNOUGHT = "dreadnought" # Tough, multiple HP, spread shots


class ProjectileOwner(Enum):
    PLAYER = "player"
    ENEMY = "enemy"


class PowerUpType(Enum):
    SHIELD = "shield"
    RAPID_FIRE = "rapid_fire"
    SPREAD_SHOT = "spread_shot"


@dataclass
class Entity:
    """Base game entity with position, velocity, and circular hitbox."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    radius: float = 12.0
    active: bool = True
    id: int = 0

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt


@dataclass
class PlayerShip(Entity):
    """Player spaceship entity."""
    radius: float = 14.0
    lives: int = 3
    invulnerable_timer: float = 0.0
    fire_cooldown_timer: float = 0.0
    speed: float = 400.0
    shield_active: bool = False
    rapid_fire_timer: float = 0.0
    spread_shot_timer: float = 0.0

    def take_damage(self, invuln_duration: float = 2.0) -> bool:
        """Apply damage to player. Returns True if a life was lost."""
        if self.invulnerable_timer > 0.0:
            return False
        if self.shield_active:
            self.shield_active = False
            self.invulnerable_timer = invuln_duration * 0.5
            return False
        
        self.lives -= 1
        self.invulnerable_timer = invuln_duration
        return True

    def is_invulnerable(self) -> bool:
        return self.invulnerable_timer > 0.0

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.fire_cooldown_timer > 0.0:
            self.fire_cooldown_timer = max(0.0, self.fire_cooldown_timer - dt)
        if self.rapid_fire_timer > 0.0:
            self.rapid_fire_timer = max(0.0, self.rapid_fire_timer - dt)
        if self.spread_shot_timer > 0.0:
            self.spread_shot_timer = max(0.0, self.spread_shot_timer - dt)


@dataclass
class Enemy(Entity):
    """Enemy ship entity with pathing, HP, and attack behavior."""
    enemy_type: EnemyType = EnemyType.SCOUT
    hp: int = 1
    max_hp: int = 1
    point_value: int = 100
    radius: float = 14.0
    shoot_cooldown: float = 2.0
    shoot_timer: float = 1.0
    formation_slot_x: float = 0.0
    formation_slot_y: float = 0.0
    phase: float = 0.0
    path_type: str = "straight"
    amplitude: float = 50.0
    frequency: float = 2.0
    entry_completed: bool = False
    entry_progress: float = 0.0
    spawn_x: float = 0.0
    spawn_y: float = 0.0

    def update(self, dt: float) -> None:
        self.phase += dt * self.frequency
        self.shoot_timer -= dt

        if not self.entry_completed:
            self.entry_progress += dt * 1.5
            if self.entry_progress >= 1.0:
                self.entry_progress = 1.0
                self.entry_completed = True
                self.x = self.formation_slot_x
                self.y = self.formation_slot_y
            else:
                t = self.entry_progress
                # Smooth interpolation from spawn to slot
                self.x = self.spawn_x + (self.formation_slot_x - self.spawn_x) * (3*t*t - 2*t*t*t)
                self.y = self.spawn_y + (self.formation_slot_y - self.spawn_y) * (3*t*t - 2*t*t*t)
            return

        # Formation movement / sway
        if self.path_type == "sine":
            self.x = self.formation_slot_x + math.sin(self.phase) * self.amplitude
            self.y = self.formation_slot_y + math.cos(self.phase * 0.5) * (self.amplitude * 0.25)
        elif self.path_type == "sweep":
            self.x = self.formation_slot_x + math.sin(self.phase) * (self.amplitude * 1.5)
            self.y = self.formation_slot_y + math.sin(self.phase * 2) * (self.amplitude * 0.4)
        elif self.path_type == "dive":
            self.y += 120.0 * dt
            self.x = self.formation_slot_x + math.sin(self.phase * 1.5) * self.amplitude
        else:
            self.x = self.formation_slot_x
            self.y = self.formation_slot_y


@dataclass
class Projectile(Entity):
    """Bullet or projectile."""
    owner: ProjectileOwner = ProjectileOwner.PLAYER
    damage: int = 1
    radius: float = 4.0
    counted_for_dodge: bool = False  # To ensure a dodge is awarded at most once


@dataclass
class Obstacle(Entity):
    """Environmental hazards such as barriers or asteroids."""
    obstacle_type: str = "barrier"  # barrier, asteroid
    hp: int = 3
    radius: float = 20.0
    rotation: float = 0.0
    rot_speed: float = 1.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self.rotation += self.rot_speed * dt


@dataclass
class LaserLane:
    """Telegraphed laser lane obstacle that warns then fires."""
    id: int
    x: float
    width: float = 60.0
    warmup_time: float = 1.8
    active_time: float = 1.2
    timer: float = 0.0
    state: str = "warning"  # warning, firing, expired

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.state == "warning" and self.timer >= self.warmup_time:
            self.state = "firing"
            self.timer = 0.0
        elif self.state == "firing" and self.timer >= self.active_time:
            self.state = "expired"


@dataclass
class PowerUp(Entity):
    """Collectable item dropped by enemies."""
    powerup_type: PowerUpType = PowerUpType.SHIELD
    radius: float = 12.0
    vy: float = 80.0


@dataclass
class Particle:
    """Visual explosion or star particle."""
    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    max_lifetime: float
    color: Tuple[int, int, int] = (255, 200, 50)
    size: float = 3.0

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        return self.lifetime > 0.0
