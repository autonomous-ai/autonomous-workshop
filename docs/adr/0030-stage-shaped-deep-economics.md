# ADR 0030: Shape deep effort by stage and persist proof first

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0028's all-high `deep-economics-v1` profile
- Relates to: ADR 0029 (host-owned fresh CAD rebuild)

## Context

Starbell Seed was the first fresh Quest run after the host-owned CAD-cache and
early-form guidance fixes. Invent produced a distinctive three-part helical
seed that opens into a six-petal star flower in 18m21s. Its sealed contract
explicitly required a minimal motion coupon and held/signature blockout before
detailed CAD.

Make did not operationalize that ordering. It spent about 23.5 minutes before
persisting any product source, then batch-wrote the complete part tree. The
first 30-minute turn ended while generating parts. The bounded recovery reused
those bytes and repaired real flower/halo geometry failures, but the numeric
motion proof arrived only near the end of the second 30-minute turn. Make never
reached all-printable preflight, product renders, Playtest, Release, or
publication. Workshop stopped safely after the two-turn recovery window and
preserved the run.

Workshop received no terminal token events, so public telemetry remains
truthfully unmeasured. Local native-session diagnostics provide separate,
non-authoritative turn observations:

| Stage / turn | Input tokens | Cached input | Output tokens | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent turn 1 | 1,261,691 | 1,115,136 | 26,642 | 3,752 | 18m21s |
| Make turn 1 | 1,895,334 | 1,621,248 | 23,493 | 5,905 | 30m00s |
| Make recovery | 2,067,470 | 1,903,616 | 17,856 | 4,723 | 30m00s |

The exact CAD kernel was not the dominant delay: observed combined generation
took tens of seconds. Most elapsed time preceded persisted proof or was spent
on reasoning, source planning, repairs, and avoidable command rediscovery. The
v1 guidance described early falsification but did not place it in the direct
host stage prompt or shape reasoning after concept selection.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v2.md`:

- Invent retains high reasoning effort.
- Make, Playtest, and Release use medium reasoning effort.
- Automatic context compaction is 24,000 tokens for every stage.
- The 30-minute native-turn boundary remains unchanged.
- One `wish` or `resume` invocation launches at most eight native turns. This
  preserves one complete Quest concept-revision path in a single command.

For an initial deep-v2 Make turn, the host appends a fixed critical-path
instruction to the normal stage prompt. The first persisted Make deliverable
must be the smallest exact causal or kinematic proof plus neutral held and
signature blockout renders under `<cad-project>/review/early-proof/`. Codex
must create, run, inspect, and record that proof before authoring the complete
part tree or detailed final geometry. A passing proof's parameters and source
are reused in the final product, and the proof directory remains in the public
toy snapshot.

The stage reference includes exact copyable command shapes for generation,
STL export, and non-destructive print-preflight so the session does not spend
tool cycles rediscovering interfaces. Recovery continues to reuse durable bytes
and prioritize the remaining checks and finalizer.

Frozen deep-v1 and older runs retain their exact marker, all-high reasoning,
32k compaction ceiling, and eight-turn invocation cap.

## Consequences

- High reasoning remains concentrated where it creates novelty: Invent.
- Make receives its ordering constraint in the direct stage prompt, not only a
  long reference file.
- A bad mechanism or weak held form should fail before a full product tree is
  written; a good proof becomes reusable source and durable public evidence.
- Context is smaller, while the existing eight-turn cap preserves a complete
  evidence-bound Quest revision without weakening CAD, Playtest, manual, or
  publication gates.
- The change adds no Python planner, model judge, aesthetic score, or new
  lifecycle stage.
- A fresh production Quest and Forge run must prove the combined quality and
  economics improvement; this policy is not itself success evidence.

## Verification

- Launcher tests bind reasoning effort to the current stage for deep-v2 runs.
- Compatibility tests retain deep-v1 runtime settings and turn limits.
- Prompt tests require the first persisted Make proof only for marked Forge and
  Quest Make checkpoints.
- Full runtime and workflow tests pass before the profile is used in production.
