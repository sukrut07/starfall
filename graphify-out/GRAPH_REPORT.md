# Graph Report - Starfall  (2026-10-26)

## Corpus Check
- 77 files · ~43,288 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 2, .css 2, .example 1)

## Summary
- 847 nodes · 1906 edges · 49 communities (40 shown, 9 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 190 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `56f1ee27`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- engine.py
- run_camera_test
- PygameRenderer
- GameEngine
- ollama_client.py
- InputCommand
- check_environment.py
- StarfallWebHandler
- MatchRepository
- OllamaClientWrapper
- STARFALL: Adaptive AI Arcade Shooter
- vision
- ai
- gameplay
- display
- scoring
- settings.yaml
- app
- starfall
- loader.py
- setup_ollama.py
- app.js
- app
- test_web_server.py
- Antigravity Prompt — STARFALL Gesture Gameplay Implementation
- get_deterministic_strategy
- ScoreKeeper
- validate_tactical_strategy
- STARFALL — Antigravity Repository Audit & Completion Prompt
- main.py
- prompts.py
- Local Ollama + Gemma 4 Setup
- Antigravity Verification Checklist
- STARFALL Architecture
- STARFALL UI Design Specification
- public/app.js
- Phase 2 — reliable two-hand tracking with MediaPipe
- Enemy
- test_collisions.py
- test_fastapi_serverless.py
- GestureController
- WavePlan
- STARFALL Deployment & Web Architecture Guide
- PinchDetector
- state.py

## God Nodes (most connected - your core abstractions)
1. `GameEngine` - 47 edges
2. `run_game()` - 32 edges
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
- `request_strategy()` --uses--> `TacticalStrategyResponse`  [INFERRED]
  api/index.py → ai/schemas.py
- `prepare_wave_plan_node()` --calls--> `WavePlan`  [EXTRACTED]
  ai/strategy_graph.py → game/waves.py
- `AIStrategyOrchestrator` --uses--> `WavePlan`  [INFERRED]
  ai/strategy_graph.py → game/waves.py
- `StarfallWebHandler` --uses--> `AIStrategyOrchestrator`  [INFERRED]
  web/server.py → ai/strategy_graph.py

## Import Cycles
- None detected.

## Communities (49 total, 9 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.06
Nodes (24): AIStrategyOrchestrator, worker(), create_strategy_graph(), aggregate_metrics_node(), build_player_profile_node(), evaluate_previous_strategy_node(), prepare_wave_plan_node(), AggregatedMetrics (+16 more)

### Community 1 - "engine.py"
Cohesion: 0.18
Nodes (11): check_projectile_dodge(), EnemyType, Entity, EntityType, PlayerShip, PowerUpType, Projectile, ProjectileOwner (+3 more)

### Community 2 - "run_camera_test"
Cohesion: 0.12
Nodes (3): run_camera_test(), CameraService, HandTracker

### Community 3 - "PygameRenderer"
Cohesion: 0.06
Nodes (6): GameStateSnapshot, BaseRenderer, format_hud_header(), format_tactical_panel(), PygameRenderer, TerminalRenderer

### Community 4 - "GameEngine"
Cohesion: 0.14
Nodes (5): GameEngine, InputCommand, test_headless_game_simulation_lifecycle(), test_strategy_queue_at_wave_boundary(), test_terminal_renderer_snapshot_generation()

### Community 6 - "InputCommand"
Cohesion: 0.08
Nodes (4): BaseController, save_calibration(), PygameKeyboardController, TerminalKeyboardController

### Community 9 - "MatchRepository"
Cohesion: 0.17
Nodes (3): main(), init_database(), MatchRepository

### Community 11 - "STARFALL: Adaptive AI Arcade Shooter"
Cohesion: 0.07
Nodes (28): 10. Automated Testing, 11. Command-Line Reference, 12. Project Directory Structure, 13. Web & Cloud Deployment (FastAPI + Vercel), 14. Developer Docs, 15. License, 1. Project Overview, 2. System Architecture (+20 more)

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

### Community 20 - "loader.py"
Cohesion: 0.15
Nodes (10): AIConfig, AppConfig, ControlsConfig, DisplayConfig, GameplayConfig, load_settings(), ScoringConfig, Settings (+2 more)

### Community 21 - "setup_ollama.py"
Cohesion: 0.27
Nodes (4): get_model_info(), list_supported_models(), ModelMetadata, setup_and_diagnose()

### Community 22 - "app.js"
Cohesion: 0.22
Nodes (8): fetchLastReport(), fetchMatches(), renderMatchesRows(), renderReportBody(), renderTextmode(), resetEnemies(), tick(), updateSimulation()

### Community 23 - "app"
Cohesion: 0.15
Nodes (12): entrypoint, framework, root, bindings, entrypoint, framework, root, rewrites (+4 more)

### Community 24 - "test_web_server.py"
Cohesion: 0.22
Nodes (3): test_web_matches_endpoint(), test_web_status_endpoint(), web_server()

### Community 25 - "Antigravity Prompt — STARFALL Gesture Gameplay Implementation"
Cohesion: 0.15
Nodes (13): Antigravity Prompt — STARFALL Gesture Gameplay Implementation, Definition of done, Mission, Phase 0 — inspect, report, then implement, Phase 10 — Git workflow, Phase 1 — get the local Python and Ollama environment correct, Phase 3 — make the game input and engine integration correct, Phase 4 — local AI tactical director with LangGraph (+5 more)

### Community 26 - "get_deterministic_strategy"
Cohesion: 0.22
Nodes (6): get_deterministic_strategy(), select_fallback_node(), test_deterministic_fallback_no_metrics(), test_fallback_adapts_to_camping(), test_fallback_adapts_to_left_bias(), test_fallback_scales_with_wave()

### Community 27 - "ScoreKeeper"
Cohesion: 0.16
Nodes (5): ScoreKeeper, test_dodge_and_wave_scoring(), test_initial_scoring_state(), test_no_negative_score_on_reset(), test_score_kills_and_accuracy()

### Community 28 - "validate_tactical_strategy"
Cohesion: 0.24
Nodes (6): validate_strategy_node(), validate_tactical_strategy(), test_extreme_difficulty_and_speed_clamped(), test_unknown_formation_rejected(), test_unknown_obstacle_rejected(), test_valid_strategy_passes()

### Community 29 - "STARFALL — Antigravity Repository Audit & Completion Prompt"
Cohesion: 0.18
Nodes (11): Architecture and maintainability, Audit before edits, Definition of done, Frontend — textmode-inspired visual system, Gameplay analytics and reasoning quality, Gesture control correctness, Objective, Ollama / Gemma configuration (+3 more)

### Community 30 - "main.py"
Cohesion: 0.08
Nodes (16): analyze_match(), AnalyzeRequest, check_ollama_reachability(), get_client_config(), get_companion_status(), get_configured_model(), get_last_match(), get_ollama_host() (+8 more)

### Community 31 - "prompts.py"
Cohesion: 0.21
Nodes (4): build_post_game_prompt(), build_wave_prompt(), generate_strategy_node(), GraphState

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
Cohesion: 0.20
Nodes (5): Design language, Interaction rules, Pygame layout, STARFALL UI Design Specification, Terminal mode

### Community 36 - "public/app.js"
Cohesion: 0.12
Nodes (18): appendTacticalLog(), init(), populateDebriefModal(), _processResults(), render(), requestNextWaveStrategy(), resetGame(), SoundFX (+10 more)

### Community 37 - "Phase 2 — reliable two-hand tracking with MediaPipe"
Cohesion: 0.50
Nodes (4): Camera preview and gesture feedback, Left hand — pinch-to-fire, Phase 2 — reliable two-hand tracking with MediaPipe, Right hand — spaceship movement

### Community 38 - "Enemy"
Cohesion: 0.19
Nodes (4): spawn_formation(), Enemy, Obstacle, spawn_obstacles()

### Community 39 - "test_collisions.py"
Cohesion: 0.24
Nodes (6): check_circle_collision(), check_point_in_laser_lane(), LaserLane, test_circle_collision(), test_inactive_no_collision(), test_laser_lane_collision()

### Community 41 - "test_fastapi_serverless.py"
Cohesion: 0.11
Nodes (8): client(), test_analyze_endpoint(), test_config_endpoint(), test_health_endpoint(), test_static_assets_serving(), test_strategy_endpoint_fallback_adaptation(), test_strategy_endpoint_invalid_payload_rejected(), test_strategy_endpoint_valid_request()

### Community 42 - "GestureController"
Cohesion: 0.15
Nodes (6): load_calibration(), GestureController, test_gesture_mapper_bounds_and_deadzone(), CalibrationOffsets, GestureMapper, HandTrackingResult

### Community 44 - "STARFALL Deployment & Web Architecture Guide"
Cohesion: 0.15
Nodes (12): 1. Architecture Overview, 2. Vercel Deployment Structure, 3. Important Cloud Deployment Limitation: Local Ollama vs Cloud, 4. Environment Variables Reference, 5. Deployment Instructions, 6. Local Testing & Verification, Automatic Deployment via GitHub (Recommended), Manual Deployment via Vercel CLI (+4 more)

### Community 45 - "PinchDetector"
Cohesion: 0.30
Nodes (5): test_pinch_detector_engage_and_release_hysteresis(), test_pinch_detector_left_hand_lost(), test_pinch_detector_scale_normalization(), test_pinch_detector_stale_frame_expiry(), PinchDetector

### Community 46 - "state.py"
Cohesion: 0.24
Nodes (3): Particle, PowerUp, GameStatus

## Knowledge Gaps
- **1 isolated node(s):** `starfall`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 392 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `main.py`, `engine.py`, `PygameRenderer`, `Enemy`, `test_collisions.py`, `WavePlan`, `state.py`, `ScoreKeeper`, `main.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GameEngine` (e.g. with `Enemy` and `EnemyType`) actually correct?**
  _`GameEngine` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `starfall` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055822466254861584 - nodes in this community are weakly interconnected._
- **Why does `run_game()` connect `main.py` to `PygameRenderer`, `GameEngine`, `InputCommand`, `check_environment.py`, `main.py`, `MatchRepository`, `GestureController`, `loader.py`, `main.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `run_game()` (e.g. with `.consume_pending_plan()` and `.get_last_evaluation()`) actually correct?**
  _`run_game()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `run_camera_test` be split into smaller, more focused modules?**
  _Cohesion score 0.11857707509881422 - nodes in this community are weakly interconnected._