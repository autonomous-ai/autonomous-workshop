# Upstream provenance — Abstract Boardgame Oracle

ABO's engine and simulation harness are built from an external snapshot
rather than written here from scratch. This file records where that snapshot
came from, exactly which parts were kept, what was deliberately left behind,
and why. There is no `snapshots.lock.json` for this anymore — schema-v8
Inventors carry their own provenance this way, in a skill's `references/`,
and the machine-checkable half is the `artifact_sha256` on this skill's entry
in `inventor.json`, verified by `discover_inventors` and
`tools/verify_skill_locks.py`'s general skill-fingerprinting machinery on
every check.

## Source

| | |
|---|---|
| Repository | `reinSPQR/vibe-ideas` |
| Commit | `a557cacb3d98e5936194e4ba11721809370195f8` |
| Commit subject | Replace legacy CAD pipeline with STEP-first skills |
| Imported on | 2026-08-26 |
| Licence | No repository-level licence file at the pinned commit. `reinSPQR/vibe-ideas` is a private repository belonging to the same owner as this one, and this is an internal transfer of that owner's own work rather than use of a third party's published library. |

This is the same repository and commit an earlier revision of this Inventor
(schema v5, deleted along with the rest of `src/inventor_workshop/` when this
repository adopted the native coding-agent runtime) recorded in its own
`UPSTREAM.md`. This file replaces that one; nothing here changes the pin.

## What is imported today

Only two files, both from `inventors/abo/` at the schema-v5 revision of this
Inventor in this repository's own history (not directly from
`reinSPQR/vibe-ideas`, which they had already been adapted from once):

| File | Role |
|---|---|
| `scripts/game.py` | The game record: title, seats, playtime, complete rules with a per-step declaration of the components each step touches, the component bill, and art direction in form language — plus the deterministic check that the rules and the bill describe one game. Self-contained; no import outside the standard library. |
| `scripts/simulation.py` | The seeded simulation harness: scripted policies of increasing strength (random, greedy, Monte Carlo lookahead, adversarial), batched play with Wilson confidence intervals, seat-balance and distinctness measurement, and the 1,000-completed-game floor. Drives a compiled engine matching the `new_game`/`player_to_move`/`legal_moves`/`apply_move`/`is_over`/`scores`/`winners` contract. |

Design decision D7 names these two as what survives of ABO's original 5,416
lines: "exactly the tested deterministic CAD/domain tools invoked by the
native Inventor subagent" that the architecture sanctions, needed because the
lane's `game-simulation` Playtest check has to run something reproducible.

### `simulation.py` was made self-contained

At the schema-v5 revision, `simulation.py` called `config.load_harness
("playtest")` to reach a ~1,556-line vendored module,
`harness/playtest.py`, for its scripted policies (`pol_random`, `pol_greedy`,
`make_mc`), its batch runner (`run_batch`, `challenge`, `run_sensitivity`),
and its statistics (`wilson`, `seat_edge`). `config.py` and the entire
`harness/` tree are deleted (see below), so keeping `simulation.py` runnable
meant inlining the specific deterministic functions it actually calls,
verbatim except for the module-level rename, directly into `simulation.py`
itself, exposed under a small `_Harness` namespace so every existing call
site (`harness.pol_random`, `harness.run_batch`, ...) still resolves without
change. Nothing about *what* is computed changed — the CLI, table-runner,
model-seat, and human-facing reporting parts of the old `harness/playtest.py`
were not brought across, because `simulation.py` never called them.

## What was deliberately not imported

Workshop's native session, not Python, now does the cognitive and
orchestration work. Everything below either did that work directly, or only
existed to serve a continuously-driven, human-owned pipeline that Workshop's
single-Wish, request-driven run has no equivalent of.

