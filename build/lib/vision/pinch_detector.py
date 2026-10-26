"""STARFALL Left-Hand Pinch Detection with Hysteresis, Smoothing, Scale Normalization, and Stale Expiry."""

from __future__ import annotations

import math
import time
from typing import Optional, Tuple


class PinchDetector:
    """Detects pinch gestures with hysteresis, distance smoothing, scale normalization, and debouncing."""

    def __init__(
        self,
        engage_threshold: float = 0.055,
        release_threshold: float = 0.085,
        debounce_frames: int = 2,
        stale_timeout_seconds: float = 0.25,
        smoothing_alpha: float = 0.85,
    ):
        self.engage_thresh = engage_threshold
        self.release_thresh = release_threshold
        self.debounce_frames = debounce_frames
        self.stale_timeout = stale_timeout_seconds
        self.smoothing_alpha = smoothing_alpha

        self.is_pinching: bool = False
        self.active_frames: int = 0
        self.inactive_frames: int = 0
        self.current_distance: float = 1.0
        self.last_update_timestamp: float = time.time()

    def update(
        self,
        has_left_hand: bool,
        thumb_tip: Tuple[float, float],
        index_tip: Tuple[float, float],
        confidence: float = 1.0,
        min_confidence: float = 0.45,
        hand_scale: float = 1.0,
        timestamp: Optional[float] = None,
    ) -> bool:
        """
        Update pinch detector state with current left-hand landmarks.
        Returns True if firing pinch is active.
        """
        now = timestamp if timestamp is not None else time.time()

        # Check for stale frame expiry
        if now - self.last_update_timestamp > self.stale_timeout:
            self.reset()

        self.last_update_timestamp = now

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
        raw_dist = math.hypot(dx, dy)

        # Scale normalization: adjust by hand scale relative to baseline palm length (0.20)
        # Closer hand has larger hand_scale -> raw_dist is divided by scale ratio
        if hand_scale > 0.01 and hand_scale != 1.0:
            scale_ratio = max(0.35, hand_scale / 0.20)
            effective_dist = raw_dist / scale_ratio
        else:
            effective_dist = raw_dist

        # Exponential moving average filter for distance smoothing
        if self.current_distance >= 0.99:
            self.current_distance = effective_dist
        else:
            self.current_distance = ((1.0 - self.smoothing_alpha) * self.current_distance) + (self.smoothing_alpha * effective_dist)

        if not self.is_pinching:
            # Check engagement threshold
            if self.current_distance <= self.engage_thresh:
                self.active_frames += 1
                if self.active_frames >= self.debounce_frames:
                    self.is_pinching = True
                    self.inactive_frames = 0
            else:
                self.active_frames = 0
        else:
            # Check release threshold (hysteresis prevents flicker)
            if self.current_distance >= self.release_thresh:
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
        self.last_update_timestamp = time.time()
