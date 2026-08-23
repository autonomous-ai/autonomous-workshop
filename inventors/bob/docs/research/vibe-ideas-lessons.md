# vibe-ideas — deep read for Bob

Source: https://github.com/reinSPQR/vibe-ideas, cloned shallow (depth 5) to
`/tmp/bob-research-vibe-ideas`, HEAD `ed3d1e8` ("Update README"), read 2026-08-22.
This is the in-house board-game inventor pipeline: ideate → rules gate (checked,
lensed, machine-played, LLM-table-played) → brief → CAD draft → owner gate 1 →
build → deterministic gate → review panel → owner gate 2 → ship → publish to
Panda Social as a draft design.

**Run record (QUEUE.json, 2026-08-13 → 08-21): 6 ideas, 1 shipped (Millbind,
~12h idea-to-ship), 1 owner-killed (Deep Claim), 3 rewound to `proposed` by the
playtest gate, 1 fork (overcap-v2). Armillary burned 6 CAD repair rounds + 2
arbitration amendments on a design whose *rules* later failed** — the single
most expensive lesson in the repo, and the reason the rules gate now plays the
game before any CAD is paid for.

---

## 1. What Bob should reuse verbatim

### 1.1 The queue as the only decision-maker — `board-game/tools/pipeline_queue.py` (1294 lines)

The single best file in the repo. Core ideas, all directly liftable:

- **The unit of work is an idea, not a tick.** "For fifteen turns an idea that
  died of an infrastructure fault was replaced by a fresh one and nothing was
  ever finished. Now the unit of work is an idea, not a turn, and an idea only
  leaves the queue by shipping or by being killed for a stated reason"
  (module docstring). Bob's daily/hourly ticks must advance existing games
  before inventing new ones.
- **Budgets live in code, not prompts.** "An agent that can read its own budget
  in its own prompt is an agent that will negotiate with it. Same for state
  transitions — a stage is complete when this file says so, not when a model
  reports success." Bob's reward/iteration budgets belong in the Python
  harness, never in the agent context.
- **`next` claims what it hands out.** State says where an idea *got to*; a
  claim (lease, `CLAIM_TTL_SECONDS = 45*60`) says someone is *moving it*. Two
  drivers on a short loop cannot double-spawn onto the same files; a crashed
  driver's lease lapses within the hour. `propose` gets its own claim
  (`propose_claim`) because it has no slug yet. `release <slug>` ends a step
  without faking progress.
- **fcntl lock + transaction around every read-modify-write** (`locked()`,
  `transaction()`, `LOCK_TIMEOUT_SECONDS = 30.0`), **atomic tmp+rename save**
  so a dashboard reading without the lock never sees a half-written file.
- **`PRIORITY` = closest-to-shipping first**: `["reviewed", "built",
  "repairing", "approved", "drafted", "briefed", "rules_ok", "proposed"]` —
  "finishing something beats starting something. `proposed` sits last so a
  backlog never crowds out a build."
