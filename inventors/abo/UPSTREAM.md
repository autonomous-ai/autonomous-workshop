# Upstream provenance — Abstract Boardgame Oracle

Abstract Boardgame Oracle is built from an external snapshot rather than written
here from scratch. This file records where that snapshot came from, exactly
which bytes were taken, what was deliberately left behind, and why. It is the
human-readable half of the guarantee; the machine-checkable half is the `abo`
entry in [`snapshots.lock.json`](../../snapshots.lock.json), verified offline by
[`tools/verify_snapshot_locks.py`](../../tools/verify_snapshot_locks.py).

## Source

| | |
|---|---|
| Repository | `reinSPQR/vibe-ideas` |
| Commit | `a557cacb3d98e5936194e4ba11721809370195f8` |
| Commit subject | Replace legacy CAD pipeline with STEP-first skills |
| Commit date | 2026-08-25 |
| Imported on | 2026-08-26 |
| Recorded in | [`upstreams.json`](../../upstreams.json), role `abstract-boardgame-donor` |

**On the pin.** `upstreams.json` previously pinned this repository at
`ed3d1e876faed95b1bf785af2fae2a8133354517`, recorded during the research pass
that catalogued it as an `inventor-snapshot`. That commit predates the
STEP-first rewrite: at `ed3d1e8` there is no `preview.py`, no
`board-game/tests/fixtures/cad_project/`, and `gate.py` is a 669-line version
that never calls a CAD skill. The design this import implements was written
against the STEP-first tree, so the pin was moved forward to `a557cac` and the
role updated at the same time. The commit and the role are the only fields that
changed; the repository is the same one already reviewed.

**Licence.** There is no repository-level licence file at the pinned commit.
`reinSPQR/vibe-ideas` is a private repository belonging to the same owner as
this one, and this is an internal transfer of that owner's own work rather than
use of a third party's published library. The only `LICENSE` files anywhere in
the upstream tree cover its own vendored `skills/cad` and `skills/step-parts`
(MIT, copyright 2026 Thompson Labs LLC); **neither is imported here** — this
repository carries its own pinned copy of those skills under
[`skills/`](../../skills/), recorded in
[`skills/PROVENANCE.md`](../../skills/PROVENANCE.md), and ABO calls that copy.

## What was imported

