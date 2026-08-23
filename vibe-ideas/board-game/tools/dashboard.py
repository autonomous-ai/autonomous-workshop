#!/usr/bin/env python3
"""dashboard.py — a view of every idea in the queue, for the owner to skim
instead of scrolling Telegram history.

    python3 board-game/tools/dashboard.py                  # writes dashboard.html once
    python3 board-game/tools/dashboard.py --open            # and opens it
    python3 board-game/tools/dashboard.py --serve            # live, at localhost:8420
    python3 board-game/tools/dashboard.py --serve --open     # live, opened for you

Telegram stays the alert channel — the two gates that need a decision fire a
notification there, plus the journal narration as it happens. This is the
other view of the same data: every idea at once, current state first, so you
can see where the queue actually stands without reconstructing it from a
chat scrollback — and, when `--serve` is running, actually answer a gate from
here too: an idea sitting in `awaiting_owner` or `awaiting_ship` gets
Approve/Reject/Rework/Ship buttons, with Reject and Rework opening a dialog
for the reason instead of routing through Telegram's reply flow. Every button
still just runs the same `pipeline_queue.py` verb the Telegram path would —
this is another front end onto it, not a second source of truth, and
`pipeline_queue.py`'s own state check is what makes it safe to act from
here even if a stale Telegram gate message is still sitting there too.

`--serve` re-reads `QUEUE.json` and the journal log on every request, so a
browser refresh always shows the current queue. The open tab does not poll on
its own unless you ask it to with `--interval <seconds>`. It binds to
127.0.0.1 only: this is pipeline internals, not something to expose on the
network. Without `--serve` it is the original one-shot file, read-only (no
server to act against) — for a quick look or for handing someone a single
HTML file.

Under `--serve`, any idea with at least one built `.stl` also gets a "view 3D
model" link to `/viewer/<slug>` — a per-idea page that loads three.js from a
CDN (no npm/build step, matching this file's own no-build philosophy) and
lets you spin every `.stl`/`.step` under that idea's build dir (the
assembled whole and every individual part), with wireframe and an
axis-aligned cross-section (GPU clip plane + a stencil-buffer-filled cut
face, the same technique panda-social-cc-agent's monitor uses, minus its
CSG-rebuilt-solid refinement). The build dir is `project/` once
board-game-builder has run in build mode, else `draft/` — a still-drafted
idea already has a model under `draft/build/`, and the viewer shows that one
too (see `model_root()`). This is `--serve`-only, not part of the one-shot
file: a full parts tree can run tens of megabytes, too large to embed as
base64 the way hero renders are — the viewer streams files from
`/viewer/<slug>/file/<path>` instead, scoped to that idea's build dir.

This is the one place allowed to read `journal.JOURNAL_LOG` — see the warning
in `journal.py`'s docstring before adding a second one. Everything else here
(`QUEUE.json`, `idea.json`, `gate.json`, `review_*.md`, hero renders) was
already readable by any pipeline tool; this script only arranges it.

The page is self-contained (renders embedded as base64), so the one-shot file
opens straight from disk with no server, and `--serve` needs no separate
static assets either.
"""
from __future__ import annotations

import argparse
import base64
import html
import http.server
import json
import subprocess
import sys
import urllib.parse
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
IDEAS = REPO_ROOT / "board-game" / "ideas"
QUEUE = REPO_ROOT / "board-game" / "QUEUE.json"
OUT = REPO_ROOT / "board-game" / "dashboard.html"
PY_ABS = REPO_ROOT / ".venv" / "bin" / "python"
QUEUE_SCRIPT = REPO_ROOT / "board-game" / "tools" / "pipeline_queue.py"

# The owner-gate verbs the dashboard's action buttons are allowed to run, and
# whether each needs a typed reason. Deliberately the same small surface
# telegram.py exposes — the dashboard is another front end onto
# pipeline_queue.py, not a second source of truth.
GATE_ACTIONS = {"approve": False, "reject": True, "rework": True, "ship": False}

LENSES = ("rules", "playtest", "printability", "fidelity", "playability")

# Rough front-to-back order: closest to shipping first, terminal states last —
# mirrors pipeline_queue.py's PRIORITY, plus the states it doesn't schedule.
STATE_ORDER = ["reviewed", "awaiting_ship", "built", "repairing", "approved",
               "awaiting_owner", "drafted", "briefed", "rules_ok", "proposed",
               "blocked", "shipped", "killed"]
