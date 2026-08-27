## Context

See `proposal.md` — Why. The constraints that actually shape the approach, all from `main`:

- **One session, host-gated.** The host writes a read-only stage packet, launches or resumes one native session, and independently re-validates what comes back. Only a gate advances a run. `_MAX_NATIVE_TURNS` is 32; the default Make⇄Playtest allowance is 4 rounds.
- **Python may not think.** `AGENTS.md` names prompt chains, Python-spawned agents, candidate generation, and semantic judging as non-extension-points. Any design that puts prompt text in Python is rejected on sight, regardless of how well it works.
- **The agent cannot reach the network.** The `workshop-product-run` permission profile disables it. Codex's own web-search tool still functions — that is how research happens — but nothing inside a turn can call an image API.
- **Credential-bearing code lives in one place.** `src/workshop/integrations/`, importable only by `workflow/native_run.py`; the import-graph test enforces this. The Factory publisher is the worked example: credentials in `$WORKSHOP_HOME/credentials/`, loaded lazily *after* the turn exits, never in the subprocess environment.
- **Adding a stage is mechanical but wide.** Roughly eight hard-coded tables across `workflow/agent_run.py`, `workflow/stage_gates.py`, and `workflow/native_run.py`, plus a mirrored half in the run-local `stage_proposal.py`, plus component registration in `.github/components.toml` and two architecture tests. There is no plugin registry.
- **Everything is content-addressed and re-verified on every read**, and materialized instruction bytes are bound to the run — a changed workflow skill fails resume closed.

## Goals / Non-Goals

**Goals**

- Land the branch's design rigor as a deterministic host gate, which is the one place `main` wants that rigor to live.
- Keep the concept a *decision made before geometry exists*, sealed and binding, rather than advice Make may reinterpret.
- Keep Python out of every cognitive step, including prompt composition, while still producing real images.
- Leave the shape of the change legible to the next stage that needs a between-turn effect.

**Non-Goals**

- No new engine adapter.
- No change to Match, Release, or Deliver.
- No attempt to restore per-call cost accounting for an agent role — see Risks.
- No revival of `snapshots.lock.json` or any second provenance mechanism.
- Not re-litigating whether images are required; the proposal settles that.

## Decisions

### D1 — Concept is its own stage, not a hardened `InventedV2`

The cheaper option is to leave the pipeline alone and give `InventedV2.concept` / `.research` a real schema. Rejected for three reasons.

`InventedV2` is a single JSON contract capped at 2 MiB with **no artifact tree**; Invent is the only stage that owns no directory. A concept is a tree — images, a descriptor, a research record. Giving Invent a tree makes it a different stage in all but name.

Second, the image effect must happen *between* a gate that validates the brief and a binding that hands it to Make. That before/effect/after shape is exactly a stage, and modelling it inside Invent would mean a gate that runs an external effect as a side effect of validating a JSON blob.

Third, separating them keeps two different decisions separable. Invent decides *which idea*; Concept decides *what it is, exactly*. Playtest feedback can then invalidate the design without discarding the idea, which is what "a failed Playtest revises the design, not only the build" has always meant.

Cost: a sixth stage in eight tables and a second finalizer subcommand. Accepted.

### D2 — The image effect runs after the gate, modelled on the Factory release wait

Release is not merely an analogy here — it is the same structure, and Concept should copy it rather than invent a variant. `_evaluate_release_stage` validates the contract, calls `_execute_release_effect` **inside the gate evaluation**, and only then builds its evidence and its `additional_artifacts` over the resulting tree. The credential-bearing call happens mid-gate, not after it.

Sequence for one Concept turn:

```
host writes STAGE.json (concept)
  └─ native turn: research → brief.json, research.json, prompts.json
       └─ finalizer writes agent-outcome.json
host: evaluate_concept_stage
       ├─ structural checks on brief/research/prompts   ← refuses here, before any spend
       ├─ _execute_concept_image_effect                 ← draws via the integrations adapter
       └─ evidence + additional_artifacts over the whole concept tree
host: one gate decision seals brief, research, prompts, and images together
       → concept_sha256 → advance to make
```

Validating **before** drawing is the point: a brief that decided nothing is refused without spending a single image call.

