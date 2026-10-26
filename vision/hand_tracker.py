"""STARFALL MediaPipe Hand Tracking Module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


@dataclass
class HandTrackingResult:
    """Processed hand tracking data for spaceship control."""
    has_right_hand: bool = False
    right_confidence: float = 0.0
    right_x: float = 0.5  # Normalized 0.0 - 1.0 (mirrored for natural interaction)
    right_y: float = 0.5  # Normalized 0.0 - 1.0
    has_left_hand: bool = False
    left_confidence: float = 0.0
    left_thumb_tip: Tuple[float, float] = (0.0, 0.0)
    left_index_tip: Tuple[float, float] = (0.0, 0.0)
    all_hands: List[Dict[str, Any]] = field(default_factory=list)


class HandTracker:
    """Extracts two-hand landmarks and handedness using MediaPipe Hand Landmarker."""

    def __init__(
        self,
        model_path: str = "assets/models/hand_landmarker.task",
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.model_path = model_path
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.detector: Optional[vision.HandLandmarker] = None
        self._init_detector()

    def _init_detector(self) -> None:
        p = Path(self.model_path)
        if not p.is_absolute():
            # Resolve relative to repo root
            p = Path(__file__).parent.parent / self.model_path

        if not p.exists():
            return

        base_options = mp_python.BaseOptions(model_asset_path=str(p))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            running_mode=vision.RunningMode.IMAGE,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: cv2.typing.MatLike, mirrored: bool = True) -> HandTrackingResult:
        """
        Process a BGR frame (e.g. from camera).
        If mirrored is True, coordinates are flipped horizontally (1.0 - x)
        to match a mirror view for natural player movement.
        """
        result = HandTrackingResult()
        if self.detector is None or frame_bgr is None:
            return result

        # Convert to RGB mp.Image
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        try:
            detection = self.detector.detect(mp_image)
        except Exception:
            return result

        if not detection.hand_landmarks or not detection.handedness:
            return result

        for landmarks, handedness in zip(detection.hand_landmarks, detection.handedness):
            label = handedness[0].category_name  # "Left" or "Right"
            score = handedness[0].score

            # Compute mirrored or un-mirrored landmark list
            pts = []
            for lm in landmarks:
                x = (1.0 - lm.x) if mirrored else lm.x
                y = lm.y
                pts.append((x, y))

            result.all_hands.append({
                "label": label,
                "score": score,
                "landmarks": pts,
            })

            # Right hand controls spaceship movement
            if label == "Right":
                result.has_right_hand = True
                result.right_confidence = score
                # Palm center estimated between wrist (0) and middle MCP (9)
                wrist = pts[0]
                middle_mcp = pts[9]
                index_tip = pts[8]
                # We blend index tip and palm center for intuitive aiming
                result.right_x = (index_tip[0] * 0.6) + (((wrist[0] + middle_mcp[0]) * 0.5) * 0.4)
                result.right_y = (index_tip[1] * 0.6) + (((wrist[1] + middle_mcp[1]) * 0.5) * 0.4)

            # Left hand controls pinch firing
            elif label == "Left":
                result.has_left_hand = True
                result.left_confidence = score
                result.left_thumb_tip = pts[4]
                result.left_index_tip = pts[8]

        return result

    def close(self) -> None:
        if self.detector:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None
