"""STARFALL Base Renderer Interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np

from game.state import GameStateSnapshot


class BaseRenderer(ABC):
    """Abstract renderer interface for Starfall game simulation snapshots."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize renderer resources (window, terminal, etc.)."""
        pass

    @abstractmethod
    def render(
        self,
        snapshot: GameStateSnapshot,
        ai_status: str = "Ready",
        webcam_frame: Optional[np.ndarray] = None,
        gesture_debug: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Render a single frame of the game."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release display and graphics resources cleanly."""
        pass
