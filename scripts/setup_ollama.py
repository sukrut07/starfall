"""STARFALL Ollama Setup and Verification Utility."""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.loader import load_settings
from ai.ollama_client import OllamaClientWrapper
from ai.model_registry import list_supported_models


def setup_and_diagnose() -> None:
    console = Console()
    console.print(Panel(
        "[bold cyan]★ STARFALL OLLAMA & GEMMA 4 SETUP WIZARD ★[/bold cyan]\n"
        "[dim]Verifies local inference, schema-constrained output, and offline fallbacks.[/dim]",
        border_style="cyan",
    ))

    # 1. Check CLI
    cli_path = shutil.which("ollama")
    if cli_path:
        console.print(f"[bold green]✔[/bold green] Ollama CLI located at: [dim]{cli_path}[/dim]")
    else:
        console.print("[bold yellow]⚠[/bold yellow] Ollama CLI not found in PATH. Install from [underline]https://ollama.com[/underline] if not already installed.")

    # 2. Check Service
    settings = load_settings()
    endpoint = settings.ai.ollama_endpoint
    target_model = settings.ai.primary_model
    alt_model = settings.ai.alternative_model

    client = OllamaClientWrapper(endpoint=endpoint, timeout_seconds=settings.ai.timeout_seconds)
    is_connected, msg, models = client.check_connection()

    if not is_connected:
        console.print(f"[bold red]✖[/bold red] Could not connect to Ollama at [bold]{endpoint}[/bold].")
        console.print(f"   [dim]{msg}[/dim]")
        console.print("\n[bold yellow]Offline Fallback Guarantee:[/bold yellow]")
        console.print("   STARFALL will automatically run using its deterministic tactical director.")
        console.print("   To enable Gemma 4, start Ollama with: [bold cyan]ollama serve[/bold cyan]")
        return

    console.print(f"[bold green]✔[/bold green] Ollama service connected at: [bold]{endpoint}[/bold]")

    # 3. List Local Models
    model_table = Table(title="[bold yellow]Local Ollama Models[/bold yellow]", border_style="yellow")
    model_table.add_column("Model Name", style="white")
    model_table.add_column("Status", justify="center")

    has_target = False
    for m in models:
        is_primary = (target_model in m)
        if is_primary:
            has_target = True
        status = "[bold green]PRIMARY CONFIGURED[/bold green]" if is_primary else ("ALTERNATIVE" if alt_model in m else "Available")
        model_table.add_row(m, status)

    if not models:
        model_table.add_row("[italic]No models installed[/italic]", "[yellow]EMPTY[/yellow]")

    console.print(model_table)

    # 4. Check Configured Target Model
    if has_target:
        console.print(f"\n[bold green]✔[/bold green] Primary model [bold cyan]{target_model}[/bold cyan] is installed and ready.")
        console.print("Performing quick schema-constrained test inference...")

        t_start = time.perf_counter()
        test_prompt = "Return a JSON object with a formation and a reason for selecting it in a space shooter."
        ok, res, latency_ms, err = client.generate_strategy(test_prompt, model_name=target_model)
        elapsed = time.perf_counter() - t_start

        if ok and res:
            console.print(f"[bold green]✔[/bold green] Test inference succeeded in [bold]{latency_ms:.1f}ms[/bold]!")
            console.print(f"   [dim]Selected Formation:[/dim] [cyan]{res.get('formation')}[/cyan]")
            console.print(f"   [dim]Tactical Reason:[/dim] {res.get('reason')}")
        else:
            console.print(f"[bold yellow]⚠[/bold yellow] Test inference returned error: {err}")
            console.print("   Deterministic fallback will be used if errors persist during gameplay.")
    else:
        console.print(f"\n[bold yellow]⚠[/bold yellow] Model [bold cyan]{target_model}[/bold cyan] is not yet downloaded.")
        console.print(Panel(
            f"[bold]To download the configured Gemma 4 model, run this command in your terminal:[/bold]\n\n"
            f"   [bold green]ollama pull {target_model}[/bold green]\n\n"
            f"[dim]Alternative lightweight model: ollama pull gemma4:e2b\n"
            f"Or for higher reasoning capacity: ollama pull gemma4:e4b[/dim]",
            title="[yellow]Model Download Instructions[/yellow]",
            border_style="yellow",
        ))

    # 5. Model Registry Summary
    console.print("\n[bold]Supported Model Registry & Licensing:[/bold]")
    for mod in list_supported_models():
        console.print(f" • [bold]{mod.display_name}[/bold] ({mod.identifier}) - {mod.license_type}")
        console.print(f"   [dim]{mod.description}[/dim]")


if __name__ == "__main__":
    setup_and_diagnose()
