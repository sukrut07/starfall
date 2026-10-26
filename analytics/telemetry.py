"""STARFALL Centralized Telemetry Event System."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryEvent:
    event_type: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)


class TelemetryCollector:
    """Collects and aggregates structured gameplay events."""

    def __init__(self, match_id: Optional[str] = None):
        self.match_id = match_id or f"match_{int(time.time())}"
        self.events: List[TelemetryEvent] = []
        self.start_time = time.time()

    def record(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.events.append(
            TelemetryEvent(
                event_type=event_type,
                timestamp=time.time() - self.start_time,
                data=data or {},
            )
        )

    def get_events_by_type(self, event_type: str) -> List[TelemetryEvent]:
        return [e for e in self.events if e.event_type == event_type]

    def get_events_for_wave(self, wave: int) -> List[TelemetryEvent]:
        return [e for e in self.events if e.data.get("current_wave") == wave or e.data.get("wave") == wave]

    def clear(self) -> None:
        self.events.clear()
        self.start_time = time.time()
