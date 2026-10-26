"""STARFALL Database Repositories."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from analytics.reports import PostGameReport
from analytics.strategy_evaluation import StrategyOutcome
from analytics.player_profile import PlayerProfile


class MatchRepository:
    """Repository for storing and retrieving matches and strategy audits."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_match(self, report: PostGameReport) -> None:
        query = """
        INSERT OR REPLACE INTO matches (
            match_id, total_score, waves_completed, survival_seconds,
            accuracy, dodges, lives_lost, report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        report_json = json.dumps(report.to_dict())
        with self.conn:
            self.conn.execute(
                query,
                (
                    report.match_id,
                    report.total_score,
                    report.waves_completed,
                    report.survival_seconds,
                    report.accuracy,
                    report.dodges,
                    report.lives_lost,
                    report_json,
                ),
            )

    def save_strategy_outcome(self, match_id: str, outcome: StrategyOutcome) -> None:
        query = """
        INSERT INTO strategy_logs (
            match_id, wave, formation, obstacle, difficulty,
            reason, evidence_json, outcome_label, was_applied, is_fallback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.conn:
            self.conn.execute(
                query,
                (
                    match_id,
                    outcome.wave,
                    outcome.formation,
                    outcome.obstacle,
                    outcome.difficulty,
                    outcome.reason,
                    json.dumps(outcome.evidence_cited),
                    outcome.outcome_label,
                    1 if outcome.was_applied else 0,
                    1 if outcome.is_fallback else 0,
                ),
            )

    def save_player_profile(self, profile: PlayerProfile) -> None:
        query = """
        INSERT INTO player_profiles (
            playstyle_tag, aim_rating, evasion_rating, primary_bias,
            confidence, profile_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.conn:
            self.conn.execute(
                query,
                (
                    profile.playstyle_tag,
                    profile.aim_rating,
                    profile.evasion_rating,
                    profile.primary_bias,
                    profile.confidence,
                    json.dumps(profile.to_dict()),
                ),
            )

    def get_recent_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        query = """
        SELECT match_id, started_at, total_score, waves_completed,
               survival_seconds, accuracy, dodges, lives_lost
        FROM matches
        ORDER BY started_at DESC
        LIMIT ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_last_match_report(self) -> Optional[Dict[str, Any]]:
        query = "SELECT report_json FROM matches ORDER BY started_at DESC LIMIT 1"
        cursor = self.conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if row and row["report_json"]:
            try:
                return json.loads(row["report_json"])
            except Exception:
                return None
        return None
