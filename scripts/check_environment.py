"""STARFALL Environment Diagnostic Script."""

from __future__ import annotations

import sys
import shutil
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.loader import load_settings
from ai.ollama_client import OllamaClientWrapper
from vision.camera import CameraService


def check_all() -> bool:
    console = Console()
    console.print(Panel("[bold cyan]★ STARFALL SYSTEM ENVIRONMENT AUDIT ★[/bold cyan]", border_style="cyan"))

    table = Table(border_style="white")
    table.add_column("Subsystem", style="yellow")
    table.add_column("Component", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    all_ok = True

    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        table.add_row("Core", "Python Version", "[green]PASS[/green]", f"Python {py_ver}")
    else:
        table.add_row("Core", "Python Version", "[red]FAIL[/red]", f"Python {py_ver} (3.11+ required)")
        all_ok = False

    # 2. Pygame
    try:
        import pygame
        table.add_row("Display", "Pygame", "[green]PASS[/green]", f"Pygame {pygame.__version__}")
    except ImportError:
        table.add_row("Display", "Pygame", "[red]FAIL[/red]", "Pygame not installed")
        all_ok = False

    # 3. OpenCV
    try:
        import cv2
        table.add_row("Vision", "OpenCV", "[green]PASS[/green]", f"OpenCV {cv2.__version__}")
    except ImportError:
        table.add_row("Vision", "OpenCV", "[red]FAIL[/red]", "OpenCV not installed")
        all_ok = False

    # 4. MediaPipe
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from pathlib import Path
        model_exists = Path("assets/models/hand_landmarker.task").exists()
        if model_exists:
            table.add_row("Vision", "MediaPipe Landmarker", "[green]PASS[/green]", f"MediaPipe {mp.__version__} (Model present)")
        else:
            table.add_row("Vision", "MediaPipe Landmarker", "[yellow]WARN[/yellow]", "Model missing in assets/models/")
    except Exception as e:
        table.add_row("Vision", "MediaPipe Landmarker", "[yellow]WARN[/yellow]", f"MediaPipe error: {str(e)}")

    # 5. Camera hardware
    cam = CameraService(camera_index=0)
    if cam.start():
        table.add_row("Vision", "Webcam Hardware", "[green]PASS[/green]", "Camera index 0 opened successfully")
        cam.stop()
    else:
        table.add_row("Vision", "Webcam Hardware", "[yellow]OPTIONAL[/yellow]", "Camera 0 not detected (keyboard mode active)")

    # 6. Ollama CLI & Service
    ollama_cli = shutil.which("ollama")
    if ollama_cli:
        table.add_row("AI", "Ollama CLI", "[green]PASS[/green]", f"Installed at {ollama_cli}")
    else:
        table.add_row("AI", "Ollama CLI", "[yellow]OPTIONAL[/yellow]", "CLI not in PATH")

    settings = load_settings()
    ollama_wrapper = OllamaClientWrapper(endpoint=settings.ai.ollama_endpoint, timeout_seconds=5.0)
    is_connected, msg, models = ollama_wrapper.check_connection()

    if is_connected:
        table.add_row("AI", "Ollama Service", "[green]PASS[/green]", f"Online at {settings.ai.ollama_endpoint}")
        model_name = settings.ai.primary_model
        if any(model_name in m for m in models):
            table.add_row("AI", f"Model ({model_name})", "[green]PASS[/green]", f"Found locally in Ollama ({len(models)} models present)")
        else:
            table.add_row("AI", f"Model ({model_name})", "[yellow]PULL REQUIRED[/yellow]", f"Run: ollama pull {model_name}")
    else:
        table.add_row("AI", "Ollama Service", "[yellow]OFFLINE[/yellow]", "Service offline (deterministic fallback active)")

    # 7. SQLite
    try:
        from persistence.database import init_database
        conn = init_database("starfall.db")
        conn.close()
        table.add_row("Storage", "SQLite Database", "[green]PASS[/green]", "starfall.db initialized")
    except Exception as e:
        table.add_row("Storage", "SQLite Database", "[red]FAIL[/red]", str(e))
        all_ok = False

    console.print(table)
    return all_ok


if __name__ == "__main__":
    check_all()
