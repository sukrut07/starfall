"""STARFALL Camera Capture Service."""

from __future__ import annotations

import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np


class CameraService:
    """Thread-safe OpenCV camera capture with graceful fallback."""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.latest_frame: Optional[np.ndarray] = None
        self.is_available: bool = False
        self.last_capture_time: float = 0.0

    def start(self) -> bool:
        """Initialize camera and start capture loop in background."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap or not self.cap.isOpened():
                self.is_available = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.is_available = False
                return False

            self.is_available = True
            self.running = True
            with self.lock:
                self.latest_frame = frame
                self.last_capture_time = time.time()

            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True
        except Exception:
            self.is_available = False
            return False

    def _capture_loop(self) -> None:
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self.lock:
                    self.latest_frame = frame
                    self.last_capture_time = time.time()
            else:
                time.sleep(0.01)

    def get_latest_frame(self, mirror: bool = True) -> Optional[np.ndarray]:
        """Retrieve copy of the latest captured frame."""
        with self.lock:
            if self.latest_frame is None:
                return None
            frame = self.latest_frame.copy()

        if mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def stop(self) -> None:
        """Release camera resources cleanly."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_available = False
