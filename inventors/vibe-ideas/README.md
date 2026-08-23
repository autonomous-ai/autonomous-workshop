# vibe-ideas

> **Monorepo snapshot.** This folder contains the inventor code imported from
> `reinSPQR/vibe-ideas` at commit `ed3d1e8`. It is the richest board-game
> workflow donor, but remains a reference until queue fencing and gate verdict
> checks use `../../workshop`. See [UPSTREAM.md](UPSTREAM.md) for provenance,
> licensing, and migration blockers. The original operating guide follows.

[`TASTE.md`](TASTE.md) is the root creative contract and links the protected
owner-rejection record used by the board-game pipeline.

An autonomous pipeline that invents physical board games, designs every piece
as CadQuery code, prints-checks them against a real bed, and carries the ones a
human approves onto a storefront. One `/bg` call advances exactly one idea by
exactly one step; the queue decides which idea and which step, so the loop can
be driven by a cron, a `/loop`, or a person typing `/bg` when they feel like it.

```
 IDEA ─────────────────────────────────────────────────────────────────
   board-game-ideator                        TASTE.md
   concept + COMPLETE rules + bill    ◀── (the owner's own rejection
   + art direction, in form language       reasons, verbatim)
        │
        ▼
 ┌────────────────────────────┐
 │ ① RULES GATE               │  rules_check → rules lens → engine → scripted
 │ check, teach, play, table  │  playtest → rule animation → independent
 └────────┬───────────────────┘  animation lens → LLM-player table + replay
          ▼                      site → playtest lens
 ┌────────────────────────────┐
 │ ② BRIEF                    │  every dimension in mm, every interface
 │ board-game-brief-writer    │  between pieces, the print plan, tiling
 └────────┬───────────────────┘  of anything bigger than the bed
          ▼
 ┌────────────────────────────┐
 │ ③ DRAFT  (fast + honest)   │──▶ renders ──▶ playability lens ──▶
 │ board-game-builder         │                📱 OWNER GATE 1 (approve/rework/reject)
 └────────┬───────────────────┘
          ▼  approved renders freeze into reference/ — a visual contract
 ┌────────────────────────────┐
 │ ④ BUILD                    │  one named assembly child per component,
 │ board-game-builder         │  fit_checks.py written from the brief's
 └────────┬───────────────────┘  interfaces
          ▼
 ┌────────────────────────────┐
 │ ⑤ GATE  (no LLM)           │  watertight, one body, bed fit, overhangs,
 │ gate.py → gate.json        │  bridges, bill match, piece-vs-piece
 └────────┬───────────────────┘  interference, fit_checks.py, optional slice
          ▼
 ┌────────────────────────────┐
 │ ⑥ PANEL — 3 lenses, blind  │  printability │ fidelity │ playability
 │ to each other              │  fidelity compares view-by-view against
 └────────┬───────────────────┘  reference/
          ▼
 ┌────────────────────────────┐
 │ ⑦ REPAIR — budget of 2     │──▶ exhausted → ARBITRATION: propose a
 │ re-gate, re-run failed lens│    brief amendment, ask the owner, block
 └────────┬───────────────────┘
          ▼ all green
        📱 OWNER GATE 2 — ship / reject
          ▼
 ┌────────────────────────────┐
 │ ⑧ PUBLISH  (optional)      │  the whole project folder + a generated
 │ publish.py                 │  RULES.md, as a DRAFT design on Panda
 └────────────────────────────┘  Social. The public flip stays human.
```

## The rules gate, in detail

Stage ① is where every idea actually dies or survives, and it is the deepest
loop in the pipeline:

1. `rules_check.py` — mechanical: schema, bill-vs-rules match, a declared
   complexity budget.
2. `board-game-lens-rules` — an independent opinion on whether the game is
   worth playing at all (dominant strategy, fake decisions, reachable ending,
   length, player count), before any brief or build time is spent.
3. `board-game-rules-engineer` writes `playtest/engine.py`, then
   `playtest.py` plays it a few thousand times with scripted policies —
   whether it ends, whether the first seat wins, whether looking ahead helps.
4. `board-game-rules-animator` renders `animation/rules.mp4`;
   `board-game-lens-animation`, a separate agent that cannot review its own
   work, must independently PASS it.
5. `table_run.py` seats real LLM players — four games at the idea's
   `players.max`, with archived player experience from prior rule iterations
   injected before the fourth — and finishes a replay/hot-seat website at
   `playtest/site/index.html` via `game_site.py`. This step is not optional:
   a game nobody sat at and thought about has no player feedback.
