---
description: Advance the board-game pipeline by exactly one step — the queue decides which idea and which stage. Designed to be driven by /loop.
argument-hint: "[slug — optional, to force one idea]"
---

# /bg — one step of the board-game pipeline

The goal is a **good CAD model**: one that prints, one that plays, one the
owner approves. Improving the agents is only how we get there.

**Do exactly one action, then stop.** Not two, not "while I'm here". This
command is meant to be run under `/loop /bg`, and a step that quietly does
three things is a step nobody can inspect. If the action finishes early, still
stop — the next invocation picks up the next one.

## Poll first

```bash
.venv/bin/python board-game/tools/telegram.py poll
```

One pass, always, before deciding anything — the owner may have tapped a
button or answered a reply-reason since the last step, and that can change
what `next` should return (an `approve` moves an idea out of
`awaiting_owner`, for instance). `poll` only ever executes what a gate
message itself offered (`approve`/`reject`/`rework`/`ship`/`amend`), gated
by `pipeline_queue.py`'s own state check, so this is safe to run every time
even when nothing is waiting. If Telegram isn't configured it prints
"nothing to poll" and this is a no-op.

## Decide

```bash
.venv/bin/python board-game/tools/pipeline_queue.py next
```

That prints one JSON object naming the `slug` and the `action`. **You do not
choose** — the queue owns prioritisation (ideas closest to shipping go first,
so finishing beats starting) and it owns the repair budget. If `$ARGUMENTS`
names a slug, still run `next` and simply skip to that idea's own action.

`next` does not just report the step, it **claims** it: the idea is marked in
progress until the step ends. This is what stops a second `/bg` — a fast
`/loop`, another terminal — from being handed the same work and spawning a
second agent onto the same files, since an idea's `state` does not change
until its step *finishes*. Two consequences for you:

- **`"action": "wait"`** means every advanceable idea is already being worked
  on by someone else. Print the `in_progress` list and stop. Do not go looking
  for something else to do; the claim exists precisely so you don't.
- **You now hold something, so you must hand it back.** See below.

Then run the matching block below, and nothing else.

## Ending a step

Exactly one of these ends every step. There is no third option, and "stop
without doing either" leaves the idea invisible to the pipeline until its
lease expires:

- The step **finished** → `advance --to <state>` (this drops the claim for you).
- The step **did not** — a gate failed and you are leaving the state where it
  is, an agent errored, a checker refused, you are stopping to report a
  problem → release it explicitly:

```bash
.venv/bin/python board-game/tools/pipeline_queue.py release <slug>
```

For a failed `propose` (no slug exists yet), the slug is the literal word
`propose`: `pipeline_queue.py release propose`.

Releasing is not an admission of failure and it never fakes progress — the
state stays exactly where it was. It only says "I am no longer working on
this", so the next tick can retry instead of waiting out the lease.

## Actions

### `propose`
Invoke `board-game-ideator` in **propose** mode. It writes
`board-game/ideas/<slug>/idea.json` and runs `rules_check.py` itself. Then:

```bash
.venv/bin/python board-game/tools/pipeline_queue.py add <slug> --title "<title>"
```

`add` clears the propose claim. If the ideator failed and no idea was added,
`release propose` instead.

Append its `PAIN_POINTS:` to `board-game/PAIN_POINTS.md` under a dated heading.