Putting the effect inside gate evaluation is what makes the seal coherent. `apply_outcome` accepts exactly one gate per outcome, so a design that gated the brief and then sealed a tree containing images the gate never saw would have no clean place for that second seal. Evaluating and effecting together means one decision covers every byte, exactly as Release covers its package.

When the credential is absent, the missing-credential exception propagates out of gate evaluation and the caller converts the **ready** proposal into a **waiting** outcome with a need, writing a wait file bound to the checkpoint and the accepted proposal — the same mechanism as `release-effect-wait.json`. Resume re-checks the credential, draws, and continues **in the same session**, so the accepted brief is never re-derived.

Release also carries an `EffectLedger` (sqlite under host state) so a repeated external effect is idempotent. Concept's effect is a draw rather than a publish, and a redraw costs money rather than duplicating a public record, so the ledger is not obviously required — but the resume path must not redraw images it already wrote. Task 6.4 covers that by checking for already-written role files before calling the provider.

*Alternative — two native turns* (author, then inspect the drawn images): doubles turn cost against a 32-turn ceiling and breaks the one-gate-per-stage rule. The inspection guarantee is recovered at the Make boundary instead (D4).

*Alternative — draw inside the Make turn*: impossible (no network in the sandbox) and wrong (the design would no longer be decided before geometry).

### D3 — The agent authors the drawing instructions; the host only carries them

The brief carries one drawing instruction per role. The adapter sends that text verbatim, attaches the references the concept named, writes back the bytes, and seals them. It never templates, extends, or rewrites.

This is the whole reason the design is admissible. The branch's `anchor_prompt` / `angle_prompt` / `exploded_prompt` / `component_prompt` are a prompt chain in Python — the named prohibition. Moving that text into the agent's output makes the same behavior legal, and it is not a workaround: the agent has the Wish, the Taste, and the research, so it is genuinely better placed to write those instructions than a Python template ever was.

There is precedent in the repository already. `toys/alice-manhattan-nocturne/art-direction/directions-v1.prompt.md` is a hand-authored generation prompt sitting beside the image it produced; this change makes that practice a contract.

Because the instructions are sealed with the images, a concept is reproducible and auditable: what was asked for and what came back are covered by one hash.

### D4 — The exploded-view check is dissolved, not relocated

The deleted inspector asked a vision model whether the exploded view depicted as many separated parts as the brief named, before drawing components. Nothing on `main` can do that: it needs a second model API inside what would have to be a turn.

An earlier draft of this design replaced it with the Make-boundary component check and called that stronger. That was wrong, and worth recording as a rejected alternative because it is a tempting mistake. The two checks answer different questions. The exploded check protected *the component images*: each was drawn using `exploded` as a shape reference, so an exploded view that omitted part X caused X's image to be drawn from a reference that did not show it, and the model invented a shape nobody specified. The Make check protects *the product's part list*. Since the brief is complete in text and its numbers govern, Make builds all N components correctly from the brief alone and the Make gate passes — while the bad component image sails through untouched. Substituting one for the other conceals a real loss.

So the dependency is removed instead of policed. A component's image is drawn from that component's own brief specification, with `front` supplied for material, finish, palette, and form language only. No image inherits shape from another. An omission in the exploded view then corrupts nothing downstream, and there is no longer a question for a gate to answer.

The exploded view keeps a purpose — it is the set's statement of the assembly and Make's map of the part breakdown — so its authored instruction must still name every component, checked as a property of the instruction. That check is now cheap and local: it can fail only the exploded view's own usefulness, never another image's correctness.

This also removes a rule that was uncheckable by construction. The old spec forbade asking for a component's shape "as it appears in" a reference *unless that component is wholly visible in it* — a condition decidable only by reading the picture, which the host may not do. The rule is now unconditional and therefore actually enforceable.

Cost: component images lose the pose and arrangement cue the exploded view gave them, so a component may not sit in its image the way it sits in the exploded view. That is a cosmetic inconsistency traded for a correctness guarantee.

### D5 — `NativeMade` gains `concept_sha256`, and both halves of the contract move together

The run-local `stage_proposal.py` re-implements contract construction that `src/workshop/*/native.py` validates; they must agree on canonical JSON byte-for-byte. Every contract change in this design is therefore two edits, and the acceptance test is a round-trip: build the contract through the finalizer, validate it through the host, assert identical identity hashes.

