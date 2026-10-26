"""STARFALL Keyboard Controllers for Pygame and Terminal frontends."""

from __future__ import annotations

import sys
import time
from typing import Optional, Set
from controls.base import BaseController
from game.state import InputCommand

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class PygameKeyboardController(BaseController):
    """Processes Pygame keyboard events and key states."""

    def __init__(self):
        self._quit_requested = False
        self._pause_triggered = False
        self._restart_triggered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle discrete keydown events (pause, restart, quit)."""
        if event.type == pygame.QUIT:
            self._quit_requested = True
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                self._quit_requested = True
            elif event.key == pygame.K_p:
                self._pause_triggered = True
            elif event.key == pygame.K_r:
                self._restart_triggered = True

    def poll(self) -> InputCommand:
        if not PYGAME_AVAILABLE:
            return InputCommand()

        keys = pygame.key.get_pressed()
        move_x = 0.0
        move_y = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += 1.0

        fire = bool(keys[pygame.K_SPACE] or keys[pygame.K_j] or keys[pygame.K_z])

        cmd = InputCommand(
            move_x=move_x,
            move_y=move_y,
            fire=fire,
            pause=self._pause_triggered,
            restart=self._restart_triggered,
            quit=self._quit_requested,
            absolute_pos=False,
        )

        self._pause_triggered = False
        self._restart_triggered = False
        return cmd


class TerminalKeyboardController(BaseController):
    """Portable non-blocking keyboard reader for terminals (macOS, Linux, Windows)."""

    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        self._old_termios = None
        self._running = False
        self._last_fire_time = 0.0
        self._active_keys: Set[str] = set()

    def start(self) -> bool:
        self._running = True
        if not self.is_windows:
            try:
                import termios
                import tty
                self._old_termios = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                pass
        return True

    def stop(self) -> None:
        self._running = False
        if not self.is_windows and self._old_termios is not None:
            try:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_termios)
            except Exception:
                pass
            self._old_termios = None

    def _read_chars(self) -> str:
        chars = ""
        if self.is_windows:
            try:
                import msvcrt
                while msvcrt.kbhit():
                    ch = msvcrt.getch()
                    try:
                        chars += ch.decode("utf-8", errors="ignore")
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            try:
                import select
                while select.select([sys.stdin], [], [], 0)[0]:
                    ch = sys.stdin.read(1)
                    if not ch:
                        break
                    chars += ch
                    # Handle escape sequences for arrow keys
                    if ch == "\x1b":
                        # Read remainder of escape code if available
                        time.sleep(0.002)
                        if select.select([sys.stdin], [], [], 0)[0]:
                            seq = sys.stdin.read(2)
                            chars += seq
            except Exception:
                pass
        return chars

    def poll(self) -> InputCommand:
        chars = self._read_chars().lower()
        cmd = InputCommand()

        if not chars:
            return cmd

        # Process input characters
        if "q" in chars or "\x1b" in chars and len(chars) == 1:
            cmd.quit = True
        if "p" in chars:
            cmd.pause = True
        if "r" in chars:
            cmd.restart = True
        if " " in chars or "j" in chars:
            cmd.fire = True

        # Movement: WASD or ANSI arrow keys
        if "a" in chars or "\x1b[d" in chars:
            cmd.move_x -= 1.0
        if "d" in chars or "\x1b[c" in chars:
            cmd.move_x += 1.0
        if "w" in chars or "\x1b[a" in chars:
            cmd.move_y -= 1.0
        if "s" in chars or "\x1b[b" in chars:
            cmd.move_y += 1.0

        return cmd
