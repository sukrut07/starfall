"""STARFALL MediaPipe Hand Tracking Module."""

from __future__ import annotations

import math
import os
import time
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
    right_scale: float = 0.20
    has_left_hand: bool = False
    left_confidence: float = 0.0
    left_thumb_tip: Tuple[float, float] = (0.0, 0.0)
    left_index_tip: Tuple[float, float] = (0.0, 0.0)
    left_scale: float = 0.20
    timestamp: float = 0.0
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

        # Process role assignment:
        # If single hand detected: that hand steers AND pinches to fire (supports single-hand play)
        if len(result.all_hands) == 1:
            hand = result.all_hands[0]
            pts = hand["landmarks"]
            score = hand["score"]
            palm_scale = math.hypot(pts[0][0] - pts[9][0], pts[0][1] - pts[9][1]) if len(pts) > 9 else 0.20

            wrist = pts[0]
            middle_mcp = pts[9]
            index_tip = pts[8]
            thumb_tip = pts[4]

            # Primary steering
            result.has_right_hand = True
            result.right_confidence = score
            result.right_scale = palm_scale
            result.right_x = (index_tip[0] * 0.6) + (((wrist[0] + middle_mcp[0]) * 0.5) * 0.4)
            result.right_y = (index_tip[1] * 0.6) + (((wrist[1] + middle_mcp[1]) * 0.5) * 0.4)

            # Single-hand pinch firing
            result.has_left_hand = True
            result.left_confidence = score
            result.left_scale = palm_scale
            result.left_thumb_tip = thumb_tip
            result.left_index_tip = index_tip

        elif len(result.all_hands) >= 2:
            # Dual hand mode: sort by mirrored x (horizontal screen position)
            # Higher x in mirrored frame = User's Right Hand (Steering)
            # Lower x in mirrored frame = User's Left Hand (Pinch Trigger)
            sorted_by_x = sorted(result.all_hands, key=lambda h: h["landmarks"][0][0])
            left_hand = sorted_by_x[0]   # Lower mirrored X (screen left)
            right_hand = sorted_by_x[1]  # Higher mirrored X (screen right)

            # Right hand (steering)
            r_pts = right_hand["landmarks"]
            r_scale = math.hypot(r_pts[0][0] - r_pts[9][0], r_pts[0][1] - r_pts[9][1]) if len(r_pts) > 9 else 0.20
            r_wrist = r_pts[0]
            r_mid = r_pts[9]
            r_idx = r_pts[8]

            result.has_right_hand = True
            result.right_confidence = right_hand["score"]
            result.right_scale = r_scale
            result.right_x = (r_idx[0] * 0.6) + (((r_wrist[0] + r_mid[0]) * 0.5) * 0.4)
            result.right_y = (r_idx[1] * 0.6) + (((r_wrist[1] + r_mid[1]) * 0.5) * 0.4)

            # Left hand (weapon trigger)
            l_pts = left_hand["landmarks"]
            l_scale = math.hypot(l_pts[0][0] - l_pts[9][0], l_pts[0][1] - l_pts[9][1]) if len(l_pts) > 9 else 0.20
            result.has_left_hand = True
            result.left_confidence = left_hand["score"]
            result.left_scale = l_scale
            result.left_thumb_tip = l_pts[4]
            result.left_index_tip = l_pts[8]

        result.timestamp = time.time()
        return result

    def close(self) -> None:
        if self.detector:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None
