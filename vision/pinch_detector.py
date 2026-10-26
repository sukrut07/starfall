"""STARFALL Left-Hand Pinch Detection with Hysteresis and Debounce."""

from __future__ import annotations

import math
from typing import Tuple


class PinchDetector:
    """Detects pinch gestures with hysteresis and debouncing to prevent jitter."""

    def __init__(
        self,
        engage_threshold: float = 0.055,
        release_threshold: float = 0.085,
        debounce_frames: int = 2,
    ):
        self.engage_thresh = engage_threshold
        self.release_thresh = release_threshold
        self.debounce_frames = debounce_frames

        self.is_pinching: bool = False
        self.active_frames: int = 0
        self.inactive_frames: int = 0
        self.current_distance: float = 1.0

    def update(
        self,
        has_left_hand: bool,
        thumb_tip: Tuple[float, float],
        index_tip: Tuple[float, float],
        confidence: float = 1.0,
        min_confidence: float = 0.45,
    ) -> bool:
        """
        Update pinch detector state with current left-hand landmarks.
        Returns True if firing pinch is active.
        """
        if not has_left_hand or confidence < min_confidence:
            # Left hand lost: immediately release pinch for safety
            self.is_pinching = False
            self.active_frames = 0
            self.inactive_frames += 1
            self.current_distance = 1.0
            return False

        # Calculate Euclidean distance between thumb and index tip
        dx = thumb_tip[0] - index_tip[0]
        dy = thumb_tip[1] - index_tip[1]
        dist = math.hypot(dx, dy)
        self.current_distance = dist

        if not self.is_pinching:
            # Check engagement threshold
            if dist <= self.engage_thresh:
                self.active_frames += 1
                if self.active_frames >= self.debounce_frames:
                    self.is_pinching = True
                    self.inactive_frames = 0
            else:
                self.active_frames = 0
        else:
            # Check release threshold (hysteresis prevents flicker)
            if dist >= self.release_thresh:
                self.inactive_frames += 1
                if self.inactive_frames >= self.debounce_frames:
                    self.is_pinching = False
                    self.active_frames = 0
            else:
                self.inactive_frames = 0

        return self.is_pinching

    def reset(self) -> None:
        self.is_pinching = False
        self.active_frames = 0
        self.inactive_frames = 0
        self.current_distance = 1.0