6. `board-game-lens-playtest` reads the machine half and the table half and
   writes `review_playtest.md` with the verdict that actually counts.

Every failure at any of these steps carries a **disposition** — `clarify`
(ambiguity, missing procedure — reword only) or `rework` (the mechanic
itself is broken) — set by the checker or lens, never by the fixer. Clarify
and rework spend separate budgets (`CLARIFY_BUDGET = 3`, `REWORK_BUDGET = 3`
in `pipeline_queue.py`); either exhausting kills the idea. `pipeline_queue.py`
freezes the idea's mechanical surface (action types, win condition, player
counts, component names/qty) before a clarify round and checks it after —
a clarify that quietly changed a mechanic is converted into a paid rework
rather than passed off as free. A rework whose Problem-ID recurs must be
classified against the previous candidate (`--lineage`, `--severity`); a
candidate that caused an equal-or-worse regression moves the idea to
`blocked` for a human decision — revert, fork, or kill — instead of another
patch.

Only after `board-game-lens-playtest` passes does the pipeline send its one
Telegram journal notification for the iteration (`journal.py rules_ready`):
the proposal, the approved rule animation, and the replay site link. No
other event in the rules gate reaches that channel.

## The queue is the pipeline

`board-game/QUEUE.json` holds every idea and its state; `pipeline_queue.py` is
the only thing allowed to move one. An agent cannot negotiate with its own
repair or rework budget because the budget lives in Python, not in a prompt,
and a stage is complete when the queue says so — not when a model reports
success.

```bash
.venv/bin/python board-game/tools/pipeline_queue.py next    # what runs now (and claims it)
.venv/bin/python board-game/tools/pipeline_queue.py list    # where everything is
```

States: `proposed → rules_ok → briefed → drafted → awaiting_owner → approved
→ built → reviewed → awaiting_ship → shipped`, with `repairing`, `blocked`
and `killed` off to the side. Two drivers can run at once: every
read-modify-write takes a file lock, and `next` hands out a *claim* — a lease
with an expiry — so a tick that lands mid-step is told to wait instead of
spawning a second agent onto the same files. A driver that dies releases its
idea when the lease lapses.

The two owner gates arrive as Telegram messages with buttons. Ship, and a
📦 Publish button follows. `dashboard.py --serve` gives the same decisions a
local web view instead of a chat scrollback.

## Loops

- **In-run:** the clarify loop and rework loop in the rules gate (budgets 3
  and 3), the build/panel repair loop (budget 2), and a re-run of only the
  lenses that failed.
- **Across runs:** every rejection reason is appended verbatim to
  `board-game/TASTE.md`, which the ideator reads before it invents anything.
  It is the only signal in the pipeline that does not come from a model, which
  is why it outranks everything an agent has learned on its own.
- **On the pipeline itself:** `PAIN_POINTS.md` collects what each step found
  awkward, `lessons.md` holds rules that graduated from advice into code, and
  `audit.py` + the `board-game-auditor` agent check the loop is not just
  getting better at its own metrics (`INTEGRITY.md`). `improve.py` runs the
  self-improvement session; it is forbidden from touching `TASTE.md`, the
  threshold baseline, `QUEUE.json`, `ideas/`, and `.env`.

## Layout

