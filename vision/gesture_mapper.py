"""STARFALL Right-Hand Gesture Coordinate Mapper."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CalibrationOffsets:
    min_x: float = 0.15
    max_x: float = 0.85
    min_y: float = 0.40
    max_y: float = 0.90


class GestureMapper:
    """Maps normalized hand coordinates to game screen coordinates with EMA smoothing and deadzones."""

    def __init__(
        self,
        screen_width: float = 800.0,
        screen_height: float = 700.0,
        smoothing_alpha: float = 0.28,
        deadzone: float = 0.02,
        calibration: Optional[CalibrationOffsets] = None,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.alpha = smoothing_alpha
        self.deadzone = deadzone
        self.calibration = calibration or CalibrationOffsets()

        self.smoothed_norm_x: Optional[float] = None
        self.smoothed_norm_y: Optional[float] = None

    def update(
        self,
        has_right_hand: bool,
        raw_norm_x: float,
        raw_norm_y: float,
        confidence: float = 1.0,
        min_confidence: float = 0.45,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Processes raw normalized hand position (0.0 to 1.0).
        Returns smoothed (game_x, game_y) coordinates, or (None, None) if hand lost.
        """
        if not has_right_hand or confidence < min_confidence:
            # Right hand lost: do not update coordinates
            return None, None

        # Remap inside calibration zone
        cal = self.calibration
        norm_x = (raw_norm_x - cal.min_x) / max(0.01, (cal.max_x - cal.min_x))
        norm_y = (raw_norm_y - cal.min_y) / max(0.01, (cal.max_y - cal.min_y))

        # Clamp remapped normalized coordinates to [0.0, 1.0]
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # First frame initialization
        if self.smoothed_norm_x is None or self.smoothed_norm_y is None:
            self.smoothed_norm_x = norm_x
            self.smoothed_norm_y = norm_y
        else:
            # Deadzone check to avoid micro-jitter
            dx = norm_x - self.smoothed_norm_x
            dy = norm_y - self.smoothed_norm_y
            if math.hypot(dx, dy) > self.deadzone:
                self.smoothed_norm_x += self.alpha * dx
                self.smoothed_norm_y += self.alpha * dy

        # Map to game screen coordinates
        game_x = self.smoothed_norm_x * self.screen_width
        # Restrict ship to bottom 45% of game area
        min_game_y = self.screen_height * 0.55
        max_game_y = self.screen_height - 30.0
        game_y = min_game_y + (self.smoothed_norm_y * (max_game_y - min_game_y))

        return game_x, game_y

    def reset(self) -> None:
        self.smoothed_norm_x = None
        self.smoothed_norm_y = None
