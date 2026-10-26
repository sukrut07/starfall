# Antigravity Prompt — STARFALL Gesture Gameplay Implementation

Copy this entire prompt into Antigravity with the local `sukrut07/starfall` repository opened. This prompt is focused on making the two-hand gesture-controlled game reliable and playable while preserving the existing project and AI architecture.

---

You are a senior Python game developer, computer-vision engineer, real-time systems engineer, and local-LLM integration engineer. Work directly in the EXISTING STARFALL repository; do not create a second project or replace the project with a static demo. Inspect the current source before changing anything. Many modules may already exist, so repair and integrate them instead of duplicating them.

## Mission

Deliver STARFALL as a genuinely playable Galaga-inspired space shooter with these modes:
1. Pygame graphical gameplay with a polished textmode-inspired HUD.
2. A real-time terminal/ASCII game with keyboard controls.
3. Pygame gesture gameplay where the player's RIGHT hand steers the spaceship and the LEFT hand thumb-index pinch fires.
4. Terminal/ASCII gesture gameplay using the same controls and same simulation engine.
5. Keyboard fallback at all times.

The enemy commander uses local Ollama + Gemma 4 and LangGraph to analyze aggregated game telemetry and choose a validated strategy for the next wave. The AI must never control each frame or block movement/shooting. The game has to remain fully playable without Ollama or the webcam.

Design inspiration: https://extension.textmode.art/. Use this as visual direction only: near-black canvas, warm off-white text, monospace/pixel typography, minimal red/cyan accents, fine grid lines, ASCII/telemetry motifs, retro-computing panels, crisp borders, a tactical status feed and a match debrief. Do not copy the reference site's source, logo, exact page, or proprietary media.

## Phase 0 — inspect, report, then implement

Before making edits:
- Inspect Git status and the current branch. Do not overwrite uncommitted user changes.
- Read `main.py`, `config/loader.py`, `config/settings.yaml`, `.env.example`, `requirements.txt`, `pyproject.toml`, `controls/`, `vision/`, `game/`, `renderers/`, `ai/`, `analytics/`, `persistence/`, `ui/`, `scripts/`, tests and README.
- Trace the real call chain from camera capture -> hand landmarks -> gesture state -> input command -> game engine -> renderers.
- Verify all constructor signatures, return types, MediaPipe API usage, dependency versions, CLI flags and config names. Resolve inconsistencies instead of coding against guessed interfaces.
- Identify what is genuinely working, what is unverified, and what is broken. Do not claim that the camera, local model, a given frame rate, or tests work unless it is actually verified.
- Preserve functioning modules; avoid broad rewrites without evidence.

## Phase 1 — get the local Python and Ollama environment correct

Use Python compatible with the dependencies already selected. Inspect package constraints before changing them. Keep requirements and pyproject declarations aligned.

Use Ollama as the local inference engine. Gemma 4 E4B is the configured preferred model; support E2B as a lower-resource alternative. Use a configurable model tag and endpoint, never scatter hard-coded model IDs across the codebase.

Default configuration:
- OLLAMA_HOST=http://localhost:11434
- OLLAMA_MODEL=gemma4:e4b
- alternate model tag: gemma4:e2b

Check model tags against the installed Ollama catalog and `ollama list`. The fact that a tag is configured does not mean the model is installed. `gemma4:e4b` is available in the Ollama Gemma 4 catalog; verify that the user's installed Ollama version can pull and run it.

Important: local Ollama inference does NOT normally require a cloud API key. Do not create or request a fake `GEMMA_API_KEY`. `OLLAMA_HOST` and `OLLAMA_MODEL` are configuration values, not credentials. Explain this in the README. Never commit `.env`, API tokens, database files, webcam captures, downloaded model weights, or private logs.

