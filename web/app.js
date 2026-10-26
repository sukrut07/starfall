/**
 * STARFALL Textmode Tactical Display & AI Commander Client Engine
 * Visual system inspired by https://extension.textmode.art/
 */

(function () {
  "use strict";

  // State
  const state = {
    density: 8,
    ramp: "classic",
    inverted: false,
    opacity: 1.0,
    contrast: 1.4,
    speed: 60,
    scanlines: true,
    glitch: false,
    bloom: true,
    colorPreset: "terminal",
    charset: "ascii",
    paused: false,
    lastFrameTime: performance.now(),
  };

  // Glyph Ramps
  const RAMPS = {
    classic: " .:-=+*#%@",
    minimal: " .·+*#",
    dense: " .,:;!|i$@#",
    braille: " ⠁⠃⠇⡇⣇⣧⣷⣿",
    cyber: " ░▒▓█",
  };

  // Color Palettes
  const PALETTES = {
    terminal: { fg: "#f0f0f0", bg: "#070707", red: "#ff2a4b", cyan: "#00e5ff", yellow: "#ffb700" },
    amber: { fg: "#ffb700", bg: "#100900", red: "#ff4400", cyan: "#ffd000", yellow: "#ffffff" },
    cyan: { fg: "#00e5ff", bg: "#001018", red: "#ff2a8d", cyan: "#ffffff", yellow: "#00ffcc" },
    arcade: { fg: "#ffffff", bg: "#050510", red: "#ff1020", cyan: "#00ffff", yellow: "#ffff00" },
  };

  // Arcade Simulation Entities
  const sim = {
    player: { x: 400, y: 420, vx: 0, targetX: 400, glyph: "^", hp: 3 },
    lasers: [],
    enemies: [],
    stars: [],
    particles: [],
    wave: 3,
    score: 4850,
    formation: "PINCER",
    lastShot: 0,
    tacticalTimer: 0,
  };

  // Init Stars
  for (let i = 0; i < 60; i++) {
    sim.stars.push({
      x: Math.random() * 800,
      y: Math.random() * 480,
      speed: 0.5 + Math.random() * 2.0,
      char: Math.random() > 0.8 ? "*" : Math.random() > 0.4 ? "." : "·",
    });
  }

  // Init Enemy Formation
  function resetEnemies() {
    sim.enemies = [];
    const types = ["drone", "elite", "drone"];
    const cols = 7;
    const rows = 3;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const isElite = r === 0 && (c === 2 || c === 4);
        sim.enemies.push({
          x: 180 + c * 70,
          y: 70 + r * 45,
          baseX: 180 + c * 70,
          baseY: 70 + r * 45,
          glyph: isElite ? "X" : r === 1 ? "M" : "W",
          hp: isElite ? 2 : 1,
          color: isElite ? "red" : "yellow",
          alive: true,
          phase: Math.random() * Math.PI * 2,
        });
      }
    }
  }
  resetEnemies();

  // Canvas References
  const canvas = document.getElementById("textmodeCanvas");
  const ctx = canvas.getContext("2d");

  // Main Simulation Loop
  function updateSimulation(dt) {
    if (state.paused) return;

    // Stars scrolling
    for (const star of sim.stars) {
      star.y += star.speed * (dt * 60);
      if (star.y > 480) {
        star.y = 0;
        star.x = Math.random() * 800;
      }
    }

    // Player smooth motion (oscillates or follows mouse if over canvas)
    const timeSec = performance.now() / 1000;
    sim.player.x += (sim.player.targetX - sim.player.x) * 0.1;
    sim.player.targetX = 400 + Math.sin(timeSec * 1.5) * 160;

    // Automatic player weapon fire
    if (performance.now() - sim.lastShot > 320) {
      sim.lasers.push({ x: sim.player.x, y: sim.player.y - 12, vy: -12, active: true });
      sim.lastShot = performance.now();
    }

    // Lasers update & collision
    for (const laser of sim.lasers) {
      laser.y += laser.vy * (dt * 60);
      if (laser.y < 10) laser.active = false;

      // Check hit against enemies
      for (const enemy of sim.enemies) {
        if (!enemy.alive) continue;
        const dx = Math.abs(laser.x - enemy.x);
        const dy = Math.abs(laser.y - enemy.y);
        if (dx < 18 && dy < 16) {
          laser.active = false;
          enemy.hp -= 1;
          // Spawn particle
          sim.particles.push({ x: enemy.x, y: enemy.y, char: "#", life: 10 });
          if (enemy.hp <= 0) {
            enemy.alive = false;
            sim.score += enemy.glyph === "X" ? 250 : 100;
            document.getElementById("feed-dodges").textContent = (parseInt(document.getElementById("feed-dodges").textContent) + 1).toString();
          }
          break;
        }
      }
    }
    sim.lasers = sim.lasers.filter((l) => l.active);

    // Enemies motion (swoop or formation breathing)
    let allDead = true;
    for (const enemy of sim.enemies) {
      if (!enemy.alive) continue;
      allDead = false;
      const t = timeSec * 2.2 + enemy.phase;
      enemy.x = enemy.baseX + Math.sin(t) * 35;
      enemy.y = enemy.baseY + Math.cos(t * 0.5) * 12;
    }

    if (allDead) {
      sim.wave += 1;
      document.getElementById("hud-wave-num").textContent = `WAVE 0${sim.wave}`;
      resetEnemies();
    }

    // Particles
    for (const p of sim.particles) {
      p.life -= 1;
    }
    sim.particles = sim.particles.filter((p) => p.life > 0);
  }

  // Render Simulation onto Textmode Glyph Grid
  function renderTextmode() {
    const pal = PALETTES[state.colorPreset] || PALETTES.terminal;
    const bg = state.inverted ? pal.fg : pal.bg;
    const fg = state.inverted ? pal.bg : pal.fg;

    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.globalAlpha = state.opacity;

    // Density grid calculation
    const cellSize = state.density;
    ctx.font = `${cellSize}px 'JetBrains Mono', monospace`;
    ctx.textBaseline = "top";
    ctx.textAlign = "left";

    // 1. Draw Starfield
    ctx.fillStyle = pal.yellow;
    for (const star of sim.stars) {
      const gx = Math.floor(star.x / cellSize) * cellSize;
      const gy = Math.floor(star.y / cellSize) * cellSize;
      ctx.fillText(star.char, gx, gy);
    }

    // 2. Draw Lasers
    ctx.fillStyle = pal.cyan;
    for (const laser of sim.lasers) {
      const gx = Math.floor(laser.x / cellSize) * cellSize;
      const gy = Math.floor(laser.y / cellSize) * cellSize;
      ctx.fillText("|", gx, gy);
    }

    // 3. Draw Enemies
    for (const enemy of sim.enemies) {
      if (!enemy.alive) continue;
      ctx.fillStyle = enemy.glyph === "X" ? pal.red : pal.yellow;
      const gx = Math.floor(enemy.x / cellSize) * cellSize;
      const gy = Math.floor(enemy.y / cellSize) * cellSize;
      ctx.fillText(enemy.glyph, gx, gy);
    }

    // 4. Draw Particles
    ctx.fillStyle = pal.red;
    for (const p of sim.particles) {
      const gx = Math.floor(p.x / cellSize) * cellSize;
      const gy = Math.floor(p.y / cellSize) * cellSize;
      ctx.fillText(p.char, gx, gy);
    }

    // 5. Draw Player Ship
    ctx.fillStyle = pal.cyan;
    const px = Math.floor(sim.player.x / cellSize) * cellSize;
    const py = Math.floor(sim.player.y / cellSize) * cellSize;
    ctx.fillText("/\\", px - cellSize, py);
    ctx.fillText("^^", px - cellSize, py + cellSize);

    // Glitch jitter FX
    if (state.glitch && Math.random() > 0.88) {
      const sliceY = Math.random() * 400;
      const sliceH = 20 + Math.random() * 30;
      const imgData = ctx.getImageData(0, sliceY, 800, sliceH);
      ctx.putImageData(imgData, (Math.random() - 0.5) * 16, sliceY);
    }

    ctx.globalAlpha = 1.0;
  }

  // Animation Frame Driver
  function tick(timestamp) {
    const dt = Math.min((timestamp - state.lastFrameTime) / 1000, 0.1);
    state.lastFrameTime = timestamp;

    updateSimulation(dt);
    renderTextmode();

    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // Mouse Interaction with Canvas
  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    sim.player.targetX = (e.clientX - rect.left) * scaleX;
  });

  // UI Event Handlers
  // Density Buttons
  document.querySelectorAll(".btn-density[data-density]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-density[data-density]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.density = parseInt(btn.dataset.density, 10);
    });
  });

  // Glyph Ramps
  document.getElementById("btn-ramp-classic")?.addEventListener("click", (e) => {
    setRamp("classic", e.target);
  });
  document.getElementById("btn-ramp-minimal")?.addEventListener("click", (e) => {
    setRamp("minimal", e.target);
  });
  document.getElementById("btn-ramp-dense")?.addEventListener("click", (e) => {
    setRamp("dense", e.target);
  });

  function setRamp(rampKey, btn) {
    document.querySelectorAll("#btn-ramp-classic, #btn-ramp-minimal, #btn-ramp-dense").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.ramp = rampKey;
  }

  // Invert Button
  document.getElementById("btn-invert-toggle")?.addEventListener("click", (e) => {
    state.inverted = !state.inverted;
    e.target.classList.toggle("active", state.inverted);
  });

  // Tab Switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.dataset.tab;
      document.getElementById(targetId)?.classList.add("active");
    });
  });

  // Sliders
  const opacitySlider = document.getElementById("slider-opacity");
  opacitySlider?.addEventListener("input", (e) => {
    state.opacity = parseInt(e.target.value, 10) / 100;
    document.getElementById("opacity-val").textContent = `${e.target.value}%`;
  });

  const contrastSlider = document.getElementById("slider-contrast");
  contrastSlider?.addEventListener("input", (e) => {
    state.contrast = parseInt(e.target.value, 10) / 100;
    document.getElementById("contrast-val").textContent = `${state.contrast.toFixed(1)}x`;
  });

  // Toggle Overlay Button
  document.getElementById("toggle-overlay")?.addEventListener("click", (e) => {
    const btn = e.target;
    btn.classList.toggle("active");
    const active = btn.classList.contains("active");
    btn.textContent = active ? "ON" : "OFF";
    canvas.style.display = active ? "block" : "none";
  });

  // FX Toggles
  document.getElementById("toggle-scanlines")?.addEventListener("click", (e) => {
    const active = toggleBtn(e.target);
    document.querySelector(".scanlines").style.display = active ? "block" : "none";
  });

  document.getElementById("toggle-glitch")?.addEventListener("click", (e) => {
    state.glitch = toggleBtn(e.target);
  });

  function toggleBtn(btn) {
    btn.classList.toggle("active");
    const active = btn.classList.contains("active");
    btn.textContent = active ? "ON" : "OFF";
    return active;
  }

  // Color Palettes
  document.querySelectorAll("#pal-terminal, #pal-amber, #pal-cyan, #pal-arcade").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pal-terminal, #pal-amber, #pal-cyan, #pal-arcade").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      if (btn.id === "pal-terminal") state.colorPreset = "terminal";
      if (btn.id === "pal-amber") state.colorPreset = "amber";
      if (btn.id === "pal-cyan") state.colorPreset = "cyan";
      if (btn.id === "pal-arcade") state.colorPreset = "arcade";
    });
  });

  // Play / Pause / Reset
  document.getElementById("btn-pause-sim")?.addEventListener("click", (e) => {
    state.paused = !state.paused;
    e.target.textContent = state.paused ? "RESUME" : "PAUSE";
  });

  document.getElementById("btn-reset-sim")?.addEventListener("click", () => {
    sim.score = 0;
    sim.wave = 1;
    document.getElementById("hud-wave-num").textContent = "WAVE 01";
    resetEnemies();
  });

  // -------------------------------------------------------------
  // REST API INTEGRATION
  // -------------------------------------------------------------

  // Load Status
  async function fetchStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error("Status check failed");
      const data = await res.json();

      // Update Ollama & Model Information
      const circle = document.getElementById("ollama-status-circle");
      const title = document.getElementById("ollama-status-title");
      const detail = document.getElementById("ollama-status-detail");
      const endpoint = document.getElementById("cfg-endpoint");
      const activeModel = document.getElementById("cfg-active-model");
      const installedTags = document.getElementById("cfg-installed-tags");
      const hudModel = document.getElementById("hud-model-name");

      if (data.ai.ollama_online) {
        circle.className = "status-circle online";
        title.textContent = "OLLAMA RUNNING (ONLINE)";
        detail.textContent = `Connected to ${data.ai.endpoint}. Available models: ${data.ai.installed_models.join(", ") || "None"}`;
      } else {
        circle.className = "status-circle offline";
        title.textContent = "OLLAMA OFFLINE (FALLBACK READY)";
        detail.textContent = data.ai.ollama_message || "Service not responding at localhost:11434";
      }

      endpoint.textContent = data.ai.endpoint;
      activeModel.textContent = data.ai.primary_model;
      hudModel.textContent = data.ai.primary_model;
      installedTags.textContent = data.ai.installed_models.length ? data.ai.installed_models.join(", ") : "None detected";

      // Select matching option if present
      const sel = document.getElementById("select-model");
      if (sel) sel.value = data.ai.primary_model;
    } catch (err) {
      const circle = document.getElementById("ollama-status-circle");
      const title = document.getElementById("ollama-status-title");
      circle.className = "status-circle offline";
      title.textContent = "OFFLINE OR LOCAL SERVER ONLY";
    }
  }

  // Load Matches Table
  async function fetchMatches() {
    try {
      const res = await fetch("/api/matches");
      if (!res.ok) return;
      const data = await res.json();
      const tbody = document.getElementById("matches-tbody");
      if (!tbody) return;

      if (!data.matches || data.matches.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center loading-row">No recorded matches found in starfall.db yet. Play a match to log debriefs!</td></tr>`;
        return;
      }

      tbody.innerHTML = data.matches
        .map(
          (m) => `
        <tr>
          <td style="color:var(--accent-cyan);">${m.match_id}</td>
          <td style="color:var(--text-dim);">${m.started_at ? m.started_at.substring(0, 19).replace("T", " ") : "-"}</td>
          <td class="text-right" style="color:var(--accent-green); font-weight:700;">${m.total_score ? m.total_score.toLocaleString() : 0}</td>
          <td class="text-center">${m.waves_completed}</td>
          <td class="text-right">${(m.accuracy * 100).toFixed(1)}%</td>
          <td class="text-right">${m.dodges}</td>
          <td class="text-right">${m.survival_seconds ? m.survival_seconds.toFixed(1) + "s" : "-"}</td>
        </tr>
      `
        )
        .join("");
    } catch (err) {
      console.error("Failed to load match history:", err);
    }
  }

  // Load Last Report
  async function fetchLastReport() {
    try {
      const res = await fetch("/api/match/last");
      if (!res.ok) return;
      const data = await res.json();
      const reportBox = document.getElementById("report-content-body");
      if (!reportBox) return;

      if (!data.report) {
        reportBox.innerHTML = `<div class="report-loading">No saved match reports found in database yet. Play a match to generate an autonomous post-game debrief.</div>`;
        return;
      }

      const r = data.report;
      reportBox.innerHTML = `
        <div class="report-section">
          <div class="report-section-title">[MATCH ID: ${r.match_id}] &bull; SCORE: ${r.total_score.toLocaleString()} &bull; SURVIVAL: ${r.survival_seconds.toFixed(1)}s</div>
          <p><strong>Observed Facts:</strong> Kills: ${r.metrics.kills} | Shots: ${r.metrics.shots_fired} | Accuracy: ${(r.metrics.accuracy * 100).toFixed(1)}% | Dodges: ${r.metrics.dodges} | Hits Taken: ${r.metrics.damage_taken}</p>
        </div>
        <div class="report-section">
          <div class="report-section-title">TACTICAL HYPOTHESIS &amp; EVALUATION</div>
          <p style="color:#d0d0d0;">${r.evaluation.reasoning_summary || "Telemetry verified. Model hypothesis and player movement vectors confirmed."}</p>
        </div>
        <div class="report-section">
          <div class="report-section-title">NEXT MISSION DIRECTIVE</div>
          <p style="color:var(--accent-yellow);">${r.next_mission || "Deploy active formation countermeasures on upcoming wave."}</p>
        </div>
      `;
    } catch (err) {
      console.error("Failed to load last report:", err);
    }
  }

  // Run Test Inference
  document.getElementById("btn-run-inference-test")?.addEventListener("click", async () => {
    const sel = document.getElementById("select-model");
    const chosenModel = sel ? sel.value : "gemma4:e2b";
    const outBox = document.getElementById("inference-json");
    outBox.textContent = `Dispatching structured tactical reasoning query to ${chosenModel}... (Please wait, cold model load may take several seconds)`;

    try {
      const res = await fetch("/api/test-inference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: chosenModel }),
      });
      const data = await res.json();
      outBox.textContent = JSON.stringify(data, null, 2);

      if (data.strategy) {
        document.getElementById("feed-formation").textContent = data.strategy.formation;
        document.getElementById("feed-latency").textContent = `${data.latency_ms} ms`;
        document.getElementById("hud-formation-name").textContent = data.strategy.formation;

        // Append to tactical feed
        const logContent = document.getElementById("tactical-log-content");
        if (logContent) {
          const nowStr = new Date().toISOString().substring(11, 19);
          const p = document.createElement("p");
          p.className = "log-line log-highlight";
          p.innerHTML = `<span class="log-ts">[${nowStr}]</span> <span class="log-tag log-ai">[${chosenModel}]</span> Formation: ${data.strategy.formation} &bull; Latency: ${data.latency_ms}ms &bull; Intent: "${data.strategy.tactical_intent}"`;
          logContent.prepend(p);
        }
      }
    } catch (err) {
      outBox.textContent = `Error dispatching inference: ${err.message}`;
    }
  });

  // Save Config to .env
  document.getElementById("btn-save-config")?.addEventListener("click", async () => {
    const sel = document.getElementById("select-model");
    const apiKeyInput = document.getElementById("input-api-key");
    const saveMsg = document.getElementById("save-msg");

    const payload = {
      primary_model: sel ? sel.value : "gemma4:e2b",
    };
    if (apiKeyInput && apiKeyInput.value.trim().length > 0) {
      payload.gemma_api_key = apiKeyInput.value.trim();
    }

    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      saveMsg.textContent = data.message || "Saved!";
      setTimeout(() => (saveMsg.textContent = ""), 4000);
      fetchStatus();
    } catch (err) {
      saveMsg.textContent = `Failed: ${err.message}`;
      saveMsg.style.color = "var(--accent-red)";
    }
  });

  // Refresh Buttons
  document.getElementById("btn-refresh-model-status")?.addEventListener("click", fetchStatus);
  document.getElementById("btn-refresh-history")?.addEventListener("click", () => {
    fetchMatches();
    fetchLastReport();
  });

  // Numeric Side Rail Scrollspy
  const sections = ["intro", "live-demo", "tactical-feed", "debrief", "model-panel", "gestures"];
  window.addEventListener("scroll", () => {
    const scrollY = window.scrollY + 200;
    for (const id of sections) {
      const el = document.getElementById(id);
      if (el) {
        const top = el.offsetTop;
        const h = el.offsetHeight;
        if (scrollY >= top && scrollY < top + h) {
          document.querySelectorAll(".rail-indicator").forEach((ind) => {
            ind.classList.toggle("active", ind.dataset.target === id);
          });
          document.querySelectorAll(".nav-link").forEach((link) => {
            link.classList.toggle("active", link.getAttribute("href") === `#${id}`);
          });
        }
      }
    }
  });

  // Rail Indicator Clicks
  document.querySelectorAll(".rail-indicator").forEach((ind) => {
    ind.addEventListener("click", () => {
      const targetId = ind.dataset.target;
      document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth" });
    });
  });

  // Initial Fetch
  fetchStatus();
  fetchMatches();
  fetchLastReport();
})();
