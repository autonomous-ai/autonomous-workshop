# ADR 0081: Shape Rounds follow Component Reviews

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-10-01
- Owners: `make-round` skill, the make_round guard
  (`make/make_round_guard.py`), product-run Make instructions
  (`references/make.md`), the Component Worker definition
  (`src/workshop/make/agents/component-worker.toml`)
- Amends: ADR 0075 and ADR 0077 (how Shape Rounds are counted and what the
  cap does); ADR 0076 (when a Component Acceptance is recorded)
- Extended by: spec B of issue #76's series (reviewer identity and the
  Manager-reviewer channel) and spec C (Interfaces, which add an Interface
  failure as a third unlock reason)

## Context

Broken God attempt 11 (`wish-20260930-201412-e8f60ec7`, Spark, Contract
Mode, Claude runtime) spent its whole product token allowance in Make and
never reached assembly. Ten Components ran 111 component rounds: 42 passed
build and print, 24 Component Reviews were recorded, and five Components
finished with a disagreeing review.

1. **A passing round was never forced to a review.** `make_round` refused a
   round only after the fifth Shape Round. Passing rounds were changed again,
   or went stale, before anyone reviewed them.
2. **A Shape Round counted any geometry change after a passing round.** One
   Component used four of its five Shape Rounds on a self-initiated tweak, a
   Manager-ordered socket change and a rerun after a Shared Helper edit
   before its first review, leaving one round for the reviewer's list.
3. **The cap bit once.** After a Component Acceptance more rounds were
   allowed, so the latest round was no longer the accepted one.
4. **Every packet hashed every shared file.** One edit to a file a single
   Component used staled all ten, and the Manager twice broadcast "your pass
   is stale, rerun". To record one review the Manager rebuilt old shared
   files byte for byte and swapped the new ones back.
5. **Failed rounds were rendered.** 69 rounds rendered images nobody would
   review.

## Decision

1. **One pure round policy.** `make_round` decides admission, Shape Round
   counting and the lock in one pure function, `round_policy`, from the
   Component's previous state (phase, latest identity, Shape Rounds used, the
   review the phase rests on with its imported-helper hashes, and recorded
   unlock reasons) and the new round (B-rep identity, imported-helper hashes,
   check result, carry key). `review_policy` applies a recorded review. They
   replace the cap-only refusal and the inline count.
2. **Review before change.** A round that passed its checks and has no
   review refuses a round with a different identity, including one that fails
   to build. The build runs, because identity is the B-rep hash; a refused
   round writes no round directory, puts back the STEP it overwrote and exits
   2 with the reason. A rerun with the same identity is admitted and not
   counted.
3. **What a Shape Round is.** The first geometry-changing round after a
   disagreeing Component Review. The repairs that follow until the next
   passing round are not counted. Build and print repairs, unchanged reruns
   and changes forced from outside the Component are never Shape Rounds. A
   build failure after a disagreement is not the Shape Round; the next round
   that builds a different B-rep is.
4. **Lock.** An agreeing review locks the Component. A disagreeing review
   recorded once the five Shape Rounds are used is a Component Acceptance and
   locks it too. A locked Component refuses a different identity unless an
   unlock reason exists; the same identity is admitted.
5. **Unlock reasons.** (a) A Shared Helper the Component imported at lock
   time has a different hash; `make_round` detects this itself. (b) An
   assembly repair: `make_round --component part_<id>.step.py
   --record-unlock <unlock.json>` records `{"assembly_round", "finding",
   "reason"}`, citing one finding the Manager recorded on that assembly round
   with `--record-visual`. It builds nothing, and is refused for a Component
   that is not locked. Spec C adds an Interface failure through the same
   record. Rounds after an unlock are admitted and never counted.