Required setup/config work:
- `.env.example` must document local settings but contain no secrets.
- The app should read `.env` only if the loader explicitly supports it; if you add python-dotenv, declare it in both dependency files and tests.
- Define precedence: explicit OS environment variables override `.env`, which overrides YAML/default values.
- Ensure CLI default arguments do not silently override configured model or renderer values. Use `None` for optional CLI overrides when the config should remain authoritative.
- Add model diagnostics: Ollama CLI presence, local endpoint health, model list, configured model presence, structured test inference, measured response latency and actionable failure guidance.
- Do not silently download models without user consent. Show the exact command the user can execute.
- Use the official Ollama Python client/API and the typed response object for current versions. Keep response parsing version-aware and thoroughly tested.
- Use schema-constrained JSON responses where supported; parse with Pydantic and independently validate every strategy.
- Use a bounded request timeout and no more than a small configurable retry count.

Run these checks when the local environment permits:
```bash
ollama --version
ollama list
ollama pull gemma4:e4b
python main.py model-check
python main.py env-check
```

If E4B is too slow or exceeds the user's available memory, document how to change `OLLAMA_MODEL=gemma4:e2b`. Measure real latency on the actual machine instead of inventing benchmarks.

## Phase 2 — reliable two-hand tracking with MediaPipe

Use OpenCV for camera capture and MediaPipe Hand Landmarker for hand landmarks. Follow the current official Python API for the installed MediaPipe version. Prefer VIDEO or LIVE_STREAM mode when appropriate; if LIVE_STREAM is used, callbacks and monotonic timestamps must be correct. Avoid blocking inference on the same thread that renders the game.

Detect a maximum of TWO hands. MediaPipe provides handedness and 21 normalized landmarks per detected hand. Correctly account for mirrored camera previews and handedness semantics. Never infer hand identity only from whether the hand appears on the left or right side of the image.

Create one clear hand-tracking data structure containing:
- normalized landmarks and handedness;
- handedness/category score when available;
- timestamp of the latest result;
- landmark confidence/state and whether the sample is fresh;
- right-hand movement coordinate;
- left-hand pinch state and pinch distance;
- tracking/FPS diagnostics for the developer overlay.

Prefer a single camera owner and a dedicated capture/tracking worker. The game thread should read the latest immutable control snapshot from a thread-safe structure/queue. Never have several modules independently open the same webcam. Always release the camera and close MediaPipe resources on normal exit, exception, pause, and restart.

### Right hand — spaceship movement

Use the RIGHT hand palm center or index fingertip as the steering point. Add a calibration step at startup that asks the player to show their right hand at a comfortable neutral point and move it toward all screen corners.

Requirements:
- Normalize input to 0..1 and map to the game playfield rather than the entire window, so the HUD/sidebar does not distort controls.
- Provide direct absolute-position mapping as the default. Optional relative/velocity mapping can be a setting, but do not make steering feel unpredictable.
- Use an exponential moving average or One Euro filter to reduce jitter. Expose a smoothing slider/setting and keep latency low.
- Add an adjustable dead zone and edge margin.
- Clamp the ship within playfield bounds.
- Handle mirrored preview correctly. Preview mirroring must not accidentally invert the actual movement mapping.
- Add outlier rejection so one erroneous landmark does not teleport the ship.
- If right-hand tracking is absent/stale for more than a short configurable threshold (start around 150–250 ms; tune by testing), freeze movement at the last safe position or pause control. Never jump using a stale coordinate.
- Show `RIGHT HAND: TRACKING / LOST` in the HUD.

### Left hand — pinch-to-fire

Calculate the distance between left thumb tip landmark 4 and left index fingertip landmark 8. Normalize by hand scale, such as wrist-to-middle-MCP distance (landmark 9), so the threshold is less sensitive to camera distance. Use a safe epsilon to avoid division by zero.

Implement a robust hysteresis state machine:
- Transition to PINCHED only when normalized distance is below the configurable engage threshold for the required debounce duration/frames.
- Transition back to RELEASED only when the distance rises above the release threshold, which must be larger than the engage threshold.
- Default interaction: holding the pinch continuously fires using the game engine's existing cooldown. Do not create a new bullet every camera frame.
- Require a fresh, valid LEFT-hand sample before firing. If the left hand is lost, ambiguous, or stale, stop firing immediately and reset/decay the pinch state.
- Add a test mode that prints the measured normalized pinch distance and current state. Let the player tune thresholds in a calibration screen.
- Add optional edge-triggered single-shot behavior as a configurable alternate mode, but continuous fire while pinched should be the MVP.
- Do not use Gemma/LLM inference for gesture recognition. Gesture recognition is deterministic local computer vision.

