"""STARFALL Enemy Archetypes and Formation Generators."""

from __future__ import annotations

import random
from typing import List
from game.entities import Enemy, EnemyType


def spawn_formation(
    formation_name: str,
    count: int,
    difficulty: int,
    play_width: float,
    play_height: float,
    start_id: int = 1,
) -> List[Enemy]:
    """
    Generate a list of enemies positioned in the requested formation pattern.
    Only supported formations are allowed.
    """
    enemies: List[Enemy] = []
    center_x = play_width * 0.5
    count = max(3, min(count, 20))
    current_id = start_id

    # Base attributes scaled slightly by difficulty
    shoot_cd = max(1.2, 3.2 - (difficulty * 0.35))

    if formation_name == "v_formation":
        # Classic V formation
        row_spacing = 38.0
        col_spacing = 50.0
        base_y = 90.0
        for i in range(count):
            side = 1 if i % 2 == 1 else -1
            layer = (i + 1) // 2
            slot_x = center_x + (side * layer * col_spacing)
            slot_y = base_y + (layer * row_spacing)
            # Leader at apex is tough dreadnought if count > 6
            e_type = EnemyType.DREADNOUGHT if i == 0 and count >= 6 else (EnemyType.RAIDER if layer % 2 == 1 else EnemyType.SCOUT)
            hp = 3 if e_type == EnemyType.DREADNOUGHT else (2 if e_type == EnemyType.RAIDER else 1)
            
            e = Enemy(
                id=current_id,
                x=center_x,
                y=-40.0 - (i * 25.0),
                spawn_x=center_x,
                spawn_y=-40.0 - (i * 25.0),
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=500 if e_type == EnemyType.DREADNOUGHT else (150 if e_type == EnemyType.RAIDER else 100),
                shoot_cooldown=shoot_cd + random.uniform(-0.3, 0.3),
                shoot_timer=random.uniform(0.5, shoot_cd),
                path_type="sine",
                amplitude=35.0,
                frequency=1.8,
            )
            enemies.append(e)
            current_id += 1

    elif formation_name == "center_sweep":
        # Two rows sweeping back and forth through center
        row_count = 2
        per_row = (count + 1) // row_count
        for i in range(count):
            row = i // per_row
            col = i % per_row
            slot_x = (play_width * 0.25) + (col * (play_width * 0.5 / max(1, per_row - 1)))
            slot_y = 90.0 + (row * 50.0)
            e_type = EnemyType.RAIDER if row == 0 else EnemyType.SCOUT
            hp = 2 if e_type == EnemyType.RAIDER else 1
            e = Enemy(
                id=current_id,
                x=slot_x,
                y=-50.0,
                spawn_x=slot_x,
                spawn_y=-50.0,
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=150 if e_type == EnemyType.RAIDER else 100,
                shoot_cooldown=shoot_cd,
                shoot_timer=random.uniform(0.5, shoot_cd),
                path_type="sweep",
                amplitude=60.0,
                frequency=2.2,
            )
            enemies.append(e)
            current_id += 1

    elif formation_name == "left_flank":
        # Concentrated heavy pressure on the left lane (tests if player camps right or stays trapped left)
        for i in range(count):
            col = i % 2
            row = i // 2
            slot_x = 70.0 + (col * 55.0)
            slot_y = 80.0 + (row * 45.0)
            e_type = EnemyType.INTERCEPTOR if i % 3 == 0 else EnemyType.SCOUT
            hp = 2 if e_type == EnemyType.INTERCEPTOR else 1
            e = Enemy(
                id=current_id,
                x=slot_x,
                y=-40.0 - (i * 20.0),
                spawn_x=slot_x,
                spawn_y=-40.0 - (i * 20.0),
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=150 if e_type == EnemyType.INTERCEPTOR else 100,
                shoot_cooldown=shoot_cd * 0.9,
                shoot_timer=random.uniform(0.3, shoot_cd),
                path_type="sine",
                amplitude=30.0,
                frequency=2.0,
            )
            enemies.append(e)
            current_id += 1

    elif formation_name == "right_flank":
        # Concentrated pressure on the right lane
        for i in range(count):
            col = i % 2
            row = i // 2
            slot_x = play_width - 150.0 + (col * 55.0)
            slot_y = 80.0 + (row * 45.0)
            e_type = EnemyType.INTERCEPTOR if i % 3 == 0 else EnemyType.SCOUT
            hp = 2 if e_type == EnemyType.INTERCEPTOR else 1
            e = Enemy(
                id=current_id,
                x=slot_x,
                y=-40.0 - (i * 20.0),
                spawn_x=slot_x,
                spawn_y=-40.0 - (i * 20.0),
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=150 if e_type == EnemyType.INTERCEPTOR else 100,
                shoot_cooldown=shoot_cd * 0.9,
                shoot_timer=random.uniform(0.3, shoot_cd),
                path_type="sine",
                amplitude=30.0,
                frequency=2.0,
            )
            enemies.append(e)
            current_id += 1

    elif formation_name == "split_formation":
        # Two separated wings, leaving center open or dangerous
        half = count // 2
        for i in range(count):
            is_left = (i < half)
            idx = i if is_left else (i - half)
            col = idx % 2
            row = idx // 2
            if is_left:
                slot_x = 80.0 + (col * 50.0)
            else:
                slot_x = play_width - 160.0 + (col * 50.0)
            slot_y = 85.0 + (row * 48.0)
            e_type = EnemyType.RAIDER if idx == 0 else EnemyType.SCOUT
            hp = 2 if e_type == EnemyType.RAIDER else 1
            e = Enemy(
                id=current_id,
                x=slot_x,
                y=-40.0,
                spawn_x=slot_x,
                spawn_y=-40.0,
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=120,
                shoot_cooldown=shoot_cd,
                shoot_timer=random.uniform(0.4, shoot_cd),
                path_type="sine",
                amplitude=25.0,
                frequency=2.5,
            )
            enemies.append(e)
            current_id += 1

    elif formation_name == "staggered_assault":
        # Staggered columns that descend aggressively
        cols = 4
        spacing = (play_width - 160.0) / max(1, cols - 1)
        for i in range(count):
            col = i % cols
            row = i // cols
            slot_x = 80.0 + (col * spacing)
            slot_y = 70.0 + (row * 50.0)
            e_type = EnemyType.DREADNOUGHT if row == 0 and col in (1, 2) else EnemyType.SCOUT
            hp = 3 if e_type == EnemyType.DREADNOUGHT else 1
            e = Enemy(
                id=current_id,
                x=slot_x,
                y=-30.0 - (row * 40.0),
                spawn_x=slot_x,
                spawn_y=-30.0 - (row * 40.0),
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=300 if e_type == EnemyType.DREADNOUGHT else 100,
                shoot_cooldown=shoot_cd * 0.95,
                shoot_timer=random.uniform(0.4, shoot_cd),
                path_type="sine",
                amplitude=40.0,
                frequency=1.9,
            )
            enemies.append(e)
            current_id += 1

    else:  # converging_pincer or fallback
        # Pincer: enemies enter from extreme left & right edges toward center
        half = count // 2
        for i in range(count):
            from_left = (i % 2 == 0)
            step = i // 2
            slot_x = (center_x - 120.0 + (step * 35.0)) if from_left else (center_x + 120.0 - (step * 35.0))
            slot_y = 80.0 + (step * 40.0)
            spawn_x = -30.0 if from_left else (play_width + 30.0)
            spawn_y = 50.0 + (step * 30.0)
            e_type = EnemyType.INTERCEPTOR if step % 2 == 1 else EnemyType.SCOUT
            hp = 2 if e_type == EnemyType.INTERCEPTOR else 1
            e = Enemy(
                id=current_id,
                x=spawn_x,
                y=spawn_y,
                spawn_x=spawn_x,
                spawn_y=spawn_y,
                formation_slot_x=slot_x,
                formation_slot_y=slot_y,
                enemy_type=e_type,
                hp=hp,
                max_hp=hp,
                point_value=150 if e_type == EnemyType.INTERCEPTOR else 100,
                shoot_cooldown=shoot_cd,
                shoot_timer=random.uniform(0.4, shoot_cd),
                path_type="sine",
                amplitude=35.0,
                frequency=2.0,
            )
            enemies.append(e)
            current_id += 1

    return enemies
