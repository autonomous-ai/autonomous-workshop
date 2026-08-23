const ui = {};
let data;
let frame;
let turn = 0;
let timer = null;
let liveGame = null;
let mode = "replay";

const byId = id => document.getElementById(id);
const escapeHtml = value => String(value ?? "").replace(/[&<>\"]/g, c => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;"
}[c]));

function currentGame() {
  return data.runs[Number(ui.run.value)]?.games[Number(ui.game.value)];
}

function setMode(next) {
  mode = next;
  document.querySelectorAll(".tab").forEach(button =>
    button.classList.toggle("active", button.dataset.mode === next));
  const rules = next === "rules";
  ui.rules.hidden = !rules;
  ui.sidebar.hidden = rules;
  ui.tableArea.hidden = rules;
  ui.movesPanel.hidden = rules;
  ui.replayControls.hidden = next !== "replay";
  ui.playControls.hidden = next !== "play";
  if (next === "replay") loadReplay();
  if (next === "play" && !frame) showMessage("Start a hot-seat game.");
}

function fillGames() {
  const run = data.runs[Number(ui.run.value)];
  ui.game.innerHTML = (run?.games || []).map((game, index) =>
    `<option value="${index}">${escapeHtml(game.label)} · ${game.seats}p · ${game.decisions} turns</option>`).join("");
  loadReplay();
}

function loadReplay() {
  stopPlayback();
  const game = currentGame();
  if (!game?.frames?.length) {
    frame = null;
    showMessage(game?.replay_error || "No replayable LLM games found.");
    return;
  }
  turn = 0;
  ui.timeline.max = game.frames.length - 1;
  ui.timeline.value = 0;
  frame = game.frames[0];
  render();
}

function showTurn(value) {
  const game = currentGame();
  if (!game?.frames?.length) return;
  turn = Math.max(0, Math.min(Number(value), game.frames.length - 1));
  ui.timeline.value = turn;
  frame = game.frames[turn];
  render();
}

function togglePlayback() {
  if (timer) return stopPlayback();
  ui.playPause.textContent = "Pause";
  timer = setInterval(() => {
    const game = currentGame();
    if (!game || turn >= game.frames.length - 1) return stopPlayback();
    showTurn(turn + 1);
  }, 850);
}

function stopPlayback() {
  clearInterval(timer);
  timer = null;
  if (ui.playPause) ui.playPause.textContent = "Play";
}

function showMessage(message) {
  ui.status.innerHTML = `<span class="status-main">${escapeHtml(message)}</span>`;
  ui.board.innerHTML = "";
  ui.moves.innerHTML = "";
  ui.raw.textContent = "";
  ui.detail.innerHTML = "";
}

function render() {
  if (!frame) return;
  const actor = frame.over ? `Game over · winner ${frame.winners.map(s => `seat ${s}`).join(", ")}` : `Turn ${frame.turn} · seat ${frame.actor}`;
  ui.status.innerHTML = `<span class="status-main">${escapeHtml(actor)}</span><span class="status-score">scores ${escapeHtml(frame.scores.join(" / "))}</span>`;
  ui.raw.textContent = JSON.stringify(frame.observation, null, 2);
  renderBoard(frame.observation);
  renderMoves();
  const p = frame.previous;
  ui.detail.innerHTML = p ? `<div class="turn-card"><p><strong>Seat ${escapeHtml(p.seat)}</strong> played ${escapeHtml(p.move)}</p>${p.why ? `<p class="why">${escapeHtml(p.why)}</p>` : ""}${p.decision ? `<p>${escapeHtml(p.decision)}</p>` : ""}</div>` : "";
}

function renderMoves() {
  const playable = mode === "play" && liveGame && !frame.over;
  ui.moves.innerHTML = frame.legal_moves.map((move, index) =>
    `<li><button class="move-button" data-choice="${index}" ${playable ? "" : "disabled"}>${escapeHtml(move)}</button></li>`).join("");
  if (playable) ui.moves.querySelectorAll("button").forEach(button =>
    button.addEventListener("click", () => playMove(Number(button.dataset.choice))));
}

function pairs(values) {
  return new Map((values || []).map(([coord, owner]) => [coord.join(","), owner]));
}

