# STARFALL Deployment & Web Architecture Guide

This document describes how to deploy the STARFALL arcade shooter to Vercel with its FastAPI backend and browser-playable MediaPipe gesture frontend, while maintaining local desktop execution with Pygame and local Gemma 4 / Ollama models.

---

## 1. Architecture Overview

STARFALL is structured with a dual-runtime model:

```
┌─────────────────────────────────────────────────────────────┐
│                       BROWSER CLIENT                        │
│  • Lightweight HTML5 Canvas Arcade Engine (60 FPS)         │
│  • Textmode Aesthetic Visual System (extension.textmode.art)│
│  • In-Browser MediaPipe Tasks Vision Hand Tracking          │
│    - Right Hand: Smooth Flight Navigation                   │
│    - Left Hand: Thumb-Index Pinch Weapon Trigger            │
│  • Failsafe Keyboard Controls (WASD / Arrows + Space)       │
└──────────────┬──────────────────────────────┬───────────────┘
               │ (Between Waves)              │ (Game Over)
               ▼                              ▼
      POST /api/strategy              POST /api/analyze
┌─────────────────────────────────────────────────────────────┐
│                VERCEL / FASTAPI BACKEND                     │
│  • api/index.py (Serverless ASGI Entrypoint)               │
│  • Pydantic v2 Telemetry & Strategy Schema Validation       │
│  • GET /api/health  (Reachability & Model Diagnostics)      │
│  • GET /api/config  (Safe Client Game Configuration)        │
│  • Reachable Remote Ollama / LLM Endpoint (Optional)        │
│  • Deterministic Tactical Fallback Engine (Zero Downtime)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Vercel Deployment Structure

Vercel detects the project via standard Python serverless conventions:

- **`api/index.py`**: The serverless ASGI application entrypoint (`app = FastAPI(...)`).
- **`vercel.json`**: Rewrites all `/api/*` routes to `api/index.py`.
- **`public/`**: Contains static frontend assets served directly by Vercel's edge CDN:
  - `public/index.html`: Canvas game, HUD, and modal interfaces.
  - `public/app.js`: 60 FPS arcade loop, Web Audio API synthesizer, MediaPipe gesture controller.
  - `public/styles.css`: High-density textmode CSS tokens and CRT scanline effects.
- **`requirements.txt`**: Serverless backend dependencies (`fastapi`, `uvicorn`, `httpx`, `pydantic`, `PyYAML`, `python-dotenv`, `ollama`).
- **`.vercelignore`**: Excludes heavy desktop modules (`pygame`, `opencv-python`, GUI windows, `.venv`, `.task` files) to ensure serverless function bundles remain lightweight (< 30 MB).

---

## 3. Important Cloud Deployment Limitation: Local Ollama vs Cloud

> [!IMPORTANT]
> **Vercel cannot connect to `http://localhost:11434` on your personal laptop.**
> In serverless execution, `localhost` points to the isolated cloud container, not your development machine.
>
> - **In Production (Vercel)**: If no remote Ollama endpoint is configured, STARFALL automatically engages the built-in **Deterministic Tactical Fallback**. The game remains 100% playable, dynamic, and responsive with zero latency.
> - **With a Reachable Inference Service**: You can configure a publicly accessible Ollama or OpenAI/Gemma-compatible endpoint in your Vercel Project Settings (`OLLAMA_HOST` and `OLLAMA_MODEL`).
> - **On Desktop**: Running `python main.py play` natively connects to your local `http://localhost:11434` instance with Gemma 4 E4B / E2B.

---

## 4. Environment Variables Reference

Configure these in `.env` (for local development) or in **Vercel Project Settings &rarr; Environment Variables**:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama or remote inference endpoint URL |
| `OLLAMA_MODEL` | `gemma4:e4b` | Tactical model identifier (`gemma4:e4b` or `gemma4:e2b`) |
| `OLLAMA_TIMEOUT_SECONDS`| `8` | Maximum async response window before fallback |
| `STARFALL_AI_ENABLED` | `true` | Toggle AI tactical query generation |
| `STARFALL_RENDERER` | `pygame` | Local desktop renderer (`pygame` or `terminal`) |
| `STARFALL_CONTROL` | `keyboard` | Local desktop control mode (`keyboard`, `gesture`, `mixed`) |
| `STARFALL_CAMERA_INDEX` | `0` | Local webcam device index for desktop version |

---

## 5. Deployment Instructions

### Automatic Deployment via GitHub (Recommended)
1. Commit and push your changes to GitHub (`git push origin main`).
2. Vercel automatically detects the push and triggers the build.
3. The build completes in ~15 seconds without `PYTHON_ENTRYPOINT_NOT_FOUND` errors.

### Manual Deployment via Vercel CLI
If using the Vercel CLI locally:
```bash
# 1. Install or update Vercel CLI
npm install -g vercel

# 2. Authenticate
vercel login

# 3. Deploy preview
vercel

# 4. Deploy to production
vercel --prod
```

---

## 6. Local Testing & Verification

### Run the FastAPI Web Server Locally
```bash
# Activate virtual environment
source .venv/bin/activate

# Launch ASGI server (serves both API and static frontend)
uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### Run Local Desktop Pygame Game
```bash
# Play with keyboard
python main.py play --renderer pygame --control keyboard

# Play with two-hand webcam gestures
python main.py play --renderer pygame --control gesture

# Test webcam hand tracking without starting a match
python main.py vision-test
```

### Run Test Suite
```bash
pytest -v
```
All 39 unit and integration tests validate collision physics, gesture hysteresis, scoring, Pydantic schemas, and FastAPI endpoints.
