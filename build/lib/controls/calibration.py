"""STARFALL Calibration Utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from vision.gesture_mapper import CalibrationOffsets


CALIBRATION_FILE = Path("config/calibration.json")


def load_calibration() -> CalibrationOffsets:
    """Load saved calibration offsets from file or return defaults."""
    if CALIBRATION_FILE.exists():
        try:
            with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CalibrationOffsets(**data)
        except Exception:
            pass
    return CalibrationOffsets()


def save_calibration(offsets: CalibrationOffsets) -> bool:
    """Save calibration offsets to file."""
    try:
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "min_x": offsets.min_x,
                "max_x": offsets.max_x,
                "min_y": offsets.min_y,
                "max_y": offsets.max_y,
            }, f, indent=2)
        return True
    except Exception:
        return False
