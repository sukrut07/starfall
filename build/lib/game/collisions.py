"""STARFALL Collision Detection and Resolution."""

from __future__ import annotations

import math
from typing import List, Tuple
from game.entities import Entity, PlayerShip, Enemy, Projectile, Obstacle, LaserLane, PowerUp


def check_circle_collision(e1: Entity, e2: Entity) -> bool:
    """Check if two circular hitboxes overlap."""
    if not (e1.active and e2.active):
        return False
    dx = e1.x - e2.x
    dy = e1.y - e2.y
    dist_sq = dx * dx + dy * dy
    radius_sum = e1.radius + e2.radius
    return dist_sq <= (radius_sum * radius_sum)


def check_point_in_laser_lane(px: float, py: float, radius: float, lane: LaserLane) -> bool:
    """Check if entity is inside an active firing laser lane."""
    if lane.state != "firing":
        return False
    left = lane.x - lane.width * 0.5
    right = lane.x + lane.width * 0.5
    return (px + radius >= left) and (px - radius <= right)


def check_projectile_dodge(
    proj: Projectile,
    player: PlayerShip,
    play_area_height: float,
    dodge_proximity: float = 65.0,
) -> bool:
    """
    Check if an enemy projectile successfully flew past the player without hitting.
    A dodge occurs when an enemy projectile crosses below the player's Y level,
    was within horizontal threat distance (dodge_proximity), and didn't hit the player.
    """
    if proj.counted_for_dodge or not proj.active:
        return False

    # Check if projectile just passed player Y
    if proj.y > player.y:
        dx = abs(proj.x - player.x)
        if dx <= dodge_proximity:
            proj.counted_for_dodge = True
            return True
        else:
            # Too far away to count as a threat dodge, but still mark counted so we don't re-test
            proj.counted_for_dodge = True

    return False