Every file below is byte-for-byte as it stands at the pinned commit, with the
single exception recorded under [Edits to vendored
files](#edits-to-vendored-files). Where the import needed to behave differently
in this repository — repository roots, interpreter paths, the CAD skill
location, the bed envelope — that change is made in ABO's own adapter layer
above `harness/`, never inside a vendored file. See design decision D7.

### `harness/` — the imported tooling

From `board-game/tools/` at the pinned commit:

| File | Lines | Upstream role |
|---|---|---|
| `rules_check.py` | 245 | Deterministic rules-versus-bill consistency check. Text only, no CAD, no model judgement. Defines the `idea.json` game record and its per-step `uses` declarations. |
| `playtest.py` | 1,556 | Seeded simulation harness: scripted policies, termination, seat balance, forced-turn fraction, branching, and the skill ladder. |
| `table_run.py` | 1,228 | Model-per-seat table harness. One plain HTTPS call per decision; the loop itself is deterministic code with no agent in it. |
| `gate.py` | 431 | STEP-first manufacturing gate. Shells out to a CAD skill, separates hard `fails` from owner-visible `unmeasured`, and writes source-closure-hashed evidence. |
| `ergonomics_check.py` | 160 | Hand-scale and legibility measurement over built geometry. |
| `preview.py` | 193 | Render and contact-sheet generation from built geometry. |

From `board-game/tests/fixtures/cad_project/` at the pinned commit, into
`harness/fixtures/cad_project/` (10 files): `README.md`, `bill.json`,
`brief.json`, `fixture.step.py`, `fixture_lib.py`, `fixture_spec.md`,
`part_receiver.step.py`, `part_slider.step.py`, `measure/check_fit.py`,
`measure/motion.json`. This is the gate's own fixture project — a two-part
slider and receiver with a declared fit — and it is what lets the CAD
characterization fixture (design D5) run offline against this repository's
locked skill.

### `agents/` — the imported agent definitions

From `.claude/agents/` at the pinned commit:

| File | Lines | Why it came across |
|---|---|---|
| `board-game-ideator.md` | 308 | Invents the complete game — concept, rules, component bill, art direction in form language. This is what ABO's research step is built from. |
| `board-game-rules-engineer.md` | 257 | Compiles locked rules into an executable engine, and must refuse or declare rather than guess where the rules run out. This is what ABO's Make is built from. |
| `board-game-lens-rules.md` | 192 | Adversarial check on the rules themselves — setup privilege, dominant strategy, fake decisions, reachable ending. Maps onto Playtest findings against the rules. |
| `board-game-lens-playtest.md` | 241 | Reads simulation output and judges what it actually showed. Maps onto `game-simulation` findings. |
| `board-game-lens-playability.md` | 51 | Judges whether the rules describe a game worth playing. Maps onto `agent-playtest` and `game-simulation` findings. |

## What was deliberately not imported

Workshop is one-Wish and request-driven. It receives one assignment, does the
work of six jobs, and returns. The upstream pipeline is a continuously-driven
queue with a human owner in the loop. Everything below exists to serve that
shape, and none of it has a place here.

| Not imported | Why |
|---|---|
| `pipeline_queue.py` (1,312 lines) | The queue itself — claims, leases, and stage transitions across runs. ABO receives one assignment and returns; there is no work to poll for and no lease to hold. Cross-run memory of what has already been proposed is Taste's job, not a queue's. |
| `QUEUE.json` | The persisted queue state that `pipeline_queue.py` drives. Importing it would give ABO cross-run state, which the inventor spec forbids outright. |
| The two human owner gates | Upstream holds a run open until a person approves the idea and, later, the published page. Workshop's six jobs contain no human wait: a run either finishes, or parks with a typed `Need`. Owner approval of a published page already lives outside the six jobs. |
| `telegram.py` (672 lines) | The approval channel those gates talk to. A notification channel is the mechanism of a human wait ABO does not have, and an outbound messaging credential has no reason to exist inside an inventor. |
| `dashboard.py` (1,199 lines) | Renders queue state for a human watching the pipeline. There is no queue and no continuous pipeline to watch. |
| `game_site.py` (292 lines) | Builds the per-game web page. Workshop's Instructions job owns the box paper and the customer-facing handoff, and it owns it for every inventor rather than per inventor. |
| `publish.py` (506 lines) | Pushes the finished game to the storefront. Workshop's Deliver job owns production, the carrier, and the receipt; publication authority is a Workshop-level contract, not an inventor's. |
| `journal.py` (385 lines) | Appends a narrative log across pipeline runs. Workshop's runtime already records typed events for one run, and a second cross-run narrative would be exactly the persistent state ABO must not keep. |
| `improve.py` (304 lines) | The upstream improvement loop, with its own repair, rework, and clarification budgets. Workshop has one bounded budget, `playtest_rounds`, and one vocabulary, `Feedback` severity. Three competing counters would give a design flaw a cheaper lane to launder itself into. See design decision D6. |
| `board-game-lens-fidelity.md` | Judges whether built geometry matches its reference *image*. ABO's numbers beat pictures: geometry is measured against the brief's millimetres by `mechanical-test`, and a render is never offered in support of a fit or topology claim. |
| `board-game-lens-animation.md`, `board-game-rules-animator.md`, `animation_gate.py`, `animation_manifest.py` | Produce and judge rules-explainer animation. Nothing in Workshop's six jobs asks for motion, and `agent-playtest` evidence comes from played games rather than from a video of them. |
| `audit.py`, `graduation_check.py`, `contact_sheet.py`, `board-game-auditor.md` | Pipeline-wide reporting and stage-promotion helpers that only mean anything relative to the queue's stages. |

## Edits to vendored files

Design decision D7 allows an imported file to be edited only where the change
cannot be made in the adapter layer, and requires the edit, the regenerated
lock, and this record to land together. One edit meets that bar.

### `harness/table_run.py`

`table_run.py` imports two modules that were deliberately not imported:

```python
import animation_gate  # noqa: E402
import game_site       # noqa: E402
```

Both are executed at module import, so `import table_run` fails outright while
those files are absent — and they are absent by design. No amount of adapter
code runs before an import statement, so this is the one case D7 contemplates.
Three call sites went with them, all of them in the command-line path rather
than in the seat-play loop:

| Removed | Why |
|---|---|
| `import animation_gate`, `import game_site` | Neither module is imported (see the table above). |
| The `animation_gate.evidence(idea_dir)` pre-flight check in `run()` | Gates the run on a rules-explainer animation being complete. Nothing in Workshop's six jobs asks for motion, so this gate would refuse every ABO run over an artifact ABO never produces. |
| `game_site.build_site(idea_dir)` and the two lines printing its replay and hot-seat URLs | Builds and advertises the per-game web page. Workshop's Instructions job owns the customer-facing handoff for every inventor. |
| Four docstring lines describing the page it built and `game_site.py serve` | The behaviour they describe no longer happens; leaving them would make the module lie about itself. |

Nothing else changed: no policy, no measurement, no prompt, no seat boundary,
no wire format. `snapshots.lock.json` was regenerated over the edited tree in
the same change, so the edited bytes are the locked bytes and any *further*
drift still fails verification.

Everything the adapter layer could reach is done there instead, in
[`config.py`](config.py): the repository root, the interpreter, the CAD skill
location, and the usable bed envelope are rebound on the imported `gate` module
at call time, and the model-seat endpoint is read through the Workshop's own
`load_dotenv` under ABO-scoped names rather than through `table_run`'s own
`.env` lookup.

## Editing a vendored file

Do not. `snapshots.lock.json` records the canonical fingerprint of this entire
inventor folder, and `tools/verify_snapshot_locks.py` recomputes it offline on
every check, so a silent byte change fails the build rather than shipping.

Where behaviour genuinely has to differ, change it in ABO's adapter modules
(`concept.py`, `make.py`, `playtest.py`, `config.py`) which sit above `harness/`
and are this repository's own code. Where that is impossible, the edit to the
vendored file, the regenerated lock, and an entry in this file land in one
commit — never separately.