| Not imported | Why |
|---|---|
| `make.py` | Owned a `MakeContext -> Made` contract via a Python callable. The native Make turn does this now, using `scripts/game.py` and `scripts/simulation.py` as tools rather than being orchestrated by more ABO Python. |
| `playtest_job.py` | Owned a `PlaytestContext -> Playtested` contract and built the `Need` a short simulation sample returns. The native Playtest stage and its host gate own this now; `simulation.py`'s own `SimulationOutcome` (`passed`, `meets_floor`, `completed_games`) is what a native turn reads instead. |
| `model_seats.py` | Dispatched one model call per seat over HTTPS from Python — Python-side model dispatch, one of the three named-forbidden mechanisms. |
| `research.py` | Invented the game and stated its physical facts as a Python capability. Invent now owns that native research, selection, and specification work. |
| `feedback.py` | Turned findings into feedback the next round could act on — a Python prompt-chain step. Playtest's native feedback loop does this now. |
| `concept.py` | ABO's old draw-and-seal hook under the deleted `Workshop(concept=...)` capability wiring. The selected design is now sealed by Invent and consumed directly by Make, so there is no separate drawing job to hook. |
| `config.py` | Rebound the vendored harness's repository root, interpreter, CAD skill location, and bed envelope at call time. With `harness/` gone and `simulation.py` self-contained, there is nothing left to rebind; CAD geometry goes through the shared locked `cad` skill directly. |
| `profile.py` | The Wish, `Workshop` construction, and the CLI entry point — a Python-spawned agent process orchestrating an entire run, the second named-forbidden mechanism. The native runtime starts and resumes exactly one root session; there is no Inventor-owned entry point anymore. |
| `cad_compat.py` | Adapted six ways the locked CAD skill differed from what `gate.py` expected. `gate.py` is gone with `harness/`; the native Make turn calls the shared `cad` / `image-to-cad` / `step-parts` skills directly. |
| `manufacturing.py` | Deterministic measurement bound to a source closure, built on top of the vendored `harness/gate.py`. Superseded by the shared Make gate's own component-correspondence and geometry checks. |
| `agents/` (5 files: `board-game-ideator.md`, `board-game-rules-engineer.md`, `board-game-lens-rules.md`, `board-game-lens-playtest.md`, `board-game-lens-playability.md`) | Prompt text for Python-spawned agent roles — Python-composed prompts handed to a subprocess, the third named-forbidden mechanism. Their judgment now lives in this skill's stage-contribution bullets and in ABO's Taste, read directly by the one native session. |
| `harness/` (the whole imported tree: `rules_check.py`, `playtest.py`'s CLI/table/model-seat/reporting parts, `gate.py`, `ergonomics_check.py`, `preview.py`, and the `fixtures/cad_project/` CAD characterization fixture) | Orchestration and CAD wrapping over a repository layout (`.venv`, a bed constant, a CAD skill path) that no longer needs adapting from Python, plus a CLI and human-table-play harness Workshop's native session has no use for. The two genuinely reusable, purely deterministic pieces this tree held for `simulation.py` — the scripted policies and the batch/statistics functions — were extracted into `simulation.py` itself; see above. Everything else in `harness/` (rules-versus-bill checking, STEP-first gating, ergonomics measurement, preview rendering, the CAD fixture) is superseded by the shared Make gate and the shared `cad`/`image-to-cad`/`step-parts` skills. |
| `tests/` (all files except `test_simulation.py`: `test_cad_characterization.py`, `test_feedback.py`, `test_game_research.py`, `test_make.py`, `test_manufacturing.py`, `test_model_seats.py`, `test_playtest_job.py`, `test_profile.py`, and the `fixtures/fixture_game.py` and `fixtures/model_seat_transcript.json` fixtures they alone used) | Tested exactly the orchestration modules above. `test_simulation.py` is kept, adapted only to import `simulation.py`'s own `_HARNESS` namespace instead of `config.load_harness("playtest")`; every assertion in it is unchanged, at `scripts/tests/test_simulation.py`. One of its test methods, which asserted the shape of a `Need` built by the deleted `playtest_job.py`, was dropped rather than adapted, since the native Playtest stage — not this skill — owns that now. |
| `pyproject.toml`, `.env.example`, `.gitignore`, `__pycache__` | Packaging and environment scaffolding for a standalone-runnable Python project. This is a Codex skill's `scripts/` directory now, not an installable package; nothing here needs its own environment file, and `__pycache__` is a reserved name the extension fingerprinter refuses outright. |

None of the above is a claim that the concern it served disappeared. Where
one survives, the capability that now carries it is named above; where it
does not, that is because the mechanism itself — Python composing a prompt,
spawning an agent process, or dispatching a model call — is what the native
architecture forbids, not because the judgment stopped mattering.

## Editing these files

`game.py` and `simulation.py` (apart from the `_Harness` inlining above) are
carried over verbatim. Where behaviour genuinely needs to change, prefer
changing `abo-inventor/SKILL.md`'s stage-contribution guidance or ABO's
Taste first; only edit the scripts themselves when the deterministic
computation itself must change, and update this file in the same change.