Because Concept is mandatory, `concept_sha256` is required on `NativeMade` rather than optional. The branch's "omitting the concept stays valid" allowance existed only because Concept was an optional add-on; it is not carried forward.

### D6 — A new `src/workshop/concept/` component

Component layout is test-enforced (`tests/architecture/test_component_layout.py` asserts the exact set). Concept gets `README.md`, `__init__.py`, `native.py`, `native_gate.py`, `schemas/`, following the shape `invent/` and `make/` already use, and is registered in `.github/components.toml` plus both architecture tests. Folding it into `invent/` would violate D1 and muddy that package's stated ownership.

### D7 — What survives of ABO's 5,416 lines

Kept, as `scripts/` under an optional `abo-rules-engine` skill: the abstract game engine (`game.py`) and the simulation harness (`simulation.py`). These are exactly the "tested deterministic CAD/domain tools invoked by the native Inventor subagent" the architecture sanctions, and the lane's `game-simulation` Playtest check needs something reproducible to run.

Deleted: `make.py`, `playtest_job.py`, `model_seats.py`, `research.py`, `feedback.py`, `concept.py`, `config.py`, `profile.py`, `cad_compat.py`, `manufacturing.py`, and the `agents/` and `harness/` trees. These are orchestration, model dispatch, and CAD wrapping — the native session and the shared locked skills do all of it.

Extension limits apply and are not generous: ≤256 files, ≤4 MiB per file, ≤16 MiB per tree, only `scripts/` may be executable, no symlinks or dotfiles, and the tree is secret-scanned and hash-bound. The kept modules must fit inside that or be trimmed further.

*Alternative — delete all ABO Python*: rejected. Without a reproducible engine, `game-simulation` has nothing to run and ABO's evidence would be model prose, which is not evidence.

### D8 — A second credential, and an honest README

The adapter reads `$WORKSHOP_HOME/credentials/concept-images.env` (0600 inside a 0700 directory), mirroring `factory.env`. It is loaded lazily, only after a native turn exits, and is scrubbed from any launched process environment.

This breaks the README's quick-start promise that Workshop "does not require a second model API key". That promise is now false for any run that reaches Concept, which is every run. The docs task corrects it rather than hiding it: without the credential a run parks at Concept with a concrete need.

### D9 — Missing external turn completion gets a bounded temporary fallback

The Codex JSONL contract's terminal success event remains external
`turn.completed`. The existing reap path is sufficient when that event is
emitted, but recorded rollouts show a separate failure: internal
`task_complete` can be persisted while the CLI never emits external
`turn.completed`, leaving the host blocked until the whole-turn timeout.

Workshop therefore uses a narrow operational fallback. After a completed
agent message, a bounded strict `agent-outcome.json` envelope for the exact
current checkpoint and gate subject arms a 30-second quiet period. Every later
external event restarts the period. If it expires, the host terminates and
reaps the CLI, then runs the normal complete proposal and stage-gate
validation. The file is only a completion signal; it cannot advance a gate.
Prose alone, a stale proposal, a proposal for another subject, and an invalid
or unsafe file do not arm the fallback.

Thirty seconds is deliberately conservative: it gives the CLI time to emit
its documented terminal event or further progress while avoiding a multi-
minute whole-turn timeout after durable work is already present.

This is a band-aid, not the real fix. The implementation does not observe the
internal rollout protocol directly and must not make that vendor-private
format a second public contract. A future runtime investigation must identify
why internal `task_complete` is not translated into external
`turn.completed`, repair the CLI or adapter boundary that drops it, and remove
the quiet-period fallback once terminal delivery is reliable.

## Risks / Trade-offs

