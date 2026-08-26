## 0. Precondition

- [x] 0.1 Confirm `add-researched-wish-breakdown` has landed: `WishResearcher`, `WishResearchRequest`, `WishResearch`, and `DefaultConcept`'s `brief_maker` and `wish_researcher` arguments exist in `src/inventor_workshop/` and its specs are under `openspec/specs/workshop/`. Do not start section 3 before this holds.

## 1. Import and lock the upstream tree

- [x] 1.1 Copy `board-game/tools/{rules_check,playtest,table_run,gate,ergonomics_check,preview}.py` and `board-game/tests/fixtures/cad_project/` from `reinSPQR/vibe-ideas` at the commit pinned in `upstreams.json` into `inventors/abo/harness/`, unmodified.
- [x] 1.2 Copy `.claude/agents/board-game-{ideator,rules-engineer}.md` into `inventors/abo/agents/`, and copy the lens definitions that map to Playtest findings (`lens-rules`, `lens-playtest`, `lens-playability`); leave `lens-fidelity` and `lens-animation` behind and record why in `UPSTREAM.md`.
- [x] 1.3 Write `inventors/abo/UPSTREAM.md`: source repository, pinned commit, import date, licence, the file-by-file inventory of what was imported, and the list of what was deliberately not imported (`pipeline_queue`, `telegram`, `dashboard`, `game_site`, `publish`, `journal`, `improve`, `QUEUE.json`, both owner gates) with the reason each has no place in a Wish-driven six-job Workshop.
- [x] 1.4 Add the `abo` entry to `snapshots.lock.json` and confirm `python tools/verify_snapshot_locks.py` computes and matches the imported tree fingerprint offline.
- [x] 1.5 Prove the lock bites: mutate one byte of a vendored file, confirm verification fails, restore it.
- [x] 1.6 Update the `reinSPQR/vibe-ideas` entry in `upstreams.json` from `inventor-snapshot` to its adopted role, keeping the same commit.

## 2. Repoint the imported harness at this repository

- [x] 2.1 Replace the upstream repo-root and `.venv` path assumptions in the imported modules with paths resolved from the inventor root and the running interpreter.
- [x] 2.2 Repoint the CAD calls at this repository's locked `skills/cad`; do not vendor a second copy and do not touch `skills/LOCK.json`.
- [x] 2.3 Write a characterization fixture that runs the imported gate's CAD calls against this repository's skill and compares results with the upstream-pinned skill for the five differing files (`verify_project`, `cadgen/catalog.py`, `cadgen/metadata.py`, `cadgen/step_targets.py`, `inspect_refs/inspect.py`). Record any behavioural difference and fix it in the adapter layer, not in a vendored file.
- [x] 2.4 Lift the hardcoded bed envelope out of the gate into ABO configuration, defaulting to the Bambu Lab P2S usable 246 × 246 × 251 mm rather than the upstream 256 mm constant.
- [x] 2.5 Remove every import of and reference to the non-ported modules from the imported tree, so nothing reaches for a queue, a journal, a notification channel or a publisher; the harness must import cleanly with those files absent.

## 3. Concept: invent the game (`workshop/abo-game-research`)

- [x] 3.1 Define ABO's game record — title, central idea, seat count, playtime, rules with per-step `uses` declarations, component bill with quantities, art direction in form language — and its on-disk shape under the concept root.
- [x] 3.2 Adapt the imported `rules_check` into ABO's consistency check over that record: a rule reaching for an absent component fails, a component no rule uses fails, exceeding the record's own declared complexity ceiling fails and is distinguished from an ambiguity finding.
- [x] 3.3 Implement the game inventor behind ABO's research step: Wish + Taste + blueprint in, one game record out, refusing rather than returning where the check fails.
- [x] 3.4 Enforce the Wish-is-structural rule: refuse a record whose only connection to the Wish is a name or a label.
- [x] 3.5 Enforce colour-freedom: refuse a record where any distinction a player must make depends on colour or material.
- [x] 3.6 Derive the physical-facts `WishResearch` from the game record, with the bill as `components`, and every stated fact carrying either a recorded source or a recorded decision with its reason.
- [x] 3.7 Implement `brief_maker` so the `ConceptBrief`'s components are exactly the bill's, naming motif variants separately; assert the bill fits `MAX_CONCEPT_COMPONENTS` and fail with a taste-legible message when it does not.
- [x] 3.8 Implement ABO's Concept hook per design D1: delegate drawing to `DefaultConcept`, write the game record and check result into the concept root, rebuild the manifest over the augmented root, return a `ConceptImages` sealed over all of it. Comment the rebuild step with a pointer to D1.
- [x] 3.9 Implement the refining round: reuse the standing research, revise the standing game against the round's feedback, never invent an unrelated one.
- [x] 3.10 Tests: good record passes; each consistency failure mode fails with the right finding and disposition; an unattributed dimension is refused; a Wish-decorative record is refused; the sealed concept's hash covers the game record; the exact rules are recoverable verbatim from a sealed concept.