STATE_COLOR = {
    "proposed": "#8a8f98", "rules_ok": "#6b7280", "briefed": "#6b7280",
    "drafted": "#2563eb", "awaiting_owner": "#d97706", "approved": "#2563eb",
    "built": "#2563eb", "repairing": "#dc2626", "reviewed": "#059669",
    "awaiting_ship": "#d97706", "shipped": "#059669", "killed": "#9ca3af",
    "blocked": "#dc2626",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def load_journal() -> dict[str, list[dict]]:
    """slug -> its entries from JOURNAL_LOG, oldest first. Missing file (no
    entry has been written since this feature shipped) is just an empty
    story per idea, not an error."""
    by_slug: dict[str, list[dict]] = {}
    if not journal.JOURNAL_LOG.is_file():
        return by_slug
    for line in journal.JOURNAL_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        by_slug.setdefault(rec.get("slug", ""), []).append(rec)
    return by_slug


def find_hero(slug: str) -> Path | None:
    home = IDEAS / slug
    for pattern in ("**/_assembled.png", "**/cover.png", "**/*_qa.png"):
        found = sorted(home.glob(pattern))
        if found:
            return found[0]
    return None


def embed_image(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def model_root(slug: str) -> Path | None:
    """Where a build's .stl/.step files live — `project/` once
    board-game-builder has run in build mode, else `draft/` for an idea
    still at the draft stage (a draft already renders its own model under
    `draft/build/`). Same order as audit.py's BUILD_DIRS: project first."""
    for sub in ("project", "draft"):
        candidate = IDEAS / slug / sub
        if candidate.is_dir():
            return candidate
    return None


def find_model_files(slug: str) -> list[dict]:
    """.step/.stl files under this idea's build dir, for the /viewer page —
    the assembled whole plus every individual part. Skips __pycache__ and the
    *_review dirs (rendered PNGs, not models)."""
    root = model_root(slug)
    if root is None:
        return []
    out = []
    for path in sorted(root.rglob("*")):
        ext = path.suffix.lower()
        if ext not in (".stl", ".step") or not path.is_file():
            continue
        if "__pycache__" in path.parts or any(p.endswith("_review") for p in path.parts):
            continue
        out.append({"path": path.relative_to(root).as_posix(), "name": path.name,
                     "ext": ext.lstrip("."), "size": path.stat().st_size})
    return out


def has_stl(slug: str) -> bool:
    return any(f["ext"] == "stl" for f in find_model_files(slug))


def gate_summary(slug: str) -> dict:
    gate = read_json(IDEAS / slug / "project" / "gate.json")
    if not gate:
        return {}
    sliced = [v for v in (gate.get("slice") or {}).values() if v.get("print_min")]
    hours = sum(v["print_min"] for v in sliced) / 60.0 if sliced else None
    return {
        "pass": gate.get("pass"),
        "parts": gate.get("part_count"),
        "shapes": gate.get("distinct_shapes"),
        "hours": hours,
        "fails": gate.get("fails") or [],
    }


def lens_verdicts(slug: str) -> list[tuple[str, str]]:
    out = []
    for lens in LENSES:
        path = IDEAS / slug / f"review_{lens}.md"
        if not path.is_file():
            continue
        first = (path.read_text(encoding="utf-8").splitlines() or [""])[0]
        out.append((lens, first.replace("Verdict:", "").strip()))
    return out


def build_timeline(item: dict, entries: list[dict]) -> list[dict]:
    """Merge QUEUE.json's state transitions (always present, even predating
    this feature) with journal entries other than `kind == "state"` (which
    QUEUE.json's own log already covers) into one chronological story."""
    events = []
    for t in item.get("log") or []:
        note = t.get("note", "")
        summary = f"{t['from']} → {t['to']}" + (f"\n{note}" if note else "")
        events.append({"at": t["at"], "kind": "state", "by": "pipeline",
                        "summary": summary, "body": ""})
    for e in entries:
        if e.get("kind") == "state":
            continue
        events.append(e)
    events.sort(key=lambda e: e.get("at", ""))
    return events


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def render_timeline(events: list[dict]) -> str:
    if not events:
        return '<p class="muted">no entries yet</p>'
    rows = []
    for e in events:
        stamp = esc(e.get("at", ""))[:16].replace("T", " ")
        kind = esc(e.get("kind", "note"))
        by = esc(e.get("by", ""))
        summary = esc(e.get("summary", "")).replace("\n", "<br>")
        body = e.get("body", "")
        detail = (f'<details class="body"><summary>detail</summary>'
                  f'<pre>{esc(body)}</pre></details>') if body.strip() else ""
        rows.append(
            f'<li><span class="ts">{stamp}</span> '
            f'<span class="kind kind-{kind}">{kind}</span> '
            f'<span class="by">{by}</span>'
            f'<div class="summary">{summary}</div>{detail}</li>')
    return f'<ul class="timeline">{"".join(rows)}</ul>'


def render_actions(slug: str, state: str, interactive: bool) -> str:
    if not interactive:
        return ""
    verbs: list[str] = []
    if state == "awaiting_owner":
        verbs = ["approve", "reject", "rework"]
    elif state == "awaiting_ship":
        verbs = ["ship", "reject"]
    if not verbs:
        return ""
    slug_js = esc(json.dumps(slug))
    buttons = "".join(
        f'<button class="act {"ok" if v in ("approve", "ship") else "warn" if v == "rework" else "bad"}" '
        f"onclick='actOn({slug_js},&quot;{v}&quot;)'>{v}</button>"
        for v in verbs)
    return f'<div class="actions">{buttons}</div>'


def render_idea(slug: str, item: dict, entries: list[dict], interactive: bool = False) -> str:
    idea = read_json(IDEAS / slug / "idea.json")
    state = item.get("state", "?")
    color = STATE_COLOR.get(state, "#6b7280")
    title = idea.get("title") or item.get("title") or slug
    concept = idea.get("concept", "")
    players = idea.get("players") or {}
    playtime = idea.get("playtime_min")
    repairs = item.get("repairs_used", 0)
    rework = item.get("rework_reason", "")

    hero = embed_image(find_hero(slug))
    hero_html = f'<img class="hero" src="{hero}" alt="{esc(title)}">' if hero else ""

    facts = []
    if players:
        facts.append(f"{esc(players.get('min', '?'))}–{esc(players.get('max', '?'))} players")
    if playtime:
        facts.append(f"~{esc(playtime)} min")
    facts_html = " · ".join(facts)

    gate = gate_summary(slug)
    gate_html = ""
    if gate:
        verdict = "PASS" if gate.get("pass") else "FAIL"
        vclass = "ok" if gate.get("pass") else "bad"
        hours = f" · ~{gate['hours']:.1f}h print" if gate.get("hours") else ""
        gate_html = (f'<div class="strip"><b class="{vclass}">GATE {verdict}</b> '
                     f'{esc(gate.get("parts"))} parts, {esc(gate.get("shapes"))} shapes'
                     f'{hours}</div>')
        if gate.get("fails"):
            items = "".join(f"<li>{esc(f)}</li>" for f in gate["fails"][:10])
            gate_html += f'<details class="body"><summary>{len(gate["fails"])} finding(s)</summary><ul>{items}</ul></details>'

    lenses = lens_verdicts(slug)
    lens_html = ""
    if lenses:
        items = " · ".join(f"{esc(name)}: {esc(v)}" for name, v in lenses)
        lens_html = f'<div class="strip">{items}</div>'

    rework_html = (f'<div class="strip warn">rework: {esc(rework)}</div>'
                   if rework else "")

    viewer_html = (f'<div class="strip"><a class="viewer-link" href="/viewer/{esc(slug)}" '
                   f'target="_blank">🧊 view 3D model</a></div>'
                   if interactive and has_stl(slug) else "")

    timeline = build_timeline(item, entries)

    return f"""
<section class="card" data-state="{esc(state)}">
  <div class="card-head">
    <h2>{esc(title)} <span class="slug">{esc(slug)}</span></h2>
    <span class="badge" style="background:{color}">{esc(state)}</span>
  </div>
  <div class="facts">{facts_html}{f' · repairs {repairs}/2' if repairs else ''}</div>
  {hero_html}
  <p class="concept">{esc(concept)}</p>
  {gate_html}
  {lens_html}
  {viewer_html}
  {rework_html}
  {render_actions(slug, state, interactive)}
  <details class="timeline-toggle" open>
    <summary>timeline ({len(timeline)})</summary>
    {render_timeline(timeline)}
  </details>
</section>"""


def render(data: dict, journal_by_slug: dict, refresh_seconds: int | None = None,
           interactive: bool = False) -> str:
    ideas = data.get("ideas") or {}

    def sort_key(kv):
        slug, item = kv
        state = item.get("state", "")
        try:
            rank = STATE_ORDER.index(state)
        except ValueError:
            rank = len(STATE_ORDER)
        return (rank, item.get("created", ""))

    ordered = sorted(ideas.items(), key=sort_key)

    counts: dict[str, int] = {}
    for _, item in ideas.items():
        counts[item.get("state", "?")] = counts.get(item.get("state", "?"), 0) + 1
    stats = " · ".join(f"{esc(k)}: {v}" for k, v in
                        sorted(counts.items(), key=lambda kv: -kv[1]))

    states_present = sorted({item.get("state", "?") for item in ideas.values()})
    filter_buttons = " ".join(
        f'<button class="filter" data-filter="{esc(s)}">{esc(s)}</button>'
        for s in states_present)

    cards = "".join(render_idea(slug, item, journal_by_slug.get(slug, []), interactive)
                     for slug, item in ordered)
    if not cards:
        cards = '<p class="muted">the queue is empty — nothing has been proposed yet.</p>'

    from datetime import datetime, timezone
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    live = f' · <span class="live">live, refreshing every {refresh_seconds}s</span>' \
        if refresh_seconds else ""
    refresh_script = (f"<script>setTimeout(function(){{location.reload();}}, "
                       f"{refresh_seconds * 1000});</script>") if refresh_seconds else ""

    modal_html = """
  <dialog id="reasonModal">
    <form method="dialog" id="reasonForm">
      <h3 id="reasonModalTitle">Reason</h3>
      <textarea id="reasonText" rows="5" placeholder="Why?" required></textarea>
      <div class="modal-actions">
        <button type="button" id="reasonCancel">Cancel</button>
        <button type="submit" class="act warn">Send</button>
      </div>
    </form>
  </dialog>""" if interactive else ""

    actions_script = """
<script>
  var reasonModal = document.getElementById('reasonModal');
  var pendingSlug = null, pendingAction = null;

  function actOn(slug, action) {
    if (action === 'reject' || action === 'rework') {
      pendingSlug = slug; pendingAction = action;
      document.getElementById('reasonModalTitle').textContent =
        action + ' ' + slug + ' — reason:';
      document.getElementById('reasonText').value = '';
      reasonModal.showModal();
      return;
    }
    if (!confirm(action + ' ' + slug + '?')) return;
    submitAction(slug, action, null);
  }

  document.getElementById('reasonCancel').addEventListener('click', function() {
    reasonModal.close();
  });
  document.getElementById('reasonForm').addEventListener('submit', function(e) {
    e.preventDefault();
    var reason = document.getElementById('reasonText').value.trim();
    if (!reason) return;
    reasonModal.close();
    submitAction(pendingSlug, pendingAction, reason);
  });

  function submitAction(slug, action, reason) {
    fetch('/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({slug: slug, action: action, reason: reason})
    }).then(function(r) { return r.json(); }).then(function(data) {
      if (!data.ok) alert((data.output || 'failed') + '');
      location.reload();
    }).catch(function(err) { alert('request failed: ' + err); });
  }
</script>""" if interactive else ""

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>board-game pipeline</title>
<style>
  :root {{
    --bg:#f7f7f8; --card:#fff; --text:#1a1a1a; --muted:#6b7280;
    --border:#e5e7eb; --ok:#059669; --bad:#dc2626; --warn-bg:#fff7ed;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#15161a; --card:#1e2025; --text:#e5e7eb; --muted:#9ca3af;
             --border:#2c2f36; --ok:#34d399; --bad:#f87171; --warn-bg:#3a2a12; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font:14px/1.5 -apple-system,
          BlinkMacSystemFont,"Segoe UI",sans-serif; margin:0; padding:24px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .meta {{ color:var(--muted); font-size:12px; margin-bottom:16px; }}
  .filters {{ margin-bottom:20px; }}
  .filter {{ background:var(--card); border:1px solid var(--border); color:var(--text);
             border-radius:6px; padding:4px 10px; margin:0 6px 6px 0; cursor:pointer;
             font-size:12px; }}
  .filter.active {{ background:var(--text); color:var(--bg); }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:16px 20px; margin-bottom:16px; max-width:760px; }}
  .card-head {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
  h2 {{ font-size:16px; margin:0; }}
  .slug {{ color:var(--muted); font-weight:400; font-size:12px; }}
  .badge {{ color:#fff; border-radius:999px; padding:3px 10px; font-size:12px;
            white-space:nowrap; }}
  .facts {{ color:var(--muted); font-size:12px; margin:4px 0 10px; }}
  .hero {{ max-width:100%; border-radius:8px; border:1px solid var(--border);
           margin-bottom:10px; display:block; }}
  .concept {{ margin:0 0 10px; }}
  .strip {{ font-size:12px; background:var(--bg); border-radius:6px; padding:6px 10px;
            margin-bottom:6px; }}
  .strip.warn {{ background:var(--warn-bg); }}
  .viewer-link {{ color:var(--text); text-decoration:none; font-weight:500; }}
  .viewer-link:hover {{ text-decoration:underline; }}
  .ok {{ color:var(--ok); }} .bad {{ color:var(--bad); }}
  details.body {{ font-size:12px; margin:4px 0 8px; }}
  details.body pre {{ white-space:pre-wrap; word-break:break-word; background:var(--bg);
                       padding:8px; border-radius:6px; max-height:300px; overflow:auto; }}
  .timeline-toggle > summary {{ cursor:pointer; font-size:12px; color:var(--muted); }}
  ul.timeline {{ list-style:none; margin:8px 0 0; padding:0; border-left:2px solid var(--border); }}
  ul.timeline li {{ padding:6px 0 6px 14px; margin-left:2px; border-bottom:1px dashed var(--border); }}
  ul.timeline li:last-child {{ border-bottom:none; }}
  .ts {{ color:var(--muted); font-size:11px; }}
  .kind {{ font-size:10px; text-transform:uppercase; letter-spacing:.04em;
           color:var(--muted); border:1px solid var(--border); border-radius:4px;
           padding:1px 5px; margin-left:6px; }}
  .by {{ font-size:11px; color:var(--muted); margin-left:6px; }}
  .summary {{ margin-top:3px; }}
  .muted {{ color:var(--muted); }}
  .live {{ color:var(--ok); }}
  .actions {{ display:flex; gap:8px; margin:10px 0 4px; }}
  .act {{ border:1px solid var(--border); border-radius:6px; padding:6px 14px;
          font-size:12px; cursor:pointer; background:var(--card); color:var(--text); }}
  .act.ok {{ background:var(--ok); color:#fff; border-color:var(--ok); }}
  .act.bad {{ background:var(--bad); color:#fff; border-color:var(--bad); }}
  .act.warn {{ background:#d97706; color:#fff; border-color:#d97706; }}
  dialog {{ background:var(--card); color:var(--text); border:1px solid var(--border);
            border-radius:10px; padding:20px; max-width:420px; width:90%; }}
  dialog::backdrop {{ background:rgba(0,0,0,.4); }}
  dialog h3 {{ margin:0 0 10px; font-size:14px; }}
  dialog textarea {{ width:100%; box-sizing:border-box; background:var(--bg); color:var(--text);
                      border:1px solid var(--border); border-radius:6px; padding:8px;
                      font:inherit; resize:vertical; }}
  .modal-actions {{ display:flex; justify-content:flex-end; gap:8px; margin-top:12px; }}
</style></head>
<body>
  <h1>board-game pipeline</h1>
  <div class="meta">generated {generated} · {len(ideas)} idea(s) · {stats}{live}</div>
  <div class="filters">
    <button class="filter active" data-filter="">all</button>
    {filter_buttons}
  </div>
  <div id="cards">{cards}</div>
  {modal_html}
<script>
  function applyFilter(f) {{
    document.querySelectorAll('.filter').forEach(function(b) {{
      b.classList.toggle('active', b.dataset.filter === f);
    }});
    document.querySelectorAll('.card').forEach(function(card) {{
      card.style.display = (!f || card.dataset.state === f) ? '' : 'none';
    }});
  }}
  document.querySelectorAll('.filter').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      sessionStorage.setItem('bgFilter', btn.dataset.filter);
      applyFilter(btn.dataset.filter);
    }});
  }});
  var saved = sessionStorage.getItem('bgFilter');
  if (saved) applyFilter(saved);
</script>
{actions_script}
{refresh_script}
</body></html>"""


# three.js has no build step in this repo (dashboard.py is the only frontend
# tool here, and it's plain stdlib Python), so the viewer loads three's ESM
# build straight from a CDN via an import map instead of adding npm/vite —
# the same "self-contained, no separate assets" spirit as the base64-embedded
# hero renders above, just via network instead of inline bytes because model
# files run too large to embed (see the module docstring).
THREE_VERSION = "0.169.0"

# %SLUG_JSON%, %TITLE_ESC% and %SLUG_ESC% are substituted below. Kept as a
# raw string (not an f-string) so the JS's own `{}` and template literals
# don't need doubling — see render() above for what that escaping looks like
# when it's unavoidable.
VIEWER_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<title>%TITLE_ESC% — 3D viewer</title>
<style>
  :root {
    --bg:#f7f7f8; --card:#fff; --text:#1a1a1a; --muted:#6b7280; --border:#e5e7eb;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#15161a; --card:#1e2025; --text:#e5e7eb; --muted:#9ca3af; --border:#2c2f36; }
  }
  * { box-sizing:border-box; }
  html, body { height:100%; margin:0; }
  body { background:var(--bg); color:var(--text); font:14px/1.5 -apple-system,
         BlinkMacSystemFont,"Segoe UI",sans-serif; display:flex; flex-direction:column; }
  .topbar { padding:10px 16px; border-bottom:1px solid var(--border); display:flex;
            align-items:baseline; gap:12px; flex:0 0 auto; }
  .topbar a { color:var(--muted); text-decoration:none; font-size:12px; }
  .topbar a:hover { text-decoration:underline; }
  .topbar h1 { font-size:15px; margin:0; }
  .topbar .slug { color:var(--muted); font-size:12px; font-weight:400; }
  .layout { flex:1 1 auto; display:flex; min-height:0; }
  .viewer-pane { flex:1 1 auto; position:relative; background:#0b0b0e; }
  #canvas-wrap { position:absolute; inset:0; }
  #canvas-wrap canvas { display:block; width:100%; height:100%; }
  .sidebar { width:300px; flex:0 0 300px; border-left:1px solid var(--border);
             overflow-y:auto; padding:12px; background:var(--card); }
  .sidebar h2 { font-size:12px; text-transform:uppercase; letter-spacing:.04em;
                color:var(--muted); margin:0 0 8px; }
  .group-dir { font-size:11px; color:var(--muted); margin:10px 0 4px; }
  .group-dir:first-child { margin-top:0; }
  .part-row { display:flex; align-items:center; gap:6px; margin-bottom:2px; }
  .part-btn { flex:1 1 auto; text-align:left; background:none; border:1px solid transparent;
              border-radius:6px; padding:5px 8px; font-size:12.5px; color:var(--text);
              cursor:pointer; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .part-btn:hover { background:var(--bg); }
  .part-btn.active { background:var(--text); color:var(--bg); }
  span.part-btn.disabled { color:var(--muted); cursor:default; }
  .step-link { font-size:10px; color:var(--muted); border:1px solid var(--border);
               border-radius:4px; padding:2px 6px; text-decoration:none; white-space:nowrap; }
  .step-link:hover { color:var(--text); border-color:var(--text); }
  .size { font-size:10px; color:var(--muted); margin-left:4px; }
  .empty { color:var(--muted); font-size:12px; padding:8px 0; }

  .stl-overlay { position:absolute; inset:0; display:flex; align-items:center;
                 justify-content:center; color:#e5e7eb; font-size:13px;
                 background:rgba(11,11,14,.5); text-align:center; padding:20px; }
  .stl-overlay-err { color:#f87171; }
  .stl-info { position:absolute; left:12px; top:12px; color:#e5e7eb; font-size:11px;
              background:rgba(0,0,0,.35); padding:4px 8px; border-radius:6px; }
  .toolbar { position:absolute; left:12px; bottom:12px; display:flex; gap:6px; }
  .toolbar button { background:rgba(30,32,37,.85); color:#e5e7eb; border:1px solid #3a3d44;
                     border-radius:6px; padding:6px 10px; font-size:11.5px; cursor:pointer; }
  .toolbar button.active { background:#2563eb; border-color:#2563eb; color:#fff; }

  .section-panel { position:absolute; right:12px; top:12px; width:220px;
                    background:rgba(20,21,25,.92); border:1px solid #3a3d44; border-radius:8px;
                    padding:10px 12px; color:#e5e7eb; font-size:12px; }
  .section-panel h3 { font-size:11px; text-transform:uppercase; letter-spacing:.04em;
                       color:#9ca3af; margin:0 0 8px; }
  .section-panel label { display:flex; align-items:center; justify-content:space-between;
                          gap:8px; margin-bottom:8px; }
  .section-panel .axis-row { display:flex; gap:4px; margin-bottom:10px; }
  .section-panel .axis-row button { flex:1 1 0; background:#26282e; border:1px solid #3a3d44;
                                     color:#e5e7eb; border-radius:5px; padding:4px 0;
                                     font-size:11px; cursor:pointer; }
  .section-panel .axis-row button.active { background:#2563eb; border-color:#2563eb; color:#fff; }
  .section-panel input[type=range] { width:130px; }
</style></head>
<body>
  <div class="topbar">
    <a href="/">&larr; dashboard</a>
    <h1>%TITLE_ESC% <span class="slug">%SLUG_ESC%</span></h1>
  </div>
  <div class="layout">
    <div class="viewer-pane">
      <div id="canvas-wrap"></div>
      <div id="loading" class="stl-overlay">loading…</div>
      <div id="error" class="stl-overlay stl-overlay-err" style="display:none"></div>
      <div id="info" class="stl-info" style="display:none"></div>
      <div class="toolbar">
        <button id="btn-wire" type="button">wireframe</button>
        <button id="btn-section" type="button">cross section</button>
        <button id="btn-reset" type="button">reset view</button>
        <button id="btn-fullscreen" type="button">fullscreen</button>
      </div>
      <div id="section-panel" class="section-panel" style="display:none">
        <h3>cross section</h3>
        <div class="axis-row">
          <button data-axis="x" type="button">X</button>
          <button data-axis="y" type="button">Y</button>
          <button data-axis="z" type="button" class="active">Z</button>
        </div>
        <label>position <input id="sec-pos" type="range" min="0" max="100" value="50"></label>
        <label>flip <input id="sec-flip" type="checkbox"></label>
        <label>show hidden half <input id="sec-ghost" type="checkbox"></label>
        <label>opacity <input id="sec-opacity" type="range" min="5" max="60" value="15"></label>
      </div>
    </div>
    <div class="sidebar">
      <h2 id="parts-header">parts</h2>
      <div id="parts-list"><p class="empty">loading…</p></div>
    </div>
  </div>

<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@%THREE_VERSION%/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@%THREE_VERSION%/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const SLUG = %SLUG_JSON%;
const MESH_COLOR = 0xff7a3d;
const INTERIOR_COLOR = 0x5b6470;
const CAP_COLOR = "#1174DC";

const wrap = document.getElementById("canvas-wrap");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const infoEl = document.getElementById("info");
const partsListEl = document.getElementById("parts-list");
const partsHeaderEl = document.getElementById("parts-header");
const sectionPanelEl = document.getElementById("section-panel");
const wireBtn = document.getElementById("btn-wire");
const sectionBtn = document.getElementById("btn-section");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0b0e);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.position.set(80, 60, 80);

// stencil:true — the cross-section's cut cap is drawn with the stencil buffer; three's
// default is false, and without it the cap would just cover the whole clip plane.
const renderer = new THREE.WebGLRenderer({ antialias: true, stencil: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.localClippingEnabled = true;
wrap.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
keyLight.position.set(1, 1.4, 1);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
fillLight.position.set(-1, 0.3, -0.6);
scene.add(fillLight);

// STL is Z-up; the viewport is Y-up. The rotation lives on the group rather than the mesh
// so the mesh keeps an identity local transform — the cross-section's bounds and
// clip-plane math stay in the file's own axes, and the section extras (interior tint, cap,
// ghost) inherit exactly the same frame by being added alongside or under the mesh.
const group = new THREE.Group();
group.rotation.x = -Math.PI / 2;
scene.add(group);

function resize() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  if (!w || !h) return;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
resize();
new ResizeObserver(resize).observe(wrap);

function frameCamera(radius) {
  const dist = radius / Math.sin((Math.min(camera.fov, 90) * Math.PI) / 360) || radius * 2.4;
  camera.position.set(dist * 0.6, dist * 0.5, dist * 0.6);
  camera.near = Math.max(radius / 100, 0.01);
  camera.far = radius * 50;
  camera.updateProjectionMatrix();
  controls.target.set(0, 0, 0);
  controls.update();
}

// ---- cross section: GPU clip plane + a stencil-buffer-filled cut cap ------------------
// Axis-aligned only (no free-drag gizmo) — enough to look inside a part without pulling in
// three-bvh-csg (the reference viewer's CSG "rebuilt solid" refinement) as a dependency.
const section = { enabled: false, axis: "z", t: 0.5, flip: false, showHidden: false, hiddenOpacity: 0.15 };
const clipPlane = new THREE.Plane();
const hiddenPlane = new THREE.Plane();
const clipArr = [clipPlane];
const hiddenArr = [hiddenPlane];
let bounds = null; // local half-extents of the centered geometry, keyed by axis

let mesh = null, interiorMesh = null, ghostMesh = null, cap = null;

function createCap(geometry, plane, targetMesh, color) {
  const base = { depthWrite: false, depthTest: false, colorWrite: false,
    stencilWrite: true, stencilFunc: THREE.AlwaysStencilFunc, clippingPlanes: [plane] };
  const backMat = new THREE.MeshBasicMaterial({ ...base, side: THREE.BackSide });
  backMat.stencilFail = backMat.stencilZFail = backMat.stencilZPass = THREE.IncrementWrapStencilOp;
  const frontMat = new THREE.MeshBasicMaterial({ ...base, side: THREE.FrontSide });
  frontMat.stencilFail = frontMat.stencilZFail = frontMat.stencilZPass = THREE.DecrementWrapStencilOp;
  const capMat = new THREE.MeshStandardMaterial({ color, metalness: 0.1, roughness: 0.75, side: THREE.DoubleSide });
  capMat.stencilWrite = true;
  capMat.stencilRef = 0;
  capMat.stencilFunc = THREE.NotEqualStencilFunc;
  capMat.stencilFail = capMat.stencilZFail = capMat.stencilZPass = THREE.ReplaceStencilOp;

  // Two invisible passes (back faces increment, front faces decrement the stencil, both
  // clipped by the plane) mark the interior of the solid where it meets the plane; the lit
  // quad then paints only those stencilled pixels, so cavities stay open while solid
  // regions read as a filled cut face. Canonical three.js section technique.
  const backPass = new THREE.Mesh(geometry, backMat); backPass.renderOrder = 1;
  const frontPass = new THREE.Mesh(geometry, frontMat); frontPass.renderOrder = 1;
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), capMat);
  quad.renderOrder = 2;
  quad.frustumCulled = false;

  const object = new THREE.Group();
  object.add(backPass, frontPass, quad);

  const inv = new THREE.Matrix4();
  const normalMat = new THREE.Matrix3();
  const local = new THREE.Plane();
  const UNIT_Z = new THREE.Vector3(0, 0, 1);

  return {
    object,
    update() {
      inv.copy(targetMesh.matrixWorld).invert();
      normalMat.getNormalMatrix(inv);
      local.copy(plane).applyMatrix4(inv, normalMat);
      local.coplanarPoint(quad.position);
      quad.quaternion.setFromUnitVectors(UNIT_Z, local.normal);
    },
    setSize(size) { quad.scale.set(size, size, 1); },
    dispose() {
      object.removeFromParent();
      quad.geometry.dispose();
      backMat.dispose(); frontMat.dispose(); capMat.dispose();
    },
  };
}

function detachSection() {
  // Only materials/quad geometry are owned here — interiorMesh/ghostMesh/cap's stencil
  // passes all share the *model's* geometry, which the caller disposes separately.
  if (cap) { cap.dispose(); cap = null; }
  if (interiorMesh) { interiorMesh.removeFromParent(); interiorMesh.material.dispose(); interiorMesh = null; }
  if (ghostMesh) { ghostMesh.removeFromParent(); ghostMesh.material.dispose(); ghostMesh = null; }
  bounds = null;
}

function attachSection(targetMesh, geometry, baseColor) {
  detachSection();
  geometry.computeBoundingBox();
  const size = new THREE.Vector3();
  geometry.boundingBox.getSize(size);
  bounds = { x: size.x / 2, y: size.y / 2, z: size.z / 2 };

  interiorMesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    color: INTERIOR_COLOR, metalness: 0, roughness: 0.9, side: THREE.BackSide, clippingPlanes: clipArr,
  }));
  interiorMesh.visible = false;
  targetMesh.add(interiorMesh);

  ghostMesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    color: baseColor, roughness: 0.55, metalness: 0.08, transparent: true,
    opacity: section.hiddenOpacity, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: hiddenArr,
  }));
  ghostMesh.visible = false;
  targetMesh.parent.add(ghostMesh);

  cap = createCap(geometry, clipPlane, targetMesh, CAP_COLOR);
  cap.object.visible = false;
  targetMesh.add(cap.object);
  cap.setSize(Math.max(size.length(), 2));
}

function updateSection() {
  if (!mesh || !bounds) return;
  if (section.enabled) {
    mesh.updateWorldMatrix(true, false);
    const axis = section.axis;
    const half = bounds[axis];
    const coord = -half + section.t * 2 * half;
    const normal = new THREE.Vector3(axis === "x" ? 1 : 0, axis === "y" ? 1 : 0, axis === "z" ? 1 : 0);
    if (section.flip) normal.negate();
    const point = new THREE.Vector3();
    point[axis] = coord;
    const localPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(normal, point);
    clipPlane.copy(localPlane).applyMatrix4(mesh.matrixWorld);
    hiddenPlane.copy(clipPlane).negate();

    if (mesh.material.clippingPlanes !== clipArr) {
      mesh.material.clippingPlanes = clipArr;
      // FrontSide while sectioning: the dedicated interior-tint mesh (BackSide) draws the
      // cut's inner walls instead — leaving the main mesh DoubleSide here would z-fight
      // its own backfaces against that tint mesh's identical geometry.
      mesh.material.side = THREE.FrontSide;
      mesh.material.needsUpdate = true;
    }
    interiorMesh.visible = true;
    cap.object.visible = true;
    cap.update();
    ghostMesh.visible = section.showHidden;
    if (ghostMesh.material.opacity !== section.hiddenOpacity) ghostMesh.material.opacity = section.hiddenOpacity;
  } else {
    if (mesh.material.clippingPlanes) {
      mesh.material.clippingPlanes = null;
      mesh.material.side = THREE.DoubleSide;
      mesh.material.needsUpdate = true;
    }
    interiorMesh.visible = false;
    cap.object.visible = false;
    ghostMesh.visible = false;
  }
}

let raf = 0;
function tick() {
  controls.update();
  updateSection();
  renderer.render(scene, camera);
  raf = requestAnimationFrame(tick);
}
tick();

const loader = new STLLoader();

function loadModel(url, name) {
  loadingEl.textContent = "loading " + name + "…";
  loadingEl.style.display = "flex";
  errorEl.style.display = "none";
  infoEl.style.display = "none";

  loader.load(url, (geometry) => {
    geometry.computeBoundingBox();
    geometry.computeVertexNormals();
    const center = new THREE.Vector3();
    geometry.boundingBox.getCenter(center);
    geometry.translate(-center.x, -center.y, -center.z);
    const sz = new THREE.Vector3();
    geometry.boundingBox.getSize(sz);
    const radius = Math.max(sz.length() / 2, 1);

    detachSection();
    if (mesh) {
      group.remove(mesh);
      mesh.geometry.dispose();
      mesh.material.dispose();
    }

    const material = new THREE.MeshStandardMaterial({
      // DoubleSide: this repo's CadQuery-exported STLs don't guarantee consistent
      // outward face winding (booleans/tessellation can leave patches flipped), so the
      // default FrontSide silently culls whole faces — DoubleSide is what actually shows
      // the model.
      color: MESH_COLOR, roughness: 0.55, metalness: 0.08, side: THREE.DoubleSide,
      wireframe: wireBtn.classList.contains("active"),
    });
    mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);
    attachSection(mesh, geometry, MESH_COLOR);
    frameCamera(radius);

    const tris = geometry.attributes.position.count / 3;
    infoEl.textContent = name + " · " + tris.toLocaleString() + " tris";
    infoEl.style.display = "block";
    loadingEl.style.display = "none";
  }, undefined, (err) => {
    loadingEl.style.display = "none";
    errorEl.textContent = "failed to load " + name + ": " + (err && err.message ? err.message : err);
    errorEl.style.display = "flex";
  });
}

wireBtn.addEventListener("click", () => {
  wireBtn.classList.toggle("active");
  if (mesh) mesh.material.wireframe = wireBtn.classList.contains("active");
});
sectionBtn.addEventListener("click", () => {
  section.enabled = !section.enabled;
  sectionBtn.classList.toggle("active", section.enabled);
  sectionPanelEl.style.display = section.enabled ? "block" : "none";
});
document.getElementById("btn-reset").addEventListener("click", () => {
  if (!mesh) return;
  const sz = new THREE.Vector3();
  mesh.geometry.boundingBox.getSize(sz);
  frameCamera(Math.max(sz.length() / 2, 1));
});
document.getElementById("btn-fullscreen").addEventListener("click", () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else wrap.parentElement.requestFullscreen();
});
document.querySelectorAll(".axis-row button").forEach((btn) => {
  btn.addEventListener("click", () => {
    section.axis = btn.dataset.axis;
    document.querySelectorAll(".axis-row button").forEach((b) => b.classList.toggle("active", b === btn));
  });
});
document.getElementById("sec-pos").addEventListener("input", (e) => { section.t = Number(e.target.value) / 100; });
document.getElementById("sec-flip").addEventListener("change", (e) => { section.flip = e.target.checked; });
document.getElementById("sec-ghost").addEventListener("change", (e) => { section.showHidden = e.target.checked; });
document.getElementById("sec-opacity").addEventListener("input", (e) => { section.hiddenOpacity = Number(e.target.value) / 100; });

function fileUrl(path) {
  return "/viewer/" + encodeURIComponent(SLUG) + "/file/" + path.split("/").map(encodeURIComponent).join("/");
}
function fmtSize(bytes) {
  return bytes > 1024 * 1024 ? (bytes / (1024 * 1024)).toFixed(1) + "MB" : Math.round(bytes / 1024) + "KB";
}
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

let entriesByPath = {};

function renderParts(files) {
  const groups = new Map(); // dir -> base -> {stl?, step?}
  for (const f of files) {
    entriesByPath[f.path] = f;
    const slash = f.path.lastIndexOf("/");
    const dir = slash === -1 ? "(root)" : f.path.slice(0, slash);
    const base = f.name.replace(/\.(stl|step)$/i, "");
    if (!groups.has(dir)) groups.set(dir, new Map());
    const g = groups.get(dir);
    if (!g.has(base)) g.set(base, {});
    g.get(base)[f.ext] = f;
  }
  const dirs = [...groups.keys()].sort((a, b) =>
    a === "(root)" ? -1 : b === "(root)" ? 1 : a.localeCompare(b));
  let out = "";
  for (const dir of dirs) {
    out += '<div class="group-dir">' + escapeHtml(dir) + "</div>";
    const parts = [...groups.get(dir).entries()].sort((a, b) => a[0].localeCompare(b[0]));
    for (const [base, pair] of parts) {
      out += '<div class="part-row">';
      out += pair.stl
        ? '<button class="part-btn" data-path="' + escapeHtml(pair.stl.path) + '" type="button">'
          + escapeHtml(base) + '<span class="size">' + fmtSize(pair.stl.size) + "</span></button>"
        : '<span class="part-btn disabled">' + escapeHtml(base) + "</span>";
      if (pair.step) {
        out += '<a class="step-link" href="' + fileUrl(pair.step.path) + '" download="'
          + escapeHtml(pair.step.name) + '">step</a>';
      }
      out += "</div>";
    }
  }
  partsListEl.innerHTML = out;
  partsListEl.querySelectorAll(".part-btn[data-path]").forEach((btn) => {
    btn.addEventListener("click", () => selectPart(btn.dataset.path));
  });
}

function selectPart(path) {
  const f = entriesByPath[path];
  if (!f) return;
  partsListEl.querySelectorAll(".part-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.path === path);
  });
  loadModel(fileUrl(path), f.name);
}

fetch("/viewer/" + encodeURIComponent(SLUG) + "/tree")
  .then((r) => r.json())
  .then((files) => {
    if (!files.length) {
      partsListEl.innerHTML = '<p class="empty">no .stl/.step files found</p>';
      loadingEl.style.display = "none";
      return;
    }
    partsHeaderEl.textContent = "parts (" + files.length + ")";
    renderParts(files);
    const main = files.find((f) => f.ext === "stl" && f.path === SLUG + ".stl")
      || files.find((f) => f.ext === "stl");
    if (main) selectPart(main.path);
    else {
      loadingEl.style.display = "none";
      errorEl.textContent = "no .stl in this project yet — only .step files (download only)";
      errorEl.style.display = "flex";
    }
  })
  .catch((e) => {
    loadingEl.style.display = "none";
    partsListEl.innerHTML = '<p class="empty">failed to list files</p>';
    errorEl.textContent = "failed to list files: " + e;
    errorEl.style.display = "flex";
  });
</script>
</body></html>"""


def render_viewer_page(slug: str, title: str) -> str:
    return (VIEWER_TEMPLATE
            .replace("%SLUG_JSON%", json.dumps(slug))
            .replace("%TITLE_ESC%", esc(title))
            .replace("%SLUG_ESC%", esc(slug))
            .replace("%THREE_VERSION%", THREE_VERSION))


def run_pipeline(cmd_args: list[str]) -> tuple[int, str]:
    """Run one pipeline_queue.py command exactly as a gate button would,
    mirroring telegram.py's run_pipeline — this is the only thing a dashboard
    POST is allowed to execute, and only with a verb from GATE_ACTIONS."""
    result = subprocess.run([str(PY_ABS), str(QUEUE_SCRIPT)] + cmd_args, cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=60)
    return result.returncode, (result.stdout + result.stderr).strip()


def make_handler(interval: int):
    """One handler class per server, closed over `interval` so the served page
    knows its own auto-refresh rate. Re-reads QUEUE.json and the journal log
    on every GET — this is a few small local files, not a scale concern, and
    reading fresh each time is the entire point of `--serve`."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urllib.parse.urlsplit(self.path).path
            if path in ("/", "/index.html"):
                data = read_json(QUEUE)
                journal_by_slug = load_journal()
                body = render(data, journal_by_slug, refresh_seconds=interval,
                               interactive=True).encode("utf-8")
                self._send(200, "text/html; charset=utf-8", body)
                return
            if path.startswith("/viewer/"):
                self._serve_viewer(path[len("/viewer/"):])
                return
            self.send_response(404)
            self.end_headers()

        def _serve_viewer(self, sub: str) -> None:
            """/viewer/<slug>, /viewer/<slug>/tree and /viewer/<slug>/file/<relpath> —
            the 3D model viewer's page, its file listing, and the raw bytes for one
            .stl/.step under that idea's project/. `target.relative_to(root)` is the
            traversal guard: an out-of-tree `..` in relpath raises ValueError and 403s
            before any read happens."""
            slug, _, rest = sub.strip("/").partition("/")
            ideas = (read_json(QUEUE).get("ideas") or {})
            if not slug or slug not in ideas:
                self._send(404, "text/plain", b"unknown idea")
                return
            if not rest:
                idea = read_json(IDEAS / slug / "idea.json")
                title = idea.get("title") or ideas[slug].get("title") or slug
                body = render_viewer_page(slug, title).encode("utf-8")
                self._send(200, "text/html; charset=utf-8", body)
                return
            if rest == "tree":
                body = json.dumps(find_model_files(slug)).encode("utf-8")
                self._send(200, "application/json", body)
                return
            if rest.startswith("file/"):
                root = model_root(slug)
                if root is None:
                    self._send(404, "text/plain", b"not found")
                    return
                root = root.resolve()
                target = (root / urllib.parse.unquote(rest[len("file/"):])).resolve()
                try:
                    target.relative_to(root)
                except ValueError:
                    self._send(403, "text/plain", b"forbidden")
                    return
                if target.suffix.lower() not in (".stl", ".step") or not target.is_file():
                    self._send(404, "text/plain", b"not found")
                    return
                self._send(200, "application/octet-stream", target.read_bytes())
                return
            self._send(404, "text/plain", b"not found")

        def _send(self, status: int, ctype: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            """The dashboard's only write path: one gate verb against one
            known slug, exactly as a Telegram button would run it.
            `pipeline_queue.py`'s own state check is the real guard — this
            just narrows what a page load can even attempt to send."""
            if self.path != "/action":
                self._json(404, {"ok": False, "output": "not found"})
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._json(400, {"ok": False, "output": "malformed request"})
                return

            action = str(payload.get("action", ""))
            slug = str(payload.get("slug", ""))
            reason = payload.get("reason")
            ideas = (read_json(QUEUE).get("ideas") or {})

            if action not in GATE_ACTIONS:
                self._json(400, {"ok": False, "output": f"unknown action {action!r}"})
                return
            if slug not in ideas:
                self._json(404, {"ok": False, "output": f"unknown slug {slug!r}"})
                return
            needs_reason = GATE_ACTIONS[action]
            if needs_reason and not (reason or "").strip():
                self._json(400, {"ok": False, "output": "a reason is required"})
                return

            cmd = [action, slug]
            if needs_reason:
                cmd += ["--reason", reason.strip()]
            code, output = run_pipeline(cmd)
            self._json(200, {"ok": code == 0, "output": output})

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:  # noqa: A002
            pass  # an admin's own local tool doesn't need an access log

    return Handler


def cmd_serve(port: int, interval: int, do_open: bool) -> int:
    httpd = http.server.HTTPServer(("127.0.0.1", port), make_handler(interval))
    url = f"http://127.0.0.1:{port}/"
    refresh_note = f"refreshing every {interval}s" if interval else "no auto-refresh, reload manually"
    print(f"serving {url} ({refresh_note}) — Ctrl+C to stop")
    if do_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--open", action="store_true", dest="do_open",
                     help="open the page in the default browser")
    ap.add_argument("--serve", action="store_true",
                     help="serve a live, auto-refreshing page instead of writing a static file")
    ap.add_argument("--port", type=int, default=8420, help="serve: port to listen on")
    ap.add_argument("--interval", type=int, default=0,
                     help="serve: seconds between auto-refresh of the open tab "
                          "(0 = no auto-refresh, reload manually)")
    args = ap.parse_args()

    if args.serve:
        return cmd_serve(args.port, args.interval, args.do_open)

    data = read_json(QUEUE)
    journal_by_slug = load_journal()
    OUT.write_text(render(data, journal_by_slug), encoding="utf-8")
    print(f"wrote {OUT}")
    if args.do_open:
        webbrowser.open(OUT.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
