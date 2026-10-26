"""STARFALL: Adaptive AI Arcade Shooter.

Main entry point supporting Terminal & Pygame modes, Keyboard & Gesture controls,
local Gemma 4 reasoning via Ollama, and LangGraph tactical orchestration.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from typing import Any, Optional

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_game(
    renderer_type: str = "pygame",
    control_type: str = "keyboard",
    model_name: Optional[str] = None,
    settings_override: Optional[Any] = None,
) -> None:
    """Launch the main game loop with chosen renderer and control interfaces."""
    from config.loader import Settings, load_settings
    from game.engine import GameEngine
    from game.state import GameStatus, InputCommand
    from controls.keyboard import PygameKeyboardController, TerminalKeyboardController
    from controls.gesture import GestureController
    from controls.calibration import load_calibration
    from renderers.terminal_renderer import TerminalRenderer
    from renderers.pygame_renderer import PygameRenderer
    from analytics.telemetry import TelemetryCollector
    from analytics.metrics import compute_metrics
    from analytics.player_profile import build_profile
    from analytics.reports import PostGameReport, generate_next_mission
    from analytics.strategy_evaluation import StrategyOutcome
    from persistence.database import init_database
    from persistence.repositories import MatchRepository
    from ai.strategy_graph import AIStrategyOrchestrator
    from ui.results_screen import print_rich_report

    try:
        import pygame
        pygame_module_available = True
    except ImportError:
        pygame_module_available = False

    settings = settings_override or load_settings()
    if model_name:
        settings.ai.primary_model = model_name

    # Validate Pygame availability if requested
    if renderer_type == "pygame" and not pygame_module_available:
        print("[Warning] Pygame not found in this environment. Falling back to Terminal mode.")
        renderer_type = "terminal"

    # Persistence
    db_conn = init_database(settings.app.database_path)
    match_repo = MatchRepository(db_conn)

    # Telemetry
    match_id = f"starfall_{int(time.time())}"
    collector = TelemetryCollector(match_id=match_id)

    # Game Engine
    engine = GameEngine(
        width=float(settings.display.pygame_width),
        height=float(settings.display.pygame_height),
        starting_lives=settings.gameplay.starting_lives,
        invuln_duration=settings.gameplay.invulnerability_duration,
        fire_cooldown=settings.controls.fire_cooldown,
    )
    engine.set_telemetry_callback(lambda ev_type, data: collector.record(ev_type, data))

    # AI Orchestrator
    orchestrator = AIStrategyOrchestrator(
        endpoint=settings.ai.ollama_endpoint,
        model_name=settings.ai.primary_model,
        timeout_seconds=settings.ai.timeout_seconds,
    )

    # Controllers
    kb_controller = None
    gesture_controller = None

    if renderer_type == "pygame":
        kb_controller = PygameKeyboardController()
    else:
        kb_controller = TerminalKeyboardController()
        kb_controller.start()

    if control_type in ("gesture", "mixed"):
        cal = load_calibration()
        gesture_controller = GestureController(
            camera_index=settings.vision.camera_index,
            model_path=settings.vision.model_path,
            screen_width=float(settings.display.pygame_width),
            screen_height=float(settings.display.pygame_height),
            smoothing_alpha=settings.vision.smoothing_alpha,
            deadzone=settings.vision.deadzone,
            pinch_engage_thresh=settings.vision.pinch_engage_thresh,
            pinch_release_thresh=settings.vision.pinch_release_thresh,
            calibration=cal,
        )
        if not gesture_controller.start():
            print(f"[Warning] Could not initialize camera {settings.vision.camera_index}. Using keyboard controls.")
            gesture_controller = None

    # Renderer
    renderer = None
    if renderer_type == "pygame":
        renderer = PygameRenderer(
            width=settings.display.pygame_width,
            height=settings.display.pygame_height,
            title=settings.app.title,
        )
    else:
        renderer = TerminalRenderer(
            cols=settings.display.terminal_width,
            rows=settings.display.terminal_height,
        )

    if not renderer.initialize():
        print(f"[Error] Failed to initialize renderer '{renderer_type}'. Exiting.")
        return

    # Start match
    engine.start_game()
    last_time = time.perf_counter()
    target_fps = settings.display.target_fps if renderer_type == "pygame" else settings.display.terminal_fps
    frame_interval = 1.0 / target_fps
    running = True

    history_outcomes = []
    last_requested_wave = 0

    try:
        while running:
            loop_start = time.perf_counter()
            dt = min(0.1, loop_start - last_time)
            last_time = loop_start

            # 1. Process Pygame Window Events if in Pygame mode
            if renderer_type == "pygame" and PYGAME_MODULE_AVAILABLE:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    if kb_controller and isinstance(kb_controller, PygameKeyboardController):
                        kb_controller.handle_event(event)

            # 2. Poll Input from Controllers
            cmd = InputCommand()
            if kb_controller:
                cmd = kb_controller.poll()

            # Merge Gesture input if active
            gest_debug = None
            webcam_frame = None
            if gesture_controller:
                gest_cmd = gesture_controller.poll()
                gest_debug = gesture_controller.get_debug_info()
                webcam_frame = gesture_controller.latest_frame
                # Gesture overrides movement/fire if detected
                if gest_cmd.absolute_pos:
                    cmd.absolute_pos = True
                    cmd.target_x = gest_cmd.target_x
                    cmd.target_y = gest_cmd.target_y
                if gest_cmd.fire:
                    cmd.fire = True

            if cmd.quit:
                running = False
                break

            # 3. Check for completed AI strategy plan from background worker
            pending_plan = orchestrator.consume_pending_plan()
            if pending_plan is not None:
                engine.queue_strategy_plan(pending_plan)

            # Check for strategy evaluation outcome
            eval_outcome = orchestrator.get_last_evaluation()
            if eval_outcome is not None and eval_outcome not in history_outcomes:
                history_outcomes.append(eval_outcome)
                match_repo.save_strategy_outcome(match_id, eval_outcome)

            # 4. Trigger AI request on wave completion if not yet requested
            current_wave = engine.wave_manager.current_wave_num
            if engine.wave_manager.in_intermission and current_wave > last_requested_wave and current_wave > 0:
                last_requested_wave = current_wave
                recent_events = collector.get_events_for_wave(current_wave)
                prev_strat = {
                    "wave": current_wave,
                    "formation": engine.wave_manager.active_plan.formation,
                    "obstacle": engine.wave_manager.active_plan.obstacle,
                    "difficulty": engine.wave_manager.active_plan.difficulty,
                    "reason": engine.wave_manager.active_plan.reason,
                    "evidence": engine.wave_manager.active_plan.evidence,
                    "is_fallback": engine.wave_manager.active_plan.is_fallback,
                }
                orchestrator.request_next_wave_plan_async(
                    wave=current_wave + 1,
                    telemetry_events=recent_events,
                    previous_strategy=prev_strat,
                    recent_outcomes=[o.to_dict() for o in history_outcomes],
                    current_difficulty=engine.wave_manager.active_plan.difficulty,
                )

            # 5. Update Game Engine
            engine.update(dt, cmd)

            # 6. Render Snapshot
            snapshot = engine.get_snapshot()
            renderer.render(
                snapshot=snapshot,
                ai_status=orchestrator.latest_status,
                webcam_frame=webcam_frame if (settings.vision.preview_enabled and renderer_type == "pygame") else None,
                gesture_debug=gest_debug,
            )

            # 7. Sleep to regulate frame rate
            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup hardware and displays cleanly
        if renderer:
            renderer.cleanup()
        if kb_controller:
            kb_controller.stop()
        if gesture_controller:
            gesture_controller.stop()

        # Build Post-Game Report
        full_metrics = compute_metrics(collector.events, total_duration=engine.match_time)
        player_prof = build_profile(full_metrics)
        next_mission = generate_next_mission(full_metrics, player_prof)

        report = PostGameReport(
            match_id=match_id,
            total_score=engine.score_keeper.total_score,
            waves_completed=engine.score_keeper.waves_completed,
            survival_seconds=engine.match_time,
            enemies_destroyed=engine.score_keeper.enemies_destroyed,
            shots_fired=engine.score_keeper.shots_fired,
            shots_hit=engine.score_keeper.shots_hit,
            accuracy=engine.score_keeper.accuracy,
            dodges=engine.score_keeper.successful_dodges,
            lives_lost=engine.score_keeper.lives_lost,
            metrics=full_metrics,
            profile=player_prof,
            adaptation_history=history_outcomes,
            next_mission=next_mission,
        )

        match_repo.save_match(report)
        match_repo.save_player_profile(player_prof)
        db_conn.close()

        # Print Debrief to terminal
        print_rich_report(report.to_dict())


def main() -> None:
    # Load local .env values before CLI defaults; existing OS environment still wins.
    if load_dotenv is not None:
        load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

    from config.loader import load_settings
    from persistence.database import init_database
    from persistence.repositories import MatchRepository
    from ui.terminal_menu import display_main_menu
    from ui.results_screen import print_rich_report
    from ui.settings_menu import display_settings_summary
    from scripts.check_environment import check_all
    from scripts.setup_ollama import setup_and_diagnose
    from scripts.test_camera import run_camera_test

    parser = argparse.ArgumentParser(
        description="STARFALL: Adaptive AI Arcade Shooter (Terminal / Pygame, Keyboard / Hand Gestures, Gemma 4 & LangGraph)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: play
    play_parser = subparsers.add_parser("play", help="Start playing STARFALL")
    play_parser.add_argument(
        "--renderer",
        choices=["terminal", "pygame"],
        default=os.getenv("STARFALL_RENDERER", "terminal"),
        help="Renderer to use: 'terminal' for ASCII or 'pygame' for graphic arcade",
    )
    play_parser.add_argument(
        "--control",
        choices=["keyboard", "gesture", "mixed"],
        default=os.getenv("STARFALL_CONTROL", "keyboard"),
        help="Control mode: 'keyboard', 'gesture' (two-hand vision), or 'mixed'",
    )
    play_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional Ollama model override (defaults to OLLAMA_MODEL / config; e.g. gemma4:e4b)",
    )

    # Command: vision-test
    subparsers.add_parser("vision-test", help="Test webcam hand tracking and pinch detection without launching full game")

    # Command: model-check
    subparsers.add_parser("model-check", help="Test Ollama connectivity, model presence, and sample inference")

    # Command: analyze-last
    subparsers.add_parser("analyze-last", help="Display the most recent post-game flight debrief")

    # Command: history
    subparsers.add_parser("history", help="Show recent match history and statistics from SQLite database")

    # Command: settings
    subparsers.add_parser("settings", help="Display current configuration settings")

    # Command: env-check
    subparsers.add_parser("env-check", help="Run comprehensive environment diagnostic")

    # Command: web
    web_parser = subparsers.add_parser("web", help="Launch textmode web companion display inspired by textmode.art")
    web_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default 8000)")

    args = parser.parse_args()

    if args.command == "play":
        run_game(renderer_type=args.renderer, control_type=args.control, model_name=args.model)

    elif args.command == "vision-test":
        run_camera_test()

    elif args.command == "model-check":
        setup_and_diagnose()

    elif args.command == "analyze-last":
        settings = load_settings()
        db_conn = init_database(settings.app.database_path)
        repo = MatchRepository(db_conn)
        last_rep = repo.get_last_match_report()
        db_conn.close()
        if last_rep:
            print_rich_report(last_rep)
        else:
            print("No saved match reports found in database yet. Play a match first!")

    elif args.command == "history":
        settings = load_settings()
        db_conn = init_database(settings.app.database_path)
        repo = MatchRepository(db_conn)
        matches = repo.get_recent_matches(limit=10)
        db_conn.close()

        from rich.console import Console
        from rich.table import Table
        c = Console()
        t = Table(title="[bold yellow]STARFALL Match History[/bold yellow]", border_style="yellow")
        t.add_column("Match ID", style="cyan")
        t.add_column("Date", style="dim")
        t.add_column("Score", style="bold green", justify="right")
        t.add_column("Waves", justify="center")
        t.add_column("Accuracy", justify="right")
        t.add_column("Dodges", justify="right")
        t.add_column("Survival", justify="right")

        for m in matches:
            t.add_row(
                m["match_id"],
                str(m["started_at"]),
                f"{m['total_score']:,}",
                str(m["waves_completed"]),
                f"{m['accuracy']:.1%}",
                str(m["dodges"]),
                f"{m['survival_seconds']:.1f}s",
            )
        if not matches:
            t.add_row("None", "-", "0", "0", "0%", "0", "0s")
        c.print(t)

    elif args.command == "settings":
        settings = load_settings()
        display_settings_summary(settings)

    elif args.command == "env-check":
        check_all()

    elif args.command == "web":
        from web.server import start_server
        start_server(host=args.host, port=args.port, blocking=True)

    else:
        # No command passed: Launch interactive terminal menu
        while True:
            choice = display_main_menu()
            if choice == "1":
                run_game(renderer_type="terminal", control_type="keyboard")
            elif choice == "2":
                run_game(renderer_type="pygame", control_type="keyboard")
            elif choice == "3":
                run_game(renderer_type="pygame", control_type="gesture")
            elif choice == "4":
                run_game(renderer_type="terminal", control_type="gesture")
            elif choice == "5":
                run_camera_test()
            elif choice == "6":
                setup_and_diagnose()
            elif choice == "7":
                settings = load_settings()
                db_conn = init_database(settings.app.database_path)
                repo = MatchRepository(db_conn)
                matches = repo.get_recent_matches(limit=10)
                db_conn.close()
                from rich.console import Console
                from rich.table import Table
                c = Console()
                t = Table(title="Recent Matches", border_style="yellow")
                t.add_column("Match ID")
                t.add_column("Score", style="green")
                t.add_column("Waves")
                t.add_column("Accuracy")
                for m in matches:
                    t.add_row(m["match_id"], str(m["total_score"]), str(m["waves_completed"]), f"{m['accuracy']:.1%}")
                c.print(t)
                input("\nPress Enter to return to menu...")
            elif choice == "8":
                settings = load_settings()
                display_settings_summary(settings)
                input("\nPress Enter to return to menu...")
            elif choice == "9":
                from web.server import start_server
                start_server(host="127.0.0.1", port=8000, blocking=True)
            elif choice in ("10", "q"):
                print("Exiting STARFALL. Dismissed, Commander.")
                break


if __name__ == "__main__":
    main()


# ==============================================================================
# VERCEL MULTI-SERVICE ENTRYPOINT ('app' SERVICE)
# ==============================================================================
# In Vercel Services mode, 'app' is the public-facing service serving the frontend
# and communicating with the internal 'api' service via the injected API_URL binding.

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(
    title="STARFALL Web Gateway Service",
    description="Public frontend service communicating with internal API service via Vercel service binding",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def proxy_to_internal_api(request: Request, path: str):
    """
    Proxy requests to the internal 'api' service using the Vercel-injected API_URL binding.
    Falls back gracefully to local in-process handler if running outside Vercel services.
    """
    api_url = os.environ.get("API_URL", "").rstrip("/")
    if api_url:
        target_url = f"{api_url}/api/{path}"
        req_headers = dict(request.headers)
        req_headers.pop("host", None)
        body = await request.body()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=req_headers,
                content=body,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
    else:
        # Local standalone fallback: delegate to local api module
        try:
            from api.index import app as local_api
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=local_api), base_url="http://testserver") as client:
                resp = await client.request(
                    method=request.method,
                    url=f"/api/{path}",
                    params=request.query_params,
                    content=await request.body(),
                    headers=dict(request.headers),
                )
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": f"API service unavailable: {str(e)}"},
            )


# Mount public static assets at / for the 'app' web service
PUBLIC_DIR = ROOT_DIR / "public"
if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")

handler = app
application = app

