"""STARFALL Obstacles and Hazards."""

from __future__ import annotations

import random
from typing import List, Tuple
from game.entities import Obstacle, LaserLane


def spawn_obstacles(
    obstacle_type: str,
    difficulty: int,
    play_width: float,
    play_height: float,
    start_id: int = 100,
) -> Tuple[List[Obstacle], List[LaserLane]]:
    """
    Generate environmental obstacles matching the requested obstacle type.
    """
    obstacles: List[Obstacle] = []
    laser_lanes: List[LaserLane] = []

    if obstacle_type == "slow_moving_barriers":
        # 2 or 3 drifting shield barriers
        barrier_count = min(3, 1 + (difficulty // 2))
        spacing = play_width / (barrier_count + 1)
        for i in range(barrier_count):
            obs = Obstacle(
                id=start_id + i,
                x=spacing * (i + 1) + random.uniform(-20, 20),
                y=play_height * 0.42 + (i % 2) * 35.0,
                vx=random.choice([-30.0, 30.0]),
                vy=0.0,
                radius=26.0,
                obstacle_type="barrier",
                hp=4,
            )
            obstacles.append(obs)

    elif obstacle_type == "drifting_asteroids":
        # Asteroids slowly moving down-screen
        count = min(4, 2 + (difficulty // 2))
        for i in range(count):
            obs = Obstacle(
                id=start_id + i,
                x=random.uniform(50.0, play_width - 50.0),
                y=random.uniform(-100.0, -20.0),
                vx=random.uniform(-20.0, 20.0),
                vy=random.uniform(35.0, 65.0),
                radius=random.uniform(16.0, 24.0),
                obstacle_type="asteroid",
                hp=2,
                rot_speed=random.uniform(-2.0, 2.0),
            )
            obstacles.append(obs)

    elif obstacle_type == "telegraphed_laser_lane":
        # 1 or 2 telegraphed vertical laser beams that activate after a warning
        lane_count = 1 if difficulty <= 2 else 2
        lane_width = 70.0
        used_x = []
        for i in range(lane_count):
            target_x = random.choice([play_width * 0.25, play_width * 0.5, play_width * 0.75])
            if target_x in used_x:
                target_x = play_width * 0.35
            used_x.append(target_x)
            
            lane = LaserLane(
                id=start_id + i,
                x=target_x,
                width=lane_width,
                warmup_time=max(1.2, 2.0 - (difficulty * 0.15)),
                active_time=1.2,
                timer=0.0,
                state="warning",
            )
            laser_lanes.append(lane)

    return obstacles, laser_lanes