- **Nothing verifies that a drawn image depicts what its instruction asked for** → This is true of every image in the set, not just the exploded view, and it is not fixable within this architecture: the host may not read pixels, and a second model grading the first is the mechanism the rewrite removed. D4 confines the blast radius — no image inherits shape from another, so a bad drawing spoils one image rather than propagating — but a component image that simply does not match its own specification will ship. Mitigation is partial and honest: the brief governs Make, not the pictures, so a wrong image misleads a human reader without corrupting the geometry.
- **Component images lose their arrangement cue** → Drawn from specification plus an appearance reference only, a component may be posed differently than it appears in the exploded view. Accepted as cosmetic; flag it if reviewers find the sets visibly incoherent.
- **Two halves of every contract can drift** (`concept/native.py` vs the finalizer's `concept` subcommand) → A round-trip test that constructs through the finalizer and validates through the host, asserting equal identity hashes; this is how the existing stages are already tested.
- **Turn and round budget pressure** → A sixth stage costs at least one turn per run, and design-invalidating feedback re-runs Concept each round. Against a 32-turn ceiling and 4 rounds the worst case is materially tighter. Mitigation: count it explicitly in the end-to-end test and assert the ceiling is not reached; the refine allowance bounds redraws.
- **Real money per run, and refining rounds redraw** → Image spend is now on the critical path of every Wish. Mitigation: the brief is validated before anything is drawn, and the refine allowance caps how many times a design may be redrawn before re-anchoring.
- **Changing the workflow skill invalidates in-flight runs** → Materialized instruction bytes are bound to the run and resume fails closed when they change. Adding `references/concept.md` and a Concept bullet to six Inventor skills changes those bytes. Mitigation: this is a breaking change for any parked run; it must be stated in the changelog fragment, and existing parked runs will need to be restarted rather than resumed.
- **Per-call cost and duration accounting for an agent role is genuinely lost** → The deleted agent door reported actual spend and wall-clock per role, including on failure. `main` has no equivalent for work done inside the one session, and this change does not add one. Image-adapter calls can be accounted for; the research that precedes them cannot. Stated plainly rather than mitigated.
- **`InventedV2` still has no structural contract** → This change hardens the *concept*, not Invent's own free-form `concept`/`research` mappings, which continue to exist upstream. That is now a visible redundancy: two places called "concept", one specified and one not. Mitigation: out of scope here, but the Concept turn should derive from Invent's result rather than restate it, and a follow-up should narrow or retire Invent's fields.
- **The 30-second completion fallback can mask a CLI lifecycle defect** → It is
  deliberately narrow and cannot pass a gate, but it terminates the wrapper
  without receiving the documented terminal event. Mitigation: keep
  `turn.completed` primary, bind the signal to the exact checkpoint and
  subject, reset on every event, document the workaround as temporary, and
  track removal behind the deeper event-translation investigation in D9.

## Migration Plan

1. **Take `main` wholesale.** Merge `origin/main`, resolving every path outside `openspec/` in favor of `main`. Delete `src/inventor_workshop/`, `skills/`, `web/`, `bin/`, `schemas/`, `snapshots.lock.json`, `upstreams.json`, and the branch's `tests/` for deleted modules. Keep `openspec/` — it is branch-owned and `main` has no equivalent. Verify by running `main`'s full offline gate set green before writing any new code.
2. **Contracts first, both halves together** — `src/workshop/concept/` and the finalizer's `concept` subcommand, with the round-trip test, before any wiring.
3. **Wire the stage** — the eight tables, the gate, the packet, `NativeMade.concept_sha256`, and the Make-gate checks.
4. **The integration last** — it is the only part that needs a credential, and everything above it is testable with a fake adapter patched at `workshop.workflow.native_run`.
5. **ABO** — independent of steps 2–4; it can land before or after.
6. **Docs and the changelog fragment** — including the README correction from D8.

**Rollback**: the change is additive to `main` except for `NativeMade`'s new required field. Reverting means reverting that field and the eight table entries; no persisted run state outlives a revert, because a run bound to a checkpoint written by the removed stage fails closed on resume rather than misbehaving.

## Open Questions

- Which image provider and model to configure by default. The specs assume no vendor, and the adapter takes its configuration explicitly, so this is a deployment choice that changes no requirement and no task.
- Whether ABO's kept scripts belong in a separate `abo-rules-engine` skill or under `abo-inventor/scripts/`. Both satisfy the manifest; the split only matters if a second ABO specialty appears later. Decide when the trimmed tree's size against the 16 MiB limit is known.
- Why a persisted internal `task_complete` is sometimes not translated into
  external `turn.completed`, and whether the durable fix belongs in the Codex
  CLI, its Goal lifecycle, or Workshop's adapter. Resolving that question and
  removing D9's quiet-period fallback is explicit future work.
