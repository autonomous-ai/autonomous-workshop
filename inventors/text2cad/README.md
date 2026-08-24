# text2cad

> **Monorepo snapshot.** This folder contains the inventor code imported from
> `nohope88/text2cad` at commit `0cb635e`. It is retained as a reference
> implementation while its infrastructure is migrated behind the shared repository root.
> Backups were excluded, including a tracked environment backup with
> live-looking credentials; rotate those upstream credentials before any run.
> See [UPSTREAM.md](UPSTREAM.md) for provenance, licensing, exclusions, and
> known release blockers. The original operating guide follows.

[`TASTE.md`](TASTE.md) defines text2cad's mechanism-first product taste and the
model-default forms it rejects.

Autonomous trend→product pipeline: scans X/HN trends, picks a 3D-printable
product that does not exist yet — the bar is that a judge cannot find it for
sale, checked by search with a URL as evidence — and produces print-ready
`.step`/`.stl` per part, fully automatic, one cycle per day. Multi-part
assemblies preferred: the mechanism is the product.

```
 INPUT ────────────────────────────────────────────────────────────────
   X/HN trends (second-brain MCP)          or a direct prompt
        │                                        │
        ▼                                        │
 ┌───────────────────────────────┐ discover_lessons.md  │
 │ ① DISCOVER — panel            │◀─(taste from human   │
 │                               │   rejects)           │
 │  3 PROPOSE ∥ lanes:           │◀─TASTE.md ── slop    │
 │  mechanism │ optical │ modular│  bans, mechanism     │
 │  search first, 2 candidates   │  vocabulary, dials   │
 │  each, blind to each other    │  NOVELTY/MECHANISM/  │
 │             ▼                 │  ORNAMENT (.env)     │
 │  3 JUDGE ∥ blind: search each │                      │
 │  on Amazon/Etsy/Printables →  │  ⚠ trend input ONLY  │
 │  EXISTS <slug> yes <url>      │    — never lessons.md│
 │             ▼                 │                      │
 │  pick_winner() — no LLM: ONE  │  all found → repropose
 │  listing kills a candidate,   │  once, then no product
 │  survivors ranked by medians  │  today                │
 └────────┬──────────────────────┘         │            │
          │──▶ 📱 Telegram: winner + medians + why it won
          │       (text, ~7min in — does not wait on renders)
          ▼                               ▼              ▼
 ┌──────────────────────────────────────────────────┐
 │ ② BRIEF                                          │
 │ 🔍 web research → ## Not this (3 nearest, differ)│
 │ spec in mm + ## Parts (color, mates) + ## Interf │
 └────────┬─────────────────────────────────────────┘
          ▼
 ┌─────────────────┐
 │ ③ DRAFT CAD     │──▶ hero.png + multi-view ──▶ 📱 Telegram (FYI;
 └────────┬────────┘    saved to reference/         --auto skips waiting)
                        photo caption carries the pitch + scores; no hero.png
                        falls back to a text proposal, never to silence
          ▼
 ┌──────────────────────────────────────────────────┐   ┌─────────────┐
 │ ④ BUILD                                          │◀──│ blocks/     │
 │ golden blocks where they fit (never design-led)  │   │ testbench-  │
 │ visual contract: match reference/ renders        │   │ verified    │
 │ fe_parts/*.stl (print pose) + part_colors.json   │   └─────────────┘
 │ writes fit_checks.py from Interfaces + Parts     │
 └────────┬─────────────────────────────────────────┘
          ▼                                  lessons.md
 ┌──────────────────────────────────┐   (hard rules, injected
 │ ⑤ GATE  (no LLM)                 │    into BUILD + REPAIR
 │ per PART: watertight? 1 body?    │     only — see DISCOVER)
 │ overhang, bridge, 160mm footprint│        ▲
 │ OrcaSlicer real slice + print est│        │ repeated lesson MUST
 │ lesson-linter on code            │        │ graduate to code
 │ runs fit_checks.py               │        │
 └────────┬─────────────────────────┘        │
          ▼                                  │
 ┌──────────────────────────────────┐        │
 │ ⑥ PANEL — 3 independent lenses   │        │
 │ printability │ fidelity │ sell   │        │
 └────────┬─────────────────────────┘        │
          ▼                                  │
 ┌──────────────────────────────────┐        │
 │ ⑦ REPAIR (severity-tiered)       │────────┘
 │ broken 2 / functional 3 / cosm 2 │──▶ budget exhausted
 │ re-gate + rescore failed lenses  │    → 📱 ESCALATE
 └────────┬─────────────────────────┘
          ▼ all green
 OUTPUT ──────────────────────────────────────────────────────────────
   out/<slug>/  <slug>.step + <slug>.stl (assembled) + renders
                + fe_parts/*.stl + part_colors.json (viewer paints these)
                + review notes + run.json (cost/turns per phase)
```