### `rules_gate`
First check whether this idea is at `proposed` because the owner sent it back
for rework (`QUEUE.json`'s entry has a non-empty `rework_reason`) rather than
because it is new or just failed the gate. If so, invoke `board-game-ideator`
in **rework** mode with the owner's `rework_reason` verbatim *before* running
the gate — an owner rework must actually change the idea, not just re-pass an
unmodified `idea.json` and walk it straight back to the same render the owner
already sent back. No separate bookkeeping needed afterward: the next
successful `rules_gate` run below moves the idea out of `proposed` anyway,
and a later owner rework overwrites `rework_reason` with its own new reason.

Every FAIL below — mechanical, the rules lens, or the playtest lens — goes
through the idea's round budgets before `board-game-ideator` is invoked again.
The failing gate's disposition decides which budget pays: `clarify` rounds
(ambiguity, missing procedures) spend the clarify budget and send the ideator
into **clarify** mode; `rework` rounds (a defect in how the game functions)
spend the rework budget and send it into **rework** mode. The disposition is
the gate's call, not the ideator's — the queue verifies after the fact that a
clarify round stayed out of the mechanics, and converts the round into a paid
rework if it did not.

```bash
.venv/bin/python board-game/tools/pipeline_queue.py gate_rework <slug> \
    --stage <rules_check|lens_rules|lens_playtest> --disposition <clarify|rework> \
    --problem-id <stable-kebab-case-id-for-rework> \
    --reason "<findings verbatim>"
```

`--problem-id` is required for a `rework` and omitted for a `clarify`. Read it
from the lens's `Problem-ID:` line. It names the recurring underlying defect,
not the current manifestation. The queue writes `.rework_request.json` and
counts recurrence. On the second occurrence it requires a structural strategy;
the ideator must choose subtraction, rollback, or replacement rather than
another patch.

When a rework FAIL has a different Problem-ID from the preceding round, also
pass the lens's mandatory classification:

```bash
--lineage <caused-regression|new-independent> \
--severity <lower|equal|higher|contract>
```

`contract` means the candidate violated a `must_preserve` or produced an
`anti_goal`. If the preceding candidate caused an equal, higher, or contract
regression, `gate_rework` exits 2 and moves the idea to `blocked`. Do not send
it to the ideator. The candidate must be reverted, forked, or killed by an
explicit decision; a compensating patch is forbidden. A lower-severity side
effect is a secondary observation and should not become the next FAIL until
another targeted test establishes that it is real.

exit 0 → the round is granted; continue exactly as below, in the mode the
disposition names.
exit 1 → the idea already used its budget for that kind of round (three
rework rounds, or three clarify rounds) and this command has already moved it
to `killed` for you. Do **not** invoke the ideator. Put the one-sentence
reason in `TASTE.md` (same as a `Disposition: kill`, below) and
`release <slug>`.
exit 2 → the last candidate created an equal-or-worse regression and the idea
is `blocked`. Do not invoke the ideator or patch the regression. Escalate the
recorded choice between reverting the candidate, forking it as a new design,
or killing it.

If the ideator replies `BLOCKED` because the required solution is a high-level
change or cannot preserve the contract, run `pipeline_queue.py advance <slug>
--to blocked --note "<the BLOCKED reason verbatim>"`. Do not leave it in
`proposed`, where the unattended loop would ask for the same impossible
rework again.

Then:
```bash
.venv/bin/python board-game/tools/rules_check.py board-game/ideas/<slug>/idea.json
```
FAIL → read `rules_check.json`'s disposition. Schema and bill/rules mismatches
are `clarify`; a declared complexity-budget overrun is `rework` with
Problem-ID `complexity-budget`. Call `gate_rework` with that disposition and,
for rework, that Problem-ID. On exit 0 invoke `board-game-ideator` in the
matching mode with the findings verbatim; leave the state at `proposed` so the
gate runs again next step, and `release <slug>` so the next step can pick it
up.

PASS → before this idea costs a single hour of `brief-writer` or `builder`
time, invoke `board-game-lens-rules` against `idea.json` — an independent
opinion on whether the game is worth playing at all (dominant strategy, fake
decisions, reachable ending, length, player count), not just internally
consistent.

FAIL → read the `Disposition:` line in `review_rules.md` and
`gate_rework --stage lens_rules --disposition <clarify|rework>` with the
disposition it says (default to rework if the line is missing — a gate that
does not say is never free). For a rework also pass the mandatory
`Problem-ID:` value. Then (on exit 0) invoke `board-game-ideator` in
**clarify** or **rework** mode to match, with the verdict verbatim; leave the
state at `proposed` and `release <slug>`, exactly like a mechanical
`rules_check.py` failure. If the ideator replies `CANNOT CLARIFY`, the
finding was a mechanic defect the gate under-called: run
`gate_rework --stage lens_rules --disposition rework --reason "<the
CANNOT CLARIFY line>" --problem-id <the lens Problem-ID>` and invoke the
ideator in **rework** mode. If that
also exits 1, the rework budget was exhausted by the conversion and the idea
is already `killed`.

PASS → play it. Reading rules and playing them are different tests, and prose
can be vague and still sound complete:

```bash
.venv/bin/python board-game/tools/playtest.py board-game/ideas/<slug>
```

An engine has to exist first. If `playtest/engine.py` is missing, invoke
`board-game-rules-engineer` in **write** mode and let it run `--quick`
itself. `PLAYTEST ERROR` means the engine is broken, which is the engineer's
defect and not the game's — send it back in **patch** mode with the error.

Then teach it. Only after the mechanical rules check, independent rules lens,
rules engine, and scripted `playtest.py` have passed, invoke
`board-game-rules-animator` in **build** mode. The animator writes the stable
artifact `board-game/ideas/<slug>/animation/rules.mp4` and a manifest bound to
the current `idea.json`.

Next invoke `board-game-lens-animation` as a **separate agent**. The animator
may not review or approve its own work. The lens must inspect the rendered
video and write `review_animation.md` with `Verdict: PASS` plus the exact video
SHA-256. On FAIL, invoke `board-game-rules-animator` in **repair** mode with the
review findings verbatim, rerender, and invoke a fresh animation lens again.
Do not continue until the independent lens passes. There is no duration target
or duration gate; clarity and complete rule coverage determine runtime.

Then seat players at it:

```bash
.venv/bin/python board-game/tools/table_run.py board-game/ideas/<slug> \
    --wire anthropic
```

The table command must also finish the generated website at
`playtest/site/index.html`. It replays every recorded LLM decision against the
current engine and provides local player-vs-player hot-seat play. Treat a
missing site as an incomplete table gate, not optional presentation work. To
open the interactive mode, run:

```bash
.venv/bin/python board-game/tools/game_site.py serve board-game/ideas/<slug>
```

Only after that website exists and contains the completed replay run, send the
one journal Telegram notification for this iteration:

```bash
.venv/bin/python board-game/tools/journal.py rules_ready <slug>
```

The command sends exactly one post: the proposal as the video caption, the
approved rule animation, and the local `playtest/site/index.html` file link.
It deliberately omits the full rule blocks.
Retries of the same `idea.json` and video are deduplicated. Do not send this
notification for a failed or incomplete gate, and do not substitute any other
journal Telegram message.

The command always plays exactly four games at the idea's `players.max` and
rejects schedules using another count. Game 1 uses fresh seat conversations;
Games 2 and 3 keep only what those seats learned in the current run; before
Game 4 the harness injects archived player-facing experience from prior rules
iterations. The injection excludes machine statistics, reviewer verdicts,
engine state, and hidden information. This needs
`PLAYTEST_BASE_URL`, `PLAYTEST_API_KEY` and `PLAYTEST_MODEL`, which it reads
from `.env`. The LLM-player table is **not optional**: the gate is not over
when the rules check passes and a machine has played it — a game nobody has
sat at and thought about has no player feedback, and `review_playtest.md`
cannot be written without it. If the table cannot run (credentials absent, API
down), report the missing measurement, `release <slug>`, and leave the idea at
`proposed`. Do **not** advance it on the machine half alone:
`pipeline_queue.py advance --to rules_ok` refuses without a current
`review_playtest.md`, and it should.

Then invoke `board-game-lens-playtest`, which reads both halves and writes
`review_playtest.md`. Its verdict is the one that counts:

- PASS → `pipeline_queue.py advance <slug> --to rules_ok`.
- `Disposition: clarify` → `gate_rework --stage lens_playtest
  --disposition clarify --reason "<verdict verbatim>"`. exit 0 →
  `board-game-ideator` in **clarify** mode with the findings verbatim; state
  stays `proposed`, `release <slug>`. exit 1 → the clarify budget is
  exhausted (three clarification rounds spent and still failing); do not
  invoke the ideator, put the reason in `TASTE.md` as below, `release
  <slug>`.
- `Disposition: rework` → `gate_rework --stage lens_playtest
  --disposition rework --problem-id <Problem-ID> --reason "<verdict
  verbatim>"`. exit 0 →
  `board-game-ideator` in **rework** mode with the findings verbatim; state
  stays `proposed`, `release <slug>`. exit 1 → the idea is already `killed`
  (three rules-gate reworks spent and still failing); do not invoke the
  ideator, put the reason in `TASTE.md` as below, `release <slug>`.
- `Disposition: kill` → do **not** rework it and do **not** call
  `gate_rework` (that budget is for reworks that are still being tried; this
  lens already decided one would be wasted). `pipeline_queue.py advance
  <slug> --to killed`, and put the one-sentence reason in `TASTE.md` so the
  next `propose` does not walk back into the same shape. A game whose problem
  is its own component arithmetic cannot be reworded into a good one, and
  sending it round again spends a cycle to rediscover that.

The ideator must write `rework_plan.json` before editing `idea.json`. It must
record the observation, hypothesis, one next-test question, confounds,
subtraction/rollback/replacement alternatives, the chosen strategy, and a
falsification condition. It must also classify the change level and declare
regression checks for the design contract plus secondary risks. The queue
rejects a high-level change under the same slug, validates the plan, and
records the actual complexity delta before granting another round or allowing
`rules_ok`.

After a structured rework, `review_playtest.md` must state
`Target-result`, `Regression-result`, and `Clean-games`. `advance --to
rules_ok` requires the target fixed, regression clean, and at least two clean
table games. This is the candidate-to-baseline promotion rule.

### `brief`
Invoke `board-game-brief-writer` in **write** mode. It writes `brief.json` +
`brief.md` and runs `ergonomics_check.py` itself. Verify it actually passed:

```bash
.venv/bin/python board-game/tools/ergonomics_check.py board-game/ideas/<slug>/brief.json
```

PASS → `advance --to briefed`. FAIL → **patch** mode with the findings; stay
put and `release <slug>`. Append its `PAIN_POINTS:`.

### `draft`
Invoke `board-game-builder` in **draft** mode. It builds real geometry fast
and renders it — this is not an illustration, it is the object, and the render
it produces becomes the visual contract if the owner says yes.

`advance --to drafted`.

### `owner_gate_1`
Before spending the owner's attention, run the same object-vs-rules lens
`panel` runs much later, but now: invoke `board-game-lens-playability`
against the **draft** — point it at `board-game/ideas/<slug>/draft/` for
renders (there is no `reference/` yet; this is pre-approval) and
`brief.json`. The rules were already judged independently at `rules_gate`, by
`board-game-lens-rules`; this lens only judges whether the object itself —
legibility, distinguishability, handling — supports them.

FAIL → the fault is in the geometry, not the rules, so invoke
`board-game-builder` in **repair** mode with the verdict verbatim, re-render,
and re-run the lens. If it now passes, continue to the PASS branch below. If
it still fails and you are stopping here, `release <slug>` — state stays at
`drafted` so the next tick tries again, the same way a `brief` gate failure is
handled.

PASS →
```bash
.venv/bin/python board-game/tools/telegram.py gate1 <slug>
```
Sends the hero render, a one-screen rules summary and the bill, with the three
reply commands. Then `advance --to awaiting_owner` and **stop**. Do not guess
what the owner would say; the whole point of this gate is that a human decides
which games are worth making — this lens only filters what should never have
reached them in the first place.

### `build`
Invoke `board-game-builder` in **build** mode. It must read every image in
`board-game/ideas/<slug>/reference/` first — the owner approved that
silhouette. Then:

```bash
.venv/bin/python board-game/tools/gate.py board-game/ideas/<slug>/project \
    --bill board-game/ideas/<slug>/project/bill.json
```

`GATE PASS` → `advance --to built`.

A `GATE PASS` line can carry an `unmeasured` list: checks that reached no
verdict rather than a good one. It is not a failure and you must not treat it
as one — pieces resting in contact legitimately weld the assembled mesh, and a
gate that failed correct designs would be routed around within a week. You do
not have to carry it either; `advance` reads it off `gate.json` and attaches it
to the idea itself, and `ship` will refuse until the owner accepts it by name.
What you owe it is the journal entry: paste the list verbatim, because it is
the part of the verdict that says what nobody looked at.

`GATE FAIL` → `pipeline_queue.py repair <slug>`:
- exit 0 → invoke `board-game-builder` in **repair** mode with the gate's
  findings verbatim, then re-run `gate.py`. (`repair` renews the claim rather
  than dropping it — the repair happens inside this same step.) If the re-run
  still fails and you are stopping here, `release <slug>`.
- exit 1 (budget exhausted) → **arbitration**: read `brief.json`, `gate.json`
  and the build source, and decide whether what remains is a genuine spec
  conflict — the brief demanding things that are mutually impossible — rather
  than a build defect. If it is, write `brief_proposed.json` alongside the
  brief with the minimum set of numbers changed and an `amendments` array
  saying what each change trades away; **never** edit `brief.json` yourself.
  Then `telegram.py arbitration <slug>` (or `telegram.py stuck <slug>` if it
  is not a spec conflict) and `advance --to blocked`.

### `panel`
Spawn all three lenses **in a single message with three tool uses** so they
run concurrently and cannot see each other's reasoning:
`board-game-lens-printability`, `board-game-lens-fidelity`,
`board-game-lens-playability`.

All three PASS → `advance --to reviewed`.
Any FAIL → treat exactly like a gate failure: `pipeline_queue.py repair <slug>`, then
builder **repair** mode with the failing verdicts, then re-run only the lenses
that failed. Budget exhausted → arbitration, as above. If a lens still fails
and you are stopping here, `release <slug>`.

### `owner_gate_2`
```bash
.venv/bin/python board-game/tools/telegram.py gate2 <slug>
```
Then `advance --to awaiting_ship` and stop. The pipeline never publishes
anything itself; the owner's `pipeline_queue.py ship` is what makes a game shipped.

## The owner's replies

These are commands the owner runs; the Telegram messages contain them ready to
paste. Never run them on the owner's behalf.

```bash
.venv/bin/python board-game/tools/pipeline_queue.py ship   <slug>
.venv/bin/python board-game/tools/pipeline_queue.py ship   <slug> --accept-unmeasured "..."
.venv/bin/python board-game/tools/pipeline_queue.py reject <slug> --reason "..."
.venv/bin/python board-game/tools/pipeline_queue.py rework <slug> --reason "..."
```

`ship` refuses while the gate has a check that reached no verdict, and prints
what they were. `--accept-unmeasured` is how the owner spends that, with the
reason recorded on the idea. It is theirs to spend and nobody else's: this is
the only place in the pipeline where "nothing looked at this" costs anything,
since gate.py cannot charge for it without failing correct designs.

A rejection reason lands in `board-game/TASTE.md` and is read by every future
ideation. It is the only signal in this pipeline that does not come from a
model, which is why it outranks everything an agent has learned on its own.

## After the ship

`ship` records the decision; it does not publish anything. A ship that lands is
answered with a **📦 Publish** button in Telegram — `poll`/`listen` run it the
same way they run the gate verbs — and the same thing is one command here,
safe to re-run:

```bash
.venv/bin/python board-game/tools/publish.py <slug>            # or --all
.venv/bin/python board-game/tools/publish.py <slug> --dry-run  # check, write nothing
```

It refuses anything whose state is not `shipped` or whose `gate.json` does not
pass, then imports the project folder into Panda Social as a **draft** design —
private, with its CDN snapshot and viewer files — and Telegrams you the id.
Flipping draft→public stays yours, in the app. The binary it drives is built
once per machine with `board-game/tools/publishdesign/build.sh`.

The rules ride along in three places: `RULES.md` written into the published
folder (complete), the story blocks on the product page (a walkthrough, capped
by the FE contract), and the description. Changing the rules of a game that is
already up does NOT mean publishing again — that would fork it into a second
design:

```bash
.venv/bin/python board-game/tools/publish.py <slug> --page         # rules + specs only
.venv/bin/python board-game/tools/publish.py <slug> --new-version  # files again, as v2
```

## Narrate it

The local dashboard keeps a complete event history. `pipeline_queue.py`
records state changes automatically, and agents may add useful detail with:

```bash
.venv/bin/python board-game/tools/journal.py append <slug> --kind <kind> \
    --by <agent-or-tool> --title "<game name>" --summary "<one plain line>" \
    [--body "<verbatim detail>" | --body-file <path>]
```

What is worth an entry, by action:

| action | narrate |
|---|---|
| `propose` | what the ideator was going for, and what its novelty search actually turned up |
| `rules_gate` | the `rules_check.py` findings verbatim, the `board-game-lens-rules` verdict line, the playtest verdict with its disposition, one quoted player line from the table, and what the rework changed (any of them triggers). On a `kill` — whether `Disposition: kill` from the playtest lens or `gate_rework` exhausting its budget — say what the players found and what it cost to find it — that is the only step in this pipeline that ends an idea on evidence rather than on taste |
| `brief` | the dimensions it chose, and every entry in `unstated_in_spec` — those are the places the spec ran out and somebody guessed |
| `draft` | what the draft looks like and anything that surprised the builder |
| `build` / `repair` | the gate findings verbatim (`--body-file .../gate.json`), including any `unmeasured` entries, then what the repair actually changed — not "fixed the overhang", but which number moved |
| `owner_gate_1` | the `board-game-lens-playability` verdict line, verbatim; on FAIL, what the repair changed |
| `panel` | each lens's verdict line, verbatim |

Write it for a person who was not here. Include what went badly: a guess that
turned out wrong is the most useful line in the whole story, and nothing in
this pipeline ever reads the journal back, so there is nobody to impress.

These `append` entries are local only. They never send Telegram. The journal
Telegram channel receives exactly one kind of notification:
`journal.py rules_ready <slug>` with the proposal, approved rule video, and
replay/playtest website link after `table_run.py` finishes. Do not send full
rule blocks, failures, state changes, builds, repairs, owner actions, panel
results, or any other event to that channel.

Never summarise a checker's output into your own words when you could paste
it — the owner is trying to see what the machine actually said.

## Rules for you

- **Never edit a gate, a threshold, `bill.json`, or a brief to make something
  pass.** If a gate looks wrong, say so and stop. A pipeline that can relax its
  own acceptance criteria produces nothing worth having.
- **Never report a check that could not run as one that passed.** A pass with
  something unmeasured is a smaller claim than a clean pass, and the difference
  is the owner's to spend at gate 2, not yours to round off in a summary.
- **Never fabricate a stage.** If a build failed, the state stays where it is
  and the failure is reported. An idea that dies of a tooling fault is retried,
  not replaced — that is the whole reason the queue exists.
- **Never work on an idea `next` did not hand you**, and never edit a `claim`
  field by hand to get around a `wait`. If you think a claim is stale, say so
  and stop — a stale one lapses on its own within the hour.
- Repair budget and state transitions belong to `pipeline_queue.py`. Do not track them
  in your own head, and do not work around a refusal.
- Report in one or two lines: what ran, what it produced, what is next.