## 4. Make (`workshop/abo-make`)

- [x] 4.1 Adapt the imported rules-engineer flow to compile the sealed rules into an executable engine written into the product artifact tree.
- [x] 4.2 Enforce refuse-or-declare: a silent rule either stops Make naming that rule, or is recorded as an assumption naming the rule, the question, the reading taken and the alternative. Never a rule invented to make the engine run.
- [x] 4.3 Return a rules gap as a finding against the rules rather than absorbing it into the engine; return a non-startable or non-terminating game the same way.
- [x] 4.4 Enforce the hidden-information contract: a declared hidden-information engine exposes a per-seat view and a resampler, resampling leaves the seat's own view unchanged, and a declared-open game is recorded as such so play can check it.
- [x] 4.5 Build STEP-first CAD for every brief component through the locked skill, with meshes derived from STEP and none present for a component without STEP.
- [x] 4.6 Enforce numbers-beat-pictures against the brief's envelope, wall, fits and print stance, and keep each component's geometry traceable to the brief facts it was built from.
- [x] 4.7 Return `Made` with `product["components"]` corresponding one-to-one with the brief's, and confirm no product file carries the bytes of a concept image.
- [x] 4.8 Tests: engine ships inside the product and is covered by its hash; a fixture game plays to a terminal state through the engine; a silent rule refuses; a declared assumption is recorded in full; a mismatched or extra component is refused; a concept image byte-copied into the product is refused; a post-Make edit invalidates the revision.

## 5. Playtest — simulation (`workshop/abo-playtest`)

