# ADR 0077: Component Workers, a root-owned Component Reviewer, and cost-ranked levers

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-09-29
- Owners: product-run Make instructions (`references/make.md`, product-run
  `AGENTS.md`), `make-round` skill, Workshop host run creation
  (`agent_run.py`, `native_run.py`), Make role agents
  (`src/workshop/make/agents/`)
- Builds on: ADR 0063 (component-first Spark Make), ADR 0073 (carry-forward
  compares B-rep identity), ADR 0076 (a Component passes on an independent
  review; five shape rounds)
- Amends: the root rule that `.codex/agents/` holds only the Inventor roster,
  and the rule that every descendant runs at the root's frozen reasoning
  effort. Both change for new runs only.

## Context

Run `wish-20260928-142712-25fb17ef` used 171M tokens: 162.9M cached input,
7.2M uncached input and 0.8M output. Tokens are priced differently, so the
count misleads. Assuming cached input at 0.1x, uncached at 1x and output at
10x (the real prices of the model are not known), cost split roughly 52%
cached, 26% output and 23% uncached. The root Manager was about 42% of cost
and its 23 sub-agents about 58%.

The root built every Component itself. heart-core and arm-right each reached
round 19. Its context averaged about 115K tokens over 665 requests, with nine
compactions near 180K. Re-reading skills, the Design Contract and design
notes with `cat` was about 84% of tool text, and about 294 images of roughly
1K tokens each stayed in context. Every request re-sent all of it.

Waiting requests (empty `write_stdin` polls at a 30000 ms yield and
`wait_agent`) were 89 requests and 11.1M tokens, but almost all cached, so
about 4% of cost. Codex 0.158.0 accepts an empty-poll yield from 5000 to
300000 ms and returns as soon as the process exits.

## Decision

Rank levers by cost, not token count. The large lever is how long the root's
context is and how many requests carry it; waiting is a small one.

1. **One worker per Component.** Once the Component list is settled, the
   root Manager spawns one `component-worker` agent per Component, in
   parallel. The worker receives only the component id and its
   `part_<id>.step.py`, its sealed `geometry:<id>` reference and declared
   camera, that Component's Design Contract rows, the nozzle and the
   shape-repair limit (5). It edits only that source and runs
   `make_round --component` until build and print pass, then reports in 10
   lines or fewer: status (passed, accepted at cap or blocked), rounds used,
   the latest round and its identity, the reviewer's text and open issues. No
   logs and no images reach the root.
2. **The root owns the reviewer.** When a worker reports build and print
   passing, the root, not the worker, asks the Component's reviewer. Each
   Component has one `component-reviewer` thread, reused by follow-up for
   every later review so its cached prefix survives. The root records the
   answer with `make_round --record-review` (ADR 0076) and forwards a
   disagreement to the same worker as the next shape round. The worker ends
   when the reviewer agrees or the cap is reached, and its context is
   discarded.
3. **Only the reviewer sees component images.** Neither the root nor a
   worker views them; workers act on the reviewer's text.
4. **Shared helpers stay with the root.** A worker never edits a shared
   helper such as `features/forms.py`; it asks the root. The root edits it and
   sends the affected Components back through a worker. Their passes are
   already invalidated by the B-rep identity check (ADR 0073).
5. **Reasoning effort per role.** The worker inherits the root's effort
   (medium by default). The reviewer runs at `low`.
6. **Longer waits.** `make_round` polls and `wait_agent` use 300000 ms instead
   of 30000 ms, in `references/make.md`, the product-run `AGENTS.md` and
   `make-round`.
7. **Unchanged.** Assembly rounds, the blind review and final verification
   stay with the root. Skill files are not trimmed or restructured. The
   auto-compaction threshold stays and is re-measured after the first run
   with workers. The host resume prompt stays; Codex keeps past user messages
   through compaction.

### How the roles reach Codex

The host materializes both roles as declarative Codex custom agents,
`.codex/agents/component-worker.toml` and
`.codex/agents/component-reviewer.toml`, from
`src/workshop/make/agents/`. They are sealed and hash-bound like every other
run input and registered the same way as Inventor agents (ADR 0054). The
reviewer's file declares `model_reasoning_effort = "low"`; the worker's
declares none, so it inherits the root. No Python schedules, routes or waits
for them: Codex owns spawning and the Manager decides when. The Inventor
roster in the checkpoint is unchanged and never includes these roles; a run
snapshot admits the two role files only when the run sealed them, and refuses
a role file that does not parse as its role.

Every new run receives both files, whatever its lifecycle. Only the
component-first Spark Make protocol uses them; in Forge and Quest they sit
unused, which keeps run creation independent of the lifecycle.

Frozen runs keep what they materialized. A run created before this change has
no role agents and its own `references/make.md`, so it keeps building
Components in the root.

## Consequences

- The root's context no longer grows with every component round, its logs or
  its images. Each worker's context is short-lived and discarded.
- More threads run at once. A run with many Components may hit the runtime's
  thread limit; the root then spawns the next worker when one finishes.
- Worker reports are the root's only view of component work, so a worker that
  misreports can mislead it. The recorded review and the B-rep identity check
  still bind what passes.
- Whether this lowers cost without lowering quality is not yet shown. It
  needs a live run, which should also re-measure the compaction threshold.

## Rejected alternatives

- **Workers spawn their own reviewer.** The root would lose the one
  independent judgement it records, and a fresh reviewer per round loses its
  cached prefix.
- **A fresh reviewer each round.** Pays the reviewer's whole prefix uncached
  every time.
- **Trim the skill files.** Out of scope for this decision; the re-read cost
  moves to short-lived workers instead.
- **Choose effort per spawn call.** The spawn tool offers no reliable
  per-call effort; a custom agent file fixes it declaratively.
