"""STARFALL Interactive Terminal Main Menu."""

from __future__ import annotations

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt


def display_main_menu(console: Optional[Console] = None) -> str:
    """Render interactive main menu and return selected choice."""
    console = console or Console()
    console.print("\n")

    banner = (
        "[bold cyan]  ███████╗████████╗ █████╗ ██████╗ ███████╗ █████╗ ██╗     ██╗     [/bold cyan]\n"
        "[bold cyan]  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║     ██║     [/bold cyan]\n"
        "[bold cyan]  ███████╗   ██║   ███████║██████╔╝█████╗  ███████║██║     ██║     [/bold cyan]\n"
        "[bold cyan]  ╚════██║   ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║██║     ██║     [/bold cyan]\n"
        "[bold cyan]  ███████║   ██║   ██║  ██║██║  ██║██║     ██║  ██║███████╗███████╗[/bold cyan]\n"
        "[bold cyan]  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝[/bold cyan]\n"
        "           [bold yellow]ADAPTIVE AI ARCADE SHOOTER  |  GEMMA 4 & LANGGRAPH[/bold yellow]"
    )
    console.print(Panel(banner, border_style="cyan", expand=False))

    menu_table = Table(title="[bold green]MISSION DISPATCH MENU[/bold green]", border_style="green", expand=False)
    menu_table.add_column("No.", style="bold yellow", justify="center")
    menu_table.add_column("Deployment Mode", style="bold white")
    menu_table.add_column("Description", style="dim")

    menu_table.add_row("1", "Play Terminal Shooter (Keyboard)", "Fast ASCII arcade with WASD / Arrow keys")
    menu_table.add_row("2", "Play Pygame Arcade (Keyboard)", "Visual 60 FPS Galaga-style space shooter")
    menu_table.add_row("3", "Play Pygame Arcade (Webcam Gestures)", "Right-hand flight control + Left-hand pinch shooting")
    menu_table.add_row("4", "Play Terminal Shooter (Webcam Gestures)", "ASCII gameplay powered by live hand tracking")
    menu_table.add_row("5", "Webcam & Gesture Calibration Test", "Live camera test, hand landmarks & pinch telemetry")
    menu_table.add_row("6", "Ollama & Gemma 4 Model Diagnostics", "Connection check, latency benchmark & test inference")
    menu_table.add_row("7", "Match History & Tactical Audit", "View past runs, AI strategies, and flight reports")
    menu_table.add_row("8", "Configuration & Settings", "Inspect game constants, timeouts, and thresholds")
    menu_table.add_row("9", "Textmode Web Companion Display", "Browser tactical console inspired by extension.textmode.art")
    menu_table.add_row("10", "Exit Flight Terminal", "Return to shell")

    console.print(menu_table)
    choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "q"], default="1")
    return choice
