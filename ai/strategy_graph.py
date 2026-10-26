"""STARFALL LangGraph Tactical AI Strategy Workflow."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from analytics.telemetry import TelemetryCollector, TelemetryEvent
from analytics.metrics import compute_metrics, AggregatedMetrics
from analytics.player_profile import build_profile, PlayerProfile
from analytics.strategy_evaluation import evaluate_strategy_outcome, StrategyOutcome
from ai.schemas import (
    ALLOWED_FORMATIONS,
    ALLOWED_OBSTACLES,
    TacticalStrategyResponse,
)
from ai.validator import validate_tactical_strategy
from ai.fallback import get_deterministic_strategy
from ai.prompts import build_wave_prompt
from ai.ollama_client import OllamaClientWrapper
from game.waves import WavePlan


class GraphState(TypedDict):
    """Typed state for the LangGraph tactical strategy pipeline."""
    wave: int
    telemetry_events: List[Any]
    aggregated_metrics: Dict[str, Any]
    player_profile: Dict[str, Any]
    previous_strategy: Dict[str, Any]
    recent_outcomes: List[Dict[str, Any]]
    allowed_formations: List[str]
    allowed_obstacles: List[str]
    current_difficulty: int
    max_difficulty: int
    is_data_sufficient: bool
    raw_model_response: Optional[Dict[str, Any]]
    proposed_strategy: Optional[Dict[str, Any]]
    is_valid: bool
    validation_errors: List[str]
    model_latency: float
    fallback_status: bool
    evaluation_outcome: Optional[Dict[str, Any]]
    final_wave_plan: Optional[Dict[str, Any]]


def create_strategy_graph(ollama_client: OllamaClientWrapper, model_name: str = "gemma4:e2b"):
    """Construct and compile the LangGraph tactical decision pipeline."""

    # Node 1: aggregate_metrics
    def aggregate_metrics_node(state: GraphState) -> Dict[str, Any]:
        raw_events = state.get("telemetry_events", [])
        events = [
            e if isinstance(e, TelemetryEvent) else TelemetryEvent(e.get("event_type", ""), e.get("timestamp", 0.0), e.get("data", {}))
            for e in raw_events
        ]
        metrics = compute_metrics(events)
        return {"aggregated_metrics": metrics.to_dict()}

    # Node 2: check_data_sufficiency
    def check_data_sufficiency_node(state: GraphState) -> Dict[str, Any]:
        m = state.get("aggregated_metrics", {})
        pos_samples = m.get("position_samples", 0)
        shots = m.get("shots_fired", 0)
        # Minimum baseline observations needed for personalized adaptation
        is_sufficient = (pos_samples >= 8 and shots >= 2)
        return {"is_data_sufficient": is_sufficient}

    # Node 3: build_player_profile
    def build_player_profile_node(state: GraphState) -> Dict[str, Any]:
        m_dict = state.get("aggregated_metrics", {})
        raw_events = state.get("telemetry_events", [])
        events = [
            e if isinstance(e, TelemetryEvent) else TelemetryEvent(e.get("event_type", ""), e.get("timestamp", 0.0), e.get("data", {}))
            for e in raw_events
        ]
        metrics = compute_metrics(events)
        profile = build_profile(metrics)
        return {"player_profile": profile.to_dict()}

    # Node 4: generate_strategy
    def generate_strategy_node(state: GraphState) -> Dict[str, Any]:
        wave = state.get("wave", 1)
        metrics = state.get("aggregated_metrics", {})
        profile = state.get("player_profile", {})
        prev_strat = state.get("previous_strategy", {})
        recent_outcomes = state.get("recent_outcomes", [])
        curr_diff = state.get("current_difficulty", 2)
        max_diff = state.get("max_difficulty", 5)

        prompt = build_wave_prompt(
            wave=wave,
            metrics=metrics,
            profile=profile,
            previous_strategy=prev_strat,
            recent_outcomes=recent_outcomes,
            current_difficulty=curr_diff,
            max_difficulty=max_diff,
        )

        ok, raw_response, latency_ms, err = ollama_client.generate_strategy(prompt, model_name=model_name)
        if not ok or raw_response is None:
            return {
                "raw_model_response": None,
                "model_latency": latency_ms,
                "is_valid": False,
                "validation_errors": [err or "Ollama strategy generation failed."],
            }

        return {
            "raw_model_response": raw_response,
            "model_latency": latency_ms,
            "is_valid": True,
            "validation_errors": [],
        }

    # Node 5: validate_strategy
    def validate_strategy_node(state: GraphState) -> Dict[str, Any]:
        raw_data = state.get("raw_model_response")
        curr_diff = state.get("current_difficulty", 2)
        max_diff = state.get("max_difficulty", 5)

        is_valid, strategy, errors = validate_tactical_strategy(
            raw_data=raw_data,
            current_difficulty=curr_diff,
            max_difficulty_delta=1,
            max_difficulty_cap=max_diff,
        )

        if is_valid and strategy is not None:
            return {
                "is_valid": True,
                "proposed_strategy": strategy.model_dump(),
                "fallback_status": False,
                "validation_errors": [],
            }
        else:
            return {
                "is_valid": False,
                "fallback_status": True,
                "validation_errors": errors,
            }

    # Node 6: select_fallback_if_needed
    def select_fallback_node(state: GraphState) -> Dict[str, Any]:
        wave = state.get("wave", 1)
        metrics = state.get("aggregated_metrics", {})
        max_diff = state.get("max_difficulty", 4)
        fallback_strat = get_deterministic_strategy(wave=wave, metrics=metrics, difficulty_cap=max_diff)

        errors = state.get("validation_errors", [])
        if not errors:
            errors = ["Insufficient data threshold triggered deterministic baseline."]

        return {
            "proposed_strategy": fallback_strat.model_dump(),
            "fallback_status": True,
            "is_valid": True,
            "validation_errors": errors,
        }

    # Node 7: evaluate_previous_strategy
    def evaluate_previous_strategy_node(state: GraphState) -> Dict[str, Any]:
        prev = state.get("previous_strategy", {})
        if not prev or "formation" not in prev:
            return {"evaluation_outcome": None}

        wave = prev.get("wave", 1)
        formation = prev.get("formation", "v_formation")
        obstacle = prev.get("obstacle", "none")
        difficulty = prev.get("difficulty", 2)
        reason = prev.get("reason", "Initial baseline")
        evidence = prev.get("evidence", [])
        is_fallback = prev.get("is_fallback", False)

        raw_events = state.get("telemetry_events", [])
        events = [
            e if isinstance(e, TelemetryEvent) else TelemetryEvent(e.get("event_type", ""), e.get("timestamp", 0.0), e.get("data", {}))
            for e in raw_events
        ]
        wave_metrics = compute_metrics(events)

        outcome = evaluate_strategy_outcome(
            wave=wave,
            formation=formation,
            obstacle=obstacle,
            difficulty=difficulty,
            reason=reason,
            evidence=evidence,
            metrics_before=None,
            metrics_wave=wave_metrics,
            is_fallback=is_fallback,
        )
        return {"evaluation_outcome": outcome.to_dict()}

    # Node 8: prepare_wave_plan
    def prepare_wave_plan_node(state: GraphState) -> Dict[str, Any]:
        strat = state.get("proposed_strategy") or {}
        is_fallback = state.get("fallback_status", False)
        plan = WavePlan(
            formation=strat.get("formation", "v_formation"),
            obstacle=strat.get("obstacle", "none"),
            difficulty=strat.get("difficulty", 2),
            spawn_count=strat.get("spawn_count", 8),
            projectile_speed=strat.get("projectile_speed", 240.0),
            reason=strat.get("reason", "Tactical baseline sweep."),
            evidence=strat.get("evidence", ["balanced_adaptation"]),
            confidence=strat.get("confidence", 0.5),
            mission=strat.get("mission"),
            is_fallback=is_fallback,
        )
        return {"final_wave_plan": plan.__dict__}

    # Router functions
    def route_sufficiency(state: GraphState) -> str:
        if state.get("is_data_sufficient", False):
            return "generate_strategy"
        return "select_fallback_if_needed"

    def route_validation(state: GraphState) -> str:
        if state.get("is_valid", False):
            return "evaluate_previous_strategy"
        return "select_fallback_if_needed"

    # Assemble graph
    builder = StateGraph(GraphState)
    builder.add_node("aggregate_metrics", aggregate_metrics_node)
    builder.add_node("check_data_sufficiency", check_data_sufficiency_node)
    builder.add_node("build_player_profile", build_player_profile_node)
    builder.add_node("generate_strategy", generate_strategy_node)
    builder.add_node("validate_strategy", validate_strategy_node)
    builder.add_node("select_fallback_if_needed", select_fallback_node)
    builder.add_node("evaluate_previous_strategy", evaluate_previous_strategy_node)
    builder.add_node("prepare_wave_plan", prepare_wave_plan_node)

    # Wire edges
    builder.set_entry_point("aggregate_metrics")
    builder.add_edge("aggregate_metrics", "check_data_sufficiency")
    builder.add_edge("check_data_sufficiency", "build_player_profile")

    builder.add_conditional_edges(
        "build_player_profile",
        route_sufficiency,
        {
            "generate_strategy": "generate_strategy",
            "select_fallback_if_needed": "select_fallback_if_needed",
        },
    )

    builder.add_edge("generate_strategy", "validate_strategy")
    builder.add_conditional_edges(
        "validate_strategy",
        route_validation,
        {
            "evaluate_previous_strategy": "evaluate_previous_strategy",
            "select_fallback_if_needed": "select_fallback_if_needed",
        },
    )

    builder.add_edge("select_fallback_if_needed", "evaluate_previous_strategy")
    builder.add_edge("evaluate_previous_strategy", "prepare_wave_plan")
    builder.add_edge("prepare_wave_plan", END)

    return builder.compile()


class AIStrategyOrchestrator:
    """Coordinates asynchronous AI strategy planning using LangGraph and worker threads."""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model_name: str = "gemma4:e2b",
        timeout_seconds: float = 10.0,
    ):
        self.endpoint = endpoint
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.ollama_client = OllamaClientWrapper(endpoint=endpoint, timeout_seconds=timeout_seconds)
        self.graph = create_strategy_graph(self.ollama_client, model_name=model_name)

        self._pending_plan: Optional[WavePlan] = None
        self._last_evaluation: Optional[StrategyOutcome] = None
        self._is_computing: bool = False
        self._lock = threading.Lock()
        self.latest_status: str = "AI Strategy Director ready."

    def request_next_wave_plan_async(
        self,
        wave: int,
        telemetry_events: List[Any],
        previous_strategy: Dict[str, Any],
        recent_outcomes: List[Dict[str, Any]],
        current_difficulty: int = 2,
    ) -> None:
        """Trigger graph execution in background worker thread so gameplay loop never freezes."""
        with self._lock:
            if self._is_computing:
                return  # Computation already running
            self._is_computing = True
            self.latest_status = f"AI Commander reasoning about Wave {wave}..."

        def worker():
            plan, outcome, status = self.execute_graph_sync(
                wave=wave,
                telemetry_events=telemetry_events,
                previous_strategy=previous_strategy,
                recent_outcomes=recent_outcomes,
                current_difficulty=current_difficulty,
            )
            with self._lock:
                self._pending_plan = plan
                self._last_evaluation = outcome
                self._is_computing = False
                self.latest_status = status

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def execute_graph_sync(
        self,
        wave: int,
        telemetry_events: List[Any],
        previous_strategy: Dict[str, Any],
        recent_outcomes: List[Dict[str, Any]],
        current_difficulty: int = 2,
    ) -> Tuple[WavePlan, Optional[StrategyOutcome], str]:
        """Execute the LangGraph workflow synchronously (used by tests and worker)."""
        initial_state: GraphState = {
            "wave": wave,
            "telemetry_events": telemetry_events,
            "aggregated_metrics": {},
            "player_profile": {},
            "previous_strategy": previous_strategy,
            "recent_outcomes": recent_outcomes,
            "allowed_formations": ALLOWED_FORMATIONS,
            "allowed_obstacles": ALLOWED_OBSTACLES,
            "current_difficulty": current_difficulty,
            "max_difficulty": 5,
            "is_data_sufficient": False,
            "raw_model_response": None,
            "proposed_strategy": None,
            "is_valid": False,
            "validation_errors": [],
            "model_latency": 0.0,
            "fallback_status": False,
            "evaluation_outcome": None,
            "final_wave_plan": None,
        }

        try:
            result = self.graph.invoke(initial_state)
            plan_dict = result.get("final_wave_plan") or {}
            plan = WavePlan(
                formation=plan_dict.get("formation", "v_formation"),
                obstacle=plan_dict.get("obstacle", "none"),
                difficulty=plan_dict.get("difficulty", current_difficulty),
                spawn_count=plan_dict.get("spawn_count", 8),
                projectile_speed=plan_dict.get("projectile_speed", 240.0),
                reason=plan_dict.get("reason", "Tactical sweep."),
                evidence=plan_dict.get("evidence", []),
                confidence=plan_dict.get("confidence", 0.5),
                mission=plan_dict.get("mission"),
                is_fallback=result.get("fallback_status", False),
            )
            eval_dict = result.get("evaluation_outcome")
            outcome = StrategyOutcome(**eval_dict) if eval_dict else None
            status_text = f"Wave {wave}: Selected {plan.formation} (fallback={plan.is_fallback}, lat={result.get('model_latency', 0):.0f}ms)"
            return plan, outcome, status_text
        except Exception as e:
            fallback_strat = get_deterministic_strategy(wave=wave)
            plan = WavePlan(
                formation=fallback_strat.formation,
                obstacle=fallback_strat.obstacle,
                difficulty=fallback_strat.difficulty,
                spawn_count=fallback_strat.spawn_count,
                projectile_speed=fallback_strat.projectile_speed,
                reason=fallback_strat.reason,
                evidence=fallback_strat.evidence,
                confidence=fallback_strat.confidence,
                mission=fallback_strat.mission,
                is_fallback=True,
            )
            return plan, None, f"Workflow error fallback: {str(e)}"

    def consume_pending_plan(self) -> Optional[WavePlan]:
        """Atomically retrieve and clear pending plan for application at wave boundary."""
        with self._lock:
            p = self._pending_plan
            self._pending_plan = None
            return p

    def get_last_evaluation(self) -> Optional[StrategyOutcome]:
        with self._lock:
            return self._last_evaluation

    def is_computing(self) -> bool:
        with self._lock:
            return self._is_computing