- **`EXPECTED_STATE` guards on every owner verb** — a stale Telegram button tap
  ("approve" on a message from three days ago) is *refused* by state check
  instead of silently corrupting the queue. This was added after real damage
  ("a stray tap could silently corrupt it — e.g. `approve` freezing a
  pre-rework render as the reference").
- **`unmeasured` follows the idea to ship.** A gate check that reached no
  verdict does not fail (false alarms get gates routed around "within a week")
  but is carried in QUEUE.json and blocks `ship` until the owner writes
  `--accept-unmeasured "why this is fine"` — the one place "nothing looked at
  this" costs anything, and only a human can pay it.
- **`reject --reason` appends verbatim to TASTE.md** and is called "the single
  most valuable sentence in this pipeline."

### 1.2 The clarify/rework budget machinery (same file)

Three separate budgets, each with a stated rationale:

- `REPAIR_BUDGET = 2` (CAD repair): "past two rounds the problem is usually the
  spec rather than the code" (imported from text2cad evidence). Exhaustion →
  arbitration (`brief_proposed.json` + owner `amend`, which **resets the budget
  because an amended brief is a different design** — and only a human can reach
  that path).
- `REWORK_BUDGET = 3` (rules-gate mechanic defects): "an idea still failing
  after three balancing passes is a shape problem, not a tuning one."
  Exhaustion on next failed gate → **killed automatically**, reason to TASTE.md.
- `CLARIFY_BUDGET = 3` (ambiguity-only fixes, free of the rework budget but
  bounded, "because an unbounded free lane is how a design flaw gets laundered").

The anti-laundering mechanism is the jewel: **`mech_surface(idea)`** hashes
exactly the mechanic-defining fields (`action_types`, `rules.win` whole block,
`players` min/max, each component's `name/qty/per_player` — deliberately *not*
`desc`, wording, `concept`, `art_direction`). A clarify round freezes the hash;
`_settle_clarify_round()` re-computes it on the idea's next queue action and, if
it moved, **converts the round after the fact**: refund clarify, charge rework,
log it. "The disposition is the gate's to assign and the queue's to enforce,
not the fixer's to claim."

Reworks require a **`rework_plan.json`** validated by `_validate_rework_plan()`
with required keys `problem_id, observation, hypothesis, test_question,
confounds, options, chosen_strategy, expected_experience_change,
falsification_condition, change_level, must_preserve_checks, anti_goal_checks,
secondary_risks`; options **must include `subtract` and at least one of
`rollback`/`replace`** ("a patch is not a diagnosis"); a `problem_id` that
recurs (occurrence ≥ 2) forbids another patch (`required_strategy:
"structural"`); `change_level: high` is refused outright — fork or kill.
A post-rework failure with a *new* problem_id must declare `--lineage
caused-regression|new-independent` and `--severity lower|equal|higher|contract`;
`caused-regression` at equal-or-worse severity is a **CASCADE STOP** (exit 2,
state → `blocked`): "Revert that candidate or fork/kill the design; do not add
a compensating rule." This is a complete, working defense against the A→B→C
repair-chain failure mode of LLM design loops. Bob should port it whole.

Post-rework promotion rule (`_rules_ok_gate_complete`): `review_playtest.md`
must carry `Target-result: fixed`, `Regression-result: clean`, and
`Clean-games: ≥2` before the candidate becomes baseline — and the review file
must be **newer than idea.json** (mtime), which is what catches stale verdicts.

### 1.3 TASTE.md — the owner-signal file

471 bytes, and the highest-leverage file per byte: "Every line here is a
rejection reason, verbatim. This is the only signal in the pipeline that does
not come from a model, so it outranks every heuristic an agent has learned on
its own." Written only by `cmd_reject`; on improve.py's FORBIDDEN list ("a
pipeline that can edit it can talk itself into anything"). Current sole entry:
Deep Claim — "The game rule sound so boring, and it seems like there is an
optimal strategy for the first player to always win than can be easily figured
out." For Bob: replace "owner rejections" with "owner rejections + marketplace
signal," but keep the invariant that the file is append-only from human/market
events and never editable by the self-improvement loop.

### 1.4 lessons.md graduation — prose must become code

The rule: **a lesson that appears twice must GRADUATE into code** and be marked
`[GRADUATED -> target]`, where the target is machine-checkable
(`module.SYMBOL` or `module:"literal"`, held to the tree by
`graduation_check.py` — "a marker that has quietly stopped being true is worse
than one that never graduated"). The tier ladder (land the fix as far upstream
as it goes) is worth copying verbatim:

| tier | lands in | non-deterministic hops to geometry |
|---|---|---|
| planner | ideator, rules_check | defect never proposed |
| block | blocks.py | one hop, right by construction |
| brief | brief_writer | two hops, template-enforced |
| prompt | builder | two hops, nothing verifies compliance |
| check | gate, checks, queue | after the build is already paid for |

"A check is a smoke alarm. It works, and the house burns on schedule."
Check-tier graduations must carry `| ceiling: <why nothing upstream holds it>`
or audit.py flags them every run.

### 1.5 The empirical rules gate — `playtest.py` (no LLM) + `table_run.py` (LLM seats, no agent)

`playtest.py` (gate R1c): an agent writes `playtest/engine.py` from idea.json
under a hard contract (`new_game, player_to_move, legal_moves, apply_move,
is_over, scores, winners`, plus `determinize`/`observation` for hidden info,
`ASSUMPTIONS` registered instead of guessed — "a rules gap found while writing
the engine is worth more than any number below"). Then thousands of scripted
playouts measure: termination, deadlock, forced-move share
(`MAX_FORCED_FRACTION = 0.25`), branching (`MIN_MEDIAN_BRANCHING = 3.0`), skill
ladder (`MIN_SKILL_EDGE = 0.15` over random), **seat bias (`MAX_SEAT_EDGE =
0.10`) — "the one that Deep Claim died of"**, runaway leader (`MAX_RUNAWAY =
0.85`), tie rate (0.25), length sanity (`SECONDS_PER_DECISION = (8, 25)`,
`LENGTH_TOLERANCE = (0.5, 2.5)`), dead moves, and assumption sensitivity
(`SENSITIVITY_DELTA = 0.10` — flip each assumption both ways; if headline
numbers move, the ambiguity is blocking). `DEFAULT_GAMES = 400`. The file
honestly labels all thresholds "UNCALIBRATED... A threshold that cannot
separate [Millbind from Deep Claim] is not a threshold, it is decoration."

`table_run.py`: one model per seat, and the loop is deliberately **code, not an
agent**: "An LLM running this loop can play a turn for a player who is slow,
quietly answer a rules question it should have recorded as a finding, show one
seat what another seat is holding, or run the game again because the first one
was dull... Here they are not prohibited, they are absent: this process has no
way to express them." A seat is one plain HTTPS call (stdlib `urllib`), chooses
**by index** from engine-generated legal moves (cannot cheat or misremember),
sees only `observation(state, seat)`. Speaks both wire formats (`--wire
anthropic|openai`). Env: `PLAYTEST_BASE_URL`, `PLAYTEST_API_KEY`,
`PLAYTEST_MODEL` from repo `.env`. Exactly 4 games at `players.max`: game 1
fresh seats, games 2–3 carry in-run learning, game 4 injects archived
player-facing experience from prior iterations (never engine state, metrics, or
reviewer verdicts — `table_experience()` in pipeline_queue.py enforces the
allowlist). Seat prompts live in `board-game/prompts/player.md` and
`breaker.md` as editable prose. Every session replays from seed + recorded
choice indices, so a mid-run engine edit is caught. `game_site.py` builds a
static replay site + server-backed hot-seat play from the same engine ("a
JavaScript rewrite of the rules... can silently disagree with the gate").

Hard-won operational constants worth stealing: `THINKING_BUDGET = 8192` with
`DEFAULT_MAX_TOKENS = 16000` above it (Millbind produced clean 200 streams that
were 100% thinking and zero text when thinking shared the answer budget);
`PLAYABLE_BRANCHING = 60` (110-option millbind midgame turns 504'd/emptied —
"the branching factor is itself the finding"); `GATEWAY_RETRIES = 5` with
doubling backoff from `RETRY_BACKOFF = 4.0`.

### 1.6 The deterministic gate — `gate.py`, "the part that cannot be talked out of a verdict"

No LLM. Nine checks in order, all run even after a failure so a repair round
sees everything at once: build (CAD kernel warnings block), bill (name-prefix
match, `tile` qty 48 → `tile_01..tile_48`), pieces (one watertight body each),
envelope (per-part vs sorted extents, never the assembly bbox), printability
(best of six axis-aligned orientations — as-modelled would fail printable
parts), interference (shared volume between placed parts; moving parts swept
via `motion.json`), slice (OrcaSlicer once per distinct shape), project-owned
`fit_checks.py`, lint (graduated lessons). Thresholds: bed 256³ −5mm margin,
`OVERHANG_FAIL_PCT = 50`, `BRIDGE_SPAN_MAX_MM = 25`, `MIN_BODY_VOLUME_MM3 =
20`. "Thresholds in this file are code-tier: improve.py may propose changes to
them only through a PR, never by editing at runtime. An agent that can lower
its own bar does not have a bar."

### 1.7 Self-improvement with authority tiers — `improve.py` + `audit.py` + `thresholds_baseline.json`

`improve.py` runs a one-shot headless session: `claude -p <prompt> --model
claude-sonnet-5 --allowedTools Bash,Read,Write,Edit,Glob,Grep --add-dir <root>
--max-turns 80 --output-format json`, timeout 2h — exactly the harness shape
Bob plans. Mechanics to copy:

- **Evidence first**: the prompt embeds `evidence()` — queue-state counts, gate
  failure kinds from every gate.json, `repeated_lessons()` (difflib ratio ≥
  0.75 near-verbatim + content-word overlap ≥ 0.35, with measured
  justification for both numbers) — "work only from it. A change with no
  evidence behind it is a preference."
- **Three authority tiers decided mechanically**: DOC (lessons, BLOCKS.md
  prose, PAIN_POINTS, README → commit direct), CODE (gates, thresholds,
  blocks, agents, improve.py itself → branch `improve/<date>` + PR), FORBIDDEN
  (TASTE.md, thresholds_baseline.json, QUEUE.json, ideas/, .env → **any touch
  reverts the whole session**).
- **All suites must pass or everything reverts** — "no partial credit for a
  change that broke the checks that prove the change was safe." Dirty tree
  refuses to start.
- **Tighten freely, loosen only by PR**: "You may TIGHTEN a threshold with
  evidence. Loosening one is a PR for a human to decide."

`audit.py` (exit 0 green / 1 amber / 2 red) checks eight risks; the four worth
naming for Bob: **GATE EROSION** (live thresholds vs `thresholds_baseline.json`
— only *loosening* flags, and the baseline is forbidden to the improver, so the
improver can't re-record it), **SHIPPED WITHOUT MEASUREMENT** (nothing shipped
without a passing gate.json), **DEGENERACY** ("optimising for pass rate rewards
proposing simpler games" — watch part families / piece counts / relief depth
drift down), **GRADUATION ROT** (deleted code a lesson claims to live in).

### 1.8 Owner gates over Telegram — `telegram.py` + `journal.py`

Two channels, one bot: `TELEGRAM_CHAT_DM` ("every message in it needs you") and
`TELEGRAM_CHAT_JOURNAL` (chatty story, "nothing in the pipeline ever reads it
back"). Unset → messages print to the terminal, "the gate still happens." Only
`journal.py rules_ready <slug>` may post to the journal channel (proposal +
approved rule-animation video + replay-site link, deduplicated by idea hash);
everything else is local JSONL for the dashboard — "Nothing in the pipeline
may read the local journal log... This keeps narrative history from becoming
another input agents learn to optimise."

Buttons carry `callback_data = "<verb>:<slug>"` with a closed verb set
(`ALLOWED_VERBS = {approve, reject, rework, ship, amend}` + `publish` offered
only after a successful ship); `reject`/`rework` open a `force_reply` prompt
for the reason; every tap answers the callback, strips the keyboard
(`editMessageReplyMarkup` with empty `inline_keyboard`) so it can't be tapped
twice, and `disable_stale()` strips the previous gate message's buttons before
a new one goes out. `poll` runs once per pipeline step; `listen` long-polls.
`heartbeat` writes `.heartbeat`; `watchdog --max-hours 28` alarms on silence —
"a pipeline that stops running looks exactly like a pipeline with nothing to
do, until you check a month later."

### 1.9 The driver contract — `.claude/commands/bg.md` (509 lines)

"Do exactly one action, then stop... a step that quietly does three things is
a step nobody can inspect." Poll → `next` → run exactly the named action →
`advance` or `release`. Closing rules for the agent, verbatim: never edit a
gate/threshold/bill/brief to make something pass; never report an unrun check
as passed; never fabricate a stage ("an idea that dies of a tooling fault is
retried, not replaced"); never work on an idea `next` did not hand you; never
edit a claim by hand. Bob's tick-driver prompt should be a direct adaptation.

---

## 2. What demonstrably failed or is weak (evidence)

1. **CAD before rules-validation wasted the whole repair economy.** Armillary,
   QUEUE.json log 2026-08-17: "board-game-lens-rules FAIL (no reachable ending
   at 2p, denial layer dominated, memorisable turn) plus PLAYTEST FAIL at 192
   turns against a claimed 30 min; ideator reworked the rules, **so the two
   exhausted CAD repair rounds were spent on a design that no longer exists**."
   By then Armillary had consumed 6 repair rounds and 2 owner arbitration
   amendments (log 08-14 04:10 → 05:28). The playtest gate was built *after*
   this. Bob must sequence: no expensive artifact work until the game has been
   machine-played and LLM-table-played.

2. **Reading rules does not find ambiguity; only playing does.** PAIN_POINTS
   2026-08-17: "Three ideas, three blocking `rules_ambiguous` findings on their
   first ever `playtest.py` run (armillary `clear_repeat` 22%, blindcap
   `contested_grove_per_crown` 100%, spineward `rob_needs_target_pearls`
   100%). **All three had already passed `rules_check.py`, and two had a
   `board-game-lens-rules` PASS.**" A schema check plus an LLM reading lens is
   not a rules gate; an executable engine + playouts is.

3. **Stale artifacts silently judge dead designs.** PAIN_POINTS 08-17
   (driver): after Armillary's rework "armillary's engine still modelled
   zenith wells, the CLEAR action and the alignment-dependent ending, all of
   which the rework deleted, and `playtest.py` would have measured that dead
   game and printed a verdict with no indication anything was wrong." Fix that
   landed: mtime comparisons in `_rules_ok_gate_complete` (review older than
   idea.json refuses) and `table_experience` (summary older than idea.json is
   discarded). Bob: every verdict artifact must be provably bound to the
   version it judged (hash, not just mtime, ideally).

4. **A scheduler hole made a state invisible.** PAIN_POINTS 08-13: `PRIORITY`
   omitted `"drafted"`, so `next` "reported 'the queue has nothing to advance'
   and silently defaulted to `propose`" while Armillary sat stuck. "This would
   have silently stalled every future idea at the same point." Bob: assert
   `set(PRIORITY) ∪ {terminal/waiting} == set(PIPELINE)` at import time — a
   one-line test the original lacked.

5. **The owner is the throughput ceiling.** QUEUE.json: Armillary drafted →
   `awaiting_owner` 08-13 17:08, approved 08-14 01:13 (8h); every idea has two
   blocking human gates plus arbitration. Fine for a supervised pipeline; for
   Bob's "publish as an AI creator" ambition, gate 1 (worth building?) is the
   one to automate first — the marketplace can be the taste signal — while
   keeping the publish-flip human. Note vibe-ideas *chose* the opposite: every
   ship is human, publish stops at DRAFT, and "the draft→public flip stays a
   human action in the app."

6. **The predecessor loop (INTEGRITY.md, turns 11–15) is a catalog of what a
   score-driven loop does wrong.** It scored builds (`total_100`,
   `vision_fidelity_60`) and the audit caught: a canary control never exercised
   in 15 turns ("if turn 16 also produces no canary build, that is a broken
   pipeline-drift control"); two scorer bugs silently *understating* results
   (prefix-match part binding forcing `unbindable`, `part_clearance` reporting
   0.0mm for any recessed part touching its own recess floor); a mechanical RED
   for a double-submitted build with no written retry policy. The rebuild's
   answer was to **delete the score entirely** — audit.py's docstring: "what
   the pipeline could still do to itself, **now that it has no score to
   inflate**." For Bob, which *wants* an RL-flavored reward: the reward must be
   external (marketplace events, owner taps), never a self-computed rubric the
   loop can optimize, and every threshold needs a baseline file the improver
   cannot touch.

7. **Weak spots acknowledged in-repo, still open:** playtest thresholds
   uncalibrated (n=2 ground truth: Millbind shipped / Deep Claim killed);
   `repeated_lessons()` is "a floor, not a ceiling" (a real paraphrase pair
   scored 0.536, below the 0.75 verbatim bar); `prior_art_search.sh` novelty is
   self-attested prose ("nothing records that they were actually run... a
   `--log` flag... would make the confirming pass auditable" — PAIN_POINTS
   08-14); rules_check can't express variant groups, shared-supply
   sufficiency, or derived quantities (three separate PAIN_POINTS entries);
   worktree-isolated shells can't reach `.env`, blocking the table gate from a
   worktree (08-17).

---

## 3. Exact integration contracts

### 3.1 Publish to Panda Social — `publish.py` + `publishdesign/main.go`

**There is no HTTP API call.** The Go binary `bin/publishdesign` is compiled
*inside* the `panda-social-backend` checkout (build.sh copies main.go into
`<backend>/cmd/publishdesign`, builds, removes) and calls
`services.ImportDesign` / `ImportDesignVersion` in-process — "the same function
POST /designs/import runs" — plus `svc.UpdateUseCase`, `svc.ReplaceStoryBlocks`,
and a direct Mongo `store.UpdateFields(..., {"print_specs": ...})`. Mongo/GCS
coordinates come from the backend's own `.env` via godotenv (child runs with
`cwd=<backend>`); publish.py passes a deliberately minimal env: `PATH`, `HOME`,
`GOOGLE_APPLICATION_CREDENTIALS` only.

Env (repo `.env`):

| var | meaning | default |
|---|---|---|
| `PANDA_OWNER_ID` | 24-hex Mongo user id owning the designs (must exist, or the design is an invisible orphan) | required |
| `PANDA_BACKEND_DIR` | panda-social-backend checkout | `../panda-social-backend` |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCS service-account json | `<backend>/secrets/gcs-sa.json` |
| `PANDA_APP_URL` | only to print `<app>/design/<slug>` link | optional |

CLI invocation (first import):
`publishdesign -owner <hex> -content <page.json> -zip <slug.zip> -thumbs
cover1.png,cover2.png -title T -desc D -prompt P -tags
"board-game,3d-print,cadquery" -status draft [-dry-run]`.
Updates: `-design <id> -zip ...` (new file version) or `-design <id> -content
...` (page rewrite) — **never re-import; "a second import would fork the game
into a second design."**

Content contract (`-content` JSON, validated by the backend's own
`models.ValidateDesignContent` before anything is written):
- `use_case`: `{label, body, image}` — empty image is filled with the design's
  own cover after import.
- `story_blocks`: `[{lead, body}]`, **body 180–400 runes, max 10 blocks**
  (`BLOCK_MIN, BLOCK_MAX, MAX_BLOCKS = 180, 400, 10`, mirrored from
  `models/design_content.go`). The rules ship in three places: complete
  `RULES.md` zipped into the design folder (no length limit), story blocks as
  the page walkthrough (last slot spent *saying* it was truncated —
  `RULES_CLOSING`), and the description pitch (`MAX_DESC = 900`; API allows
  2000, "a store blurb has no business being longer").
- `print_specs`: `{materials, part_count, dimensions_mm{x,y,z}}` — dimensions
  are the **largest single part's bbox** ("will it fit my bed"), and weight is
  deliberately omitted because a curated value permanently outranks the
  slicer's measured one (`models.MergedPrintSpecs`).

Zip: project folder wrapped in one dir named `<slug>/` (the layout
`findDesignFolder` expects; folder name feeds `detectPrimarySTL`), skipping
`__pycache__/.git/.claude/.idea/.vscode`, `.pyc/.pyo`, `.DS_Store`, and
`build/` when the root already carries the same assembled STL. Thumbs: cover
order `("_assembled.png", "_qa.png")`, max 5, index 0 = cover; png/jpg/webp.

Refusals: queue state ≠ `shipped` (unless `--force`), `gate.json` missing or
`pass: false`, already in `published.json` (idempotent no-op). Result JSON
(stdout last line) → `published.json`, real example
(`ideas/millbind/published.json`): `id 6a7ede3376c66515a8c43b58`, `slug
millbind`, `status draft`, `history_id`, `project_url
https://cdn.autonomous.ai/panda-social/<id>/<history_id>/`, `snapshot_bytes
30211204`, `thumbnails [...]`, `applied ["use_case","story_blocks(10)",
"print_specs"]`, plus `published_at`, `owner_id` added by publish.py.
`importTimeout` 30 min in Go; 3600s subprocess timeout in Python.

**Bob implication:** publishing = a Python wrapper deciding *whether*, a
backend-native import doing *how*, always landing as **draft**, with
`published.json` as the idempotency receipt and `--page`/`--new-version` as the
only update paths. If Bob publishes via the public Panda Social HTTP API
instead, mirror the same shape: import once, update in place, never re-import.

### 3.2 Telegram owner gates — `telegram.py`

Env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_DM`, `TELEGRAM_CHAT_JOURNAL` (all in
repo `.env`; unset → terminal fallback, gate still happens). Transport is
`curl` to `https://api.telegram.org/bot{token}/{method}` — methods used:
`sendMessage` (3500-char chunks, `--data-urlencode text=...`, optional
`reply_markup` on last chunk), `sendPhoto`/`sendVideo` (`-F photo=@file`,
caption split at 1024 on paragraph/line/word boundary, remainder as follow-up
message), `editMessageReplyMarkup` (strip stale keyboards),
`answerCallbackQuery` (always, or the button spins; answered *before* the
minutes-long publish runs), `getUpdates` (offset long-poll).

Message contracts: gate 1 = hero render + buttons
`[{✅ Approve|approve:<slug>}, {❌ Reject|reject:<slug>}, {🔧 Rework|rework:<slug>}]`
+ one-screen rules summary as follow-up ("a gate nobody reads is a gate that
always says yes"); gate 2 = render + `ship:<slug>`/`reject:<slug>` + gate
stats, lens verdict first-lines, and the NOT MEASURED list *before* the Ship
button; arbitration = `amend:<slug>`; post-ship offer = `publish:<slug>`.
`reject`/`rework` taps open a `force_reply` reason prompt tracked in
`.telegram_pending.json`. State files: `.telegram_offset`,
`.telegram_pending.json`, `.telegram_messages.json` (per-slug last
button-bearing message, for `disable_stale`). `run_pipeline()` whitelists two
executables only — pipeline_queue.py for the five queue verbs (60s timeout),
publish.py for `publish` (1800s). Free-text pasted commands still work
(`approve armillary`) — "the button is a shortcut, not a replacement."

### 3.3 LLM table endpoint — `table_run.py`

`PLAYTEST_BASE_URL` + `PLAYTEST_API_KEY` + `PLAYTEST_MODEL` from `.env`
(`load_env_file` reads only the named keys, never prints values). Path logic:
base ending in `/v\d+` is used as-is, else `/v1/` is inserted; tails are
`messages` (anthropic wire, header `anthropic-version: 2023-06-01`) or
`chat/completions` (openai wire). Output: one session json per game +
`playtest/table/run_<wire>.json` summary.

---

## 4. States and budgets

### 4.1 State machine (`PIPELINE`, pipeline_queue.py)

| state | action `next` runs | on success → | notes |
|---|---|---|---|
| `proposed` | `rules_gate` | `rules_ok` | rules_check → lens_rules → engine → playtest.py → animation + lens → table_run → lens_playtest; `advance --to rules_ok` refuses without a fresh `review_playtest.md` |
| `rules_ok` | `brief` | `briefed` | brief-writer + ergonomics_check.py |
| `briefed` | `draft` | `drafted` | fast real geometry + renders |
| `drafted` | `owner_gate_1` | `awaiting_owner` | playability lens first, then Telegram gate 1 |
| `awaiting_owner` | *(none — skipped)* | — | owner: approve / reject / rework |
| `approved` | `build` | `built` | approve froze draft renders into `reference/` (visual contract) |
| `built` | `panel` | `reviewed` | 3 lenses spawned concurrently, blind to each other |
| `reviewed` | `owner_gate_2` | `awaiting_ship` | Telegram gate 2 |
| `awaiting_ship` | *(none)* | — | owner: ship (+`--accept-unmeasured`) / reject |
| `repairing` | `repair` | `built` | inside the claiming step; lease renewed |
| `shipped` / `killed` / `blocked` | *(none)* | — | blocked = arbitration or cascade stop; only owner `amend` exits it |

Priority: `reviewed > built > repairing > approved > drafted > briefed >
rules_ok > proposed`. Nothing advanceable → `propose` (with its own claim).

### 4.2 Budgets and leases

| constant | value | on exhaustion |
|---|---|---|
| `REPAIR_BUDGET` (CAD, per design) | 2 | arbitration (`brief_proposed.json` → owner `amend` resets) or `stuck` escalation |
| `REWORK_BUDGET` (rules mechanics) | 3 | next failed gate → auto-`killed`, reason → TASTE.md |
| `CLARIFY_BUDGET` (rule text only) | 3 | same kill path; mech-surface change converts round to rework retroactively |
| `CLAIM_TTL_SECONDS` | 45 min | lease lapses, work re-handed out |
| `LOCK_TIMEOUT_SECONDS` | 30 s | stuck-process error, names the lock file |
| watchdog `--max-hours` | 28 | Telegram alarm on silent pipeline |

### 4.3 Gate / playtest thresholds (baseline-pinned in `thresholds_baseline.json`)

Gate: bed 256×256×256 −5mm margin · overhang fail 50% · bridge 25mm · min body
20mm³ · min relief 0.6mm · min grasp 8mm · finger room 12mm · min protrusion
2mm · max stack aspect 3.0 · seat clearance 0.4mm · CAD wall clock 180s.
Playtest: forced ≤ 0.25 · branching ≥ 3.0 · skill edge ≥ 0.15 · seat edge ≤
0.10 · runaway ≤ 0.85 · ties ≤ 0.25 · undefined share ≤ 0.15 · sensitivity Δ
0.10 · 400 games / 120 ladder games / 240 MC rollouts / 900s deadline.

---

## 5. Bob design directives distilled

1. Port `pipeline_queue.py` nearly whole: transactionful queue, claims/leases,
   PRIORITY, EXPECTED_STATE, unmeasured-carried-to-ship, TASTE append on kill.
   Add the missing import-time PRIORITY/PIPELINE consistency assert.
2. Keep all budgets, dispositions, and the mech-surface freeze in the harness.
   The clarify-laundering converter and cascade-stop are exactly the anti-drift
   machinery an unattended RL-ish loop needs.
3. Gate order is the economics: engine + playouts + LLM table *before* any
   costly artifact stage. Armillary's 6 wasted repair rounds are the receipt.
4. Bind every verdict to the version it judged (hash idea.json into engines,
   reviews, animations); vibe-ideas got burned by staleness twice.
5. Reward comes from outside the loop (marketplace events, owner words), never
   a self-computed score — that is the entire lesson of INTEGRITY.md turns
   11–15 and the rebuild's "no score to inflate" design.
6. Self-improvement = evidence-fed one-shot `claude -p` session with
   DOC/CODE/FORBIDDEN tiers, suite-or-revert, baseline file the session cannot
   touch, tighten-free/loosen-by-PR, and repeat-lesson graduation up the tier
   ladder.
7. Publish lands as **draft**; a human flips public. Idempotent via a
   `published.json` receipt; updates go in place, never as re-imports.
8. Telegram: closed verb set, state-checked replies, keyboard stripping,
   heartbeat + watchdog. Terminal fallback so the pipeline runs before the bot
   exists.
