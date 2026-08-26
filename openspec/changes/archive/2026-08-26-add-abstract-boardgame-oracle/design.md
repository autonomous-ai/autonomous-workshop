## Context

See `proposal.md` — Why. What matters here are the three seams the port has to land on, and the one place where the upstream pipeline's shape and Workshop's shape genuinely disagree.

The Workshop side, as it stands today:

- `_playtest_policy_needs` (`src/inventor_workshop/workshop.py:168`) is the gate. For `invented-games` it requires `agent-playtest`, `game-simulation`, `mechanical-test` and `print-test`; every passing one must declare `evidence_class="ai-simulation"`; `agent-playtest` needs two or more distinct non-empty `agent_roles`; and `game-simulation` needs `executable=true`, `completed_games >= 1000`, and all four of `optimizing`/`social`/`exploratory`/`adversarial` in `player_styles`.
- `gameplay.py` already carries an `ExecutableGame` protocol and a seeded league runner with reproducible traces. Its shape (`reset`/`observe`/`legal_actions`/`step`/`is_terminal`/`outcome`/`canonical_state`) is close to but not identical with the upstream engine contract (`new_game`/`player_to_move`/`legal_moves`/`apply_move`/`is_over`/`scores`/`winners`/`observation`/`determinize`).
- Concept runs above Make and its brief is the binding component breakdown. `ConceptBrief` caps components at 12 (`MAX_CONCEPT_COMPONENTS`, `jobs.py:36`) and `WishResearch` is a closed record of *physical* facts — `object`, `category`, `envelope_mm`, `wall_mm`, `features`, `print`, `components`, `fits` — with `WishResearchFinding.field` restricted to exactly those names. There is no field in it for game rules.
- `DefaultConcept` (`concept.py:758`) accepts `concept_artist`, `explode_inspector`, `brief_maker` and `wish_researcher`, requires a fresh empty workspace, writes `research/`, draws in dependency order, and seals the root.

The upstream side: `vibe-ideas` at the commit already pinned in `upstreams.json`. `board-game/tools/` is 11,782 lines. The parts that map are `rules_check.py` (245), `playtest.py` (1,556), `table_run.py` (1,228), `gate.py` (431), `ergonomics_check.py` (160) and `preview.py` (193), plus the `board-game-ideator`, `board-game-rules-engineer` and lens agent definitions. The parts that do not are `pipeline_queue.py` (1,312), `telegram.py` (672), `dashboard.py` (1,199), `game_site.py` (292), `publish.py` (506), `journal.py` (385) and `improve.py` (304).

The disagreement: upstream invents the game *first* (`idea.json` — concept, rules, bill, art direction) and derives the numeric CAD brief from it second (`brief.json`). Workshop's `TOY_TASKS` puts `make.rules` — "write complete executable rules and AI-player models" — under the **make** job, below a Concept that has already locked the component breakdown. For an abstract game those two orderings cannot both be right: the pieces are the rules, so a brief that locks a bill before the rules exist locks a bill nothing decided.

## Goals / Non-Goals

**Goals:**

- Land the port on the existing seams without changing any existing capability's requirements, so this change can be reviewed and reverted as one inventor.
- Make the 1,000-game floor real rather than declared, including the case where the budget runs out first.
- Keep every claim inside what it measured, and keep the harness that produces model-seat evidence free of agency.

**Non-Goals:**

- Reconciling `gameplay.py`'s `ExecutableGame` protocol with the upstream engine contract. Both stay; ABO uses the upstream one because that is what its rules engineer writes against and what its simulation harness drives. Unifying them is a later, lane-wide change.
- Promoting any of the ported harness into `src/inventor_workshop/`. Everything lands under `inventors/abo/`.
- Changing Leo, or moving him onto ABO's machinery.
- Porting the upstream owner-facing surface in any form — not as a queue, not as a wait, not as a notification.

## Decisions

### D1. The game is invented at Concept; the rules' digest is what Concept seals

ABO owns the Concept job through `Workshop(concept=...)`, which `docs/ARCHITECTURE.md` explicitly permits and which does not change its customization level. Its hook invents the game, runs the rules-versus-bill check, derives a `ConceptBrief` whose components are the game's bill, and delegates the image work to `DefaultConcept` by supplying `brief_maker=` (ABO's brief) and `wish_researcher=` (the physical facts of that same invention).

The rules *text* does not fit inside `WishResearch` — its `field` vocabulary is closed to the eight physical-fact names — so the rules do not travel as a research field. Instead ABO writes the game record (`game/idea.json`, `game/rules_check.json`) into the concept root after `DefaultConcept` returns, rebuilds the artifact manifest over the augmented root, and returns a `ConceptImages` sealed over all of it. `concept_sha256` therefore covers the rules, the bill, the check result, the research and the pixels together, and `MakeContext`'s seal re-check catches a rules edit made while Make was running.

