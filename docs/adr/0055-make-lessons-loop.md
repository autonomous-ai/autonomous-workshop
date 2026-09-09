# ADR 0055: Make outcomes teach the design vault, and the vault teaches Make

- Status: Accepted
- Date: 2026-09-07
- Owners: Make gate, workflow, and design-vault maintainers

## Context

Only Playtest learned. After a sealed Playtest round the host posts confirmed
findings to the vault as evidence rows on anti-pattern nodes, queues
dismissals for review, and writes the product's own `games/<wish-id>` page
(ADR on the design vault, 2026-08-29). That loop fires on Quest runs alone.

Spark and Forge runs, which are most of them, never reached it. A Make that
failed its CAD gate, parked on a need, asked Invent for a revision, or ran
out of token budget wrote its evidence into the run's artifacts and stopped
there. Two consecutive microduck runs (2026-09-06 Forge, 2026-09-07 Spark)
hit the same wall, a 0.90 likeness floor that a mechanised adaptation of a
photo cannot meet, and the second run discovered it from scratch over
eighteen likeness rounds and 30M tokens. The lesson existed in the first
run's `final-rereview.json`; no code read it back.

## Decision

`workshop.make.vault_lessons` mirrors the Playtest module in both directions.

Write path. `_record_make_evidence` builds rows from four host-observed Make
outcomes and posts them through the same queue Playtest uses:

- a failed host CAD gate (`deterministic-cad-gate`, weight 3);
- a proposal the host refused (`deterministic-host-gate`; protocol codes
  such as `make-contract-invalid` yield no row);
- a Make-to-Invent revision request, one row per feedback item
  (`codex-authored-revision-request`, weight 2);
- a Make that parks on a need (`codex-authored-need`, weight 2).

The budget watcher queues a fifth kind on its own thread when the product
token cap stops a Make (`deterministic-host-budget`). Every row is
classified onto one anti-pattern node by failure class (`classify_make_failure`);
`likeness-wall` and `unbounded-repair-loop` join the vault as new
physical-process anti-patterns, the rest map onto nodes it already had
(`underbuilt-shell`, `sealed-volume-overlap`, `unswept-drive-cycle`,
`support-dependent-geometry`, ...). A passed Make posts the product page
alone, so every Spark and Forge wish now leaves a `games/<wish-id>` node with
a `make-*` verdict; a later Playtest rewrites it with its own.

Read path. Every Invent and Make packet carries `make_lessons`: at most ten
evidence rows, newest first and Workshop products before harvested sources,
drawn from the anti-patterns the concept's mechanisms risk and from the Make
failure classes themselves, each with the vault's recorded fixes. Spark's
first round, which has no sealed concept yet, draws on the mechanisms the
Wish names. The constitution tells the Manager to read them before designing
or repairing and to say in the source when one applies; they never waive a
gate.

## Consequences

- The next duck-shaped wish reads "IoU 0.688 against a 0.90 floor after 18
  rounds" before its first likeness round, with the fix list beside it.
- The vault gains a page per wish for the routes that run most, so its
  exemplar lists stop being Quest-only.
- Rows are bounded and classified; an unclassified failure is dropped rather
  than banked under a phantom node, the same rule the vault applies to
  harvested rows.
- A vault that is unreachable delays the rows to the next phase exactly as
  it delays Playtest rows; nothing in Make waits on the network.