### Camera preview and gesture feedback

Provide a visible optional preview with landmarks, handedness labels, fingertip line, pinch threshold/state, FPS, and tracking confidence. Use a distinct color for right hand and left hand. Render the camera preview mirrored only for user familiarity, not to determine handedness.

Expose these controls in config/settings:
- camera index;
- preview enabled/disabled;
- frame width/height if configurable;
- detection/presence/tracking thresholds;
- maximum hand count = 2;
- smoothing alpha or filter parameters;
- engage/release thresholds;
- debounce duration/frames;
- stale-frame timeout;
- direct/relative steering mode;
- fire mode (hold or edge-trigger).

Build a `vision-test` mode that starts the camera and shows left/right identity, confidence, current movement coordinate, normalized pinch distance, pinch state and FPS without starting the game. It must show an actionable error if the camera cannot open and must clean up on quit.

## Phase 3 — make the game input and engine integration correct

Do not let vision call Pygame rendering or mutate game entities directly. Vision produces a common input command consumed by the game engine. Keyboard and gesture controllers must return the same command shape.

Use one authoritative game simulation for the Pygame and terminal renderers. Keep renderers responsible only for drawing and UI; keep collision, bullet movement, enemy patterns, waves, score and telemetry in the engine.

Support modes:
- `python main.py play --renderer pygame --control keyboard`
- `python main.py play --renderer pygame --control gesture`
- `python main.py play --renderer pygame --control mixed`
- `python main.py play --renderer terminal --control keyboard`
- `python main.py play --renderer terminal --control gesture`

Ensure CLI commands and help match real code. Terminal mode must be a continuously updating ASCII game, not a turn-based mock or static menu. Use non-blocking input and restore terminal settings on all exit paths. Avoid clearing the whole terminal every frame. If platform-specific terminal input cannot be supported, detect it and show a clear fallback/limitation.

Game mechanics to verify:
- spaceship movement and screen bounds;
- left-hand pinch triggers the normal fire cooldown, not frame-rate bullet spam;
- player projectiles collide with enemies exactly once;
- enemy projectiles/hazards can damage the player;
- invulnerability, lives, wave progression, pause/restart/game over;
- telemetry events are emitted for movement sampling, shots, hits, kills, damage, dodges and wave outcomes;
- terminal and Pygame game simulations behave equivalently under the same deterministic inputs.

Provide reliable keyboard controls when camera setup fails: arrows/WASD move, space shoots, P pauses, R restarts after game over, Q/Escape exits. Let the player switch out of gesture mode without restarting the process if feasible.

## Phase 4 — local AI tactical director with LangGraph

Gemma 4 should analyze summarized per-wave statistics, select a supported enemy pattern for the NEXT wave, and explain the selection. Do not send every webcam frame, landmark, game frame, or game-loop tick to the LLM. Do not call the model synchronously from the game update/render loop.

Implement or repair a real LangGraph stateful pipeline:
1. aggregate current-wave telemetry;
2. verify minimum sample sufficiency;
3. build a measured player profile;
4. evaluate the previous strategy outcome if comparable data exists;
5. generate a proposed strategy using Gemma through Ollama;
6. parse a structured Pydantic response;
7. independently validate allowlisted formation/obstacle names and all numeric bounds;
8. route invalid output, timeout, exception, empty content or insufficient data to a deterministic fallback;
9. send a validated immutable plan to a thread-safe queue;
10. apply it only at the next wave boundary;
11. measure subsequent outcomes and store an adaptation audit.

Player telemetry should include shots fired, hits, accuracy, screen-zone occupancy, movement distance/speed, camping ratio, threat encounters, successful dodges, damage taken, lives lost, survival duration, wave outcome and strategy ID. Define each metric precisely and include its sample count. Low accuracy is not by itself proof of poor aim; enemy movement or formation difficulty may explain it. Use confidence/insufficient-data labels.

