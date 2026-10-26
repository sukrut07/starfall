# Graph Report - Starfall  (2026-10-26)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 586 nodes · 1491 edges · 20 communities (16 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 170 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `50e12a15`
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
- typing
- loader.py
- ai/__init__.py
- check_environment.py
- OllamaClientWrapper
- vision
- ai
- gameplay
- display
- scoring
- settings.yaml
- app
- starfall

## God Nodes (most connected - your core abstractions)
1. `GameEngine` - 47 edges
2. `run_game()` - 37 edges
3. `InputCommand` - 28 edges
4. `PygameRenderer` - 23 edges
5. `ScoreKeeper` - 23 edges
6. `create_strategy_graph()` - 23 edges
7. `GameStateSnapshot` - 22 edges
8. `PlayerShip` - 21 edges
9. `WavePlan` - 20 edges
10. `TelemetryCollector` - 19 edges

## Surprising Connections (you probably didn't know these)
- `AIStrategyOrchestrator` --uses--> `StrategyOutcome`  [INFERRED]
  ai/strategy_graph.py → analytics/strategy_evaluation.py
- `AIStrategyOrchestrator` --uses--> `WavePlan`  [INFERRED]
  ai/strategy_graph.py → game/waves.py
- `GestureController` --uses--> `InputCommand`  [INFERRED]
  controls/gesture.py → game/state.py
- `save_calibration()` --uses--> `CalibrationOffsets`  [INFERRED]
  controls/calibration.py → vision/gesture_mapper.py
- `test_headless_game_simulation_lifecycle()` --uses--> `GameStatus`  [INFERRED]
  tests/test_game_modes.py → game/state.py

## Import Cycles
- None detected.

## Communities (20 total, 4 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.06
Nodes (23): aggregate_metrics_node(), build_player_profile_node(), evaluate_previous_strategy_node(), AggregatedMetrics, compute_metrics(), build_profile(), PlayerProfile, generate_next_mission() (+15 more)

### Community 1 - "engine.py"
Cohesion: 0.06
Nodes (26): prepare_wave_plan_node(), check_circle_collision(), check_point_in_laser_lane(), check_projectile_dodge(), spawn_formation(), Enemy, EnemyType, Entity (+18 more)

### Community 2 - "gesture.py"
Cohesion: 0.06
Nodes (11): GestureController, run_camera_test(), test_gesture_mapper_bounds_and_deadzone(), test_pinch_detector_engage_and_release_hysteresis(), test_pinch_detector_left_hand_lost(), CameraService, CalibrationOffsets, GestureMapper (+3 more)

### Community 3 - "PygameRenderer"
Cohesion: 0.06
Nodes (7): GameStateSnapshot, GameStatus, BaseRenderer, format_hud_header(), format_tactical_panel(), PygameRenderer, TerminalRenderer

### Community 4 - "GameEngine"
Cohesion: 0.08
Nodes (9): GameEngine, ScoreKeeper, test_headless_game_simulation_lifecycle(), test_strategy_queue_at_wave_boundary(), test_terminal_renderer_snapshot_generation(), test_dodge_and_wave_scoring(), test_initial_scoring_state(), test_no_negative_score_on_reset() (+1 more)

### Community 5 - "create_strategy_graph"
Cohesion: 0.07
Nodes (16): get_deterministic_strategy(), AIStrategyOrchestrator, worker(), create_strategy_graph(), generate_strategy_node(), select_fallback_node(), validate_strategy_node(), validate_tactical_strategy() (+8 more)

### Community 6 - "InputCommand"
Cohesion: 0.08
Nodes (6): BaseController, load_calibration(), save_calibration(), PygameKeyboardController, TerminalKeyboardController, InputCommand

### Community 8 - "loader.py"
Cohesion: 0.15
Nodes (10): AIConfig, AppConfig, ControlsConfig, DisplayConfig, GameplayConfig, load_settings(), ScoringConfig, Settings (+2 more)

### Community 9 - "ai/__init__.py"
Cohesion: 0.15
Nodes (6): get_model_info(), list_supported_models(), ModelMetadata, build_post_game_prompt(), build_wave_prompt(), GraphState

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

## Knowledge Gaps
- **1 isolated node(s):** `starfall`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 255 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `main.py`, `engine.py`, `PygameRenderer`, `InputCommand`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GameEngine` (e.g. with `Enemy` and `EnemyType`) actually correct?**
  _`GameEngine` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `starfall` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06179775280898876 - nodes in this community are weakly interconnected._
- **Why does `run_game()` connect `main.py` to `gesture.py`, `PygameRenderer`, `GameEngine`, `create_strategy_graph`, `InputCommand`, `loader.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `run_game()` (e.g. with `.consume_pending_plan()` and `.get_last_evaluation()`) actually correct?**
  _`run_game()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06253585771658061 - nodes in this community are weakly interconnected._