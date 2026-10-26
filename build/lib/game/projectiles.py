"""STARFALL Projectile Management."""

from __future__ import annotations

import math
from typing import List, Tuple
from game.entities import Projectile, ProjectileOwner, PlayerShip, Enemy


def create_player_projectiles(player: PlayerShip, base_speed: float = -620.0, current_id: int = 1000) -> List[Projectile]:
    """Create player bullets based on active powerups."""
    bullets: List[Projectile] = []
    
    if player.spread_shot_timer > 0.0:
        # Triple spread shot
        angles = [-0.18, 0.0, 0.18]
        for idx, ang in enumerate(angles):
            vx = math.sin(ang) * abs(base_speed)
            vy = base_speed * math.cos(ang)
            b = Projectile(
                id=current_id + idx,
                x=player.x + (math.sin(ang) * 15.0),
                y=player.y - 12.0,
                vx=vx,
                vy=vy,
                radius=4.5,
                owner=ProjectileOwner.PLAYER,
                damage=1,
            )
            bullets.append(b)
    else:
        # Standard double laser
        b1 = Projectile(
            id=current_id,
            x=player.x - 7.0,
            y=player.y - 12.0,
            vx=0.0,
            vy=base_speed,
            radius=4.0,
            owner=ProjectileOwner.PLAYER,
            damage=1,
        )
        b2 = Projectile(
            id=current_id + 1,
            x=player.x + 7.0,
            y=player.y - 12.0,
            vx=0.0,
            vy=base_speed,
            radius=4.0,
            owner=ProjectileOwner.PLAYER,
            damage=1,
        )
        bullets.extend([b1, b2])

    return bullets


def create_enemy_projectile(
    enemy: Enemy,
    player: PlayerShip,
    speed: float = 240.0,
    current_id: int = 2000,
) -> List[Projectile]:
    """Create enemy projectiles based on enemy archetype."""
    bullets: List[Projectile] = []

    if enemy.enemy_type.value == "interceptor":
        # Aimed projectile toward player current position
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            vx = (dx / dist) * speed
            vy = (dy / dist) * speed
        else:
            vx, vy = 0.0, speed

        b = Projectile(
            id=current_id,
            x=enemy.x,
            y=enemy.y + enemy.radius,
            vx=vx,
            vy=vy,
            radius=5.0,
            owner=ProjectileOwner.ENEMY,
            damage=1,
        )
        bullets.append(b)

    elif enemy.enemy_type.value == "dreadnought":
        # Dual angled spread
        for idx, ang in enumerate([-0.25, 0.25]):
            b = Projectile(
                id=current_id + idx,
                x=enemy.x + (-10.0 if idx == 0 else 10.0),
                y=enemy.y + enemy.radius,
                vx=math.sin(ang) * speed,
                vy=math.cos(ang) * speed,
                radius=5.5,
                owner=ProjectileOwner.ENEMY,
                damage=1,
            )
            bullets.append(b)
    else:
        # Straight downward bullet
        b = Projectile(
            id=current_id,
            x=enemy.x,
            y=enemy.y + enemy.radius,
            vx=0.0,
            vy=speed,
            radius=4.5,
            owner=ProjectileOwner.ENEMY,
            damage=1,
        )
        bullets.append(b)

    return bullets