| Path | What |
|---|---|
| `.claude/commands/bg.md` | the driver — one step per invocation |
| `.claude/agents/` | ideator, brief-writer, builders, rules engineer, rule animator, independent lenses, auditor |
| `board-game/tools/pipeline_queue.py` | state machine, claims, clarify/rework/repair budgets |
| `board-game/tools/gate.py` | the deterministic build gate (no LLM) |
| `board-game/tools/rules_check.py`, `ergonomics_check.py`, `interference.py` | mechanical checks the gate and brief stage call |
| `board-game/tools/playtest.py`, `table_run.py`, `game_site.py` | scripted engine playtest, LLM-player table, replay/hot-seat website |
| `board-game/tools/animation_gate.py`, `animation_manifest.py` | freshness/approval gate for the rule animation |
| `board-game/tools/telegram.py`, `journal.py`, `dashboard.py` | owner gates, journal narration, local queue view |
| `board-game/tools/publish.py`, `publishdesign/` | ships an approved game to Panda Social |
| `board-game/tools/audit.py`, `improve.py` | integrity checks and the self-improvement session |
| `board-game/prompts/` | the player and adversarial-breaker prompts `table_run.py` sends to each seat |
| `board-game/blocks/` | reusable CAD blocks the builder composes from first |
| `board-game/ideas/<slug>/` | one game: idea.json, brief, draft, project, playtest/, animation/, reference/, verdicts |
| `board-game/site/` | shared JS/CSS the generated per-idea replay sites load |
| `cadcode/` | the CAD skill the builder drives (own LICENSE) |
| `evaluate-cad-reconstruction/` | separate skill: scoring CAD reconstructions |

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python cadquery trimesh numpy manifold3d pillow matplotlib
cp .env.example .env        # Telegram bot token + chat ids
```

The LLM-player table also needs `PLAYTEST_BASE_URL`, `PLAYTEST_API_KEY` and
`PLAYTEST_MODEL` in `.env` (not in `.env.example` — set them yourself); without
them `table_run.py` reports the missing measurement and the rules gate cannot
pass.

Then drive it:

```bash
/bg                          # one step, in Claude Code
/loop 10m /bg                # or let it run
scripts/start-dashboard.sh   # queue + journal + 3D viewer in a browser
.venv/bin/python board-game/tools/game_site.py serve board-game/ideas/<slug>  # one idea's replay/hot-seat site
```

Requires the `claude` CLI, and the `cadcode` skill in this repo (the builder
calls `cadcode/scripts/cad` and `cadcode/scripts/review` directly). The gate
targets a Bambu Lab P2S — 256mm nominal, minus a 5mm margin per side — via
`BED_X_MM` / `BED_Y_MM` / `BED_Z_MM` in `gate.py`. Change those for another
printer. Slicing is optional: without `ORCASLICER_CLI`/`ORCA_PROFILE` set in
`.env`, `gate.py` still runs every mesh check and skips the slice check.

## Publishing needs a second, private repo

`board-game/tools/publish.py` imports a shipped game into Panda Social as a
draft design. It drives `bin/publishdesign`, a Go CLI that must be **compiled
against a checkout of `panda-social-backend`** — a private repo — because it
calls that backend's own `services.ImportDesign`, the same function
`POST /designs/import` runs. That is deliberate: the CDN snapshot, the
`_tree.json` the viewer reads, the GLB, the thumbnails, `root_id` and the
unique slug all come from the backend's code rather than a second
implementation that drifts out of sync with it.

Without that repo, everything up to and including OWNER GATE 2 works; only the
last box in the diagram does not. Nothing else in the pipeline imports it.

```bash
board-game/tools/publishdesign/build.sh [path/to/panda-social-backend]
.venv/bin/python board-game/tools/publish.py <slug> --dry-run
```

`.env` also needs `PANDA_OWNER_ID`, `PANDA_BACKEND_DIR` and
`GOOGLE_APPLICATION_CREDENTIALS` for that half. Mongo and GCS settings are not
duplicated here — the CLI runs with the backend checkout as its working
directory and reads that repo's own `.env`.

Rules changes to an already-shipped game do not mean publishing again — that
would fork it into a second design:

```bash
.venv/bin/python board-game/tools/publish.py <slug> --page         # rules + specs only
.venv/bin/python board-game/tools/publish.py <slug> --new-version  # files again, as v2
```

## What is not in git

Anything a clone can re-derive: exported meshes (`*.stl`, `*.step`,
`*.step.json`), part renders, `build/`, and the deterministic check outputs
(`rules_check.json`, `ergonomics_check.json`). Regenerate them from the source
that is committed:

```bash
.venv/bin/python cadcode/scripts/cad    board-game/ideas/<slug>/project --out-dir board-game/ideas/<slug>/project/build
.venv/bin/python cadcode/scripts/review board-game/ideas/<slug>/project
.venv/bin/python board-game/tools/gate.py board-game/ideas/<slug>/project --bill board-game/ideas/<slug>/project/bill.json
```

What stays is what no clone can re-derive: the source, `gate.json` (a
measurement over one specific source hash), the panel's verdicts, and the two
renders a human actually looked at and approved — `_assembled.png` and
`_qa.png`, under both `reference/` (the approved draft) and
`project/<slug>_review/` (what was built) — plus `playtest/` and
`animation/`, the recorded evidence a game passed the rules gate at all.

`board-game/history/` is the archive of the older turn-based loop, kept out of
the repo; `contact_sheet.py` and `score_build.py` are its tools and read
nothing the current pipeline writes.
