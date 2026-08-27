# ADR 0016: Selectable effort routes

- Status: Accepted
- Date: 2026-08-27
- Owners: CLI, Workflow, Runtime, Invent, Make, Playtest, and Release
- Supersedes: ADR 0015's single fixed lifecycle for new runs

## Context

One fixed creative workflow makes fast product experiments pay for the same
number of native turns as deeper work. Match also consumes a separate turn even
though Inventor selection is useful context for whichever creative stage acts
first. Workshop needs a quick path for testing, a balanced default, and an
evidence-heavy path without turning skipped work into a false pass.

Effort must be frozen per run. Resume cannot reinterpret an existing run after
the installed host, CLI default, or product-run playbook changes.

## Decision

`workshop wish --effort <mode>` accepts three public effort names:

```text
Spark: Wish -> Make -> Release
Forge: Wish -> Invent -> Make -> Release
Quest: Wish -> Invent -> Make -> Playtest -> Release
```

Forge is the CLI default. The exact lowercase values are `spark`, `forge`, and
`quest`.

New effort-aware runs use checkpoint schema v4 and freeze the selected value
together with the immutable materialized
`references/effort-routes-v1.md` capability. Optional stages pass through by
selecting the next enabled stage in the canonical sequence. A passed-through
stage receives no native turn, Goal, authored artifact, deterministic gate, or
evidence receipt.

Match is not an active stage in effort-aware runs. Inventor selection is folded
into the first active creative stage:

- Forge and Quest seal the roster-bound assignment and Invented contract from
  one Invent turn.
- Spark seals the assignment, a compact Invented contract, and Made contract
  from one Make turn.

The existing typed Match and Invented contracts remain the exact provenance
boundary. Folding their authoring into one Goal removes process and model-turn
overhead without letting Python select an Inventor or invent a concept.

Spark and Forge use the truthful direct-Release contract: full-tier,
thickness-checked, print-ready CAD is required and Release records
`playtest_status: not-run` with canonical omission bytes. Quest activates the
existing bounded Make–Playtest feedback protocol. Only a passing Playtest for
the current Made revision may advance to its evidence-bound Release.

All three routes retain terminal authenticated Factory publication, exact
public hash readback, one persistent native session, one Goal per active stage,
credential isolation, and host-owned deterministic gates.

## Alternatives considered

### Keep Match but hide it from status

Rejected because it would still consume a native turn and would make the
displayed route misleading.

### Have Python choose a default Inventor for shorter routes

Rejected because Inventor selection is cognitive work owned by the native
Manager and Taste-aware subagents.

### Create successful placeholder artifacts for skipped stages

Rejected because omission is not evidence. Pass-through changes the route; it
does not fabricate a stage result.

## Consequences

- Spark reaches a release proposal in two native turns, Forge in three, and
  Quest in four when no repair or publication wait occurs.
- The first active creative stage has a compound finalizer contract and gate.
- Playtest documentation and deterministic gates are active for Quest while
  remaining explicitly absent for Spark and Forge.
- CLI receipts expose the frozen effort, and status/resume preserve it.
- Workflow tests must cover every exact route plus Quest feedback repair.

## Compatibility and migration

Checkpoint schema-v3 runs remain readable under the topology frozen in their
materialized assets. Pre-ADR-0015 Make–Playtest runs, ADR-0015 direct-Release
runs, and historical Deliver checkpoints are not reinterpreted as effort-aware
runs. The old Match stage and its standalone finalizer command remain readable
for those sessions.

## Verification

- CLI tests prove all three names are parsed and forwarded, with Forge as the
  default.
- Pure workflow tests prove optional stages are absent from checkpoint
  artifacts and illegal transitions fail closed.
- Deterministic end-to-end tests execute Spark, Forge, and Quest through exact
  finalizers, host gates, CAD replay, Release validation, and Factory doubles.
- A Quest failure-path test proves Playtest feedback returns to Make without a
  Match stage and still consumes the shared round budget.