- [x] 5.1 Adapt the imported simulation harness to run against the engine bytes inside the revision under test, and to bind every output to that revision's hash.
- [x] 5.2 Write the `adversarial` policy (deny the opponent's best reply) per design D3, and map `optimizing` and `exploratory` onto the ported lookahead/Monte-Carlo and randomized policies.
- [x] 5.3 Count only completed games toward the total; report turn-cap, deadline and engine-error abandonments separately.
- [x] 5.4 Enforce the 1,000-completed-game floor, and return `WaitingFor(Need("playtest", "game-simulation", ...))` reporting the completed count when the deadline arrives short — never a pass over a smaller sample, never a silently extended deadline.
- [x] 5.5 Measure and record style distinctness over the sample; report two styles that never diverge as one.
- [x] 5.6 Emit the measured properties: termination, seat advantage across a seat-swapped balanced sample, forced-turn fraction, branching, declared move kinds never legal or never chosen, and the stronger-versus-weaker policy margin.
- [x] 5.7 Exercise both readings of every declared engine assumption and report whether the reading changed the outcome.
- [x] 5.8 Port the always-forced move-kind rule: a kind claimed to carry no decision that is ever seen alongside another legal move is reported as a contract finding and counted as a real branch.
- [x] 5.9 Assemble the `game-simulation` result with `evidence_class="ai-simulation"`, `executable=true`, the completed count, the four `player_styles`, a named evaluator and exact version, and sealed evidence referenced by hash.
- [x] 5.10 Tests: the floor rejects 999 completed games; abandoned games do not count; the short return produces a `Need` and no passing result; two collapsed styles are refused; a recorded seed set reproduces the same games against the same engine bytes.

## 6. Playtest — model seats (`workshop/abo-playtest`)

- [x] 6.1 Adapt the imported model-seat harness: deterministic loop, one plain HTTPS call per decision, endpoint and model read through `load_dotenv` under ABO-scoped names.
- [x] 6.2 Enforce the seat boundary: choice is an index into the engine's enumerated moves and anything else is refused; a seat is shown only its permitted view; a seat reaches no file, engine, evidence or other seat's messages.
- [x] 6.3 Assemble `agent-playtest` with at least two distinct non-empty roles, and record seat reports of decision-free turns and of the game getting smaller as simulation findings — never as evidence of enjoyment.
- [x] 6.4 Feed the model-seat games into `game-simulation`'s `social` style while keeping the two results and their evidence files separate.
- [x] 6.5 Return a `Need` when no model-seat endpoint is configured; never report a passing `agent-playtest` built from scripted policies alone.
- [x] 6.6 Tests: one role or a repeated role does not pass; an out-of-range or non-index reply is refused rather than interpreted; a hidden-information seat is never handed the full state; the recorded-transcript path runs the whole harness with no network.

## 7. Playtest — manufacturing (`workshop/abo-playtest`)

- [x] 7.1 Adapt the imported gate to compute `mechanical-test` over the revision's geometry: solid validity, mesh topology, dimensions against the brief, interference in declared poses, clearance at declared fits.
- [x] 7.2 Adapt it to compute `print-test`: bed fit per part against the configured envelope, minimum wall thickness, overhang and bridging, and slicing under a pinned printer, material and profile.
- [x] 7.3 Bind both results to the source-closure hash so a measurement computed from stale geometry is detectable, and refuse evidence whose sources have since changed.
- [x] 7.4 Map `fails` to blocking findings and `unmeasured` to a non-pass for the owning result; an unrun check must never count as a pass.
- [x] 7.5 Keep renders and previews out of support for topology, fit, interference or printability claims.
- [x] 7.6 Tests: an oversize undeclared part fails `print-test` naming it; two parts intersecting in a declared pose fail `mechanical-test` naming both; absent slicer configuration reports unmeasured and blocks the pass; stale-source evidence is refused.

## 8. Feedback and the round loop

- [x] 8.1 Map every blocking finding to `Feedback` with area, finding, evidence refs, severity and a concrete change; a finding about the game names the rule it is about.
- [x] 8.2 Apply the severity rule from design D6: rules ambiguity or incompleteness is `improve`; a functional defect or a failed manufacturing measurement is `block`.
- [x] 8.3 Route design-invalidating feedback into the next round's Concept so the game is revised, not compensated for in CAD.
- [x] 8.4 Confirm `playtest_rounds` is the only budget: no repair, rework or clarification counter survives, and Wish text cannot raise the allowance.
- [x] 8.5 Tests: a dominant line produces blocking feedback naming the rule; a silent rule produces improving feedback that still returns the game to the loop; exhausting the allowance stops the run truthfully.

## 9. The inventor (`workshop/abo-inventor`)

- [x] 9.1 Scaffold `inventors/abo/` via `workshop create inventor abo --name "Abstract Boardgame Oracle" --lane invented-games --level custom-playtest --root .`, then replace the generated seams with sections 3–8.
- [x] 9.2 Write `TASTE.md`: frontmatter `name` and a `description` that reads as a selection boundary against the personalized-games inventor; a body committing to abstract structure over theme, a low piece-type ceiling with the learnability reason, depth from combinatorial structure rather than an added action type, shape-only distinction, perfect information as a stated preference not a ban, and the skill ladder as the test of "hard to master"; and the upstream owner-rejection ledger carried across as durable "do not propose this shape again" entries.
- [x] 9.3 Write `inventor.json` (schema v5, `custom-make` and `custom-playtest` among its capabilities, `source.kind=upstream-snapshot`, declared checks) carrying no creative prose.
- [x] 9.4 Write `profile.py`: `create_wish`, `build_workshop` wiring the Concept hook and the two seams, `describe`, and the `profile`/`wish`/`preview`/`run` CLI, following the bundled profiles' shape.
- [x] 9.5 Write `README.md` answering the seven questions `docs/BUILD_AN_INVENTOR.md` requires, and stating which engine protocol ABO uses and why (design non-goal 1).
- [x] 9.6 Write `pyproject.toml` declaring anything the harness needs beyond the locked skill and the standard library.
- [x] 9.7 Tests: ABO refuses a Wish whose meaningful content is a person, relationship, place or memory; accepts an abstract-strategy Wish; and the personalized-games inventor's Taste hash and profile are byte-identical before and after this change.
- [x] 9.8 Tests: no cross-run state survives a run; a missing Concept capability parks the run before Make is reached; a missing model-seat endpoint parks Playtest.

## 10. Offline proof and documentation

- [x] 10.1 Add the fixture game, fixture engine and recorded model-seat transcript so every declared check runs with no model credential, no network and no printer.
- [x] 10.2 Run the repository checks: `PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'`, `workshop inventors --root inventors --check-entrypoints`, `workshop check inventors/abo --run`, `python tools/verify_skill_locks.py`, `python tools/verify_snapshot_locks.py`, `python tools/scan_secrets.py`, `git diff --check`.
- [x] 10.3 Add ABO's row to `inventors/README.md`.
- [x] 10.4 Add ABO's row and truthful status to `docs/ADOPTION.md`, and correct its "next adoption slices" list, which names Leo for the lane evidence requirement that ABO now satisfies.
- [x] 10.5 Confirm no credential, endpoint or key reaches `TASTE.md`, `inventor.json`, an artifact, an evidence file or any committed source, and that `.env.example` names only the ABO-scoped variables.
- [x] 10.6 Run one end-to-end rehearsal with fixtures for every capability, and record in `README.md` exactly which claims that rehearsal supports and which it does not.
