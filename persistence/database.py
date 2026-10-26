"""STARFALL SQLite Database Setup."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_score INTEGER NOT NULL,
    waves_completed INTEGER NOT NULL,
    survival_seconds REAL NOT NULL,
    accuracy REAL NOT NULL,
    dodges INTEGER NOT NULL,
    lives_lost INTEGER NOT NULL,
    report_json TEXT
);

CREATE TABLE IF NOT EXISTS strategy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    wave INTEGER NOT NULL,
    formation TEXT NOT NULL,
    obstacle TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    reason TEXT NOT NULL,
    evidence_json TEXT,
    outcome_label TEXT,
    was_applied INTEGER DEFAULT 1,
    is_fallback INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    playstyle_tag TEXT,
    aim_rating TEXT,
    evasion_rating TEXT,
    primary_bias TEXT,
    confidence REAL,
    profile_json TEXT
);
"""


def init_database(db_path: str = "starfall.db") -> sqlite3.Connection:
    """Initialize SQLite database and create tables if not existing."""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.executescript(SCHEMA_SQL)
    return conn
