"""STARFALL Standalone Camera and Gesture Visualizer."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
from vision.camera import CameraService
from vision.hand_tracker import HandTracker
from vision.pinch_detector import PinchDetector
from vision.gesture_mapper import GestureMapper


def run_camera_test(camera_index: int = 0) -> None:
    print(f"Opening camera index {camera_index} for gesture diagnostics...")
    cam = CameraService(camera_index=camera_index)
    if not cam.start():
        print(f"Error: Unable to open camera {camera_index}.")
        return

    tracker = HandTracker()
    pinch = PinchDetector()
    mapper = GestureMapper()

    print("Camera running. Press 'q' or ESC in the window to quit.")
    fps_start = time.time()
    frames = 0
    fps = 0.0

    try:
        while True:
            frame = cam.get_latest_frame(mirror=True)
            if frame is None:
                time.sleep(0.01)
                continue

            frames += 1
            if time.time() - fps_start >= 1.0:
                fps = frames / (time.time() - fps_start)
                frames = 0
                fps_start = time.time()

            result = tracker.process_frame(frame, mirrored=False)
            h, w = frame.shape[:2]

            # Draw landmarks
            for hand in result.all_hands:
                label = hand["label"]
                pts = hand["landmarks"]
                color = (0, 255, 255) if label == "Right" else (255, 120, 255)

                for px, py in pts:
                    cv2.circle(frame, (int(px * w), int(py * h)), 4, color, -1)

                wrist = pts[0]
                cv2.putText(
                    frame,
                    f"{label} ({hand['score']:.2f})",
                    (int(wrist[0] * w) - 20, int(wrist[1] * h) - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

            # Check right hand movement
            if result.has_right_hand:
                gx, gy = mapper.update(True, result.right_x, result.right_y, result.right_confidence)
                cv2.circle(frame, (int(result.right_x * w), int(result.right_y * h)), 8, (0, 255, 0), 2)
                cv2.putText(frame, "RIGHT: MOVE SHIP", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Check left hand pinch
            is_firing = pinch.update(
                has_left_hand=result.has_left_hand,
                thumb_tip=result.left_thumb_tip,
                index_tip=result.left_index_tip,
                confidence=result.left_confidence,
            )
            dist_text = f"Pinch Dist: {pinch.current_distance:.3f}"
            pinch_status = "PINCH: FIRING!" if is_firing else "Left: Open"
            p_color = (0, 255, 0) if is_firing else (0, 165, 255)
            cv2.putText(frame, f"{pinch_status} ({dist_text})", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, p_color, 2)

            # FPS
            cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow("STARFALL - Hand Gesture Diagnostic", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

    finally:
        cam.stop()
        tracker.close()
        cv2.destroyAllWindows()
        print("Camera diagnostic exited cleanly.")


if __name__ == "__main__":
    run_camera_test()
