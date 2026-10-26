"""Tests for STARFALL Collisions and Dodges."""

import pytest
from game.entities import PlayerShip, Enemy, Projectile, ProjectileOwner, LaserLane
from game.collisions import (
    check_circle_collision,
    check_point_in_laser_lane,
    check_projectile_dodge,
)


def test_circle_collision():
    e1 = PlayerShip(x=100.0, y=100.0, radius=15.0)
    e2 = Enemy(x=120.0, y=100.0, radius=10.0)
    # distance = 20, sum radii = 25 -> collision
    assert check_circle_collision(e1, e2) is True

    e3 = Enemy(x=150.0, y=100.0, radius=10.0)
    # distance = 50, sum radii = 25 -> no collision
    assert check_circle_collision(e1, e3) is False


def test_inactive_no_collision():
    e1 = PlayerShip(x=100.0, y=100.0, radius=15.0, active=False)
    e2 = Enemy(x=105.0, y=100.0, radius=10.0, active=True)
    assert check_circle_collision(e1, e2) is False


def test_laser_lane_collision():
    lane = LaserLane(id=1, x=200.0, width=60.0, state="warning")
    # Warning state does NOT damage
    assert check_point_in_laser_lane(200.0, 300.0, 14.0, lane) is False

    lane.state = "firing"
    # Inside lane
    assert check_point_in_laser_lane(200.0, 300.0, 14.0, lane) is True
    # Outside lane
    assert check_point_in_laser_lane(100.0, 300.0, 14.0, lane) is False


def test_projectile_dodge_detection():
    player = PlayerShip(x=400.0, y=600.0, radius=14.0)
    # Bullet at y=610 (passed player), x=420 (within proximity)
    proj = Projectile(x=420.0, y=610.0, radius=4.0, owner=ProjectileOwner.ENEMY)

    assert check_projectile_dodge(proj, player, 700.0, dodge_proximity=60.0) is True
    assert proj.counted_for_dodge is True

    # Second check must NOT award dodge again
    assert check_projectile_dodge(proj, player, 700.0, dodge_proximity=60.0) is False
