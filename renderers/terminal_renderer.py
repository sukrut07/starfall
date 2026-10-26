"""STARFALL Real-time ASCII Terminal Game Renderer."""

from __future__ import annotations

import os
import shutil
import sys
from typing import Any, Dict, List, Optional
import numpy as np

from game.state import GameStateSnapshot, GameStatus
from renderers.base import BaseRenderer
from renderers.hud import format_hud_header, format_tactical_panel


class TerminalRenderer(BaseRenderer):
    """High-performance real-time ASCII arcade renderer."""

    def __init__(self, cols: int = 72, rows: int = 22):
        self.cols = cols
        self.rows = rows
        self._initialized = False

    def initialize(self) -> bool:
        # Hide terminal cursor and clear screen
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()
        self._initialized = True
        return True

    def cleanup(self) -> None:
        # Restore terminal cursor and clear screen
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()
        self._initialized = False

    def render(
        self,
        snapshot: GameStateSnapshot,
        ai_status: str = "Ready",
        webcam_frame: Optional[np.ndarray] = None,
        gesture_debug: Optional[Dict[str, Any]] = None,
    ) -> None:
        term_size = shutil.get_terminal_size((80, 28))
        if term_size.columns < 60 or term_size.lines < 24:
            # Terminal resize warning
            sys.stdout.write("\033[H\033[2J")
            sys.stdout.write(f"TERMINAL TOO SMALL: {term_size.columns}x{term_size.lines}. Please expand to at least 74x26.\n")
            sys.stdout.flush()
            return

        lines: List[str] = []

        # 1. Title & HUD Bar
        lines.append("╔══════════════════════════════════════════════════════════════════════╗")
        lines.append("║                   ★ STARFALL : ADAPTIVE AI SHOOTER ★                 ║")
        lines.append("╠══════════════════════════════════════════════════════════════════════╣")
        
        hud = format_hud_header(snapshot)
        lines.append(f"║ {hud.ljust(68)[:68]} ║")
        lines.append("╠══════════════════════════════════════════════════════════════════════╣")

        # 2. Game Grid Buffer
        grid = [[" " for _ in range(self.cols)] for _ in range(self.rows)]

        # Background stars
        stars_locs = [(10, 3), (25, 7), (55, 4), (40, 11), (15, 17), (62, 14), (32, 18), (5, 9)]
        for sx, sy in stars_locs:
            if 0 <= sx < self.cols and 0 <= sy < self.rows:
                grid[sy][sx] = "·"

        # Sim coordinates to grid scaling: sim is 800w x 700h
        sx_scale = self.cols / 800.0
        sy_scale = self.rows / 700.0

        # Draw Laser Lanes
        for lx, lwidth, lstate, _ in snapshot.laser_lanes:
            col_x = int(lx * sx_scale)
            char = "█" if lstate == "firing" else "│"
            for r in range(self.rows):
                if 0 <= col_x < self.cols:
                    grid[r][col_x] = char

        # Draw Obstacles
        for ox, oy, _, otype, _ in snapshot.obstacles:
            gx = int(ox * sx_scale)
            gy = int(oy * sy_scale)
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                grid[gy][gx] = "#" if otype == "barrier" else "O"

        # Draw Powerups
        for px, py, ptype in snapshot.powerups:
            gx = int(px * sx_scale)
            gy = int(py * sy_scale)
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                grid[gy][gx] = "S" if ptype == "shield" else ("R" if ptype == "rapid_fire" else "W")

        # Draw Enemies
        for ex, ey, etype, hp, max_hp in snapshot.enemies:
            gx = int(ex * sx_scale)
            gy = int(ey * sy_scale)
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                if etype == "dreadnought":
                    char = "Ω"
                elif etype == "interceptor":
                    char = "X"
                elif etype == "raider":
                    char = "W"
                else:
                    char = "▼"
                grid[gy][gx] = char

        # Draw Enemy Bullets
        for bx, by in snapshot.enemy_bullets:
            gx = int(bx * sx_scale)
            gy = int(by * sy_scale)
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                grid[gy][gx] = "v"

        # Draw Player Bullets
        for bx, by in snapshot.player_bullets:
            gx = int(bx * sx_scale)
            gy = int(by * sy_scale)
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                grid[gy][gx] = "!"

        # Draw Player Ship
        px = int(snapshot.player_x * sx_scale)
        py = int(snapshot.player_y * sy_scale)
        if 0 <= px < self.cols and 0 <= gy < self.rows:
            p_char = "▲" if not snapshot.player_invulnerable or (int(snapshot.match_time * 8) % 2 == 0) else "△"
            if snapshot.player_shield:
                if px > 0:
                    grid[py][px - 1] = "("
                grid[py][px] = p_char
                if px < self.cols - 1:
                    grid[py][px + 1] = ")"
            else:
                grid[py][px] = p_char

        # Format grid rows into frame lines
        for r in range(self.rows):
            row_str = "".join(grid[r])
            # Overlays for special states
            if snapshot.status == GameStatus.START_SCREEN and r == 9:
                row_str = "        PRESS [SPACE] OR PINCH TO ENGAGE STARFALL HYPERDRIVE        "
            elif snapshot.status == GameStatus.PAUSED and r == 10:
                row_str = "                        === TACTICAL PAUSE ===                      "
            elif snapshot.status == GameStatus.GAME_OVER and r == 9:
                row_str = "                         *** MISSION FAILED ***                     "
            elif snapshot.status == GameStatus.GAME_OVER and r == 11:
                row_str = "                     PRESS [R] TO RESTART MISSION                   "
            elif snapshot.in_intermission and r == 9 and snapshot.status == GameStatus.PLAYING:
                plan_name = snapshot.active_plan.formation.upper().replace('_', ' ')
                row_str = f"               >>> INCOMING WAVE {snapshot.current_wave + 1}: {plan_name} <<<               "[:self.cols]

            lines.append(f"║{row_str.ljust(self.cols)[:self.cols]}║")

        # 3. Tactical AI Briefing Panel
        lines.append("╠══════════════════════════════════════════════════════════════════════╣")
        tac_lines = format_tactical_panel(snapshot, ai_status)
        for tline in tac_lines[:4]:
            lines.append(f"║ {tline.ljust(68)[:68]} ║")

        # Gesture status if active
        if gesture_debug and gesture_debug.get("camera_active"):
            r_hand = "RIGHT: DETECTED" if gesture_debug.get("has_right_hand") else "RIGHT: MISSING"
            l_hand = "PINCH: FIRING" if gesture_debug.get("is_pinching") else ("LEFT: DETECTED" if gesture_debug.get("has_left_hand") else "LEFT: MISSING")
            gest_str = f"VISION: [ACTIVE] | {r_hand} | {l_hand} (dist: {gesture_debug.get('pinch_distance', 0):.2f})"
            lines.append(f"║ {gest_str.ljust(68)[:68]} ║")
        else:
            lines.append("║ CONTROLS: [A/D] or [←/→] Move | [SPACE] Fire | [P] Pause | [Q] Quit ║")

        lines.append("╚══════════════════════════════════════════════════════════════════════╝")

        # Render frame using cursor home for zero-flicker display
        sys.stdout.write("\033[H" + "\n".join(lines))
        sys.stdout.flush()
