"""STARFALL Ollama API Client Integration."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import ollama
from ai.schemas import TacticalStrategyResponse, PostGameAnalysisResponse
from ai.prompts import TACTICAL_DIRECTOR_SYSTEM_PROMPT, POST_GAME_ANALYST_SYSTEM_PROMPT


class OllamaClientWrapper:
    """Robust client wrapper for local Ollama service."""

    def __init__(self, endpoint: str = "http://localhost:11434", timeout_seconds: float = 10.0):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.client: Optional[ollama.Client] = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            self.client = ollama.Client(host=self.endpoint, timeout=self.timeout_seconds)
        except Exception:
            self.client = None

    def check_connection(self) -> Tuple[bool, str, List[str]]:
        """
        Check if Ollama is reachable and list available local models.
        Returns (is_connected, status_message, list_of_models).
        """
        if self.client is None:
            self._init_client()
        if self.client is None:
            return False, "Ollama client initialization failed.", []

        try:
            resp = self.client.list()
            models = [m.model for m in resp.models] if hasattr(resp, "models") else []
            return True, f"Connected to Ollama at {self.endpoint}.", models
        except Exception as e:
            return False, f"Failed to connect to Ollama at {self.endpoint}: {str(e)}", []

    def check_model_present(self, model_name: str) -> bool:
        """Check if a specific model tag is already pulled."""
        ok, _, models = self.check_connection()
        if not ok:
            return False
        # Exact match or prefix match (e.g. gemma4:e2b vs gemma4:e2b)
        return any(model_name in m for m in models)

    def generate_strategy(
        self,
        prompt: str,
        model_name: str = "gemma4:e2b",
    ) -> Tuple[bool, Optional[Dict[str, Any]], float, str]:
        """
        Query Gemma 4 with schema-constrained JSON for tactical wave selection.
        Returns (success, parsed_dict, latency_ms, error_msg).
        """
        if self.client is None:
            self._init_client()
        if self.client is None:
            return False, None, 0.0, "Ollama client unavailable."

        start_time = time.perf_counter()
        try:
            messages = [
                {"role": "system", "content": TACTICAL_DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat(
                model=model_name,
                messages=messages,
                format=TacticalStrategyResponse.model_json_schema(),
                options={"temperature": 0.15, "top_p": 0.9},
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Current ollama-python returns a typed ChatResponse; tolerate mappings too.
            message = getattr(response, "message", None)
            content = getattr(message, "content", None)
            if content is None and isinstance(response, dict):
                # Current ollama-python returns a typed ChatResponse; tolerate mappings too.
            message = getattr(response, "message", None)
            content = getattr(message, "content", None)
            if content is None and isinstance(response, dict):
                content = response.get("message", {}).get("content", "")
            content = content or ""
            content = content or ""
            if not content:
                return False, None, latency_ms, "Empty response from Ollama."

            # Parse JSON
            parsed = json.loads(content)
            return True, parsed, latency_ms, ""

        except json.JSONDecodeError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return False, None, latency_ms, f"Malformed JSON from model: {str(e)}"
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return False, None, latency_ms, f"Ollama chat error: {str(e)}"

    def generate_post_game_analysis(
        self,
        prompt: str,
        model_name: str = "gemma4:e2b",
    ) -> Tuple[bool, Optional[Dict[str, Any]], float, str]:
        """
        Query Gemma 4 for structured post-game debrief.
        Returns (success, parsed_dict, latency_ms, error_msg).
        """
        if self.client is None:
            self._init_client()
        if self.client is None:
            return False, None, 0.0, "Ollama client unavailable."

        start_time = time.perf_counter()
        try:
            messages = [
                {"role": "system", "content": POST_GAME_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat(
                model=model_name,
                messages=messages,
                format=PostGameAnalysisResponse.model_json_schema(),
                options={"temperature": 0.2},
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content = response.get("message", {}).get("content", "")
            if not content:
                return False, None, latency_ms, "Empty post-game response from Ollama."

            parsed = json.loads(content)
            return True, parsed, latency_ms, ""

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return False, None, latency_ms, f"Post-game analysis error: {str(e)}"
