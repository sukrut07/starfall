"""STARFALL Settings Menu."""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config.loader import Settings, load_settings


def display_settings_summary(settings: Settings, console: Optional[Console] = None) -> None:
    """Print clean settings overview."""
    console = console or Console()
    table = Table(title="[bold cyan]STARFALL Configuration Settings[/bold cyan]", border_style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Setting", style="white")
    table.add_column("Current Value", style="bold green")

    # Display
    table.add_row("Display", "Pygame Resolution", f"{settings.display.pygame_width}x{settings.display.pygame_height} @ {settings.display.target_fps} FPS")
    table.add_row("Display", "Terminal Size", f"{settings.display.terminal_width}x{settings.display.terminal_height}")
    
    # Controls
    table.add_row("Controls", "Default Mode", settings.controls.default_mode)
    table.add_row("Controls", "Fire Cooldown", f"{settings.controls.fire_cooldown}s")

    # Vision
    table.add_row("Vision", "Camera Index", str(settings.vision.camera_index))
    table.add_row("Vision", "Pinch Engage / Release", f"{settings.vision.pinch_engage_thresh} / {settings.vision.pinch_release_thresh}")
    table.add_row("Vision", "Smoothing Alpha", str(settings.vision.smoothing_alpha))

    # AI
    table.add_row("AI Director", "Ollama Endpoint", settings.ai.ollama_endpoint)
    table.add_row("AI Director", "Primary Model", settings.ai.primary_model)
    table.add_row("AI Director", "Alternative Model", settings.ai.alternative_model)
    table.add_row("AI Director", "Timeout", f"{settings.ai.timeout_seconds}s")
    table.add_row("AI Director", "Allowed Formations", f"{len(settings.ai.allowed_formations)} registered")

    # Storage
    table.add_row("Storage", "SQLite DB", settings.app.database_path)

    console.print(table)