function renderBoard(observation) {
  if (Array.isArray(observation?.bases) && Array.isArray(observation?.top_caps)) {
    renderOvercap(observation);
    return;
  }
  ui.board.innerHTML = `<pre>${escapeHtml(JSON.stringify(observation, null, 2))}</pre>`;
}

function renderOvercap(observation) {
  const bases = pairs(observation.bases);
  const caps = pairs(observation.top_caps);
  let cells = "";
  for (let q = 0; q < 7; q++) {
    for (let r = 0; r < 7; r++) {
      const key = `${q},${r}`;
      const base = (bases.get(key) || "").toLowerCase();
      const cap = (caps.get(key) || "").toLowerCase();
      const left = r * 54 + q * 27;
      const top = q * 46;
      cells += `<div class="hex ${base}" style="left:${left}px;top:${top}px">${cap ? `<span class="cap ${cap}" title="${cap} cap"></span>` : `<span class="coord">${q},${r}</span>`}</div>`;
    }
  }
  ui.board.innerHTML = `<div><div class="overcap-board">${cells}</div><div class="board-key"><span><i class="swatch spire"></i>Spire</span><span><i class="swatch sill"></i>Sill</span></div></div>`;
}

async function newGame() {
  try {
    const response = await fetch("/api/games", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({seats: Number(ui.seats.value), seed: Number(ui.seed.value)})});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error);
    liveGame = body.game_id;
    frame = body.frame;
    render();
  } catch (error) {
    showMessage(`Could not start: ${error.message}. Use game_site.py serve, not a file URL.`);
  }
}

async function playMove(choice) {
  const response = await fetch(`/api/games/${liveGame}/moves`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({choice})});
  const body = await response.json();
  if (!response.ok) return showMessage(body.error);
  frame = body.frame;
  render();
}

function renderRules() {
  const chunks = [];
  for (const [name, body] of Object.entries(data.rules || {})) {
    const items = Array.isArray(body) ? body : [body];
    chunks.push(`<section><h2>${escapeHtml(name)}</h2><ol>${items.map(item => `<li>${escapeHtml(typeof item === "object" ? (item.text || JSON.stringify(item)) : item)}</li>`).join("")}</ol></section>`);
  }
  ui.rules.innerHTML = chunks.join("");
}

async function init() {
  Object.assign(ui, {
    run: byId("run-select"), game: byId("game-select"), timeline: byId("timeline"),
    playPause: byId("play-pause"), status: byId("status"), board: byId("board"),
    moves: byId("moves"), raw: byId("raw-state").querySelector("pre"), detail: byId("turn-detail"),
    sidebar: byId("sidebar"), tableArea: byId("table-area"), movesPanel: byId("moves-panel"),
    replayControls: byId("replay-controls"), playControls: byId("play-controls"), rules: byId("rules-panel"),
    seats: byId("seat-count"), seed: byId("seed")
  });
  const embedded = byId("game-data");
  data = embedded
    ? JSON.parse(embedded.textContent)
    : await fetch("data.json").then(response => response.json());
  document.title = `${data.title} · table replay`;
  byId("game-title").textContent = data.title;
  byId("game-concept").textContent = data.concept;
  ui.seats.min = data.players.min || 2;
  ui.seats.max = data.players.max || 4;
  ui.seats.value = data.players.min || 2;
  ui.run.innerHTML = data.runs.map((run, index) => `<option value="${index}">${escapeHtml(run.name)} · ${escapeHtml(run.model)}</option>`).join("");
  renderRules();
  fillGames();
  document.querySelectorAll(".tab").forEach(button => button.addEventListener("click", () => setMode(button.dataset.mode)));
  ui.run.addEventListener("change", fillGames);
  ui.game.addEventListener("change", loadReplay);
  ui.timeline.addEventListener("input", event => showTurn(event.target.value));
  byId("back").addEventListener("click", () => showTurn(turn - 1));
  byId("forward").addEventListener("click", () => showTurn(turn + 1));
  ui.playPause.addEventListener("click", togglePlayback);
  byId("new-game").addEventListener("click", newGame);
}

init().catch(error => showMessage(error.message));
