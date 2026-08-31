# ADR 0033: Phase deep Make at a proof checkpoint

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, product-run protocol, and CAD-skill maintainers
- Supersedes for new runs: ADR 0032's `deep-economics-v4` profile

## Context

Deep-v4 restored high reasoning to Make, reduced its compaction ceiling to 16k,
and required a blind review of the first form/mechanism proof. An identical
production Quest Wish then exposed a more basic economic failure: neither Make
turn wrote a file.

Invent's initial high-reasoning turn reached its 30-minute boundary after
writing a complete source; a 2m23s recovery finalized it. Make then used its
12-minute initial boundary and full 30-minute recovery while making 40 tool
calls but leaving zero durable Make files. Inspection of tool-call categories
showed repeated instruction/reference reads, skill-tree enumeration, help
discovery, and interpreter checks before source creation. The preserved run did
not reach print preflight, Playtest, Release, GitHub, or Factory publication.

Local native-session diagnostics, which are not host telemetry and are not
added into a single token figure, reported:

| Stage / turn | Input | Cached input | Output | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent initial | 945,603 | 835,328 | 13,902 | 1,353 | 30m00s |
| Invent recovery | 231,484 | 190,976 | 2,250 | 238 | 2m23s |
| Make proof | 326,804 | 259,584 | 3,563 | 583 | 12m00s |
| Make recovery | 638,973 | 519,680 | 6,210 | 715 | 30m00s |

This was a false saving: Make used fewer tokens than some prior profiles only
because it never produced the artifact. Economics must be measured per
completed desirable product, not by minimizing an unfinished turn.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v5.md`.

- Invent starts with high reasoning and a 20-minute boundary. A recoverable
  continuation uses medium reasoning for 10 minutes and must finalize the
  strongest viable source already developed instead of restarting research,
  selection, exploration, or subagents.
- Make begins with a medium-reasoning eight-minute proof phase at 24k context.
  Before optional references, tool help, delegation, or broad discovery it
  writes the smallest exact mechanism/form source, generates and exports it,
  renders neutral held/signature images, and obtains one blind review.
- The host supplies exact `gen`, `export`, and `render_product` command shapes.
  The stage-scoped Make reference replaces the combined 455-line
  Make/Playtest reference; Playtest receives its own concise reference.
- After the proof bytes and review are durable, the Manager writes canonical
  checkpoint-bound `.make-proof-ready.json`. The launcher may use only that
  exact regular file as a voluntary native-turn completion marker.
- The marker is not an artifact, stage proposal, gate, aesthetic verdict, or
  transition. It can only return control to the host. The host resumes the
  same session, stage, checkpoint, and Make Goal at high reasoning with a
  normal 30-minute turn. Only the exact Make finalizer and
  `agent-outcome.json` can propose advancement.
- Final Make reuses the proof source, persists one complete baseline, performs
  print preflight, final renders and blind review, one focused repair at most,
  one integrated verifier, and finalization. It does not restart exploration.
- Playtest and Release use medium reasoning. Every deep-v5 stage compacts at
  24k, and one CLI invocation remains capped at eight native turns.

The marker's contents are untrusted native output. The host validates exact
canonical bytes, exact current checkpoint binding, a stable regular file, the
1 KiB size bound, and the exact trusted path. A malformed regular marker is
removed and proof mode continues; a symlink or special file fails closed.
Validity is intentionally not proof validity: all existing final CAD, visual,
Playtest, manual, Factory publication, and GitHub snapshot requirements remain.

## Alternatives considered

- **Keep v4 and make prompts louder.** Rejected because two bounded turns and
  40 tool calls produced no bytes; prose without an observable phase boundary
  did not control sequencing.
- **End the Make Goal after proof and create a second Goal.** Rejected because
  proof and final product are one stage objective; splitting Goals would make
  an intermediate host lifecycle that the architecture does not have.
- **Make proof a deterministic stage gate.** Rejected because the early blind
  read is model judgment. Exact bytes can safely control liveness without being
  promoted into authoritative aesthetic evidence.
- **Use low reasoning for all deep work.** Rejected because paired v3 evidence
  showed weaker visual judgment with more gross Make input.

## Consequences

- Useful Make bytes now have a shorter, observable deadline, while the
  expensive high-reasoning phase starts only after a concrete direction exists.
- Invent recovery can no longer consume another full high-reasoning window to
  redo work that is already durable.
- One additional trusted launcher marker is accepted, but it has no authority
  beyond ending the current process turn.
- 24k replaces v4's 16k Make ceiling so the final high-reasoning phase has
  enough exact product context; savings must come from progressive disclosure
  and phase ordering, not context starvation.
- Frozen v4 and older runs retain their exact profiles and remain resumable.
- A fresh production Quest and Forge must still demonstrate terminal desirable
  products, authenticated publication, GitHub snapshots, elapsed time, and
  separate input/output telemetry before deep-route economics are proven.

## Compatibility and migration

The capability-file hash remains the whole runtime-profile identity for a
persistent native thread. Deep-v4 keeps high Invent/Make, medium later, 16k
Make/24k other compaction, and 12/30-minute Make boundaries. Deep-v3, v2, v1,
Spark, and unmarked historical behavior remain unchanged. Existing run roots
contain their materialized protocol, so repository upgrades do not rewrite
their instructions.

## Verification

- Runtime tests prove exact-path marker acceptance and liveness while refusing
  outside paths, stale files, and symlinks.
- Workflow tests prove checkpoint-bound canonical marker validation, v5
  medium-proof to high-final Make switching, bounded decisive Invent recovery,
  and frozen v4 compatibility.
- Asset tests prove current Make and Playtest references are separate,
  stage-scoped, and packaged with the v5 capability.
- Full deterministic repository tests pass before the first v5 production run.
- Production validation must preserve failures and publish successes; token
  reduction without a completed high-quality product is not a passing result.
