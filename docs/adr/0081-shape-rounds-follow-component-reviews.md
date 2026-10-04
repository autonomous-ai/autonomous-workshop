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
- Extended by: spec B of issue #76's series (issue #77, reviewer identity
  and the Manager-reviewer channel; see "Extension: one proven Component
  Reviewer" below) and spec C (Interfaces, which add an Interface failure as
  a third unlock reason; ADR 0082); amended by issue #97 (2026-10-04, see
  "Amendment: a Blocked Report ruling binds the Component Reviewer" below)

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

## Extension: one proven Component Reviewer (issue #77)

### Context

In attempt 11 the review was not independent, and nothing could tell. The
Manager asked reviewers to "re-review … taking into account …" and to
"re-issue your chest-cage r0005 review with three changes", forwarded a
review with "Ignore item 1", and spawned a fresh reviewer for most reviews
although ADR 0077 keeps one thread per Component. `reviewer` was free text
("component-reviewer", "<subagent name>"). The reviewer only reads images and
returns text, so no hook saw which agent judged which packet. Reviewers also
asked for detail that cannot print at that scale (1 mm rivets, 0.6-0.9 mm
raised bands, sharp cones), one driver of 64 print-gate failures in 111
rounds.

### Decision

1. **Reviewer id.** On a runtime that proves who reviewed, `reviewer` is the
   native agent id the runtime returned when the reviewer was spawned. The
   launcher names the runtime to `make_round` with
   `WORKSHOP_REVIEWER_RUNTIME`; for Claude Code the id is 17 lowercase hex
   characters. `--record-review` refuses any other value, binds the
   Component's first id in its component state (`reviewer_id`, kept across
   rounds) and refuses a review naming another id with a message naming the
   bound one.
2. **Evidence.** The make_round guard is also registered for `Read` and
   `SubagentStart`. It appends every subagent start (`agent_id`,
   `agent_type`, `session_id`) to `subagents.jsonl`, and every `Read` by a
   `component-reviewer` (`agent_id`, `agent_type`, resolved path, sha256 of
   the file when the hook runs) to `reviewer-reads.jsonl`, both beside the
   nonce table in host state, outside the workspace. It never denies a read
   or a spawn.
3. **Host verification.** The check that admits worker nonces also checks,
   for every review recorded on a worker's round (a review carried forward
   is judged on its original round; a summary the revision source sealed
   keeps its evidence): the id has the runtime's format; the subagent log
   started it as a `component-reviewer`; the read log shows it read every
   image of that round's packet (front, top, iso and each `compare-NN.png`)
   with the packet's hashes; and every review of the Component names the same
   id. Any failure refuses the Make output like an unissued nonce; an
   unreadable log is a host-state conflict.
4. **Fixed channel.** The review request is the packet path, its sha256 and
   the Component's contract rows, nothing else, sent once per packet to the
   Component's one reviewer thread. The Manager writes the answer unchanged,
   never asks for a second review of a packet (one review per packet is
   already enforced) and never edits, filters or summarizes it. It tells the
   worker only "review recorded for round N"; the worker reads `review.json`
   in that round.
5. **Printable repairs.** The reviewer definition explains the print stance
   (a rotation the stance explains is not a difference) and the printing
   limits at the run's nozzle, citing the wiki pages they come from
   (`wall-thickness-and-hollowing`, `fdm-minimum-feature-sizes`,
   `overhangs-and-print-orientation`). Repairs stay within them; the
   agree/disagree judgement is still form against the reference (ADR 0076).
6. **Scope.** The checkpoint freezes `component_reviewer_binding` for new
   Claude Code runs with the guard. Codex runs keep the free-text reviewer
   and no read evidence until Codex exposes equivalent subagent and read
   evidence; Grok has no guard. Frozen runs keep their materialized hook,
   tool and definitions; an older guard ignores the new events.

### Consequences

- "Independent review" in the run report rests on host evidence: an agent
  the runtime started as the Component Reviewer read the exact images.
- The Manager can still type any id; the host check against the subagent and
  read logs is what makes the binding hold. Like the nonce table, the logs
  are tamper-resistant, not tamper-proof, on Claude Code.
- A reviewer that judges from a summary, or a review re-issued by a new
  agent, is refused at Make acceptance and must be redone by the bound
  reviewer on a fresh round.
- The `SubagentStart` hook input (`agent_id`, `agent_type`) is taken from
  Claude Code's documented hook contract and its 2.1.286 binary; a live run
  must confirm it, together with the `Read` hook from a subagent.

### Verification

`make_round` tests cover a refused non-id reviewer, the first id binding, a
second id refused and the same id accepted, and the free-text path without a
runtime. Guard tests cover a reviewer `Read` logged with id, type, path and
hash, reads by other agents or the root not logged, a subagent start logged,
and both logs written beside the script rather than in the workspace. Host
tests cover a pass and refusals for an id with no start record, another
agent type, a missed image, other bytes, a second reviewer, a non-id and a
changed packet, and an unreadable log as a host conflict. Launcher and
checkpoint tests cover the hook registration, the environment and the frozen
binding.

## Amendment: a Blocked Report ruling binds the Component Reviewer (2026-10-04, issue #97)

Status: Accepted; implemented and deterministically tested; not yet
validated by a live run.

