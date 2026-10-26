# Graph Report - Starfall  (2026-10-26)

## Corpus Check
- 66 files · ~27,875 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: .example 1, (none) 1, .task 1)

## Summary
- 665 nodes · 1660 edges · 24 communities (20 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 185 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ed8e1111`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- engine.py
- gesture.py
- PygameRenderer
- GameEngine
- create_strategy_graph
- InputCommand
- server.py
- OllamaClientWrapper
- typing
- main.py
- STARFALL: Adaptive AI Arcade Shooter
- vision
- ai
- gameplay
- display
- scoring
- settings.yaml
- app
- starfall
- run_camera_test
- PinchDetector
- app.js

## God Nodes (most connected - your core abstractions)
1. `GameEngine` - 47 edges
2. `run_game()` - 37 edges
3. `InputCommand` - 28 edges
4. `create_strategy_graph()` - 23 edges
5. `ScoreKeeper` - 23 edges
6. `PygameRenderer` - 23 edges
7. `OllamaClientWrapper` - 22 edges
8. `TelemetryCollector` - 22 edges
9. `GameStateSnapshot` - 22 edges
10. `MatchRepository` - 22 edges

## Surprising Connections (you probably didn't know these)
- `StarfallWebHandler` --uses--> `OllamaClientWrapper`  [INFERRED]
  web/server.py → ai/ollama_client.py
- `AIStrategyOrchestrator` --uses--> `StrategyOutcome`  [INFERRED]
  ai/strategy_graph.py → analytics/strategy_evaluation.py
- `AIStrategyOrchestrator` --uses--> `WavePlan`  [INFERRED]
  ai/strategy_graph.py → game/waves.py
- `MatchRepository` --uses--> `StrategyOutcome`  [INFERRED]
  persistence/repositories.py → analytics/strategy_evaluation.py
- `run_game()` --uses--> `Settings`  [INFERRED]
  main.py → config/loader.py

## Import Cycles
- None detected.

## Communities (24 total, 4 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.05
Nodes (15): AIStrategyOrchestrator, worker(), build_profile(), PlayerProfile, generate_next_mission(), PostGameReport, TelemetryCollector, main() (+7 more)

### Community 1 - "engine.py"
Cohesion: 0.07
Nodes (25): prepare_wave_plan_node(), check_circle_collision(), check_point_in_laser_lane(), check_projectile_dodge(), spawn_formation(), Enemy, EnemyType, Entity (+17 more)

### Community 2 - "gesture.py"
Cohesion: 0.12
Nodes (6): GestureController, test_gesture_mapper_bounds_and_deadzone(), CalibrationOffsets, GestureMapper, HandTracker, HandTrackingResult

### Community 3 - "PygameRenderer"
Cohesion: 0.06
Nodes (7): GameStateSnapshot, GameStatus, BaseRenderer, format_hud_header(), format_tactical_panel(), PygameRenderer, TerminalRenderer

### Community 4 - "GameEngine"
Cohesion: 0.07
Nodes (11): GameEngine, Particle, ScoreKeeper, InputCommand, test_headless_game_simulation_lifecycle(), test_strategy_queue_at_wave_boundary(), test_terminal_renderer_snapshot_generation(), test_dodge_and_wave_scoring() (+3 more)

### Community 5 - "create_strategy_graph"
Cohesion: 0.06
Nodes (24): get_deterministic_strategy(), build_post_game_prompt(), build_wave_prompt(), PostGameAnalysisResponse, TacticalStrategyResponse, create_strategy_graph(), aggregate_metrics_node(), build_player_profile_node() (+16 more)

### Community 6 - "InputCommand"
Cohesion: 0.09
Nodes (3): BaseController, PygameKeyboardController, TerminalKeyboardController

### Community 7 - "server.py"
Cohesion: 0.12
Nodes (4): test_web_matches_endpoint(), test_web_status_endpoint(), web_server(), start_server()

### Community 8 - "OllamaClientWrapper"
Cohesion: 0.05
Nodes (19): get_model_info(), list_supported_models(), ModelMetadata, OllamaClientWrapper, GraphState, AIConfig, AppConfig, ControlsConfig (+11 more)

### Community 9 - "typing"
Cohesion: 0.16
Nodes (4): AggregatedMetrics, NextRunMission, evaluate_strategy_outcome(), StrategyOutcome

### Community 11 - "STARFALL: Adaptive AI Arcade Shooter"
Cohesion: 0.07
Nodes (26): 10. Automated Testing, 11. Command-Line Reference, 12. Project Directory Structure, 13. License, 1. Project Overview, 2. System Architecture, 3. Adaptive Enemy Director Workflow, 4. Hardware and Model Configuration (+18 more)

### Community 12 - "vision"
Cohesion: 0.15
Nodes (13): vision, camera_index, deadzone, debounce_frames, min_detection_confidence, min_tracking_confidence, model_path, pinch_engage_thresh (+5 more)

### Community 13 - "ai"
Cohesion: 0.18
Nodes (11): ai, allowed_formations, allowed_obstacles, alternative_model, enabled, max_difficulty_delta, min_observations_for_profile, ollama_endpoint (+3 more)

### Community 14 - "gameplay"
Cohesion: 0.22
Nodes (9): gameplay, invulnerability_duration, max_difficulty, max_enemies_per_wave, max_projectile_speed, player_hitbox_radius, star_count, starting_difficulty (+1 more)

### Community 15 - "display"
Cohesion: 0.29
Nodes (7): display, pygame_height, pygame_width, target_fps, terminal_fps, terminal_height, terminal_width

### Community 16 - "scoring"
Cohesion: 0.29
Nodes (7): scoring, bonus_target, boss_kill, enemy_kill, life_lost_penalty, successful_dodge, wave_completed

### Community 17 - "settings.yaml"
Cohesion: 0.40
Nodes (4): controls, default_mode, fire_cooldown, move_speed

### Community 18 - "app"
Cohesion: 0.40
Nodes (5): app, database_path, debug, title, version

### Community 21 - "PinchDetector"
Cohesion: 0.25
Nodes (5): test_pinch_detector_engage_and_release_hysteresis(), test_pinch_detector_left_hand_lost(), test_pinch_detector_scale_normalization(), test_pinch_detector_stale_frame_expiry(), PinchDetector

### Community 22 - "app.js"
Cohesion: 0.27
Nodes (4): renderTextmode(), resetEnemies(), tick(), updateSimulation()

## Knowledge Gaps
- **1 isolated node(s):** `starfall`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 296 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `main.py`, `engine.py`, `main.py`, `PygameRenderer`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GameEngine` (e.g. with `Enemy` and `EnemyType`) actually correct?**
  _`GameEngine` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `starfall` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05221518987341772 - nodes in this community are weakly interconnected._
- **Why does `run_game()` connect `main.py` to `gesture.py`, `PygameRenderer`, `GameEngine`, `create_strategy_graph`, `InputCommand`, `OllamaClientWrapper`, `main.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `run_game()` (e.g. with `.consume_pending_plan()` and `.get_last_evaluation()`) actually correct?**
  _`run_game()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06842105263157895 - nodes in this community are weakly interconnected._