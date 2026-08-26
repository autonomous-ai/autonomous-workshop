# Abstract Boardgame Oracle

ABO invents original abstract strategy games — a handful of piece types on a
rich board, depth from combinatorial structure rather than from added rules,
every distinction carried by shape — and then measures them hard enough to know
whether any of that is true.

Its creative constitution is [`TASTE.md`](TASTE.md). Its provenance is
[`UPSTREAM.md`](UPSTREAM.md): the simulation, model-seat and manufacturing
machinery under [`harness/`](harness/) was imported from `reinSPQR/vibe-ideas`
at a pinned commit and is locked byte-for-byte in
[`snapshots.lock.json`](../../snapshots.lock.json).

## The seven questions

**1. Which category and audience does this inventor serve?**
The `invented-games` lane, for grown-ups (14+). Two strangers who want a game
they can be taught in one explanation and still be losing at in a year.

**2. What makes its output recognizable without a logo?**
One square footprint shared across a piece family, with rank cut into the piece
as notch count, relief, or height — never printed on it and never coloured. A
board that is more interesting than the pieces standing on it. Two actions and
a win condition you can say in one sentence.

**3. How does it turn useful Wishes into play?**
It invents the whole game at Concept rather than at Make. For an abstract game
the pieces *are* the rules, so a brief that locks a component breakdown before
the rules exist locks a bill nothing decided. ABO's researcher invents the game
— rules with a per-step declaration of the components each step touches, the
component bill, art direction in form language — proves mechanically that the
rules and the box describe the same game, and returns that as the researched
breakdown the brief and every concept image are derived from. The rules seal
into the concept root alongside the pixels, so `concept_sha256` covers the game
as well as the picture of it.

**4. Which customization level does it use, and why?**
`custom-playtest`, which means it owns both `MakeContext -> Made` and
`PlaytestContext -> Playtested`. It also owns the Concept job through
`Workshop(concept=...)`, which `docs/ARCHITECTURE.md` permits and which does not
change the level. It needs all three because an invented game has no rules until
somebody writes them, no engine until somebody compiles them, and no evidence
until somebody plays it a thousand times.

**5. Which shared capabilities are required for a real run?**
The Concept image provider and the exploded-view check, exactly as every other
inventor needs them. Plus ABO's own: a game inventor behind the research step, a
rules-engine compiler, a CAD builder over the repository's locked `skills/cad`,
and a model-seat endpoint (`ABO_PLAYTEST_BASE_URL`, `ABO_PLAYTEST_API_KEY`,
`ABO_PLAYTEST_MODEL`). Absent any of them the run parks with a typed `Need`
naming that capability — never a default, a fixture, or an assertion.

**6. Which evidence classes can pass Playtest?**
`ai-simulation`, and only that. Four results: `game-simulation` (at least 1,000
*completed* seeded games across four genuinely distinct executing player
styles), `agent-playtest` (games where every seat's decision came from an
independent model, reporting at least two distinct roles), `mechanical-test`
and `print-test` (deterministic measurement over the exact geometry, bound to a
hash of the sources it was computed from). No ABO result ever claims that a
person understood the game, enjoyed it, or would play it again. That is learned
after delivery, through Reviews.

