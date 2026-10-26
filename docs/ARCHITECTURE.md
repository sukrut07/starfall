# STARFALL Architecture

## Runtime architecture

```mermaid
flowchart LR
  subgraph Inputs
    KB[Keyboard input]
    CAM[OpenCV webcam]
    MP[MediaPipe two-hand landmarks]
    PINCH[Scale-normalized pinch with hysteresis]
    CAM --> MP --> PINCH
  end
  subgraph Core
    CMD[Input command]
    ENG[Shared deterministic game engine]
    EVT[Telemetry events]
    SCORE[Authoritative score]
    ENG --> EVT
    ENG --> SCORE
  end
  subgraph AI
    PROF[Metrics and player profile]
    LG[LangGraph workflow]
    OLL[Ollama local Gemma 4]
    VAL[Pydantic schema and allowlist validator]
    FALL[Deterministic fallback]
    PROF --> LG --> OLL --> VAL
    VAL -->|valid plan| PLAN[Wave plan queue]
    VAL -->|invalid or timeout| FALL --> PLAN
  end
  subgraph Views
    TERM[ASCII terminal renderer]
    PYG[Pygame renderer]
  end
  KB --> CMD
  PINCH --> CMD
  CMD --> ENG
  ENG --> TERM
  ENG --> PYG
  EVT --> PROF
  PLAN -->|apply only between waves| ENG
```

## Decision lifecycle

```mermaid
sequenceDiagram
  actor Player
  participant Engine
  participant Metrics
  participant Graph as LangGraph
  participant Model as Ollama/Gemma 4
  participant Validator
  Player->>Engine: Move and fire
  Engine->>Metrics: Emit bounded telemetry events
  Note over Engine: Wave ends / intermission
  Engine->>Graph: Submit summarized wave state asynchronously
  Graph->>Metrics: Aggregate metrics and check sample sufficiency
  Graph->>Model: Request constrained tactical plan
  Model-->>Graph: Structured response
  Graph->>Validator: Check schema, allowlists and bounds
  alt Valid
    Validator-->>Graph: Accepted plan and grounded explanation
  else Invalid or service down
    Validator-->>Graph: Deterministic fallback
  end
  Graph-->>Engine: Queue plan
  Note over Engine: Apply at next wave boundary
  Engine->>Metrics: Measure outcome
```

## Responsibilities

- `game/`: deterministic update, entities, collisions, waves and scoring.
- `controls/`: keyboard and gesture controllers emitting the same input shape.
- `vision/`: camera lifetime, MediaPipe landmarks, pinch detection and coordinate mapping.
- `renderers/`: terminal and Pygame visualization only; no game rules.
- `analytics/`: event collection, metrics, player profile and outcome comparisons.
- `ai/`: Ollama client, model configuration, prompt/schema, LangGraph, validation and fallback.
- `persistence/`: SQLite schema and repositories; no SQL scattered through game classes.
- `ui/`: terminal navigation and results.
- `scripts/`: diagnostic and local setup helpers.

## Model contract

Gemma receives a compact summary of observed telemetry and supported options. It cannot submit arbitrary code or directly mutate the engine. Pydantic validates the schema; application validation enforces allowlists and numeric limits. The game thread consumes a validated wave plan between waves. A timeout, exception or invalid result uses a deterministic fallback.

## Local setup and licensing

Ollama runs the local model API at the configured host. Local Ollama does not need a cloud API key by default. Verify the selected model tag using `ollama list` and the local inference diagnostic rather than assuming the tag is installed. Gemma is open-weight under Google's Gemma terms, not OSI-approved open-source software.