*Alternatives considered.* Adding an optional sealed-extras input to `DefaultConcept` is cleaner and is probably where this ends up, but it changes `workshop/concept-job` and `workshop/concept-images` — both of which the in-flight `add-researched-wish-breakdown` change is already modifying. Deferred rather than stacked. Extending `WISH_RESEARCH_FIELDS` with a `rules` member was rejected outright: it makes a lane-specific concept a shared contract, and the citation rule ("a source, or a recorded decision, never both and never neither") does not mean anything applied to invented rules.

*Consequence.* `TOY_TASKS`' `make.rules` is satisfied across two jobs for this inventor: Concept decides the rules, Make writes the executable model of them. The task's evidence line — "setup, legal actions, end condition, scoring, ties, and simulator source" — is still produced in full, and the simulator source is still a Make output.

### D2. The component cap is a taste alignment, not an obstacle

`MAX_CONCEPT_COMPONENTS = 12` would be a real constraint for a themed game with many piece families. For ABO it is the same constraint its Taste already imposes — the upstream owner killed a design for exactly this, at four egg families plus five other component types, *after* it had cleared every mechanical gate. The reference game carries five components. ABO does not need the cap raised and should not ask for it.

### D3. Four styles means four policies that play, and one of them has to be written

Upstream's scripted policies are `random`, `greedy` and `first`, plus a Monte-Carlo/lookahead policy used for the skill ladder. Mapping onto Workshop's four names:

| Workshop style | Backed by | Status |
|---|---|---|
| `optimizing` | the lookahead / Monte-Carlo policy | ported |
| `exploratory` | the randomized policy | ported |
| `adversarial` | a policy that plays to deny the opponent rather than to advance itself | **new** |
| `social` | the model-per-seat harness | ported |

`greedy` and `first` stay as ladder rungs — they are how the depth measurement is computed — but they are not declared as styles, because neither is a distinct *style* of play as the lane means it. `adversarial` has no upstream equivalent and is written for this change: it selects the move that most reduces the opponent's best reply, which is a different objective from maximizing one's own score and will diverge from `optimizing` on real positions. Style distinctness is then *measured* over the sample rather than asserted, so a badly written adversarial policy that collapses onto `optimizing` is caught by the same check.

Using the model seats for `social` also means `game-simulation` and `agent-playtest` share evidence: the model-seat games count toward both. They stay separate results with separate evidence files, because they answer different questions — the sample size and the measured properties for one, the distinct roles and their reports for the other.

### D4. The 1,000-game floor is enforced on completed games, with a truthful short return

Upstream defaults to 400 games plus a 120-game ladder and took 728 seconds on the reference game with a 900-second deadline. Scaling to 1,000+ completed games is roughly a 30-minute simulation for an engine of that complexity, and a slower engine will not finish.

ABO therefore counts only games that reached a terminal state. Games abandoned at the turn cap, abandoned at the deadline, or ended by an engine error are reported separately and excluded. When the deadline arrives short of 1,000, ABO returns `WaitingFor(Need("playtest", "game-simulation", ...))` reporting how far it got — not a passing result over a smaller sample, and not a silently extended deadline. The allowance that governs the run is `playtest_rounds`; the simulation deadline is a configuration of the capability, and neither can be raised by Wish text.

### D5. The gate runs against this repository's locked CAD skill, and nothing is vendored twice

Upstream `gate.py` shells out to `skills/cad/scripts/verify_project` and friends. This repository's `skills/cad` is a *newer* pin of the same upstream (`peterat617/text-to-3d` at `54804a8`, per `skills/PROVENANCE.md`); a tree comparison shows five substantive differences — `verify_project`, `cadgen/catalog.py`, `cadgen/metadata.py`, `cadgen/step_targets.py`, `inspect_refs/inspect.py` — and a `requirements.txt` difference, the rest being bytecode caches.

The port repoints at `skills/cad` and treats those five files as a compatibility task with a characterization fixture, rather than vendoring a second copy. `skills/LOCK.json` is untouched. The bed envelope becomes ABO configuration rather than a module constant, because upstream hardcodes 256 mm while its own documentation states the Bambu Lab P2S usable envelope as 246 × 246 × 251 mm, and a printer constant that disagrees with the printer is the kind of thing that only shows up at Deliver.

`gate.py`'s existing separation of hard `fails` from owner-visible `unmeasured` maps directly onto the spec's requirement that an unrun check is not a pass: `fails` become blocking `Feedback`, `unmeasured` entries prevent the corresponding result from passing rather than being reported alongside a pass.

### D6. Budgets become feedback severities; the queue does not come across in any form