Gemma may select only existing strategies implemented by the engine. It must not generate Python/code, create arbitrary enemy types, alter score/lives, bypass collisions, directly spawn unbounded entities, or manipulate player input. Hard limits must be enforced in code rather than relying on prompt instructions.

The AI response should contain `formation`, `obstacle`, `difficulty`, `spawn_count`, `projectile_speed`, `reason`, `evidence`, `confidence` and `mission` only if those fields are used by the engine. Reject unknown keys/enum values where appropriate; enforce min/max counts and speeds. Make sure every accepted field actually affects gameplay.

Use a concise evidence-grounded system prompt. Ask for a brief explanation citing telemetry field names and observed values, not hidden chain-of-thought. The report must distinguish facts from hypotheses and must not claim that an adaptation helped until the next wave's metrics have been recorded.

Fallback requirements:
- game remains playable if Ollama is closed;
- model request is bounded by a timeout;
- invalid schema/JSON or unknown formation triggers fallback;
- plans are not applied while a wave is active;
- latest safe plan remains available during slow inference;
- log whether a plan is model-generated or fallback-generated.

## Phase 5 — terminal and graphical interface

Make the Pygame interface polished, not merely functional. Use the Textmode reference for a restrained retro-instrumentation design.

Graphical interface layout:
- Main playfield occupies about 70–75% of the window.
- Right-side tactical panel shows `COMMAND LINK` (Ollama status, selected model and actual most recent inference time), `WAVE INTEL` (active formation/hazard/difficulty), `PLAYER TELEMETRY` (accuracy, zone occupancy, dodge rate, lives), and `TACTICAL FEED` (last validated strategy reason and evidence).
- Top HUD shows score, wave, lives, FPS and active control mode.
- Optional small webcam preview shows detected hands and pinch feedback.
- During AI inference, show `STRATEGY PENDING`; never freeze game input to await the response.
- Display `APPLIED`, `FALLBACK`, `REJECTED` or `ERROR` explicitly; never present a proposed strategy as applied until it is actually used.
- Add an intro/start screen, pause/settings UI, controls/calibration screen, clear game-over state and post-match debrief.
- Prefer vector-drawn art and original simple sprites if no licensed assets are available. Do not download unlicensed artwork.

Terminal interface:
- A polished interactive menu listing keyboard game, gesture game, Pygame, camera test, model check, history, settings and exit.
- A live ASCII arcade playfield with ship, enemies, player bullets, enemy bullets, hazards and powerups.
- HUD includes score, lives, wave, accuracy, active formation, model status and control status.
- Tactics log updates only when meaningful events happen, not every frame.
- Terminal rendering and game input must be non-blocking and portable. Document known OS limitations.

## Phase 6 — analytics and post-game report

At game end, produce both a terminal report and graphical debrief with:
- total score, enemies destroyed, waves cleared, survival time, shots/hits/accuracy, dodges, damage and lives lost;
- position-zone distribution and camping ratio, with sample sizes;
- player profile with confidence or insufficient evidence;
- each chosen strategy, why it was chosen, whether it was applied, whether fallback was used, model latency and next-wave outcome;
- comparison of player metrics before and after a strategy change, labeling outcomes `improved`, `worsened` or `inconclusive` using explicit thresholds;
- one actionable next-run mission with a measurable target.

Persist match results and strategy outcomes in SQLite. Do not send webcam frames to the LLM. Handle zero shots safely and do not fabricate metrics in a model-written report; use application-computed values as authoritative and the LLM for concise interpretation only.

## Phase 7 — required file layout (merge with existing modules; do not duplicate them)

