# Antigravity Verification Checklist

Use with `docs/ANTIGRAVITY_MASTER_PROMPT.md`. Check each item only after testing it.

## Repository and dependencies
- [ ] Python version and OS recorded.
- [ ] Imports match installed dependency versions.
- [ ] `python main.py --help` succeeds.
- [ ] README commands exist and behave as documented.
- [ ] No secrets, local databases or webcam captures are tracked.
- [ ] Dependency installation succeeds in a clean virtual environment.

## Game
- [ ] Terminal renderer is continuous, interactive and non-flickering.
- [ ] Pygame renderer works from the same engine.
- [ ] Collisions and scores are deterministic; duplicate kills do not double-score.
- [ ] Keyboard fallback works without camera and Ollama.
- [ ] Terminal state is restored on exit.

## Vision
- [ ] Camera test displays handedness and confidence.
- [ ] Right hand controls movement.
- [ ] Left pinch fires; release stops firing.
- [ ] Lost tracking does not reuse stale coordinates.
- [ ] Camera is released on exit.
- [ ] Gesture-math tests run without physical hardware.

## Gemma 4 and Ollama
- [ ] Ollama CLI presence checked.
- [ ] Service health checked.
- [ ] Actual `ollama list` tags recorded.
- [ ] Configured model tag confirmed installed.
- [ ] Structured test inference succeeds when available.
- [ ] Timeout and malformed JSON activate fallback.
- [ ] Strategy is validated and applied only at wave boundaries.
- [ ] Actual latency recorded on this machine; no guessed performance claims.

## Analytics and release
- [ ] Rates guard against zero denominators.
- [ ] Explanations cite real telemetry and label uncertainty.
- [ ] Reports distinguish observed facts from causal claims.
- [ ] `pytest -q` and headless smoke test were run.
- [ ] README commands are verified.
- [ ] Model and asset licensing are documented accurately.