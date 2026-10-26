# STARFALL UI Design Specification

Visual reference: https://extension.textmode.art/ (inspiration only).

## Design language
- Near-black background (#080909), warm off-white text (#f2f0e7), restrained danger red (#d84a52) and telemetry cyan (#66d9e8).
- Monospaced typography and clear grid divisions, with a safe monospace fallback.
- ASCII/text glyphs, compact telemetry, wave timelines, `TACTICAL FEED` and `FLIGHT DEBRIEF` sections.
- Subtle scanlines only if readability and performance remain good.
- Do not copy the reference site's logo, code, exact layout or proprietary media.

## Pygame layout
1. Playfield takes approximately 70–75% of window width.
2. Tactical sidebar includes command link (Ollama status, model and latency), wave intel (formation, obstacle and difficulty), player telemetry (accuracy, position zones, dodge rate and lives), and tactical feed (latest explanation and fallback state).
3. HUD shows score, wave, lives, FPS and input mode.
4. Webcam inset appears only when enabled; gesture status remains visible.
5. Intermission overlay displays a pending strategy; the game never waits synchronously for inference.
6. Pause, calibration, settings and results share typography, spacing and colors.

## Terminal mode
- STARFALL title and model/camera status.
- ASCII playfield with player, enemies, bullets, obstacles and pickups.
- Compact status row with score, wave, lives, accuracy and gesture state.
- Small tactical log refreshed on events, not every frame.
- Visible keyboard shortcuts and terminal cleanup on exit.

## Interaction rules
- Menus support keyboard navigation.
- Lost-hand state displays `HAND LOST — INPUT SAFE`; firing stops immediately.
- AI plan status distinguishes `PENDING`, `APPLIED`, `FALLBACK` and `FAILED`.
- Do not claim “AI learned” when it only selected a different pattern based on a small sample.