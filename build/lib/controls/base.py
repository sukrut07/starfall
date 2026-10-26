"""STARFALL Base Input Controller Interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from game.state import InputCommand


class BaseController(ABC):
    """Abstract controller producing normalized InputCommand."""

    @abstractmethod
    def poll(self) -> InputCommand:
        """Poll the current input state and return an InputCommand."""
        pass

    def start(self) -> bool:
        """Initialize controller resources if needed."""
        return True

    def stop(self) -> None:
        """Release controller resources cleanly."""
        pass
