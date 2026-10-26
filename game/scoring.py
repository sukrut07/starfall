"""STARFALL Authoritative Scoring System."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ScoreKeeper:
    """Authoritative score keeper shared across all game frontends."""
    total_score: int = 0
    enemies_destroyed: int = 0
    shots_fired: int = 0
    shots_hit: int = 0
    successful_dodges: int = 0
    waves_completed: int = 0
    lives_lost: int = 0
    bonus_targets: int = 0
    high_score: int = 0

    # Configurable point values
    enemy_kill_pts: int = 100
    tough_kill_pts: int = 500
    dodge_pts: int = 25
    wave_pts: int = 250
    bonus_pts: int = 150
    life_lost_penalty: int = 0

    def record_shot(self) -> None:
        self.shots_fired += 1

    def record_hit(self) -> None:
        self.shots_hit += 1

    def record_enemy_kill(self, is_tough: bool = False) -> int:
        self.enemies_destroyed += 1
        pts = self.tough_kill_pts if is_tough else self.enemy_kill_pts
        self.total_score += pts
        self._update_high_score()
        return pts

    def record_dodge(self) -> int:
        self.successful_dodges += 1
        self.total_score += self.dodge_pts
        self._update_high_score()
        return self.dodge_pts

    def record_wave_completed(self) -> int:
        self.waves_completed += 1
        self.total_score += self.wave_pts
        self._update_high_score()
        return self.wave_pts

    def record_bonus(self) -> int:
        self.bonus_targets += 1
        self.total_score += self.bonus_pts
        self._update_high_score()
        return self.bonus_pts

    def record_life_lost(self) -> None:
        self.lives_lost += 1
        if self.life_lost_penalty > 0:
            self.total_score = max(0, self.total_score - self.life_lost_penalty)

    @property
    def accuracy(self) -> float:
        """Returns accuracy as a ratio 0.0 - 1.0, safely handling 0 shots fired."""
        if self.shots_fired <= 0:
            return 0.0
        return min(1.0, self.shots_hit / self.shots_fired)

    def _update_high_score(self) -> None:
        if self.total_score > self.high_score:
            self.high_score = self.total_score

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_score": self.total_score,
            "enemies_destroyed": self.enemies_destroyed,
            "shots_fired": self.shots_fired,
            "shots_hit": self.shots_hit,
            "accuracy": round(self.accuracy, 4),
            "successful_dodges": self.successful_dodges,
            "waves_completed": self.waves_completed,
            "lives_lost": self.lives_lost,
            "bonus_targets": self.bonus_targets,
            "high_score": self.high_score,
        }

    def reset(self) -> None:
        current_high = self.high_score
        self.total_score = 0
        self.enemies_destroyed = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.successful_dodges = 0
        self.waves_completed = 0
        self.lives_lost = 0
        self.bonus_targets = 0
        self.high_score = current_high
