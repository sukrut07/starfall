"""STARFALL Pygame Graphical Arcade Renderer."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from game.state import GameStateSnapshot, GameStatus
from renderers.base import BaseRenderer


class PygameRenderer(BaseRenderer):
    """Polished graphical arcade renderer with HUD, AI Commander panel, and Webcam PIP."""

    def __init__(self, width: int = 800, height: int = 700, title: str = "STARFALL: Adaptive AI Arcade Shooter"):
        self.width = width
        self.height = height
        self.title = title
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_med: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        # Parallax Starfield
        self.stars_layer1: List[List[float]] = []  # [x, y, speed]
        self.stars_layer2: List[List[float]] = []

    def initialize(self) -> bool:
        if not PYGAME_AVAILABLE:
            return False

        pygame.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Helvetica", 34, bold=True)
        self.font_med = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.font_small = pygame.font.SysFont("Courier", 13)

        # Initialize stars
        self.stars_layer1 = [[random.uniform(0, self.width), random.uniform(0, self.height), random.uniform(25.0, 50.0)] for _ in range(50)]
        self.stars_layer2 = [[random.uniform(0, self.width), random.uniform(0, self.height), random.uniform(70.0, 130.0)] for _ in range(40)]
        return True

    def cleanup(self) -> None:
        if PYGAME_AVAILABLE and pygame.get_init():
            try:
                pygame.quit()
            except Exception:
                pass
        self.screen = None

    def render(
        self,
        snapshot: GameStateSnapshot,
        ai_status: str = "Ready",
        webcam_frame: Optional[np.ndarray] = None,
        gesture_debug: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.screen:
            return

        # 1. Update and Render Starfield
        self.screen.fill((8, 12, 24))  # Deep space dark blue
        self._render_starfield()

        # 2. Render Laser Lanes
        self._render_laser_lanes(snapshot.laser_lanes)

        # 3. Render Obstacles
        self._render_obstacles(snapshot.obstacles)

        # 4. Render Powerups
        self._render_powerups(snapshot.powerups)

        # 5. Render Enemies
        self._render_enemies(snapshot.enemies)

        # 6. Render Bullets
        self._render_bullets(snapshot.player_bullets, snapshot.enemy_bullets)

        # 7. Render Particles
        self._render_particles(snapshot.particles)

        # 8. Render Player Spaceship
        self._render_player(snapshot)

        # 9. Render HUD & AI Commander Panel
        self._render_hud(snapshot, ai_status)

        # 10. Render Webcam PIP Preview if available
        if webcam_frame is not None:
            self._render_webcam_pip(webcam_frame, gesture_debug)

        # 11. Render Special Overlays (Start, Pause, Game Over)
        self._render_state_overlays(snapshot)

        pygame.display.flip()

    def _render_starfield(self) -> None:
        dt = 0.016
        for s in self.stars_layer1:
            s[1] = (s[1] + s[2] * dt) % self.height
            pygame.draw.circle(self.screen, (100, 120, 160), (int(s[0]), int(s[1])), 1)

        for s in self.stars_layer2:
            s[1] = (s[1] + s[2] * dt) % self.height
            pygame.draw.circle(self.screen, (200, 220, 255), (int(s[0]), int(s[1])), 2)

    def _render_laser_lanes(self, lanes: List[Tuple[float, float, str, float]]) -> None:
        for lx, lwidth, lstate, timer in lanes:
            rect = pygame.Rect(int(lx - lwidth * 0.5), 0, int(lwidth), self.height)
            surf = pygame.Surface((int(lwidth), self.height), pygame.SRCALPHA)
            if lstate == "warning":
                pulse = int(127 + 127 * math.sin(timer * 12))
                surf.fill((255, 50, 50, max(20, min(80, pulse // 3))))
                pygame.draw.line(surf, (255, 80, 80, pulse), (0, 0), (0, self.height), 2)
                pygame.draw.line(surf, (255, 80, 80, pulse), (int(lwidth) - 1, 0), (int(lwidth) - 1, self.height), 2)
            elif lstate == "firing":
                surf.fill((255, 30, 30, 180))
                # Intense white core
                pygame.draw.rect(surf, (255, 240, 240, 240), (int(lwidth * 0.35), 0, int(lwidth * 0.3), self.height))
            self.screen.blit(surf, rect.topleft)

    def _render_obstacles(self, obstacles: List[Tuple[float, float, float, str, int]]) -> None:
        for ox, oy, radius, otype, hp in obstacles:
            ix, iy = int(ox), int(oy)
            ir = int(radius)
            if otype == "barrier":
                # Glowing blue energy barrier
                pygame.draw.circle(self.screen, (30, 80, 160), (ix, iy), ir)
                pygame.draw.circle(self.screen, (80, 160, 255), (ix, iy), ir, 3)
                pygame.draw.line(self.screen, (180, 220, 255), (ix - ir + 4, iy), (ix + ir - 4, iy), 2)
            else:
                # Jagged asteroid
                pygame.draw.circle(self.screen, (100, 95, 90), (ix, iy), ir)
                pygame.draw.circle(self.screen, (150, 140, 130), (ix, iy), ir, 2)

    def _render_powerups(self, powerups: List[Tuple[float, float, str]]) -> None:
        for px, py, ptype in powerups:
            ix, iy = int(px), int(py)
            color = (80, 200, 255) if ptype == "shield" else ((255, 200, 50) if ptype == "rapid_fire" else (220, 80, 255))
            pygame.draw.circle(self.screen, color, (ix, iy), 12, 2)
            tag = "S" if ptype == "shield" else ("R" if ptype == "rapid_fire" else "W")
            t_surf = self.font_small.render(tag, True, color)
            self.screen.blit(t_surf, (ix - 4, iy - 7))

    def _render_enemies(self, enemies: List[Tuple[float, float, str, int, int]]) -> None:
        for ex, ey, etype, hp, max_hp in enemies:
            ix, iy = int(ex), int(ey)
            if etype == "dreadnought":
                # Heavy red warship
                pts = [(ix, iy + 22), (ix - 24, iy - 16), (ix - 10, iy - 22), (ix + 10, iy - 22), (ix + 24, iy - 16)]
                pygame.draw.polygon(self.screen, (180, 25, 25), pts)
                pygame.draw.polygon(self.screen, (255, 90, 90), pts, 2)
                # HP bar
                bar_w = 34
                pct = max(0.0, hp / max_hp)
                pygame.draw.rect(self.screen, (60, 10, 10), (ix - bar_w // 2, iy - 30, bar_w, 4))
                pygame.draw.rect(self.screen, (255, 50, 50), (ix - bar_w // 2, iy - 30, int(bar_w * pct), 4))
            elif etype == "interceptor":
                # Sleek yellow interceptor
                pts = [(ix, iy + 16), (ix - 16, iy - 14), (ix, iy - 6), (ix + 16, iy - 14)]
                pygame.draw.polygon(self.screen, (220, 180, 20), pts)
                pygame.draw.polygon(self.screen, (255, 230, 80), pts, 2)
            elif etype == "raider":
                # Purple sweeping raider
                pts = [(ix, iy + 14), (ix - 18, iy - 10), (ix - 4, iy - 14), (ix + 4, iy - 14), (ix + 18, iy - 10)]
                pygame.draw.polygon(self.screen, (150, 40, 180), pts)
                pygame.draw.polygon(self.screen, (220, 90, 255), pts, 2)
            else:
                # Basic red scout
                pts = [(ix, iy + 14), (ix - 14, iy - 12), (ix + 14, iy - 12)]
                pygame.draw.polygon(self.screen, (210, 40, 40), pts)
                pygame.draw.polygon(self.screen, (255, 120, 120), pts, 2)

    def _render_bullets(self, p_bullets: List[Tuple[float, float]], e_bullets: List[Tuple[float, float]]) -> None:
        # Player lasers: cyan vertical beams
        for bx, by in p_bullets:
            ix, iy = int(bx), int(by)
            pygame.draw.line(self.screen, (160, 240, 255), (ix, iy - 6), (ix, iy + 6), 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (ix, iy - 6), 2)

        # Enemy projectiles: energetic orange/red plasma
        for bx, by in e_bullets:
            ix, iy = int(bx), int(by)
            pygame.draw.circle(self.screen, (255, 120, 30), (ix, iy), 5)
            pygame.draw.circle(self.screen, (255, 230, 150), (ix, iy), 2)

    def _render_particles(self, particles: List[Tuple[float, float, Tuple[int, int, int], float]]) -> None:
        for px, py, color, size in particles:
            pygame.draw.circle(self.screen, color, (int(px), int(py)), max(1, int(size)))

    def _render_player(self, snapshot: GameStateSnapshot) -> None:
        px, py = int(snapshot.player_x), int(snapshot.player_y)

        # Invulnerability flicker
        if snapshot.player_invulnerable and (int(snapshot.match_time * 12) % 2 == 0):
            return

        # Thruster plume particles
        flame_h = random.uniform(10, 20)
        flame_pts = [(px - 6, py + 12), (px + 6, py + 12), (px, py + 12 + flame_h)]
        pygame.draw.polygon(self.screen, (255, 140, 30), flame_pts)
        pygame.draw.polygon(self.screen, (255, 240, 120), [(px - 3, py + 12), (px + 3, py + 12), (px, py + 12 + flame_h * 0.5)])

        # Delta-wing fighter fuselage
        ship_pts = [
            (px, py - 18),         # Nose
            (px - 16, py + 12),    # Left wing
            (px - 6, py + 8),      # Inset
            (px + 6, py + 8),      # Inset
            (px + 16, py + 12),    # Right wing
        ]
        pygame.draw.polygon(self.screen, (40, 140, 230), ship_pts)
        pygame.draw.polygon(self.screen, (140, 220, 255), ship_pts, 2)
        # Cockpit canopy
        pygame.draw.ellipse(self.screen, (220, 250, 255), (px - 3, py - 8, 6, 12))

        # Shield bubble if active
        if snapshot.player_shield:
            surf = pygame.Surface((56, 56), pygame.SRCALPHA)
            pygame.draw.circle(surf, (50, 180, 255, 80), (28, 28), 24)
            pygame.draw.circle(surf, (120, 220, 255, 200), (28, 28), 24, 2)
            self.screen.blit(surf, (px - 28, py - 28))

    def _render_hud(self, snapshot: GameStateSnapshot, ai_status: str) -> None:
        # Top HUD bar background
        hud_bg = pygame.Surface((self.width, 48), pygame.SRCALPHA)
        hud_bg.fill((12, 18, 36, 210))
        self.screen.blit(hud_bg, (0, 0))
        pygame.draw.line(self.screen, (40, 70, 120), (0, 48), (self.width, 48), 1)

        # Score & High Score
        score_surf = self.font_med.render(f"SCORE: {snapshot.score:06d}", True, (255, 255, 255))
        self.screen.blit(score_surf, (16, 14))

        # Wave
        wave_surf = self.font_med.render(f"WAVE: {snapshot.current_wave}", True, (80, 210, 255))
        self.screen.blit(wave_surf, (190, 14))

        # Lives
        lives_text = "LIVES: " + ("♥ " * snapshot.player_lives)
        lives_surf = self.font_med.render(lives_text, True, (255, 70, 90))
        self.screen.blit(lives_surf, (290, 14))

        # Accuracy & Dodges
        acc_text = f"ACC: {snapshot.accuracy:.1%} | DODGES: {snapshot.dodges}"
        acc_surf = self.font_small.render(acc_text, True, (180, 200, 230))
        self.screen.blit(acc_surf, (430, 18))

        # Bottom AI Commander Briefing Panel
        panel_h = 76
        panel_y = self.height - panel_h
        panel_bg = pygame.Surface((self.width, panel_h), pygame.SRCALPHA)
        panel_bg.fill((10, 16, 32, 220))
        self.screen.blit(panel_bg, (0, panel_y))
        pygame.draw.line(self.screen, (40, 80, 140), (0, panel_y), (self.width, panel_y), 1)

        plan = snapshot.active_plan
        badge = "[FALLBACK]" if plan.is_fallback else "[GEMMA 4 ADAPTED]"
        badge_color = (255, 170, 60) if plan.is_fallback else (80, 240, 160)

        title_surf = self.font_small.render(f"AI TACTICAL DIRECTOR {badge} - {plan.formation.upper()} (Diff: {plan.difficulty})", True, badge_color)
        self.screen.blit(title_surf, (16, panel_y + 8))

        reason_surf = self.font_small.render(f"ANALYSIS: {plan.reason}", True, (220, 225, 235))
        self.screen.blit(reason_surf, (16, panel_y + 28))

        ev_text = f"EVIDENCE: {', '.join(plan.evidence)} (Conf: {plan.confidence:.0%}) | STATUS: {ai_status}"
        ev_surf = self.font_small.render(ev_text, True, (140, 165, 195))
        self.screen.blit(ev_surf, (16, panel_y + 48))

    def _render_webcam_pip(self, frame_bgr: np.ndarray, gesture_debug: Optional[Dict[str, Any]]) -> None:
        """Render Picture-in-Picture webcam preview in the top-right corner."""
        try:
            pip_w, pip_h = 160, 120
            small_bgr = cv2.resize(frame_bgr, (pip_w, pip_h))
            # Convert BGR to RGB
            small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
            # Create pygame surface from numpy array (transposed for pygame)
            pip_surf = pygame.surfarray.make_surface(np.rot90(np.fliplr(small_rgb)))

            pos_x = self.width - pip_w - 14
            pos_y = 54
            # Draw border
            border_color = (60, 220, 120) if (gesture_debug and gesture_debug.get("is_pinching")) else (50, 100, 180)
            pygame.draw.rect(self.screen, border_color, (pos_x - 2, pos_y - 2, pip_w + 4, pip_h + 4), 2)
            self.screen.blit(pip_surf, (pos_x, pos_y))

            # Overlay gesture status text
            if gesture_debug:
                is_pinch = gesture_debug.get("is_pinching", False)
                pinch_txt = "FIRE [PINCH]" if is_pinch else f"DIST: {gesture_debug.get('pinch_distance', 0):.2f}"
                p_col = (80, 255, 120) if is_pinch else (220, 220, 220)
                txt_surf = self.font_small.render(pinch_txt, True, p_col)
                self.screen.blit(txt_surf, (pos_x + 6, pos_y + pip_h - 18))
        except Exception:
            pass

    def _render_state_overlays(self, snapshot: GameStateSnapshot) -> None:
        if snapshot.status == GameStatus.START_SCREEN:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_large.render("STARFALL", True, (80, 210, 255))
            t2 = self.font_med.render("ADAPTIVE AI ARCADE SHOOTER", True, (255, 200, 80))
            t3 = self.font_small.render("Press [SPACE] or Pinch Left Hand to Launch", True, (240, 240, 240))
            t4 = self.font_small.render("Right Hand: Move | Left Hand Pinch: Fire | [P]: Pause", True, (160, 180, 210))

            self.screen.blit(t1, (self.width // 2 - t1.get_width() // 2, 220))
            self.screen.blit(t2, (self.width // 2 - t2.get_width() // 2, 270))
            self.screen.blit(t3, (self.width // 2 - t3.get_width() // 2, 340))
            self.screen.blit(t4, (self.width // 2 - t4.get_width() // 2, 380))

        elif snapshot.status == GameStatus.PAUSED:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            p_text = self.font_large.render("TACTICAL PAUSE", True, (255, 220, 50))
            sub_text = self.font_small.render("Press [P] to Resume Mission", True, (220, 220, 220))
            self.screen.blit(p_text, (self.width // 2 - p_text.get_width() // 2, 280))
            self.screen.blit(sub_text, (self.width // 2 - sub_text.get_width() // 2, 330))

        elif snapshot.status == GameStatus.GAME_OVER:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            go_text = self.font_large.render("MISSION TERMINATED", True, (255, 60, 60))
            sc_text = self.font_med.render(f"FINAL SCORE: {snapshot.score:06d} | WAVES CLEARED: {snapshot.current_wave}", True, (255, 255, 255))
            r_text = self.font_small.render("Press [R] to Deploy New Vessel | [Q] to Return to Menu", True, (220, 220, 220))

            self.screen.blit(go_text, (self.width // 2 - go_text.get_width() // 2, 250))
            self.screen.blit(sc_text, (self.width // 2 - sc_text.get_width() // 2, 300))
            self.screen.blit(r_text, (self.width // 2 - r_text.get_width() // 2, 350))

        elif snapshot.in_intermission and snapshot.status == GameStatus.PLAYING:
            plan_name = snapshot.active_plan.formation.upper().replace('_', ' ')
            wave_alert = self.font_med.render(f"INCOMING WAVE {snapshot.current_wave + 1}: {plan_name}", True, (255, 215, 60))
            self.screen.blit(wave_alert, (self.width // 2 - wave_alert.get_width() // 2, 280))