### Context

Broken God attempt 17 (`wish-20261004-050844-831e5160`) lost the
legs-pelvis lock and about 5.5M worker tokens to one repeated request. From
r0005 on, every review asked the worker to remove the pelvis arch struts and
hang a shield over open space, which the sealed print stance ("prints
upright on its soles; no part needs support; the pelvis gets a
pointed-arch underside") forbids. The worker filed Blocked Report 1; the
Manager ruled "keep the struts; if a later review asks again, give this
reason". The reviewer never saw that ruling: the fixed request (decision 4
of the #77 extension) is only the packet path and hash, and the packet had
no ruling. It repeated the request on every round, and the worker spent
Shape Rounds r0006, r0007, r0009 and r0010 on it, reaching the cap of five.

### Decision

For new runs:

1. **Rulings travel in the packet.** A component round writes the
   Component's decided rulings into its visual packet and summary as
   `rulings`, oldest first: `{"report", "round", "rows", "request",
   "ruling", "decided_at"}`, copied from `measure/blocked-reports.jsonl`
   (the worker's report as `request`, the Manager's last decision as
   `ruling`). A ruling is a report of this Component whose last answer is a
   decision that waits on nothing; an open, waiting, need or amended report
   is not one. They are bound by the packet hash like the contract rows;
   make_round copies them and judges nothing. An unreadable ledger refuses
   the component round before anything is built.
2. **The request stays fixed.** The Manager still sends only the packet
   path and hash; the ruling reaches the reviewer through the packet, never
   through the Manager's words.
3. **The reviewer is bound.** The Component Reviewer definition says: never
   ask again, as a difference, for what a ruling rules out. A reviewer who
   thinks a ruling wrong lists it under `ruling_disputes`, each `{"report",
   "reason"}` naming a ruling of the packet. A Ruling Dispute is not a
   difference: like a Reference Conflict (ADR 0084) it costs no Shape
   Round, never reaches the worker (`review.json` is written without it;
   the round keeps `ruling-disputes.json`), and a review whose only
   findings are disputes agrees. `--record-review` refuses a disagreeing
   review with no differences and a dispute, and a dispute naming no ruling
   of the packet.
4. **What a review judged includes its rulings.** The rulings join the
   carry key, appended only when there are any, so a Component with none
   keeps its keys. A disagreement does not carry to an unchanged rerun made
   after a new ruling: that rerun is not a Shape Round (decision 3) and is
   reviewed afresh, against the ruling. `--record-review` refuses a review
   of a packet rendered before the Component's latest ruling; the worker
   reruns unchanged.
5. **Shape Round counting is unchanged.** Whether a disagreeing review's
   differences only repeat a ruled-out request is a judgement of text, and
   make_round makes none. The deterministic parts are decisions 3 and 4: the
   reviewer itself separates disputes from differences, a dispute-only
   review agrees, and a ruling buys an unchanged rerun a fresh review
   without spending a Shape Round.

### Consequences

- A ruled-out request costs at most the review that prompted the Blocked
  Report. In attempt 17 the ruling would have reached the r0006 reviewer,
  which, bound by it, could have agreed on the remaining printable repairs.
- A reviewer that ignores its instructions and repeats a ruled-out request
  as a difference still spends a Shape Round; nothing deterministic can tell
  that difference from a new one. The five-round cap and the Component
  Acceptance still bound the loop.
- Ruling Disputes stay in the round evidence (summary, `ruling-disputes.json`
  and the summary's `dispute` line) for the Manager; they are not added to
  the run report. A Manager who agrees with one answers with the tools it
  has (a Contract Amendment or a need), never by telling the worker to
  repair toward the dispute.
- A new ruling on a locked Component changes its carry key, so its next
  unchanged rerun after an unlock is reviewed again instead of carried.
  Locks themselves, `--require-component-passes` and the assembly packet
  are unchanged.

### Compatibility

Runs created before this change keep their materialized `make_round`,
agent definitions and instructions, including on resume; their packets
carry no rulings and their reviews have no `ruling_disputes`. Only
`workshop resume --refresh-tools`, the operator's explicit request, brings
the new rules to an existing run. The ledger format of issue #88 is
unchanged.

### Verification

`make_round` tests cover a packet and summary carrying only the
Component's decided rulings (not open, waiting or another Component's), an
unchanged packet and carry key without one, an unchanged rerun after a
ruling reviewed afresh without a Shape Round and a dispute-only review that
locks and carries its dispute, a dispute-only disagreement refused, disputes
beside differences spending only the differences' Shape Round, a review of
a packet older than a ruling refused, malformed disputes refused, a dispute
with no ruling in the packet refused, and an invalid ledger refusing the
round before a build. `make_round --self-check` holds the ruling selection
and the carry key rule. The agent asset tests hold the reviewer and worker
definitions.

## Rejected alternatives

- **Keep counting any change after a passing round and raise the cap.** It
  still spends repairs on guesses and outside changes.
- **Refuse by source hash before building.** A source edit that leaves the
  B-rep unchanged (a comment, a rename) would be refused; the B-rep is the
  geometry the reviewer judged.
- **Run the source to record its imports.** It costs a second CAD import per
  round and runs the Component's module-level code outside `gen`.