```text
starfall/
├── main.py
├── requirements.txt
├── pyproject.toml
├── .env.example
├── README.md
├── config/
│   ├── settings.yaml
│   └── loader.py
├── game/
│   ├── engine.py
│   ├── state.py
│   ├── entities.py
│   ├── enemies.py
│   ├── projectiles.py
│   ├── obstacles.py
│   ├── collisions.py
│   ├── scoring.py
│   └── waves.py
├── controls/
│   ├── base.py
│   ├── keyboard.py
│   ├── gesture.py
│   └── calibration.py
├── vision/
│   ├── camera.py
│   ├── hand_tracker.py
│   ├── pinch_detector.py
│   └── gesture_mapper.py
├── renderers/
│   ├── base.py
│   ├── pygame_renderer.py
│   ├── terminal_renderer.py
│   └── hud.py
├── ai/
│   ├── ollama_client.py
│   ├── model_registry.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── strategy_graph.py
│   ├── validator.py
│   └── fallback.py
├── analytics/
│   ├── telemetry.py
│   ├── metrics.py
│   ├── player_profile.py
│   ├── strategy_evaluation.py
│   └── reports.py
├── persistence/
│   ├── database.py
│   └── repositories.py
├── ui/
│   ├── terminal_menu.py
│   ├── settings_menu.py
│   └── results_screen.py
├── scripts/
│   ├── check_environment.py
│   ├── setup_ollama.py
│   └── test_camera.py
└── tests/
    ├── test_gestures.py
    ├── test_metrics.py
    ├── test_scoring.py
    ├── test_strategy_validation.py
    ├── test_fallback.py
    └── test_game_modes.py
```

Keep the current structure if it is already close. Do not introduce empty placeholder modules solely to match this tree. All imports and documented commands must resolve.

## Phase 8 — dependencies and environment

Check and align the currently used versions rather than blindly upgrading everything. Expected core libraries include:
- pygame
- opencv-python
- mediapipe
- numpy
- ollama
- langgraph
- pydantic
- rich
- prompt_toolkit
- PyYAML
- python-dotenv (only if `.env` loading is implemented)
- pytest

Pin compatible lower bounds or a lock strategy where appropriate. Check that MediaPipe's supported Python/platform wheels are compatible with the project's Python version. Avoid loading camera or graphics modules at import time for help/menu-only commands when feasible.

## Phase 9 — automated tests and acceptance criteria

Write or repair tests that do not require a physical webcam or downloaded LLM:
- pinching uses normalized distance and hysteresis correctly;
- pinch starts after engage threshold and stops after release threshold;
- ambiguous/missing/stale left hand forces firing false;
- missing right hand doesn't move ship to origin;
- coordinate mapping, mirroring, deadzone, smoothing and bounds are correct;
- the same synthetic input produces consistent results in the shared engine;
- firing obeys cooldown and cannot fire once per camera frame;
- score/collision events are not duplicated;
- metrics handle zero denominators and insufficient observations;
- unknown model formations and out-of-bounds numeric values are rejected;
- mock Ollama timeout/invalid JSON activates fallback;
- model-generated plans are queued and applied only at wave boundaries;
- report claims derive from telemetry;
- terminal/game smoke run completes and cleans up.

Execute `python main.py --help`, environment/model diagnostics when possible, `pytest -q`, and a deterministic smoke test. Manually test the webcam if access is available. Clearly separate automated test results from hardware-specific verification.

## Phase 10 — Git workflow

- Inspect `git status` before edits and preserve unrelated user changes.
- Do not commit `.env`, credentials, local database, camera captures, downloaded model weights or generated cache files.
- Make focused commits with meaningful messages after tests pass. Do not force-push or overwrite remote history.
- If you cannot push to GitHub from the environment, report the exact local commands needed; do not claim a push happened.
- Update README with real commands and the new gesture calibration workflow.

## Definition of done

1. A user can start the game in keyboard, gesture, terminal and Pygame modes.
2. Right-hand movement and left-hand pinch-to-fire work with robust calibration and safe hand-loss behavior.
3. The game remains responsive while Gemma generates a strategy.
4. Ollama diagnostics prove whether E4B is installed and can complete a structured inference; otherwise they explain how to fix it.
5. LangGraph performs real state transitions and its validated plan changes the following wave.
6. Fallback behavior works without model/network availability.
7. The terminal UI is a real live game, and both renderers use one simulation.
8. The Textmode-inspired interface is readable, polished and original.
9. Reports are based on actual telemetry and are persisted.
10. Tests and commands have been executed and their actual results documented.

Start by auditing the real code, then implement, test, fix, and commit the working changes. Do not stop at a plan or another file tree.