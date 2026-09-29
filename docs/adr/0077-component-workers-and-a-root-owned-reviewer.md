# ADR 0077: Component Workers and a root-owned Component Reviewer

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-09-29
- Owners: product-run Make instructions (`references/make.md`, product-run
  `AGENTS.md`), `make-round` skill, Workshop host run creation
  (`agent_run.py`, `native_run.py`), Make role agents
  (`src/workshop/make/agents/`)
- Builds on: ADR 0060 (visual feedback within Make rounds), ADR 0063
  (component-first Spark Make), ADR 0073 (carry-forward compares B-rep
  identity), ADR 0074 (every Component scored against its own image), ADR
  0075 (acceptance needs a second reader)
- Amends: the root rule that `.codex/agents/` holds only the Inventor roster,
  the rule that every descendant runs at the root's frozen reasoning effort,
  and ADR 0060's rule that the Manager records every Make round's visual
  feedback. All three change for new runs only.

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

A Component's round passes on its build, its print gates and its likeness:
every scored image reaches the 0.90 IoU floor, or stalled out and was
accepted after a second reader agreed (ADR 0074, ADR 0075). `make_round` also
keeps every round pending until its visual feedback is recorded with
`--record-visual`; `--require-component-passes` refuses a Component whose
latest round is still pending.

## Decision

Rank levers by cost, not token count. The large lever is how long the root's
context is and how many requests carry it; waiting is a small one.

1. **One worker per Component.** Once the Component list is settled, the
   root Manager spawns one `component-worker` agent per Component, in
   parallel. The worker receives only the component id and its
   `part_<id>.step.py`, its sealed `geometry:<id>` reference and declared
   camera, that Component's Design Contract rows and the nozzle. It edits
   only that source and runs `make_round --component`, repairing from the
   summary: gate failures, the IoU against the floor, the worst bands and the
   stall streak. It reports in 10 lines or fewer when a round's checks pass,
   when the image stalls out (`stalled 3/3`), or when it is blocked: status,
   rounds used, the latest round with its IoU, packet hash and identity, the
   reviewer's text it acted on, and open issues. No logs and no images reach
   the root.
2. **The root owns the reviewer.** Each Component has one
   `component-reviewer` thread, reused by follow-up so its cached prefix
   survives; each request judges the new packet afresh. The root asks it
   only twice in a Component's life cycle:
   - **Visual check**, when a worker reports a round whose checks pass. The
     reviewer views that round's packet and answers in `--record-visual`
     shape; the root adds the packet hash and records it. A fail goes back to
     the same worker as its repair list. The IoU floor still decides form
     before this point, so the reviewer is not asked about a round that has
     not reached it.
   - **Acceptance**, when the image stalls out below the floor. The reviewer
     is ADR 0075's second reader: it views the latest round's
     `compare-NN.png` images and answers whether the remaining differences
     are acceptable. The root writes the acceptance review and has the worker
     rerun the round unchanged with `--accept-likeness` and
     `--acceptance-review`. That round's checks then pass, so it goes to the
     visual check like any other. A disagreement goes back to the same worker
     for more repair rounds; the root asks again only after the worker has
     applied every difference in rounds that changed the geometry and the
     image is still stalled out.
3. **Only the reviewer sees component images.** Neither the root nor a
   worker views them; workers act on the round summary and the reviewer's
   text.
4. **Shared helpers stay with the root.** A worker never edits a shared
   helper such as `features/forms.py`; it asks the root. The root edits it and
   sends the affected Components back through a worker. Their passes are
   already invalidated by the B-rep identity check (ADR 0073).
5. **Reasoning effort per role.** The worker inherits the root's effort
   (medium by default). The reviewer runs at `low`.
6. **Longer waits.** `make_round` polls and `wait_agent` use 300000 ms instead
   of 30000 ms, in `references/make.md`, the product-run `AGENTS.md` and
   `make-round`.
7. **Parallel component packets.** `make_round` refuses visual feedback
   whose packet's sources no longer match the project. It hashed every
   source and STEP in the project, so a sibling worker's edit staled a
   pending review and a Component could never pass while others were being
   repaired. A component round's packet now binds its own source and STEP
   and every shared file (helpers, the combined entry, design constraints),
   but not another Component's own `part_<id>.step.py` or STEP. A shared
   helper edit still stales every pending component packet. The assembly
   packet still binds everything.
8. **Unchanged.** `make_round`'s pass rule is unchanged. Assembly
   rounds, their visual feedback, the blind review and final verification
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

## Alternatives considered

- **Pass a component round on its checks alone, without visual feedback.**
  Would let the reviewer be asked only at stall-out, but changes
  `make_round`'s pass rule and ADR 0060's visual evidence for every
  Component.
- **Workers record their own visual feedback.** A worker does not view
  images; recording a pass it did not see would be false evidence.
- **Review every round.** The IoU floor already decides form below 0.90, so a
  review there adds cost without changing the outcome.
- **Workers spawn their own reviewer.** The root would lose the one
  independent judgement it records, and a fresh reviewer per round loses its
  cached prefix.
- **A fresh reviewer each request.** Pays the reviewer's whole prefix
  uncached every time.
- **Trim the skill files.** Out of scope for this decision; the re-read cost
  moves to short-lived workers instead.
- **Choose effort per spawn call.** The spawn tool offers no reliable
  per-call effort; a custom agent file fixes it declaratively.

## Consequences

- The root's context no longer grows with every component round, its logs or
  its images. Each worker's context is short-lived and discarded.
- More threads run at once. A run with many Components may hit the runtime's
  thread limit; the root then spawns the next worker when one finishes.
- Each Component that passes costs at least one reviewer request, because
  `make_round` keeps a round pending until its visual feedback is recorded
  and a worker cannot record what it has not seen. Dropping that requirement
  for component rounds was considered and rejected: it would change a gate
  to save one low-effort request per Component.
- Worker reports are the root's only view of component work, so a worker that
  misreports can mislead it. The recorded visual feedback, the acceptance
  review and the B-rep identity check still bind what passes.
- Whether this lowers cost without lowering quality is not yet shown. It
  needs a live run, which should also re-measure the compaction threshold.

## Compatibility and migration

Frozen runs keep what they materialized. A run created before this change has
no role agents and its own `references/make.md`, so it keeps building
Components in the root. A host tool refresh of such a run may bring the new
`make-round/SKILL.md`; its component rule defers to the run's own
`references/make.md`, so the old run still inspects in the root. A pending
component packet written before the refresh bound every source, so the new
tool refuses its feedback as stale; rerunning that component round writes a
packet in the new form.

## Verification

- `tests/make/test_role_agents.py`: both role files parse, the reviewer runs at
  `low`, the worker inherits the root's effort, and each role's instructions
  keep their confinement.
- `tests/workflow/test_agent_run.py`, `tests/workflow/test_native_host.py` and
  `tests/runtime/test_codex_native_session.py`: new runs seal and register both
  roles, and a missing or altered role file is refused.
- `tests/runtime/test_agent_assets.py`: `references/make.md`, the product-run
  `AGENTS.md` and `make-round` carry the worker, reviewer and 300000 ms rules.
- `tests/make/test_make_round.py`: a component round whose checks pass stays
  pending, and does not satisfy `--require-component-passes`, until its visual
  feedback is recorded; another Component's own source or STEP does not stale
  its packet, while its own source, a shared helper or the combined entry
  does.
- No live run has exercised the roles yet.