Upstream has three budgets — repair (2), rework (3), clarify (3) — and a `clarify`-versus-`rework` disposition on every gate failure, with the queue verifying after the fact that a clarification stayed out of the mechanics. Workshop has one budget, `playtest_rounds`, and one vocabulary, `Feedback` severity.

The disposition survives as severity and area: an ambiguity or an incompleteness in the rules is `improve` against the rules area; a defect in how the game functions, or a failed manufacturing measurement, is `block`. The upstream after-the-fact mechanic-surface check has no equivalent and is dropped — under Workshop both dispositions spend the same single allowance, so there is no cheaper lane for a clarification to launder a design flaw into, which is the specific failure that check existed to catch.

The claims, leases, `QUEUE.json`, the two owner gates and the Telegram channel are dropped entirely. They exist upstream because that pipeline is a continuously-driven queue with a human in it; ABO receives one assignment and returns.

### D7. The port lands under `inventors/abo/` as a locked snapshot with a thin adapter layer

Structure:

```text
inventors/abo/
  TASTE.md UPSTREAM.md README.md inventor.json pyproject.toml
  profile.py                    Wish, Workshop construction, CLI
  concept.py make.py playtest.py    the three seams (D1, and the two hooks)
  agents/                       ideator + rules-engineer definitions
  harness/                      the imported tree: rules_check, playtest,
                                table_run, gate, ergonomics, preview
  tests/                        offline checks
  toys/                         creations
```

`harness/` is byte-locked through `snapshots.lock.json` and `tools/verify_snapshot_locks.py`; the adapters above it are this repository's own code. Anything that has to change in an imported file changes in the adapter layer where possible, and where it cannot, the change and the lock update land in the same commit with `UPSTREAM.md` recording it. `snapshots.lock.json` is currently `{"snapshots": {}}`, so ABO is the first real exercise of that machinery.

### D8. Offline checks prove the contracts with no credential and no network

ABO ships a small fixture game and a fixture engine. Its declared checks prove: the engine contract; the rules-versus-bill check on a good and a deliberately inconsistent game; the 1,000-completed-game floor, including the short-return path; style distinctness, including two styles that collapse onto each other; the component correspondence between brief and product; concept-seal re-check on a mid-round rules edit; artifact-hash binding on every result; and the `unmeasured`-is-not-a-pass rule. The fixture runs scripted policies only. The model-seat path is exercised against a recorded transcript, never a live endpoint.

## Risks / Trade-offs

- **A real run is expensive and slow.** 1,000+ completed games plus model seats plus a full CAD gate is tens of minutes and real model spend per round, multiplied by `playtest_rounds`. → The floor is not negotiable, so the pressure goes onto engine speed and per-style allocation; the short return (D4) makes an under-budget run visibly incomplete instead of quietly passing. A caller who cannot afford it gets a `Need`, which is the honest outcome.
- **`social` as a model style is the weakest of the four.** A model seat playing to win is not obviously a "social" player, and the lane never defines the term. → Declared as what it is — the style whose decisions come from a model rather than a script — and reported that way, rather than dressed up. If the lane later defines `social` more sharply, the mapping changes in one place.
- **Two engine protocols now coexist** (`gameplay.py`'s and the imported one). → Accepted for this change and named as a non-goal. The risk is a later inventor picking the wrong one; `README.md` in the inventor states which it uses and why.
- **The rebuilt-manifest step in D1 is unusual.** An inventor writing into a root that a shared job just sealed reads like tampering even though ABO owns the job. → The Concept hook does it in one place with a comment pointing at this decision, and the offline check proves the returned concept's hash covers the game record. The cleaner seam is noted for a follow-up change.
- **Five CAD-skill files differ from what the imported gate was written against.** → A characterization fixture against this repository's skill is a task, not an assumption. If a difference turns out to be behavioural rather than cosmetic, the fallback is to fix it in the adapter, not to pin an older skill; `skills/LOCK.json` stays as it is.
- **`board-game-ideator` upstream reads `QUEUE.json` to avoid re-proposing.** Without a queue, ABO has no memory of what it has already invented. → Correct for a request-driven inventor: each Wish is answered on its own. The upstream owner-rejection ledger becomes part of `TASTE.md`, which is where a durable "do not propose this shape again" belongs.
- **Depending on an unlanded change.** ABO cannot be applied until `add-researched-wish-breakdown` lands, since `WishResearcher`, `WishResearch` and the `brief_maker` seam come from it. → Stated in the proposal's Impact and first in the task list; if that change's contract shifts, D1 is the part that moves.

## Migration Plan

Additive. No existing spec, inventor, lock or sealed toy changes; `inventors/README.md` and `docs/ADOPTION.md` gain a row and a corrected slice list. Rollback is deleting `inventors/abo/`, reverting the `snapshots.lock.json` entry and the two doc edits. No persisted run state, schema or on-disk contract is touched, so no existing run becomes unreadable.
