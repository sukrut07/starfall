# STARFALL — Antigravity Repository Audit & Completion Prompt

Paste this prompt into Antigravity with the `starfall` repository open.

---

You are editing the existing repository `sukrut07/starfall`. This is an implementation-and-verification task, not a request to rewrite the README or create duplicate modules. Inspect the actual files, imports, dependency versions, tests, Git status, and CLI before editing. Preserve working code and only refactor where a concrete defect is verified.

## Objective

Deliver a playable Galaga-inspired adaptive arcade shooter with a real-time terminal ASCII renderer, Pygame frontend, optional MediaPipe/OpenCV gesture controls, local Ollama + Gemma 4 tactical reasoning, LangGraph orchestration, validated enemy tactics, telemetry, SQLite match history and post-game analysis. It must remain playable if Ollama or the webcam is unavailable.

## Audit before edits

1. Inspect `main.py`, all imported modules, `requirements.txt`, `pyproject.toml`, `.env.example`, `config/settings.yaml`, `ai/ollama_client.py`, `ai/strategy_graph.py`, `vision/`, `controls/`, renderers and tests.
2. Find mismatches between README claims and code: CLI command names, constructor signatures, dependency/API versions, env loading, model identifiers, camera asset path, threading, terminal input portability and whether generated strategy fields are actually applied to the game.
3. Do not claim a test passed unless you run it. Do not claim Gemma is installed or the webcam works unless those checks are actually performed in the environment.
4. Verify installed Ollama model tags. Do not assume `gemma4:e4b` is installed or supported; check `ollama list` and the current catalog if available.

## Ollama / Gemma configuration

- Local endpoint defaults to `http://localhost:11434`. Default model is configurable, preferably `gemma4:e2b`; allow `gemma4:e4b` if supported by the user's Ollama installation.
- Local Ollama inference does not require a cloud API key by default. `OLLAMA_HOST` and `OLLAMA_MODEL` are settings, not secrets. Do not ask for a Gemma API key.
- Make configuration precedence explicit. If the code is intended to load `.env`, implement `python-dotenv` deliberately and add it to dependencies; otherwise document shell environment setup and YAML fallback accurately.
- Never commit `.env`, tokens, local databases, model weights or webcam captures. Keep `.env.example` secret-free.
- Implement diagnostics for Python version, imports, camera access, Ollama health, installed model tags and a real structured test inference. Each failure should suggest a specific fix.
- Use the supported Ollama client API and Pydantic schema-constrained JSON output, then independently validate parsed responses.
- Model calls must run asynchronously relative to the gameplay loop. Queue completed plans and apply them only at a wave boundary.
- When Ollama is offline, times out, returns invalid JSON, proposes an unknown formation or exceeds limits, use a tested deterministic fallback.
- Keep inputs, movement, physics, collisions and scoring deterministic; Gemma controls only a validated tactical plan.

## Gesture control correctness

- Inspect MediaPipe calls against the installed package version. The repository uses `assets/models/hand_landmarker.task`; ensure it exists and is licensed correctly, or provide a documented downloader with integrity checks.
- Handle handedness semantics and preview mirroring correctly. Right hand moves the ship; left-hand pinch fires.
- Normalize pinch distance relative to hand scale where possible instead of relying only on raw pixel distance.
- Add pinch engagement/release hysteresis, smoothing, debounce, stale-frame expiry and explicit hand-loss behavior.
- If left-hand tracking is lost, firing must stop; if right-hand tracking is lost, hold position or pause movement rather than using stale coordinates.
- Keep keyboard fallback available and release the camera reliably.
- Test gesture math without physical hardware. Camera test should show handedness, confidence, pinch state and FPS.

## Gameplay analytics and reasoning quality

- Collect facts: positions at a bounded sample rate, shots/hits, kills, enemy projectile encounters, dodges under a documented definition, damage, lives, wave results, selected/applied strategy, model latency and fallback activation.
- Derive metrics with zero-denominator safety and record sample counts. Do not infer intent or classify playstyle if evidence is insufficient.
- Ask Gemma for a concise decision/explanation from structured telemetry; do not request private chain-of-thought. Explanations must cite real metric names and values.
- Validator must enforce allowlists and numeric bounds for difficulty, spawn counts, projectile speed, obstacles and other fields. Verify that the strategy fields returned by the model are actually used by the game engine.
- Record strategy requests and outcomes separately. Do not claim a strategy worked solely because the model returned a response.
- Post-game analysis must distinguish observed facts, hypotheses and inconclusive results.

## Frontend — textmode-inspired visual system

Use `https://extension.textmode.art/` as visual inspiration only; do not copy its logo, source code, proprietary assets or exact page.

Visual direction:
- near-black background, warm off-white text, restrained red/cyan accents;
- monospaced/pixel typography with a safe monospace fallback;
- thin grid lines, compact instrumentation, ASCII glyphs, telemetry readouts, wave timeline, `TACTICAL FEED` and `FLIGHT DEBRIEF` sections;
- restrained motion and scanline/noise effects only if readability and performance remain good.

Implement the experience in Pygame and the terminal, not as a web-only mockup. Pygame HUD should show score, lives, wave, accuracy, gesture states, Ollama status, selected formation and last validated AI explanation. Terminal interface must be genuinely playable with non-blocking input and terminal-state restoration on all exits.

## Terminal mode

- Test terminal mode on the current OS and document limitations honestly.
- Use portable non-blocking input. Avoid repeated shell clear calls that cause flicker.
- Both renderers must use the same authoritative simulation.
- If a platform cannot support a feature, provide a graceful fallback without claiming it works.
- Ensure CLI help, menu, keyboard play, gesture + terminal play, model check, camera test, environment check, history and report commands correspond to real code.

## Architecture and maintainability

- Keep responsibilities separate: simulation, controls, vision, renderers, analytics, AI, persistence, UI and scripts.
- Avoid importing camera/model dependencies at module import time if keyboard-only gameplay should work without them.
- Close database connections, camera devices, worker threads and Pygame in `finally` blocks or context managers.
- Do not create empty placeholder modules. Remove only genuinely unused files after checking imports.
- Use structured logging, not per-frame log spam.

## Required execution sequence

1. Summarize audit findings briefly.
2. Fix import errors, interface mismatches and dependency/API compatibility first.
3. Run `python scripts/check_environment.py` and fix it or explain why a check cannot run.
4. Run `python main.py --help`, `python main.py model-check`, and camera test where environment permits.
5. Run `pytest -q`, fix failures and rerun.
6. Run a deterministic/headless smoke test with fake controls and mock Ollama responses.
7. Manually verify terminal and Pygame modes if the environment supports them.
8. Update README so commands and setup match real code. Make no unsupported test-count or benchmark claims.
9. Provide exact commands run, pass/fail results, unverified hardware-dependent features and remaining limitations.

## Definition of done

- Terminal keyboard mode is playable.
- Pygame mode is playable.
- MediaPipe controls work with a supported camera; mathematical control behavior is independently tested.
- Ollama diagnostics report actual model tags and run a real inference when available.
- LangGraph is executed and its validated plan changes the following wave.
- Deterministic fallback works when Ollama is unavailable.
- Reports are based on stored telemetry.
- README, env example, dependencies and CLI help agree.
- Do the actual work in the repository; do not stop at recommendations or a proposed file tree.