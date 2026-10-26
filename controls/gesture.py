"""STARFALL Gesture Controller integrating camera vision and gesture mapping."""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple, Any
import cv2
import numpy as np

from controls.base import BaseController
from game.state import InputCommand
from vision.camera import CameraService
from vision.hand_tracker import HandTracker, HandTrackingResult
from vision.pinch_detector import PinchDetector
from vision.gesture_mapper import GestureMapper, CalibrationOffsets


class GestureController(BaseController):
    """Two-hand gesture controller: Right hand moves spaceship, Left hand pinches to fire."""

    def __init__(
        self,
        camera_index: int = 0,
        model_path: str = "assets/models/hand_landmarker.task",
        screen_width: float = 800.0,
        screen_height: float = 700.0,
        smoothing_alpha: float = 0.28,
        deadzone: float = 0.02,
        pinch_engage_thresh: float = 0.055,
        pinch_release_thresh: float = 0.085,
        calibration: Optional[CalibrationOffsets] = None,
    ):
        self.camera = CameraService(camera_index=camera_index)
        self.tracker = HandTracker(model_path=model_path)
        self.pinch_detector = PinchDetector(
            engage_threshold=pinch_engage_thresh,
            release_threshold=pinch_release_thresh,
        )
        self.mapper = GestureMapper(
            screen_width=screen_width,
            screen_height=screen_height,
            smoothing_alpha=smoothing_alpha,
            deadzone=deadzone,
            calibration=calibration,
        )

        self.last_result: HandTrackingResult = HandTrackingResult()
        self.latest_frame: Optional[np.ndarray] = None
        self.is_camera_active: bool = False
        self.last_fire_state: bool = False
        self.last_target_x: Optional[float] = None
        self.last_target_y: Optional[float] = None

    def start(self) -> bool:
        self.is_camera_active = self.camera.start()
        return self.is_camera_active

    def stop(self) -> None:
        self.camera.stop()
        self.tracker.close()
        self.is_camera_active = False

    def poll(self) -> InputCommand:
        cmd = InputCommand()
        if not self.is_camera_active:
            return cmd

        # Fetch raw unmirrored frame so MediaPipe classifies anatomical handedness correctly
        raw_frame = self.camera.get_latest_frame(mirror=False)
        if raw_frame is None:
            # Stale / missing frame: hold last ship position if known
            if self.last_target_x is not None and self.last_target_y is not None:
                cmd.absolute_pos = True
                cmd.target_x = self.last_target_x
                cmd.target_y = self.last_target_y
            return cmd

        # Process with MediaPipe; mirror coordinates (1.0 - x) for natural user mirror-view
        self.last_result = self.tracker.process_frame(raw_frame, mirrored=True)
        # Flip frame horizontally for user visual preview
        self.latest_frame = cv2.flip(raw_frame, 1)

        # 1. Right hand movement mapping
        if self.last_result.has_right_hand:
            gx, gy = self.mapper.update(
                has_right_hand=True,
                raw_norm_x=self.last_result.right_x,
                raw_norm_y=self.last_result.right_y,
                confidence=self.last_result.right_confidence,
            )
            if gx is not None and gy is not None:
                cmd.absolute_pos = True
                cmd.target_x = gx
                cmd.target_y = gy
                self.last_target_x = gx
                self.last_target_y = gy
        else:
            # Explicit hand-loss behavior: hold last position rather than jumping to stale coords
            if self.last_target_x is not None and self.last_target_y is not None:
                cmd.absolute_pos = True
                cmd.target_x = self.last_target_x
                cmd.target_y = self.last_target_y

        # 2. Left hand pinch firing (with scale normalization & stale protection)
        is_firing = self.pinch_detector.update(
            has_left_hand=self.last_result.has_left_hand,
            thumb_tip=self.last_result.left_thumb_tip,
            index_tip=self.last_result.left_index_tip,
            confidence=self.last_result.left_confidence,
            hand_scale=self.last_result.left_scale,
            timestamp=self.last_result.timestamp,
        )
        cmd.fire = is_firing
        self.last_fire_state = is_firing

        return cmd


    def get_debug_info(self) -> Dict[str, Any]:
        """Telemetry and status for HUD overlays."""
        return {
            "camera_active": self.is_camera_active,
            "has_right_hand": self.last_result.has_right_hand,
            "right_confidence": round(self.last_result.right_confidence, 2),
            "right_x": round(self.last_result.right_x, 3),
            "right_y": round(self.last_result.right_y, 3),
            "has_left_hand": self.last_result.has_left_hand,
            "left_confidence": round(self.last_result.left_confidence, 2),
            "pinch_distance": round(self.pinch_detector.current_distance, 3),
            "is_pinching": self.pinch_detector.is_pinching,
        }