**7. What is missing, synthetic, experimental, or blocked today?**
See [What today's rehearsal supports](#what-todays-rehearsal-supports) below.
Status is `experimental`.

## Which engine protocol, and why

This repository carries two. `src/inventor_workshop/gameplay.py` has an
`ExecutableGame` protocol (`reset`/`observe`/`legal_actions`/`step`/
`is_terminal`/`outcome`/`canonical_state`). The imported harness drives a
different one (`new_game`/`player_to_move`/`legal_moves`/`apply_move`/
`is_over`/`scores`/`winners`/`observation`/`determinize`, plus `PLAYERS`,
`MAX_TURNS` and `HIDDEN_INFO`).

**ABO uses the imported one.** It is what its rules engineer writes against and
what `harness/playtest.py` calls, and reconciling the two would be a lane-wide
change rather than one inventor's. The design names that as a non-goal, and this
line exists so the next inventor in this lane does not have to guess which
protocol it inherited. See [`make.py`](make.py) for the contract ABO enforces on
a compiled engine.

## How it is put together

```text
inventors/abo/
  TASTE.md          the creative constitution — direction, never evidence
  UPSTREAM.md       provenance, the file-by-file inventory, and what was left behind
  inventor.json     operational facts only; no creative prose
  profile.py        Wish, Workshop construction, and the CLI
  config.py         where the imported harness finds this repository, and the printer
  cad_compat.py     the six ways the locked CAD skill differs from the one the gate expects
  game.py           the game record, and the checks that refuse one
  research.py       invent the game, then state its physical facts
  concept.py        the Concept hook: draw it, then seal the rules with the pixels
  make.py           compile the rules into an engine; build STEP-first CAD
  simulation.py     seeded play, the 1,000-completed-game floor, and what it measures
  model_seats.py    a model decides each turn, and no part of the harness is an agent
  manufacturing.py  deterministic measurement bound to its source closure
  feedback.py       findings become feedback the next round can act on
  playtest_job.py   the four results, assembled and bound to the revision
  agents/           the imported ideator, rules engineer, and three lenses
  harness/          the imported tree — byte-locked, not edited
  tests/            offline checks; no credential, no network, no printer
```

`playtest_job.py` is not called `playtest.py` because `harness/table_run.py`
imports the vendored simulation harness as a bare `import playtest`, and a
module of that name at the inventor root would shadow it.

## Running it

```bash
PYTHONPATH=../../src python3 profile.py profile
PYTHONPATH=../../src python3 profile.py preview notchline "I wish for ..."
PYTHONPATH=../../src python3 profile.py run notchline "I wish for ..." --playtest-rounds 2
```

Checks, which need no credential, no network and no printer:

```bash
PYTHONPATH=../../src python3 -m unittest discover -s tests -p 'test_*.py'
```

Point `ABO_REFERENCE_CAD_SKILL` at a checkout of the upstream `skills/cad` to
run the CAD characterization's dynamic half; without it that comparison reports
itself unmeasured rather than claiming agreement.

## What today's rehearsal supports

An end-to-end rehearsal runs with fixtures for every capability: a fixture game
(`tests/fixtures/fixture_game.py`), a fixture engine
(`tests/fixtures/fixture_engine.py`), a recorded model-seat transcript, a
deterministic concept artist that draws swatches, and a stand-in STEP generator.

**What the rehearsal supports.** That the game record's consistency check
refuses each way rules and a bill can disagree. That a Wish which only names the
game is refused, and a Wish built around a person is routed away. That the
sealed concept's hash covers the rules, and that they are recoverable verbatim.
That a compiled engine plays a fixture game to a terminal state, refuses a
silent rule, and declares the reading it took. That the product's components
correspond one-to-one with the brief's, that a concept image cannot be laundered
into the product, and that a post-Make edit invalidates the revision. That the
1,000-completed-game floor rejects a smaller sample and returns a `Need`
reporting how far it got. That four player styles are measured distinct rather
than declared. That a seat can only answer with an index, is shown only its own
view, and never sees another seat's messages. That an unmeasured manufacturing
check never counts as a pass, and that stale-source evidence is refused.

**What it does not support.** It is not evidence that any game is good, that any
geometry is printable, or that anybody enjoyed anything.

- **No game has been invented.** No game inventor or rules-engine compiler is
  configured here; the fixture game is a fixture, chosen to make checks fail for
  the reason the test says.
- **No geometry has been validated.** `cadgen`, `build123d` and `trimesh` are
  not installed on the machine these checks run on, so every geometry
  measurement reports itself *unmeasured* and neither `mechanical-test` nor
  `print-test` passes. That is the rule working, not a gap being tolerated.
- **Nothing has been sliced or printed.** No slicer or profile is pinned, so
  print time and material are unmeasured.
- **No model has played.** The model-seat transcript is synthetic and marked as
  such, and the code refuses to build a passing `agent-playtest` from any
  recorded transport — a recording is evidence about the run it came from.
- **The floor has never been met in this repository.** A rehearsal plays a few
  dozen games; a real run needs a thousand completed ones, which is tens of
  minutes of simulation per round.

A real ABO run therefore parks with four truthful `Need`s today, naming exactly
what would satisfy each one. That is the honest state, and it is visible in
`profile.py run` without reading any of this.