## Loops & self-improvement

- **In-run:** build loop (cad tool JSON), repair loop (tiered), panel rescore
  (failed lenses only).
- **Across runs:** every repair appends a lesson; a lesson that repeats MUST
  graduate to code (gate linter / golden block / brief constraint) — never
  advisory text twice. Human rejects teach `discover_lessons.md`.
- **Weekly:** `improve.py` analyzes the week's runs and improves the pipeline.
  Doc-tier changes (lessons) merge to main; **code-tier changes go to a PR**
  for human review. `blocks/` is human-approved by policy (SkillsBench 2026:
  human-curated skills +16.2pt vs ~0 LLM-authored).

## Models

Per-phase model via `{PHASE}_MODEL` in `.env` — e.g. `BUILD_MODEL`,
`LENS-FIDELITY_MODEL` (phase name uppercased). Default: `claude-sonnet-5`
direct; if the `PANDA_DEV_KEY` proxy is enabled, values must use the proxy's
`anthropic,claude-opus-5` format instead.

Current mix (since 2026-08-12) — Opus 5 where mistakes cascade, Sonnet 5
default elsewhere:

| Phase | Model | Why |
|---|---|---|
| discover, brief, build | Opus 5 | spec/code errors cascade downstream |
| arbitration | Opus 5 | judgment call, no retry |
| repair2, repair3 | Opus 5 | escalation ladder above Sonnet repair1 |
| lens-fidelity | Opus 5 | on Sonnet it chronically exhausted 35 turns (2 runs, 2 timeouts) |
| draft, other lenses, repair1 | Sonnet 5 (default) | cheap, re-gated / rescored anyway |

Pre-mix `.env` kept at `.env.bak-pre-modelmix`.

## Ops (panda, UTC)

| Cron | What |
|---|---|
| `15 0 * * *` | `autoloop.py` — daily cycle, lessons auto-commit, Telegram summary |
| `0 1 * * 0` | `improve.py` — weekly self-improvement session |
| `0 4 * * *` | `watchdog.sh` — dead-man alert if heartbeat >28h stale |

## Multi-part colors (publish lane)

A multi-part design ships per-part STLs in `out/<slug>/fe_parts/` (named
`assembled_<part>.stl`) and its colorway in `out/<slug>/part_colors.json`
(`{"assembled_foo.stl": "#hex"}` — authored by the design phase). `publish.py`
then does the rest automatically:

1. `gcs_upload_project.py` uploads assembled.stl + the fe_parts siblings +
   `_tree.json` to the history CDN prefix.
2. `fe_colors.py` keys the colors the way the FE actually resolves them:
   `render_three43_fe.mjs FE_DUMP_GROUPS=1` dumps the FE part numbering
   (contact-face slivers TAKE part numbers — ecm-website known bug, so plain
   filename keys miskey any fragmented assembly), each group is owned to its
   part geometrically, and the result is upserted onto the history's
   `thumbnail_jobs` doc (`assembly_parts` + `part_colors`), then re-verified
   with `FE_STRICT=1` (exit 4 = a real part would still render white; Telegram
   warns). Single-mesh designs skip cleanly. Manual run:
   `/root/.local/bin/uv run --with trimesh --with numpy --with pymongo python fe_colors.py <slug> [--dry-run]`

No fe_parts dir -> viewer shows the assembled mesh uncolored (publish-seed
white), same as before.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python cadquery trimesh numpy manifold3d
cp .env.example .env   # fill Telegram creds; OrcaSlicer paths for slice gate
./text2cad "phone stand with cable slot"      # one-shot
./text2cad --discover                          # proposal only
./text2cad --discover --auto                   # full cycle
```

Requires: `claude` CLI (authenticated), `uv`, OrcaSlicer (optional, for the
slice gate), the `cadcode` + `shape-analysis` skills in `~/.claude/skills/`,
and the `second-brain` MCP registered (trend source).
