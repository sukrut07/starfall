"""STARFALL Player Behavior Profiling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any
from analytics.metrics import AggregatedMetrics


@dataclass
class PlayerProfile:
    playstyle_tag: str = "Balanced Explorer"
    aim_rating: str = "Uncalibrated"
    evasion_rating: str = "Uncalibrated"
    primary_bias: str = "None"
    observed_weakness: str = "Insufficient observations to determine weakness."
    confidence: float = 0.3
    is_sufficient_data: bool = False
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "playstyle_tag": self.playstyle_tag,
            "aim_rating": self.aim_rating,
            "evasion_rating": self.evasion_rating,
            "primary_bias": self.primary_bias,
            "observed_weakness": self.observed_weakness,
            "confidence": round(self.confidence, 2),
            "is_sufficient_data": self.is_sufficient_data,
            "evidence": self.evidence,
        }


def build_profile(metrics: AggregatedMetrics, min_observations: int = 10) -> PlayerProfile:
    """Build an evidence-based player profile distinguishing measurement from hypothesis."""
    profile = PlayerProfile()
    evidence: List[str] = []

    # Check data sufficiency
    total_samples = metrics.position_samples
    total_shots = metrics.shots_fired

    if total_samples < min_observations or total_shots < 4:
        profile.is_sufficient_data = False
        profile.confidence = 0.25
        profile.observed_weakness = "Baseline calibration in progress. More gameplay telemetry required."
        profile.evidence = [f"position_samples={total_samples}", f"shots={total_shots}"]
        return profile

    profile.is_sufficient_data = True
    confidence = min(0.95, 0.45 + (min(50, total_samples) * 0.008) + (min(40, total_shots) * 0.006))
    profile.confidence = confidence

    # Aim Rating
    if metrics.accuracy >= 0.42:
        profile.aim_rating = "Sharpshooter"
        evidence.append(f"accuracy={metrics.accuracy:.2f} (high)")
    elif metrics.accuracy >= 0.22:
        profile.aim_rating = "Deliberate"
        evidence.append(f"accuracy={metrics.accuracy:.2f} (moderate)")
    else:
        profile.aim_rating = "Rapid Spray"
        evidence.append(f"accuracy={metrics.accuracy:.2f} (low)")

    # Evasion Rating
    if metrics.threats_encountered >= 2:
        if metrics.dodge_rate >= 0.65:
            profile.evasion_rating = "Acrobatic Dodger"
            evidence.append(f"dodge_rate={metrics.dodge_rate:.2f} (high)")
        elif metrics.dodge_rate >= 0.35:
            profile.evasion_rating = "Moderate Mobility"
            evidence.append(f"dodge_rate={metrics.dodge_rate:.2f} (fair)")
        else:
            profile.evasion_rating = "Target Susceptible"
            evidence.append(f"dodge_rate={metrics.dodge_rate:.2f} (low)")
    else:
        profile.evasion_rating = "Low Threat Exposure"

    # Spatial / Movement Style
    if metrics.camping_ratio >= 0.55:
        profile.playstyle_tag = "Stationary Anchor"
        profile.primary_bias = "Center Camping" if metrics.center_zone_ratio > 0.5 else ("Left Camping" if metrics.left_zone_ratio > 0.4 else "Right Camping")
        profile.observed_weakness = f"High stationary ratio ({metrics.camping_ratio:.1%}). Susceptible to converging or flanking attacks."
        evidence.append(f"camping_ratio={metrics.camping_ratio:.2f}")
    elif metrics.left_zone_ratio >= 0.58:
        profile.playstyle_tag = "Port-Wing Specialist"
        profile.primary_bias = "Left Lane Bias"
        profile.observed_weakness = f"Heavy left-side occupancy ({metrics.left_zone_ratio:.1%}). Vulnerable to right-side sweeps that force lateral movement."
        evidence.append(f"left_zone_ratio={metrics.left_zone_ratio:.2f}")
    elif metrics.right_zone_ratio >= 0.58:
        profile.playstyle_tag = "Starboard Cruiser"
        profile.primary_bias = "Right Lane Bias"
        profile.observed_weakness = f"Heavy right-side occupancy ({metrics.right_zone_ratio:.1%}). Vulnerable to left-side pressure."
        evidence.append(f"right_zone_ratio={metrics.right_zone_ratio:.2f}")
    elif metrics.average_speed >= 280.0:
        profile.playstyle_tag = "High-Speed Interceptor"
        profile.primary_bias = "Broad Sweeper"
        profile.observed_weakness = "High traversal speed can cause erratic aiming or accidental collisions with projectiles."
        evidence.append(f"avg_speed={metrics.average_speed:.1f}")
    else:
        profile.playstyle_tag = "Balanced Tactical Pilot"
        profile.primary_bias = "Balanced Lanes"
        profile.observed_weakness = "Well-balanced positioning. Requires escalating projectile speed or multi-lane threats to breach defense."
        evidence.append("zone_distribution=even")

    profile.evidence = evidence
    return profile
