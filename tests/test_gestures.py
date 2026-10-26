"""Tests for STARFALL Gesture Mapping and Pinch Detection."""

import pytest
from vision.pinch_detector import PinchDetector
from vision.gesture_mapper import GestureMapper, CalibrationOffsets


def test_pinch_detector_engage_and_release_hysteresis():
    detector = PinchDetector(
        engage_threshold=0.05,
        release_threshold=0.08,
        debounce_frames=2,
    )

    # Initially not pinching
    assert not detector.is_pinching

    # Distance at 0.04 (below engage threshold) frame 1
    # Needs debounce frames = 2
    res1 = detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.53, 0.5))
    assert res1 is False  # Frame 1 debounce

    # Frame 2 with same distance -> engage!
    res2 = detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.53, 0.5))
    assert res2 is True
    assert detector.is_pinching is True

    # Hovering distance 0.065 (between 0.05 and 0.08) -> hysteresis keeps it PINCHING
    res3 = detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.565, 0.5))
    assert res3 is True

    # Distance increases to 0.10 (above 0.08) frame 1
    res4 = detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.60, 0.5))
    assert res4 is True  # Frame 1 debounce for release

    # Frame 2 above release -> releases pinch!
    res5 = detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.60, 0.5))
    assert res5 is False
    assert detector.is_pinching is False


def test_pinch_detector_left_hand_lost():
    detector = PinchDetector(debounce_frames=1)
    detector.update(has_left_hand=True, thumb_tip=(0.5, 0.5), index_tip=(0.52, 0.5))
    assert detector.is_pinching is True

    # Hand is lost -> must immediately release
    detector.update(has_left_hand=False, thumb_tip=(0.0, 0.0), index_tip=(0.0, 0.0))
    assert detector.is_pinching is False


def test_gesture_mapper_bounds_and_deadzone():
    mapper = GestureMapper(
        screen_width=800.0,
        screen_height=700.0,
        smoothing_alpha=0.5,
        deadzone=0.05,
        calibration=CalibrationOffsets(min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0),
    )

    # Initial frame
    gx, gy = mapper.update(has_right_hand=True, raw_norm_x=0.5, raw_norm_y=0.5)
    assert gx == pytest.approx(400.0)
    assert gy is not None
    # Y is mapped to bottom 45% of screen
    assert 385.0 <= gy <= 670.0

    # Tiny micro-jitter within deadzone (0.05) should NOT change smoothed coordinate
    gx2, gy2 = mapper.update(has_right_hand=True, raw_norm_x=0.51, raw_norm_y=0.51)
    assert gx2 == pytest.approx(400.0)

    # Right hand lost returns None, None
    gx_lost, gy_lost = mapper.update(has_right_hand=False, raw_norm_x=0.5, raw_norm_y=0.5)
    assert gx_lost is None
    assert gy_lost is None