6. **Carry-forward.** On the next passing round after an unlock, or an
   unchanged rerun of a locked or disagreed Component, a B-rep identity,
   shown reference bytes and cameras, and the Component's contract rows
   (its Unique Geometry and the requirements and references scoped to it)
   all equal to the reviewed round's carry the review or Acceptance forward
   as `review.carried_from`, without a render or a reviewer call. A locked
   Component relocks on the new helper hashes, and the round exits 0. A
   different B-rep returns it to "passed, awaiting review" with its Shape
   Round count kept; a disagreeing review then, at the cap, is a new
   Component Acceptance, so the run cannot loop.
7. **Import-scoped staleness.** A component packet and lock bind the
   Component's own source and STEP and the project-local modules its source
   imports, read transitively from its import statements (including each
   package's `__init__.py`). A change to another Component's files, the
   combined entry, a spec, or an unimported Shared Helper stales nothing of
   it. The assembly packet still binds every project file.
8. **No render on failure.** A component round that fails its checks is not
   rendered; its visual status is `not-rendered`. `--record-review` refuses a
   round without a packet, and still refuses a second review of a round that
   has one, a carried review included.
9. **Summary and state.** Each component round adds `shape_round`,
   `shape_rounds_used`, `phase`, `locked` (`{"round", "source"}`), `unlock`,
   `imported_helpers` and `carry_key`; a carried round's `review` holds
   `carried_from`. The summary text has `shape`, `helpers`, `unlock` and
   `lock` lines. The component state holds the policy state. Exit codes keep
   their meaning; a refused round is exit 2.
10. **Roles.** The make_round guard treats `--record-unlock` like
    `--record-review`: only the root Workshop Manager runs it. The Make
    reference and the Component Worker say: report when build and print pass,
    then wait; change geometry only after a recorded disagreeing review or an
    unlock; read the round summary for Shape Round and lock status.

## Consequences

- Tokens go to repairs the reviewer asked for. A worker that guesses is
  refused at once, after one build, with a reason telling it to wait.
- Five Shape Rounds mean five repairs of reviewer feedback, and a Component
  Acceptance is the geometry that was accepted.
- A Shared Helper edit sends back only the Components that import it, and
  one that rebuilds the same B-rep keeps its review with no reviewer call.
- A worker can still change shape freely while its round fails build or
  print; the next passing round is reviewed before anything else.
- Imports are read statically. A helper reached only through a dynamic
  import (`importlib`, `exec`) or a data file a helper reads is not bound;
  the assembly packet and `--require-component-passes`, which compare the
  freshly built B-rep, still catch the change before assembly.

## Compatibility and migration

Runs created before this change keep their materialized `make_round`,
guard and instructions, including on resume. Only new runs get the new
rules. `workshop resume --refresh-tools` is the operator's explicit request
to rewrite a run's host-owned tools; a Component whose state an earlier
`make_round` wrote is then read from its latest round (awaiting review,
disagreed, locked or open) and continues under these rules.

## Verification

A table test drives `round_policy` and `review_policy` through every case
above without CAD. The `make_round` tests, with a fake build, print gates and
renderer, cover refusal of a changed geometry before review, Shape Round
counting, no render on failure, imported and unimported helper staleness,
the new summary fields, carry-forward after a helper change, an awaiting
review after a moved B-rep, the assembly unlock record and its refusals, a
new Acceptance at the cap after an unlock, and a second review refused. The
guard tests cover `--record-unlock` as a root-only call, and
`make_round --self-check` holds the core rules. A rerun of Broken God
(attempt 12) after specs A-C land, comparing total rounds, print-gate
failures, time from a passing round to its review, tokens at assembly and
Component Acceptances, needs the owner's go-ahead.

## Rejected alternatives

- **Keep counting any change after a passing round and raise the cap.** It
  still spends repairs on guesses and outside changes.
- **Refuse by source hash before building.** A source edit that leaves the
  B-rep unchanged (a comment, a rename) would be refused; the B-rep is the
  geometry the reviewer judged.
- **Run the source to record its imports.** It costs a second CAD import per
  round and runs the Component's module-level code outside `gen`.
