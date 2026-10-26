# Local Ollama + Gemma 4 Setup

STARFALL's local model integration does **not** require a cloud API key by default. `OLLAMA_HOST` is an endpoint setting and `OLLAMA_MODEL` is a model tag, not a secret. Never put credentials in the repository.

## 1. Install and verify Ollama

Install Ollama from https://ollama.com, then open a new terminal.

```bash
ollama --version
ollama list
```

## 2. Pull the selected model

The repository defaults to `gemma4:e2b`. To try E4B, first verify the supported tag in the current Ollama library or your local CLI, then pull the exact tag documented there.

```bash
ollama pull gemma4:e2b
# Optional alternative only if this tag is supported:
ollama pull gemma4:e4b
ollama list
```

A successful pull is not enough by itself. Run STARFALL's model diagnostic and ensure a structured tactical request succeeds. Hardware, quantization, context size, concurrent applications and OS affect latency; measure it on the target machine instead of relying on generic estimates.

## 3. Python environment

Use a Python version compatible with the installed MediaPipe and project dependencies.

```bash
python --version
python -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Environment values

Example `.env` content (do not commit `.env`):

```dotenv
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b
STARFALL_RENDERER=pygame
STARFALL_CONTROL=gesture
STARFALL_CAMERA_INDEX=0
STARFALL_DEBUG=false
STARFALL_DB_PATH=starfall.db
```

Confirm the actual configuration loader's precedence. If the application does not load dotenv, export variables in the shell or update the loader intentionally; merely creating `.env` does not make Python read it.

Do not add a “Gemma API key”: Ollama's local API does not need one by default. Do not expose the Ollama port publicly.

## 5. Diagnostics

Run the commands actually implemented by the CLI:

```bash
python main.py --help
python main.py model-check
python main.py env-check
python main.py vision-test
pytest -q
```

If any command fails, fix the root cause and update the documentation. The real CLI is the source of truth.

## 6. Performance pattern

- Gesture tracking and the simulation run on their own cadence.
- Send summarized telemetry between waves, not each frame.
- Use bounded model timeouts.
- Validate model output against a schema, allowlist and numeric limits.
- Queue the plan and apply it at a wave boundary.
- Use a predefined strategy on timeout or invalid output.
- Record actual inference latency on the user's machine.

## Privacy and licensing

Camera frames should remain local and must not be sent to the model during normal gameplay. Store numeric telemetry locally. Gemma is open-weight and governed by Google's Gemma terms; verify the license of any alternative model before describing it as open source. Check asset and MediaPipe model licenses before redistribution.