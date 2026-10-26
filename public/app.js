/**
 * STARFALL Browser Arcade Engine & AI Tactical Interface
 * Visual system inspired by textmode aesthetics (https://extension.textmode.art/)
 * Browser-based MediaPipe hand gesture controls & FastAPI tactical integration.
 */

(function () {
  "use strict";

  // ==========================================================================
  // AUDIO SYNTHESIZER (WEB AUDIO API - ZERO EXTERNAL ASSETS)
  // ==========================================================================
  class SoundFX {
    constructor() {
      this.ctx = null;
      this.enabled = true;
    }

    _init() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) this.ctx = new AudioContext();
      }
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume();
      }
    }

    playLaser() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "square";

      const now = this.ctx.currentTime;
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(160, now + 0.12);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.12);
    }

    playExplosion() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      // Noise burst with lowpass filter
      const now = this.ctx.currentTime;
      const bufferSize = this.ctx.sampleRate * 0.25;
      const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }

      const noise = this.ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = this.ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(800, now);
      filter.frequency.exponentialRampToValueAtTime(80, now + 0.25);

      const gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(this.ctx.destination);

      noise.start(now);
      noise.stop(now + 0.25);
    }

    playHit() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sawtooth";

      const now = this.ctx.currentTime;
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.linearRampToValueAtTime(60, now + 0.2);

      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.2);
    }

    playWaveClear() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      [440, 554, 659, 880].forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = "sine";
        const t = now + idx * 0.08;
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.15, t);
        gain.gain.exponentialRampToValueAtTime(0.01, t + 0.12);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(t);
        osc.stop(t + 0.12);
      });
    }
  }

  const sfx = new SoundFX();

  // ==========================================================================
  // GAME SIMULATION STATE
  // ==========================================================================
  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");

  const state = {
    mode: "START", // START, PLAYING, PAUSED, GAME_OVER
    controlMode: "keyboard", // keyboard or gesture
    fps: 60,
    lastTime: performance.now(),
    matchStartTime: 0,
    survivalSeconds: 0,
    score: 0,
    lives: 3,
    wave: 1,
    inIntermission: false,
    intermissionTimer: 0,

    // Active AI Strategy
    strategy: {
      formation: "v_formation",
      obstacle: "none",
      difficulty: 2,
      spawn_count: 8,
      projectile_speed: 240.0,
      reason: "Initial baseline wave deployment.",
      is_fallback: true,
      source: "deterministic_fallback",
    },

    // Telemetry Collection
    telemetry: {
      shotsFired: 0,
      shotsHit: 0,
      dodges: 0,
      livesLost: 0,
      positionSamples: 0,
      leftZoneTicks: 0,
      centerZoneTicks: 0,
      rightZoneTicks: 0,
      stationaryTicks: 0,
      totalTicks: 0,
      appliedStrategies: [],
    },
  };

  // Keyboard input state
  const keys = {
    left: false,
    right: false,
    up: false,
    down: false,
    fire: false,
  };

  // Player Spacecraft
  const player = {
    x: 400,
    y: 420,
    vx: 0,
    vy: 0,
    targetX: 400,
    targetY: 420,
    speed: 420.0,
    width: 28,
    height: 24,
    lastShotTime: 0,
    shotCooldownMs: 190,
    invulnerableTimer: 0, // In seconds
  };

  // Game Entities
  let playerLasers = [];
  let enemyProjectiles = [];
  let enemies = [];
  let obstacles = [];
  let particles = [];
  let floatingTexts = [];

  // Parallax Starfield (ASCII glyphs)
  const stars = [];
  for (let i = 0; i < 70; i++) {
    stars.push({
      x: Math.random() * 800,
      y: Math.random() * 480,
      speed: 0.6 + Math.random() * 2.2,
      glyph: Math.random() > 0.85 ? "*" : Math.random() > 0.4 ? "·" : ".",
      color: Math.random() > 0.7 ? "#ffb700" : "#777788",
    });
  }

  // ==========================================================================
  // MEDIAPIPE GESTURE CONTROLLER (CLIENT-SIDE BROWSER VISION)
  // ==========================================================================
  const gestureController = {
    videoEl: document.getElementById("webcamVideo"),
    canvasEl: document.getElementById("webcamCanvas"),
    landmarker: null,
    stream: null,
    isInitialized: false,
    isRunning: false,

    // Smoothed state
    rightHand: {
      detected: false,
      rawX: 400,
      rawY: 420,
      smoothX: 400,
      smoothY: 420,
      lastSeen: 0,
      alpha: 0.28, // Exponential moving average
      deadzone: 5.0,
    },
    leftHand: {
      detected: false,
      isPinching: false,
      pinchDistance: 1.0,
      engageThreshold: 0.26, // Scale-normalized
      releaseThreshold: 0.38,
      lastSeen: 0,
    },

    async init() {
      if (this.isInitialized) return true;
      const cameraMsg = document.getElementById("cameraMsg");

      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("Webcam access not supported by this browser.");
        }

        if (cameraMsg) cameraMsg.textContent = "Requesting webcam permission...";
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" },
          audio: false,
        });
        this.videoEl.srcObject = this.stream;
        await this.videoEl.play();

        if (cameraMsg) cameraMsg.textContent = "Loading MediaPipe hand vision model...";

        // Load MediaPipe Hand Landmarker from Tasks Vision
        if (window.FilesetResolver && window.HandLandmarker) {
          const vision = await window.FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
          );
          this.landmarker = await window.HandLandmarker.createFromOptions(vision, {
            baseOptions: {
              modelAssetPath:
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
              delegate: "GPU",
            },
            runningMode: "VIDEO",
            numHands: 2,
          });
        }

        this.isInitialized = true;
        this.isRunning = true;
        if (cameraMsg) cameraMsg.style.display = "none";
        this._startLoop();
        return true;
      } catch (err) {
        console.warn("MediaPipe gesture initialization fallback:", err);
        if (cameraMsg) {
          cameraMsg.textContent = `Camera error: ${err.message}. Using keyboard flight controls.`;
          cameraMsg.style.color = "var(--accent-red)";
        }
        return false;
      }
    },

    _startLoop() {
      const processFrame = () => {
        if (!this.isRunning) return;
        const now = performance.now();

        if (this.landmarker && this.videoEl.readyState >= 2) {
          try {
            const results = this.landmarker.detectForVideo(this.videoEl, now);
            this._processResults(results, now);
          } catch (e) {
            // Non-fatal frame drop
          }
        }
        requestAnimationFrame(processFrame);
      };
      requestAnimationFrame(processFrame);
    },

    _processResults(results, now) {
      let foundRight = false;
      let foundLeft = false;

      const badgeRight = document.getElementById("badge-right-hand");
      const badgeLeft = document.getElementById("badge-left-hand");

      if (results && results.landmarks && results.landmarks.length > 0) {
        for (let i = 0; i < results.landmarks.length; i++) {
          const lms = results.landmarks[i];
          const handedness =
            results.handednesses && results.handednesses[i] && results.handednesses[i][0]
              ? results.handednesses[i][0].categoryName
              : i === 0
              ? "Right"
              : "Left";

          // Note: In mirrored webcam, "Right" hand appears on screen left
          // Handedness from MediaPipe is mirror-reversed
          if (handedness === "Left" || (results.landmarks.length === 1 && !foundRight)) {
            // Right Hand (Flight Steering)
            foundRight = true;
            this.rightHand.lastSeen = now;
            this.rightHand.detected = true;

            // Palm center: average of wrist (0), index MCP (5), pinky MCP (17)
            const palmX = (lms[0].x + lms[5].x + lms[17].x) / 3.0;
            const palmY = (lms[0].y + lms[5].y + lms[17].y) / 3.0;

            // Mirror coordinate mapping to canvas
            const targetCanvasX = (1.0 - palmX) * 800;
            const targetCanvasY = Math.max(100, Math.min(450, palmY * 480));

            // Deadzone check
            const dx = targetCanvasX - this.rightHand.smoothX;
            const dy = targetCanvasY - this.rightHand.smoothY;

            if (Math.hypot(dx, dy) > this.rightHand.deadzone) {
              this.rightHand.smoothX += dx * this.rightHand.alpha;
              this.rightHand.smoothY += dy * this.rightHand.alpha;
            }

            if (badgeRight) {
              badgeRight.className = "status-badge tracked";
              badgeRight.textContent = `TRACKED (${Math.round(this.rightHand.smoothX)}, ${Math.round(this.rightHand.smoothY)})`;
            }
          }

          if (handedness === "Right" || (results.landmarks.length === 2 && foundRight)) {
            // Left Hand (Pinch Weapon Trigger)
            foundLeft = true;
            this.leftHand.lastSeen = now;
            this.leftHand.detected = true;

            // Distance between thumb tip (4) and index fingertip (8)
            const tTip = lms[4];
            const iTip = lms[8];
            const rawPinch = Math.hypot(tTip.x - iTip.x, tTip.y - iTip.y);

            // Scale normalize by distance from wrist (0) to middle MCP (9)
            const handScale = Math.hypot(lms[0].x - lms[9].x, lms[0].y - lms[9].y) || 0.2;
            const normPinch = rawPinch / handScale;
            this.leftHand.pinchDistance = normPinch;

            // Dual-threshold hysteresis
            if (!this.leftHand.isPinching && normPinch <= this.leftHand.engageThreshold) {
              this.leftHand.isPinching = true;
            } else if (this.leftHand.isPinching && normPinch >= this.leftHand.releaseThreshold) {
              this.leftHand.isPinching = false;
            }

            if (badgeLeft) {
              if (this.leftHand.isPinching) {
                badgeLeft.className = "status-badge pinching";
                badgeLeft.textContent = "PINCHING [FIRING]";
              } else {
                badgeLeft.className = "status-badge tracked";
                badgeLeft.textContent = "OPEN [READY]";
              }
            }
          }
        }
      }

      // Stale frame timeout (250ms)
      if (!foundRight && now - this.rightHand.lastSeen > 250) {
        this.rightHand.detected = false;
        if (badgeRight) {
          badgeRight.className = "status-badge lost";
          badgeRight.textContent = "LOST (HOLDING)";
        }
      }

      if (!foundLeft && now - this.leftHand.lastSeen > 250) {
        this.leftHand.detected = false;
        this.leftHand.isPinching = false;
        if (badgeLeft) {
          badgeLeft.className = "status-badge lost";
          badgeLeft.textContent = "LOST (CEASED)";
        }
      }
    },
  };

  // ==========================================================================
  // ENEMY FORMATION GENERATOR (GALAGA-INSPIRED)
  // ==========================================================================
  function spawnWaveEnemies(formationName, spawnCount) {
    enemies = [];
    const count = Math.min(20, Math.max(4, spawnCount));

    for (let i = 0; i < count; i++) {
      let baseX = 400;
      let baseY = 80;
      let glyph = "W";
      let hp = 1;
      let isElite = false;

      if (formationName === "v_formation") {
        const offset = Math.floor(i / 2) + 1;
        const side = i % 2 === 0 ? -1 : 1;
        baseX = 400 + side * offset * 60;
        baseY = 60 + offset * 32;
        if (i === 0) {
          baseX = 400;
          baseY = 50;
          isElite = true;
          glyph = "X";
          hp = 2;
        }
      } else if (formationName === "converging_pincer" || formationName === "split_formation") {
        const isLeft = i % 2 === 0;
        const row = Math.floor(i / 2);
        baseX = isLeft ? 160 + (i % 3) * 50 : 640 - (i % 3) * 50;
        baseY = 60 + row * 40;
        if (row === 0) {
          isElite = true;
          glyph = "X";
          hp = 2;
        }
      } else if (formationName === "left_flank") {
        baseX = 140 + (i % 4) * 65;
        baseY = 60 + Math.floor(i / 4) * 45;
        if (i === 0 || i === 3) { isElite = true; glyph = "X"; hp = 2; }
      } else if (formationName === "right_flank") {
        baseX = 460 + (i % 4) * 65;
        baseY = 60 + Math.floor(i / 4) * 45;
        if (i === 0 || i === 3) { isElite = true; glyph = "X"; hp = 2; }
      } else {
        // Standard echelon / center sweep
        const cols = 6;
        const col = i % cols;
        const row = Math.floor(i / cols);
        baseX = 220 + col * 70;
        baseY = 60 + row * 40;
        if (row === 0 && (col === 2 || col === 3)) {
          isElite = true;
          glyph = "X";
          hp = 2;
        }
      }

      enemies.push({
        x: baseX,
        y: baseY,
        baseX: baseX,
        baseY: baseY,
        glyph: glyph,
        hp: hp,
        maxHp: hp,
        isElite: isElite,
        width: 24,
        height: 20,
        phase: Math.random() * Math.PI * 2,
        isDiving: false,
        diveAngle: 0,
        diveProgress: 0,
        lastFireTime: performance.now() + Math.random() * 3000,
        alive: true,
      });
    }

    // Spawn Obstacles if specified by strategy
    obstacles = [];
    if (state.strategy.obstacle === "drifting_asteroids") {
      for (let j = 0; j < 3; j++) {
        obstacles.push({
          x: 100 + Math.random() * 600,
          y: -40 - j * 160,
          vy: 80.0 + Math.random() * 40.0,
          radius: 18,
          glyph: "#",
          hp: 3,
        });
      }
    } else if (state.strategy.obstacle === "slow_moving_barriers") {
      obstacles.push({
        x: 200,
        y: 180,
        vx: 60,
        radius: 22,
        glyph: "[===]",
        hp: 6,
      });
    }
  }

  // ==========================================================================
  // FASTAPI BACKEND CLIENT
  // ==========================================================================
  async function fetchHealthDiagnostics() {
    const dot = document.getElementById("ai-status-dot");
    const label = document.getElementById("ai-status-label");
    const hudModel = document.getElementById("hud-model-tag");

    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();

      if (data.inference_reachable) {
        dot.className = "live-dot pulse";
        label.textContent = `AI: ${data.configured_model} (ONLINE)`;
        if (hudModel) hudModel.textContent = data.configured_model;
      } else {
        dot.className = "live-dot offline";
        label.textContent = "AI: FALLBACK ACTIVE";
        if (hudModel) hudModel.textContent = "DETERMINISTIC FALLBACK";
      }
    } catch (err) {
      dot.className = "live-dot offline";
      label.textContent = "AI: OFFLINE (FALLBACK READY)";
      if (hudModel) hudModel.textContent = "DETERMINISTIC FALLBACK";
    }
  }

  async function requestNextWaveStrategy(upcomingWave) {
    const totalShots = Math.max(1, state.telemetry.shotsFired);
    const accuracy = state.telemetry.shotsHit / totalShots;

    const totalZoneSamples = Math.max(
      1,
      state.telemetry.leftZoneTicks + state.telemetry.centerZoneTicks + state.telemetry.rightZoneTicks
    );

    const payload = {
      wave: upcomingWave,
      shots_fired: state.telemetry.shotsFired,
      shots_hit: state.telemetry.shotsHit,
      accuracy: accuracy,
      movement_distribution: {
        left: state.telemetry.leftZoneTicks / totalZoneSamples,
        center: state.telemetry.centerZoneTicks / totalZoneSamples,
        right: state.telemetry.rightZoneTicks / totalZoneSamples,
      },
      camping_ratio: state.telemetry.stationaryTicks / Math.max(1, state.telemetry.totalTicks),
      dodges: state.telemetry.dodges,
      lives_lost: state.telemetry.livesLost,
      current_difficulty: state.strategy.difficulty,
    };

    appendTacticalLog(
      `Dispatched wave ${upcomingWave} telemetry to AI Tactical Director (acc=${(accuracy * 100).toFixed(0)}%, dodges=${state.telemetry.dodges})...`
    );

    try {
      const res = await fetch("/api/strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("HTTP " + res.status);
      const strat = await res.json();

      state.strategy = strat;
      state.telemetry.appliedStrategies.push(strat);

      document.getElementById("hud-formation").textContent = strat.formation.toUpperCase();
      document.getElementById("hud-obstacle").textContent = strat.obstacle.toUpperCase();
      document.getElementById("hud-latency").textContent = `${strat.latency_ms} ms`;
      document.getElementById("hud-source").textContent = strat.is_fallback
        ? "DETERMINISTIC FALLBACK"
        : strat.source.toUpperCase();

      appendTacticalLog(
        `[${strat.source.toUpperCase()}] Plan validated: Formation=${strat.formation}, Spawns=${strat.spawn_count}, Hazard=${strat.obstacle}. Rationale: "${strat.reason}"`
      );
    } catch (err) {
      // Deterministic client fallback
      state.strategy.formation = upcomingWave % 2 === 0 ? "converging_pincer" : "v_formation";
      state.strategy.spawn_count = Math.min(16, 6 + upcomingWave * 2);
      state.strategy.projectile_speed = 220 + upcomingWave * 25;
      state.strategy.is_fallback = true;

      appendTacticalLog(
        `[FALLBACK] Local tactical rule applied for wave ${upcomingWave}: ${state.strategy.formation.toUpperCase()}.`
      );
    }
  }

  async function submitMatchDebrief() {
    const totalShots = Math.max(1, state.telemetry.shotsFired);
    const accuracy = state.telemetry.shotsHit / totalShots;
    const totalZoneSamples = Math.max(
      1,
      state.telemetry.leftZoneTicks + state.telemetry.centerZoneTicks + state.telemetry.rightZoneTicks
    );

    const payload = {
      match_id: `stf-web-${Date.now().toString(36)}`,
      total_score: state.score,
      waves_completed: Math.max(0, state.wave - 1),
      survival_seconds: state.survivalSeconds,
      enemies_destroyed: state.telemetry.shotsHit,
      shots_fired: state.telemetry.shotsFired,
      shots_hit: state.telemetry.shotsHit,
      accuracy: accuracy,
      dodges: state.telemetry.dodges,
      lives_lost: state.telemetry.livesLost,
      movement_distribution: {
        left: state.telemetry.leftZoneTicks / totalZoneSamples,
        center: state.telemetry.centerZoneTicks / totalZoneSamples,
        right: state.telemetry.rightZoneTicks / totalZoneSamples,
      },
      camping_ratio: state.telemetry.stationaryTicks / Math.max(1, state.telemetry.totalTicks),
      strategies_applied: state.telemetry.appliedStrategies,
    };

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("HTTP " + res.status);
      const debrief = await res.json();
      populateDebriefModal(debrief);
    } catch (err) {
      // Fallback local report population
      populateDebriefModal({
        match_id: payload.match_id,
        total_score: payload.total_score,
        waves_completed: payload.waves_completed,
        survival_seconds: payload.survival_seconds,
        accuracy: payload.accuracy,
        dodges: payload.dodges,
        profile: {
          playstyle_tag: accuracy > 0.6 ? "Precision Marksman" : "Dynamic Scout",
          observed_weakness: "Lateral quadrant positioning biased during pincer formations.",
        },
        next_mission: {
          title: "Acrobatic Threat Evasion",
          rationale: "Increase active threat dodges and center-lane coverage on upcoming waves.",
          measurement_description: `Achieve at least ${payload.dodges + 5} close-proximity projectile dodges.`,
        },
      });
    }
  }

  function populateDebriefModal(data) {
    document.getElementById("debrief-meta-line").textContent = `MATCH ID: ${data.match_id} • SURVIVAL: ${data.survival_seconds.toFixed(1)}s`;
    document.getElementById("deb-score").textContent = data.total_score.toLocaleString();
    document.getElementById("deb-waves").textContent = data.waves_completed;
    document.getElementById("deb-accuracy").textContent = `${(data.accuracy * 100).toFixed(1)}%`;
    document.getElementById("deb-dodges").textContent = data.dodges;

    const prof = data.profile || {};
    document.getElementById("deb-profile-summary").innerHTML = `
      <strong>Classification:</strong> <span style="color:var(--accent-cyan); font-weight:700;">${prof.playstyle_tag || "Cadet Pilot"}</span><br>
      <strong>Tactical Weakness:</strong> ${prof.observed_weakness || "None observed."}
    `;

    const miss = data.next_mission || {};
    document.getElementById("deb-next-mission").innerHTML = `
      <strong>${miss.title || "Combat Calisthenics"}</strong> &mdash; ${miss.rationale || "Maintain active tactical maneuvering."}<br>
      <span style="color:var(--accent-yellow); font-weight:700;">Target Goal:</span> ${miss.measurement_description || "Clear 3 waves with > 50% accuracy."}
    `;
  }

  function appendTacticalLog(text) {
    const box = document.getElementById("tacticalLogBox");
    if (!box) return;
    const now = new Date().toTimeString().substring(3, 8);
    const div = document.createElement("div");
    div.className = "log-entry";
    div.innerHTML = `<span class="log-time">[${now}]</span> <span class="log-tag">[TAC]</span> ${text}`;
    box.prepend(div);
  }

  // ==========================================================================
  // GAME ENGINE SIMULATION
  // ==========================================================================
  function resetGame() {
    state.score = 0;
    state.lives = 3;
    state.wave = 1;
    state.matchStartTime = performance.now();
    state.survivalSeconds = 0;
    state.inIntermission = false;
    state.telemetry = {
      shotsFired: 0,
      shotsHit: 0,
      dodges: 0,
      livesLost: 0,
      positionSamples: 0,
      leftZoneTicks: 0,
      centerZoneTicks: 0,
      rightZoneTicks: 0,
      stationaryTicks: 0,
      totalTicks: 0,
      appliedStrategies: [],
    };

    player.x = 400;
    player.y = 420;
    player.targetX = 400;
    player.targetY = 420;
    player.invulnerableTimer = 1.0;

    playerLasers = [];
    enemyProjectiles = [];
    particles = [];
    floatingTexts = [];

    spawnWaveEnemies("v_formation", 8);
    updateHUD();
  }

  function updateHUD() {
    document.getElementById("hud-score").textContent = `${state.score.toLocaleString()} PTS`;
    const acc = state.telemetry.shotsFired > 0 ? (state.telemetry.shotsHit / state.telemetry.shotsFired) * 100 : 0;
    document.getElementById("hud-accuracy").textContent = `${acc.toFixed(1)}%`;
    document.getElementById("hud-dodges").textContent = state.telemetry.dodges;

    const livesStr = Array(Math.max(0, state.lives)).fill("◆").join(" ") || "EMPTY";
    document.getElementById("hud-lives").textContent = livesStr;

    const mins = Math.floor(state.survivalSeconds / 60);
    const secs = Math.floor(state.survivalSeconds % 60);
    document.getElementById("hud-time").textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    document.getElementById("footer-wave-status").textContent = `WAVE 0${state.wave} IN PROGRESS`;
  }

  function updateSimulation(dt) {
    if (state.mode !== "PLAYING") return;

    state.survivalSeconds = (performance.now() - state.matchStartTime) / 1000;
    state.telemetry.totalTicks++;

    // Track spatial quadrant and camping
    if (player.x < 266) state.telemetry.leftZoneTicks++;
    else if (player.x > 533) state.telemetry.rightZoneTicks++;
    else state.telemetry.centerZoneTicks++;

    // Stars scrolling
    for (const s of stars) {
      s.y += s.speed * (dt * 60);
      if (s.y > 480) {
        s.y = 0;
        s.x = Math.random() * 800;
      }
    }

    // 1. Process Input into Player Motion
    let moveX = 0;
    let moveY = 0;

    if (state.controlMode === "gesture" && gestureController.rightHand.detected) {
      // Gesture movement (smoothed coordinates)
      const targetX = gestureController.rightHand.smoothX;
      const targetY = gestureController.rightHand.smoothY;
      player.x += (targetX - player.x) * 0.22;
      player.y += (targetY - player.y) * 0.22;
    } else {
      // Keyboard movement
      if (keys.left) moveX -= 1;
      if (keys.right) moveX += 1;
      if (keys.up) moveY -= 1;
      if (keys.down) moveY += 1;

      if (moveX === 0 && moveY === 0) {
        state.telemetry.stationaryTicks++;
      }

      player.x += moveX * player.speed * dt;
      player.y += moveY * player.speed * dt;
    }

    // Playfield bounds clamping
    player.x = Math.max(20, Math.min(780, player.x));
    player.y = Math.max(100, Math.min(460, player.y));

    // Player Weapon Firing
    const isFiring =
      keys.fire ||
      (state.controlMode === "gesture" &&
        gestureController.leftHand.detected &&
        gestureController.leftHand.isPinching);

    const now = performance.now();
    if (isFiring && now - player.lastShotTime >= player.shotCooldownMs) {
      player.lastShotTime = now;
      playerLasers.push({
        x: player.x,
        y: player.y - 14,
        vy: -680.0,
        active: true,
      });
      state.telemetry.shotsFired++;
      sfx.playLaser();
    }

    if (player.invulnerableTimer > 0) {
      player.invulnerableTimer -= dt;
    }

    // 2. Update Player Lasers & Collision with Enemies / Obstacles
    for (const laser of playerLasers) {
      laser.y += laser.vy * dt;
      if (laser.y < 5) laser.active = false;

      // Check hits against enemies
      for (const enemy of enemies) {
        if (!enemy.alive) continue;
        const dx = Math.abs(laser.x - enemy.x);
        const dy = Math.abs(laser.y - enemy.y);
        if (dx < 16 && dy < 14) {
          laser.active = false;
          enemy.hp -= 1;
          state.telemetry.shotsHit++;
          spawnSparkParticles(enemy.x, enemy.y, "#00e5ff", 6);

          if (enemy.hp <= 0) {
            enemy.alive = false;
            const points = enemy.isElite ? 250 : 100;
            state.score += points;
            spawnExplosionParticles(enemy.x, enemy.y);
            sfx.playExplosion();
            floatingTexts.push({
              text: `+${points}`,
              x: enemy.x,
              y: enemy.y - 10,
              life: 1.0,
              color: enemy.isElite ? "#ff2a4b" : "#ffb700",
            });
          }
          break;
        }
      }

      // Check hits against obstacles
      for (const obs of obstacles) {
        if (obs.hp <= 0) continue;
        const dist = Math.hypot(laser.x - obs.x, laser.y - obs.y);
        if (dist < obs.radius) {
          laser.active = false;
          obs.hp -= 1;
          spawnSparkParticles(laser.x, laser.y, "#ffb700", 5);
          if (obs.hp <= 0) {
            state.score += 50;
            spawnExplosionParticles(obs.x, obs.y);
          }
          break;
        }
      }
    }
    playerLasers = playerLasers.filter((l) => l.active);

    // 3. Update Enemies (Breathing formation + Dive bombing attacks)
    const timeSec = now / 1000;
    let anyAlive = false;

    for (const enemy of enemies) {
      if (!enemy.alive) continue;
      anyAlive = true;

      if (!enemy.isDiving) {
        // Formation oscillation
        enemy.x = enemy.baseX + Math.sin(timeSec * 2.0 + enemy.phase) * 35;
        enemy.y = enemy.baseY + Math.cos(timeSec * 1.0 + enemy.phase) * 10;

        // Occasional dive bomb trigger
        if (Math.random() < 0.0015 && enemy.isElite) {
          enemy.isDiving = true;
          enemy.diveProgress = 0;
        }
      } else {
        // Swoop motion
        enemy.diveProgress += dt * 0.9;
        enemy.y += 180.0 * dt;
        enemy.x += Math.sin(enemy.diveProgress * Math.PI * 2) * 80.0 * dt;

        if (enemy.y > 490) {
          enemy.y = -20;
          enemy.isDiving = false;
        }
      }

      // Enemy fire projectile
      if (now - enemy.lastFireTime > 2600 + Math.random() * 2000) {
        enemy.lastFireTime = now;
        enemyProjectiles.push({
          x: enemy.x,
          y: enemy.y + 12,
          vx: (player.x - enemy.x) * 0.25,
          vy: state.strategy.projectile_speed || 240.0,
          active: true,
        });
      }
    }

    // 4. Update Enemy Projectiles & Player Collisions / Dodges
    for (const p of enemyProjectiles) {
      p.x += (p.vx || 0) * dt;
      p.y += p.vy * dt;

      if (p.y > 490 || p.x < 0 || p.x > 800) {
        p.active = false;
      }

      const distToPlayer = Math.hypot(p.x - player.x, p.y - player.y);

      // Successful Dodge Detection (proximity <= 42px without collision)
      if (distToPlayer <= 42 && distToPlayer > 16 && !p.dodgedLogged && p.y > player.y - 10) {
        p.dodgedLogged = true;
        state.telemetry.dodges++;
        state.score += 25;
        floatingTexts.push({
          text: "DODGE! +25",
          x: player.x,
          y: player.y - 25,
          life: 0.8,
          color: "#00ff66",
        });
      }

      // Player Damage Hit Detection
      if (distToPlayer < 16 && player.invulnerableTimer <= 0) {
        p.active = false;
        player.invulnerableTimer = 2.0; // 2 seconds invulnerability
        state.lives -= 1;
        state.telemetry.livesLost++;
        sfx.playHit();
        spawnExplosionParticles(player.x, player.y);

        if (state.lives <= 0) {
          triggerGameOver();
          return;
        }
      }
    }
    enemyProjectiles = enemyProjectiles.filter((p) => p.active);

    // 5. Update Obstacles
    for (const obs of obstacles) {
      if (obs.hp <= 0) continue;
      obs.y += (obs.vy || 0) * dt;
      obs.x += (obs.vx || 0) * dt;

      if (obs.x < 100 || obs.x > 700) obs.vx = -obs.vx;
      if (obs.y > 500) obs.y = -60;

      // Obstacle vs Player collision
      const dist = Math.hypot(player.x - obs.x, player.y - obs.y);
      if (dist < obs.radius + 12 && player.invulnerableTimer <= 0) {
        player.invulnerableTimer = 2.0;
        state.lives -= 1;
        state.telemetry.livesLost++;
        sfx.playHit();
        if (state.lives <= 0) {
          triggerGameOver();
          return;
        }
      }
    }

    // 6. Check Wave Progression
    if (!anyAlive && !state.inIntermission) {
      state.inIntermission = true;
      state.intermissionTimer = 2.2;
      sfx.playWaveClear();
      floatingTexts.push({
        text: `WAVE 0${state.wave} CLEARED!`,
        x: 400,
        y: 220,
        life: 2.0,
        color: "#00e5ff",
      });

      // Request next wave plan from FastAPI
      requestNextWaveStrategy(state.wave + 1);
    }

    if (state.inIntermission) {
      state.intermissionTimer -= dt;
      if (state.intermissionTimer <= 0) {
        state.inIntermission = false;
        state.wave += 1;
        spawnWaveEnemies(state.strategy.formation, state.strategy.spawn_count);
      }
    }

    // 7. Update Particles & Floating Texts
    for (const p of particles) {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt;
    }
    particles = particles.filter((p) => p.life > 0);

    for (const ft of floatingTexts) {
      ft.y -= 25.0 * dt;
      ft.life -= dt;
    }
    floatingTexts = floatingTexts.filter((ft) => ft.life > 0);

    updateHUD();
  }

  function spawnSparkParticles(x, y, color, count) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 60 + Math.random() * 120;
      particles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 0.25 + Math.random() * 0.25,
        color,
        glyph: "*",
      });
    }
  }

  function spawnExplosionParticles(x, y) {
    const glyphs = ["#", "*", "x", "·"];
    for (let i = 0; i < 16; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 40 + Math.random() * 180;
      particles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 0.4 + Math.random() * 0.4,
        color: Math.random() > 0.5 ? "#ff2a4b" : "#ffb700",
        glyph: glyphs[Math.floor(Math.random() * glyphs.length)],
      });
    }
  }

  function triggerGameOver() {
    state.mode = "GAME_OVER";
    sfx.playHit();

    document.getElementById("gameOverOverlay").classList.remove("hidden");
    const acc = state.telemetry.shotsFired > 0 ? (state.telemetry.shotsHit / state.telemetry.shotsFired) * 100 : 0;
    document.getElementById("game-over-summary").textContent = `Final Score: ${state.score.toLocaleString()} • Waves Cleared: ${Math.max(
      0,
      state.wave - 1
    )} • Accuracy: ${acc.toFixed(1)}% • Dodges: ${state.telemetry.dodges}`;

    // Submit match debrief to FastAPI
    submitMatchDebrief();
  }

  // ==========================================================================
  // TEXTMODE RENDERING SYSTEM
  // ==========================================================================
  function render() {
    // Clear screen
    ctx.fillStyle = "#070707";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.font = "14px 'JetBrains Mono', monospace";
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";

    // 1. Draw Starfield
    for (const s of stars) {
      ctx.fillStyle = s.color;
      ctx.fillText(s.glyph, s.x, s.y);
    }

    // 2. Draw Obstacles
    for (const obs of obstacles) {
      if (obs.hp <= 0) continue;
      ctx.fillStyle = "#ffb700";
      ctx.fillText(obs.glyph, obs.x, obs.y);
    }

    // 3. Draw Enemy Projectiles
    ctx.fillStyle = "#ff2a4b";
    for (const p of enemyProjectiles) {
      ctx.fillText("!", p.x, p.y);
    }

    // 4. Draw Player Lasers
    ctx.fillStyle = "#00e5ff";
    for (const l of playerLasers) {
      ctx.fillText("|", l.x, l.y);
    }

    // 5. Draw Enemies
    for (const enemy of enemies) {
      if (!enemy.alive) continue;
      ctx.fillStyle = enemy.isElite ? "#ff2a4b" : "#ffb700";
      ctx.fillText(enemy.glyph, enemy.x, enemy.y);
    }

    // 6. Draw Player Spacecraft
    if (state.mode === "PLAYING" || state.mode === "PAUSED") {
      // Blinking if invulnerable
      const isVisible = player.invulnerableTimer <= 0 || Math.floor(performance.now() / 120) % 2 === 0;
      if (isVisible) {
        ctx.fillStyle = "#00e5ff";
        ctx.fillText("/\\", player.x, player.y - 6);
        ctx.fillText("<^^>", player.x, player.y + 6);
      }
    }

    // 7. Draw Particles
    for (const p of particles) {
      ctx.fillStyle = p.color;
      ctx.fillText(p.glyph, p.x, p.y);
    }

    // 8. Draw Floating Score / Text Popups
    for (const ft of floatingTexts) {
      ctx.fillStyle = ft.color;
      ctx.fillText(ft.text, ft.x, ft.y);
    }
  }

  // ==========================================================================
  // MAIN ANIMATION LOOP
  // ==========================================================================
  function tick(timestamp) {
    const dt = Math.min((timestamp - state.lastTime) / 1000, 0.1);
    state.lastTime = timestamp;

    updateSimulation(dt);
    render();

    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // ==========================================================================
  // EVENT LISTENERS & USER CONTROLS
  // ==========================================================================
  // Keyboard Listeners
  window.addEventListener("keydown", (e) => {
    if (e.code === "ArrowLeft" || e.code === "KeyA") keys.left = true;
    if (e.code === "ArrowRight" || e.code === "KeyD") keys.right = true;
    if (e.code === "ArrowUp" || e.code === "KeyW") keys.up = true;
    if (e.code === "ArrowDown" || e.code === "KeyS") keys.down = true;
    if (e.code === "Space") {
      keys.fire = true;
      e.preventDefault();
    }
    if (e.code === "KeyP") togglePause();
    if (e.code === "KeyR" && (state.mode === "GAME_OVER" || state.mode === "PAUSED")) {
      startGame();
    }
  });

  window.addEventListener("keyup", (e) => {
    if (e.code === "ArrowLeft" || e.code === "KeyA") keys.left = false;
    if (e.code === "ArrowRight" || e.code === "KeyD") keys.right = false;
    if (e.code === "ArrowUp" || e.code === "KeyW") keys.up = false;
    if (e.code === "ArrowDown" || e.code === "KeyS") keys.down = false;
    if (e.code === "Space") keys.fire = false;
  });

  function togglePause() {
    if (state.mode === "PLAYING") {
      state.mode = "PAUSED";
      document.getElementById("pauseOverlay").classList.remove("hidden");
    } else if (state.mode === "PAUSED") {
      state.mode = "PLAYING";
      document.getElementById("pauseOverlay").classList.add("hidden");
    }
  }

  function startGame() {
    document.getElementById("startOverlay").classList.add("hidden");
    document.getElementById("pauseOverlay").classList.add("hidden");
    document.getElementById("gameOverOverlay").classList.add("hidden");
    document.getElementById("debriefModal").classList.add("hidden");

    resetGame();
    state.mode = "PLAYING";
  }

  // Button Listeners
  document.getElementById("btn-start-game")?.addEventListener("click", startGame);
  document.getElementById("btn-header-play")?.addEventListener("click", () => {
    if (state.mode === "START" || state.mode === "GAME_OVER") startGame();
  });
  document.getElementById("btn-resume-game")?.addEventListener("click", togglePause);
  document.getElementById("btn-restart-game")?.addEventListener("click", startGame);
  document.getElementById("btn-retry-game")?.addEventListener("click", startGame);
  document.getElementById("btn-pause-toggle")?.addEventListener("click", togglePause);

  // Debrief Modal Listeners
  document.getElementById("btn-show-debrief")?.addEventListener("click", () => {
    document.getElementById("debriefModal").classList.remove("hidden");
  });
  document.getElementById("btn-close-debrief")?.addEventListener("click", () => {
    document.getElementById("debriefModal").classList.add("hidden");
  });

  // Mode Selection (Keyboard vs Gesture)
  function setControlMode(mode) {
    state.controlMode = mode;
    document.getElementById("active-ctrl-badge").textContent = mode.toUpperCase();
    document.getElementById("footer-control-mode").textContent = `CONTROL: ${mode.toUpperCase()} ACTIVE`;

    const btnKey = document.getElementById("tab-ctrl-keyboard");
    const btnGest = document.getElementById("tab-ctrl-gesture");
    const btnSelectKey = document.getElementById("btn-select-keyboard");
    const btnSelectGest = document.getElementById("btn-select-gesture");
    const hint = document.getElementById("ctrl-hint-text");

    if (mode === "gesture") {
      btnKey?.classList.remove("active");
      btnGest?.classList.add("active");
      btnSelectKey?.classList.remove("active");
      btnSelectGest?.classList.add("active");
      if (hint) {
        hint.textContent =
          "Two-hand vision steering active. Right hand moves ship position; Left thumb-index pinch triggers weapon.";
      }
      gestureController.init();
    } else {
      btnGest?.classList.remove("active");
      btnKey?.classList.add("active");
      btnSelectGest?.classList.remove("active");
      btnSelectKey?.classList.add("active");
      if (hint) {
        hint.textContent =
          "Standard arcade navigation. Arrow keys or WASD for precise lateral thrusters; Spacebar to fire cannon bursts.";
      }
    }
  }

  document.getElementById("tab-ctrl-keyboard")?.addEventListener("click", () => setControlMode("keyboard"));
  document.getElementById("tab-ctrl-gesture")?.addEventListener("click", () => {
    setControlMode("gesture");
    document.getElementById("calibrationModal").classList.remove("hidden");
  });
  document.getElementById("btn-select-keyboard")?.addEventListener("click", () => setControlMode("keyboard"));
  document.getElementById("btn-select-gesture")?.addEventListener("click", () => {
    setControlMode("gesture");
    document.getElementById("calibrationModal").classList.remove("hidden");
  });

  // Calibration Modal Triggers
  document.getElementById("btn-open-calibration")?.addEventListener("click", () => {
    document.getElementById("calibrationModal").classList.remove("hidden");
    gestureController.init();
  });
  document.getElementById("btn-launch-calib-side")?.addEventListener("click", () => {
    document.getElementById("calibrationModal").classList.remove("hidden");
    gestureController.init();
  });
  document.getElementById("btn-close-calib")?.addEventListener("click", () => {
    document.getElementById("calibrationModal").classList.add("hidden");
  });
  document.getElementById("btn-skip-to-keyboard")?.addEventListener("click", () => {
    setControlMode("keyboard");
    document.getElementById("calibrationModal").classList.add("hidden");
  });
  document.getElementById("btn-confirm-gesture")?.addEventListener("click", () => {
    setControlMode("gesture");
    document.getElementById("calibrationModal").classList.add("hidden");
    startGame();
  });

  // Scanlines Toggle
  document.getElementById("btn-toggle-scanlines")?.addEventListener("click", (e) => {
    const el = document.getElementById("scanlinesOverlay");
    const active = e.target.classList.toggle("active");
    el.style.display = active ? "block" : "none";
  });

  // Audio Toggle
  document.getElementById("btn-toggle-audio")?.addEventListener("click", (e) => {
    sfx.enabled = !sfx.enabled;
    e.target.classList.toggle("active", sfx.enabled);
    e.target.textContent = sfx.enabled ? "SFX: ON" : "SFX: OFF";
  });

  // Initial Health Probe
  fetchHealthDiagnostics();
})();
