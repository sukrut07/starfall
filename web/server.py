"""STARFALL Web Companion Server: Textmode tactical frontend and API service."""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is available
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.loader import load_settings
from persistence.database import init_database
from persistence.repositories import MatchRepository
from ai.ollama_client import OllamaStrategyClient
from analytics.telemetry import TelemetryCollector
from analytics.metrics import compute_metrics
from analytics.player_profile import build_profile
from analytics.reports import PostGameReport, generate_next_mission

WEB_DIR = Path(__file__).resolve().parent


class StarfallWebHandler(BaseHTTPRequestHandler):
    """HTTP Request handler serving STARFALL textmode interface and REST endpoints."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard access log spam; only log errors."""
        if len(args) > 1 and str(args[1]) != "200":
            super().log_message(format, *args)

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/status":
            self._handle_status()
        elif path == "/api/matches":
            self._handle_matches()
        elif path == "/api/match/last":
            self._handle_match_last()
        elif path == "/api/telemetry/live":
            self._handle_telemetry_live()
        else:
            self._serve_static(path)

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload"}, status=400)
            return

        if path == "/api/test-inference":
            self._handle_test_inference(payload)
        elif path == "/api/config":
            self._handle_update_config(payload)
        else:
            self._send_json({"error": f"Unknown endpoint: {path}"}, status=404)

    def _handle_status(self) -> None:
        settings = load_settings()
        
        # Check Ollama
        client = OllamaStrategyClient(
            endpoint=settings.ai.ollama_endpoint,
            model_name=settings.ai.primary_model,
            timeout_seconds=5.0,
        )
        is_healthy, msg, models = client.check_health()

        # Database stats
        db_path = settings.app.database_path
        match_count = 0
        if os.path.exists(db_path):
            try:
                db_conn = init_database(db_path)
                repo = MatchRepository(db_conn)
                matches = repo.get_recent_matches(limit=100)
                match_count = len(matches)
                db_conn.close()
            except Exception:
                pass

        env_file = ROOT_DIR / ".env"
        has_env = env_file.exists()
        has_gemma_key = bool(os.environ.get("GEMMA_API_KEY") or os.environ.get("GEMINI_API_KEY"))

        data = {
            "status": "online",
            "app_name": settings.app.name,
            "version": settings.app.version,
            "ai": {
                "endpoint": settings.ai.ollama_endpoint,
                "primary_model": settings.ai.primary_model,
                "fallback_model": settings.ai.fallback_model,
                "timeout_seconds": settings.ai.timeout_seconds,
                "ollama_online": is_healthy,
                "ollama_message": msg,
                "installed_models": models,
                "has_env_file": has_env,
                "has_gemma_api_key": has_gemma_key,
            },
            "gameplay": {
                "starting_lives": settings.gameplay.starting_lives,
                "max_difficulty": settings.gameplay.max_difficulty,
                "base_enemy_speed": settings.gameplay.base_enemy_speed,
            },
            "persistence": {
                "database_path": str(settings.app.database_path),
                "recorded_matches": match_count,
            },
            "server_time": time.time(),
        }
        self._send_json(data)

    def _handle_matches(self) -> None:
        settings = load_settings()
        try:
            db_conn = init_database(settings.app.database_path)
            repo = MatchRepository(db_conn)
            matches = repo.get_recent_matches(limit=20)
            db_conn.close()
            self._send_json({"matches": matches})
        except Exception as e:
            self._send_json({"error": str(e), "matches": []}, status=500)

    def _handle_match_last(self) -> None:
        settings = load_settings()
        try:
            db_conn = init_database(settings.app.database_path)
            repo = MatchRepository(db_conn)
            report = repo.get_last_match_report()
            db_conn.close()
            if report:
                self._send_json({"report": report.to_dict()})
            else:
                self._send_json({"report": None, "message": "No matches logged yet."})
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _handle_telemetry_live(self) -> None:
        """Return simulated live tactical state for visualization on the textmode canvas."""
        t = time.time()
        data = {
            "timestamp": t,
            "wave": 3,
            "score": 4850,
            "lives": 3,
            "accuracy": 0.824,
            "dodge_count": 7,
            "kill_count": 28,
            "current_formation": "PINCER",
            "active_strategy": "V-FORMATION_CONVERGE",
            "ai_tactical_intent": "Counters player left-screen camping by compressing laser grid.",
            "latency_ms": 312,
            "player_x": 0.35,
            "player_y": 0.85,
            "enemies": [
                {"type": "drone", "x": 0.25, "y": 0.20, "glyph": "W"},
                {"type": "drone", "x": 0.50, "y": 0.15, "glyph": "M"},
                {"type": "drone", "x": 0.75, "y": 0.20, "glyph": "W"},
                {"type": "elite", "x": 0.38, "y": 0.28, "glyph": "X"},
                {"type": "elite", "x": 0.62, "y": 0.28, "glyph": "X"},
            ],
            "lasers": [
                {"x": 0.35, "y": 0.60, "glyph": "|"},
                {"x": 0.35, "y": 0.45, "glyph": "|"},
            ],
        }
        self._send_json(data)

    def _handle_test_inference(self, payload: Dict[str, Any]) -> None:
        """Trigger structured Gemma 4 inference with custom or default metrics."""
        settings = load_settings()
        model_name = payload.get("model") or settings.ai.primary_model
        
        from ai.strategy_graph import AIStrategyOrchestrator
        orchestrator = AIStrategyOrchestrator(
            endpoint=settings.ai.ollama_endpoint,
            model_name=model_name,
            timeout_seconds=settings.ai.timeout_seconds,
        )

        from analytics.telemetry import TelemetryCollector
        c = TelemetryCollector("web_test_match")
        c.record("shot_fired", {"x": 400, "y": 600})
        c.record("enemy_killed", {"enemy_type": "elite", "x": 400, "y": 200})
        c.record("projectile_dodge", {"distance": 22.0})

        metrics = compute_metrics(c.events, wave_count=2, match_duration=45.0)
        profile = build_profile(metrics)

        start_time = time.time()
        plan, reasoning = orchestrator.reason_synchronous(metrics, profile, current_wave=2)
        latency = round((time.time() - start_time) * 1000.0, 1)

        result = {
            "model_used": model_name,
            "latency_ms": latency,
            "is_fallback": plan.is_fallback,
            "fallback_reason": plan.fallback_reason,
            "strategy": {
                "formation": plan.formation,
                "spawn_count": plan.spawn_count,
                "projectile_speed": plan.projectile_speed,
                "fire_rate_multiplier": plan.fire_rate_multiplier,
                "obstacle_type": plan.obstacle_type,
                "difficulty_rating": plan.difficulty_rating,
                "tactical_intent": plan.tactical_intent,
            },
            "reasoning": reasoning,
            "profile": {
                "playstyle": profile.playstyle.value,
                "confidence": profile.confidence,
                "weakness": profile.primary_weakness,
            },
        }
        self._send_json(result)

    def _handle_update_config(self, payload: Dict[str, Any]) -> None:
        """Safely update configuration or .env variables."""
        api_key = payload.get("gemma_api_key")
        model = payload.get("primary_model")

        env_path = ROOT_DIR / ".env"
        existing_lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        keys_set = set()
        new_lines = []
        for line in existing_lines:
            stripped = line.strip()
            if stripped.startswith("GEMMA_API_KEY=") and api_key is not None:
                new_lines.append(f"GEMMA_API_KEY={api_key}\n")
                keys_set.add("GEMMA_API_KEY")
            elif stripped.startswith("OLLAMA_MODEL=") and model is not None:
                new_lines.append(f"OLLAMA_MODEL={model}\n")
                keys_set.add("OLLAMA_MODEL")
            else:
                new_lines.append(line)

        if api_key is not None and "GEMMA_API_KEY" not in keys_set:
            new_lines.append(f"GEMMA_API_KEY={api_key}\n")
        if model is not None and "OLLAMA_MODEL" not in keys_set:
            new_lines.append(f"OLLAMA_MODEL={model}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # Update current process environment
        if api_key:
            os.environ["GEMMA_API_KEY"] = api_key
        if model:
            os.environ["OLLAMA_MODEL"] = model

        self._send_json({
            "status": "success",
            "message": "Configuration updated successfully in .env",
            "updated_model": model,
            "has_api_key": bool(api_key),
        })

    def _serve_static(self, path: str) -> None:
        if path in ("/", ""):
            file_name = "index.html"
        else:
            file_name = path.lstrip("/")

        target_file = (WEB_DIR / file_name).resolve()

        try:
            target_file.relative_to(WEB_DIR)
        except ValueError:
            self._send_json({"error": "Forbidden path"}, status=403)
            return

        if not target_file.exists() or not target_file.is_file():
            self._send_json({"error": f"File not found: {file_name}"}, status=404)
            return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            content = target_file.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_json({"error": f"Failed to read file: {e}"}, status=500)


def start_server(host: str = "127.0.0.1", port: int = 8000, blocking: bool = True) -> Optional[ThreadingHTTPServer]:
    """Start the STARFALL textmode companion HTTP server."""
    server = ThreadingHTTPServer((host, port), StarfallWebHandler)
    url = f"http://{host}:{port}"
    print(f"\n=======================================================")
    print(f" STARFALL Textmode Tactical Companion Display Online")
    print(f" Server URL: {url}")
    print(f" Inspired by: https://extension.textmode.art/")
    print(f"=======================================================\n")

    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web companion server...")
            server.server_close()
            return None
    else:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server


if __name__ == "__main__":
    start_server(host="127.0.0.1", port=8000, blocking=True)
