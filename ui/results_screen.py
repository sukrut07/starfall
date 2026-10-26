"""STARFALL Post-Game Debrief Screen Formatter."""

from __future__ import annotations

from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from analytics.reports import PostGameReport


def print_rich_report(report_dict: Dict[str, Any], console: Optional[Console] = None) -> None:
    """Display comprehensive post-game debrief formatted with Rich."""
    console = console or Console()

    console.print("\n")
    console.print(Panel(
        f"[bold cyan]★ STARFALL POST-GAME FLIGHT DEBRIEF ★[/bold cyan]\n"
        f"[dim]Match ID: {report_dict.get('match_id', 'unknown')}[/dim]",
        border_style="cyan",
        expand=False,
    ))

    # 1. Match Summary Table
    summary_table = Table(title="[bold yellow]1. MATCH PERFORMANCE SUMMARY[/bold yellow]", border_style="yellow")
    summary_table.add_column("Metric", style="white", justify="left")
    summary_table.add_column("Value", style="bold green", justify="right")
    summary_table.add_column("Assessment", style="dim", justify="left")

    score = report_dict.get("total_score", 0)
    waves = report_dict.get("waves_completed", 0)
    dur = report_dict.get("survival_seconds", 0.0)
    acc = report_dict.get("accuracy", 0.0)
    dodges = report_dict.get("dodges", 0)
    lives_lost = report_dict.get("lives_lost", 0)
    kills = report_dict.get("enemies_destroyed", 0)

    summary_table.add_row("Total Score", f"{score:,}", "High combat effectiveness" if score > 1000 else "Standard sortie")
    summary_table.add_row("Waves Completed", str(waves), "Multi-wave escalation reached" if waves >= 3 else "Initial engagement")
    summary_table.add_row("Survival Duration", f"{dur:.1f}s", "Sustained dogfight" if dur > 60 else "Quick clash")
    summary_table.add_row("Firing Accuracy", f"{acc:.1%}", "Sharpshooter grade" if acc >= 0.4 else ("Moderate" if acc >= 0.25 else "Suppressive fire"))
    summary_table.add_row("Successful Dodges", str(dodges), f"{dodges * 25} tactical bonus points")
    summary_table.add_row("Enemies Destroyed", str(kills), f"{kills * 100} kill points")
    summary_table.add_row("Lives Lost", str(lives_lost), "Flawless defense" if lives_lost == 0 else f"{lives_lost} hull breaches")

    console.print(summary_table)

    # 2. Player Profiling & Spatial Metrics
    prof = report_dict.get("profile", {})
    metrics = report_dict.get("metrics", {})
    profile_panel_text = (
        f"[bold]Playstyle Designation:[/bold] [cyan]{prof.get('playstyle_tag', 'Pilot')}[/cyan]\n"
        f"[bold]Aim Rating:[/bold] {prof.get('aim_rating', 'Standard')} | [bold]Evasion Rating:[/bold] {prof.get('evasion_rating', 'Standard')}\n"
        f"[bold]Spatial Preference:[/bold] {prof.get('primary_bias', 'Balanced')}\n"
        f"[dim]Left Lane: {metrics.get('left_zone_ratio', 0):.0%} | Center: {metrics.get('center_zone_ratio', 0):.0%} | Right Lane: {metrics.get('right_zone_ratio', 0):.0%}[/dim]\n"
        f"[dim]Stationary Camping Ratio: {metrics.get('camping_ratio', 0):.0%} | Average Speed: {metrics.get('average_speed', 0):.1f} px/s[/dim]\n"
        f"[bold yellow]Observed Tactical Weakness:[/bold yellow]\n  {prof.get('observed_weakness', 'None logged.')}\n"
        f"[dim]Confidence: {prof.get('confidence', 0):.0%} (Evidence: {', '.join(prof.get('evidence', []))})[/dim]"
    )
    console.print("\n")
    console.print(Panel(profile_panel_text, title="[bold magenta]2. BEHAVIORAL PROFILE & SPATIAL AUDIT[/bold magenta]", border_style="magenta"))

    # 3. AI Adaptation History
    adaptations = report_dict.get("adaptation_history", [])
    if adaptations:
        adapt_table = Table(title="[bold red]3. ENEMY ADAPTATION AUDIT (GEMMA 4 & LANGGRAPH)[/bold red]", border_style="red")
        adapt_table.add_column("Wave", justify="center")
        adapt_table.add_column("Formation & Obstacle", style="cyan")
        adapt_table.add_column("AI Tactical Reasoning", style="white")
        adapt_table.add_column("Outcome", justify="center")

        for ad in adaptations:
            w = str(ad.get("wave", "?"))
            form = f"{ad.get('formation', '').upper()} + {ad.get('obstacle', '')}"
            reason = ad.get("reason", "")
            lbl = ad.get("outcome_label", "inconclusive").upper()
            lbl_color = "green" if lbl == "HELPFUL" else ("red" if lbl == "HARMFUL" else "yellow")
            adapt_table.add_row(w, form, reason, f"[{lbl_color}]{lbl}[/{lbl_color}]")

        console.print("\n")
        console.print(adapt_table)

    # 4. Next-Run Mission
    mission = report_dict.get("next_mission", {})
    if mission:
        mission_text = (
            f"[bold green]MISSION OBJECTIVE: {mission.get('title', 'Combat Training').upper()}[/bold green]\n\n"
            f"[bold]Target:[/bold] {mission.get('measurement_description', '')}\n"
            f"[dim]Current Baseline: {mission.get('current_value')} | Target Threshold: {mission.get('target_value')}[/dim]\n\n"
            f"[bold]Flight Instructor Rationale:[/bold]\n{mission.get('rationale', '')}"
        )
        console.print("\n")
        console.print(Panel(mission_text, title="[bold green]4. NEXT-RUN TRAINING MISSION[/bold green]", border_style="green"))

    console.print("\n")
