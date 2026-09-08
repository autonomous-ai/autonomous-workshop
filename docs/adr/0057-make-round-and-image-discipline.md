# ADR 0057: One command per Make round, one image view per round

- Status: Accepted
- Date: 2026-09-08
- Owners: Make skills and product-run protocol maintainers

## Context

The first published wind-up microduck (wish-20260907-095852-07806a43,
2026-09-07) cost 38.8M tokens for one Spark product, 13 points of the Codex
weekly quota. Its rollouts show why. The Manager made 925 model requests
averaging 44k tokens of context each; 95% of the input was cache re-reads,
which the plan meters at roughly the same rate as fresh tokens. Of its 673
shell calls, 430 were `cat`, `rg`, `sed`, and `tail` over skill sources and
the run's own logs, 103 ran a tool, and 58 viewed an image. Each call is a
request, and each request carries the whole context, so the bill is the call
count times the context size, not the size alone.

## Decision

Two rules in the product-run constitution, and one skill to make them
cheap to follow.

`make-round` is a host-owned domain skill (`make/skills/make-round`). Its
`SKILL.md` is the tool card: the exact invocations of every cad and
image-to-cad gate, so the Manager never reads a script to learn a flag. Its
`scripts/make_round` runs one Make iteration as one command: export every
part, wall-check only the parts whose STL bytes changed since the previous
round, score likeness against each Wish reference with the previous pose
replayed, run the motion gate when the project declares a manifest, and
optionally run the integrated `verify_project` once. It prints a summary of
a dozen lines and keeps every tool's full output under
`measure/rounds/rNNNN/`. Every verdict comes from the original tool; the
script never lowers a threshold, never edits source, and never replaces the
final verifier the Make gate requires.

The constitution now directs each repair round through `make_round`, forbids
reading skill scripts for their flags, and limits image viewing to one per
round, only when a decision depends on what a number cannot tell, because a
viewed image stays in the context of every later request.

## Consequences

- Expected effect on a run like the microduck: shell calls from about 670 to
  about 200 and average context from 44k toward 30k, which together should
  put a Spark run under 15M tokens. The next run measures it.
- The skill roster gains an entry; the reviewed-skill lock records it under
  this repository, not the upstream CAD repository.
- Nothing about gates, thresholds, or evidence changes; a round that skips
  unchanged parts still exports and hashes every part, so a silent change
  cannot hide.
