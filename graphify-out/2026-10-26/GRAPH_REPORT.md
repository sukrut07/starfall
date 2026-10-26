# Graph Report - Starfall  (2026-10-26)

## Corpus Check
- 73 files · ~34,349 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .task 1)

## Summary
- 734 nodes · 1731 edges · 37 communities (31 shown, 6 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 186 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `762f50b4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- engine.py
- gesture.py
- PygameRenderer
- GameEngine
- ollama_client.py
- InputCommand
- test_web_server.py
- StarfallWebHandler
- OllamaClientWrapper
- loader.py
- STARFALL: Adaptive AI Arcade Shooter
- vision
- ai
- gameplay
- display
- scoring
- settings.yaml
- app
- starfall
- main
- app.js
- vercel.json
- AIStrategyOrchestrator
- Antigravity Prompt — STARFALL Gesture Gameplay Implementation
- get_deterministic_strategy
- ai/__init__.py
- validate_tactical_strategy
- STARFALL — Antigravity Repository Audit & Completion Prompt
- prompts.py
- Local Ollama + Gemma 4 Setup
- Antigravity Verification Checklist
- STARFALL Architecture
- STARFALL UI Design Specification
- Phase 2 — reliable two-hand tracking with MediaPipe

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
- `prepare_wave_plan_node()` --calls--> `WavePlan`  [EXTRACTED]
  ai/strategy_graph.py → game/waves.py
- `AIStrategyOrchestrator` --uses--> `StrategyOutcome`  [INFERRED]
  ai/strategy_graph.py → analytics/strategy_evaluation.py
- `AIStrategyOrchestrator` --uses--> `WavePlan`  [INFERRED]
  ai/strategy_graph.py → game/waves.py
- `StarfallWebHandler` --uses--> `AIStrategyOrchestrator`  [INFERRED]
  web/server.py → ai/strategy_graph.py

## Import Cycles
- None detected.

## Communities (37 total, 6 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.06
Nodes (22): aggregate_metrics_node(), build_player_profile_node(), evaluate_previous_strategy_node(), AggregatedMetrics, compute_metrics(), build_profile(), PlayerProfile, generate_next_mission() (+14 more)

### Community 1 - "engine.py"
Cohesion: 0.06
Nodes (25): check_circle_collision(), check_point_in_laser_lane(), check_projectile_dodge(), spawn_formation(), Enemy, EnemyType, Entity, EntityType (+17 more)

### Community 2 - "gesture.py"
Cohesion: 0.06
Nodes (14): save_calibration(), GestureController, run_camera_test(), test_gesture_mapper_bounds_and_deadzone(), test_pinch_detector_engage_and_release_hysteresis(), test_pinch_detector_left_hand_lost(), test_pinch_detector_scale_normalization(), test_pinch_detector_stale_frame_expiry() (+6 more)

### Community 3 - "PygameRenderer"
Cohesion: 0.06
Nodes (7): GameStateSnapshot, GameStatus, BaseRenderer, format_hud_header(), format_tactical_panel(), PygameRenderer, TerminalRenderer

### Community 4 - "GameEngine"
Cohesion: 0.08
Nodes (10): GameEngine, ScoreKeeper, InputCommand, test_headless_game_simulation_lifecycle(), test_strategy_queue_at_wave_boundary(), test_terminal_renderer_snapshot_generation(), test_dodge_and_wave_scoring(), test_initial_scoring_state() (+2 more)

### Community 6 - "InputCommand"
Cohesion: 0.09
Nodes (3): BaseController, PygameKeyboardController, TerminalKeyboardController

### Community 7 - "test_web_server.py"
Cohesion: 0.16
Nodes (4): test_web_matches_endpoint(), test_web_status_endpoint(), web_server(), start_server()

### Community 9 - "OllamaClientWrapper"
Cohesion: 0.21
Nodes (3): OllamaClientWrapper, check_all(), setup_and_diagnose()

### Community 10 - "loader.py"
Cohesion: 0.18
Nodes (9): AIConfig, AppConfig, ControlsConfig, DisplayConfig, GameplayConfig, load_settings(), ScoringConfig, Settings (+1 more)

### Community 11 - "STARFALL: Adaptive AI Arcade Shooter"
Cohesion: 0.07
Nodes (27): 10. Automated Testing, 11. Command-Line Reference, 12. Project Directory Structure, 13. Developer Docs, 14. License, 1. Project Overview, 2. System Architecture, 3. Adaptive Enemy Director Workflow (+19 more)

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

### Community 21 - "main"
Cohesion: 0.18
Nodes (4): main(), print_rich_report(), display_settings_summary(), display_main_menu()

### Community 22 - "app.js"
Cohesion: 0.22
Nodes (8): fetchLastReport(), fetchMatches(), renderMatchesRows(), renderReportBody(), renderTextmode(), resetEnemies(), tick(), updateSimulation()

### Community 23 - "vercel.json"
Cohesion: 0.40
Nodes (4): buildCommand, cleanUrls, outputDirectory, $schema

### Community 25 - "Antigravity Prompt — STARFALL Gesture Gameplay Implementation"
Cohesion: 0.15
Nodes (13): Antigravity Prompt — STARFALL Gesture Gameplay Implementation, Definition of done, Mission, Phase 0 — inspect, report, then implement, Phase 10 — Git workflow, Phase 1 — get the local Python and Ollama environment correct, Phase 3 — make the game input and engine integration correct, Phase 4 — local AI tactical director with LangGraph (+5 more)

### Community 26 - "get_deterministic_strategy"
Cohesion: 0.22
Nodes (6): get_deterministic_strategy(), select_fallback_node(), test_deterministic_fallback_no_metrics(), test_fallback_adapts_to_camping(), test_fallback_adapts_to_left_bias(), test_fallback_scales_with_wave()

### Community 27 - "ai/__init__.py"
Cohesion: 0.25
Nodes (4): get_model_info(), list_supported_models(), ModelMetadata, GraphState

### Community 28 - "validate_tactical_strategy"
Cohesion: 0.27
Nodes (5): validate_tactical_strategy(), test_extreme_difficulty_and_speed_clamped(), test_unknown_formation_rejected(), test_unknown_obstacle_rejected(), test_valid_strategy_passes()

### Community 29 - "STARFALL — Antigravity Repository Audit & Completion Prompt"
Cohesion: 0.18
Nodes (11): Architecture and maintainability, Audit before edits, Definition of done, Frontend — textmode-inspired visual system, Gameplay analytics and reasoning quality, Gesture control correctness, Objective, Ollama / Gemma configuration (+3 more)

### Community 31 - "prompts.py"
Cohesion: 0.15
Nodes (6): build_post_game_prompt(), build_wave_prompt(), create_strategy_graph(), generate_strategy_node(), prepare_wave_plan_node(), validate_strategy_node()

### Community 32 - "Local Ollama + Gemma 4 Setup"
Cohesion: 0.25
Nodes (8): 1. Install and verify Ollama, 2. Pull the selected model, 3. Python environment, 4. Environment values, 5. Diagnostics, 6. Performance pattern, Local Ollama + Gemma 4 Setup, Privacy and licensing

### Community 33 - "Antigravity Verification Checklist"
Cohesion: 0.29
Nodes (6): Analytics and release, Antigravity Verification Checklist, Game, Gemma 4 and Ollama, Repository and dependencies, Vision

### Community 34 - "STARFALL Architecture"
Cohesion: 0.29
Nodes (6): Decision lifecycle, Local setup and licensing, Model contract, Responsibilities, Runtime architecture, STARFALL Architecture

### Community 35 - "STARFALL UI Design Specification"
Cohesion: 0.33
Nodes (5): Design language, Interaction rules, Pygame layout, STARFALL UI Design Specification, Terminal mode

### Community 37 - "Phase 2 — reliable two-hand tracking with MediaPipe"
Cohesion: 0.50
Nodes (4): Camera preview and gesture feedback, Left hand — pinch-to-fire, Phase 2 — reliable two-hand tracking with MediaPipe, Right hand — spaceship movement

## Knowledge Gaps
- **1 isolated node(s):** `starfall`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 345 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `main.py`, `engine.py`, `PygameRenderer`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GameEngine` (e.g. with `Enemy` and `EnemyType`) actually correct?**
  _`GameEngine` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `starfall` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06441947565543071 - nodes in this community are weakly interconnected._
- **Why does `run_game()` connect `main.py` to `gesture.py`, `PygameRenderer`, `GameEngine`, `InputCommand`, `loader.py`, `main`, `AIStrategyOrchestrator`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `run_game()` (e.g. with `.consume_pending_plan()` and `.get_last_evaluation()`) actually correct?**
  _`run_game()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06483075157773953 - nodes in this community are weakly interconnected._