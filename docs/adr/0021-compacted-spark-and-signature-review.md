# ADR 0021: Compact Spark context and bind final signature review

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, Workflow, Make, Release, and product-run instruction maintainers
- Relates to: ADR 0019 (Spark economics), ADR 0020 (signature evidence)
- Supersedes for new runs: ADR 0019's v1 profile and ADR 0020's image-only signature proof
- Superseded in part by: ADR 0022

## Context

Pocket Eclipse Menagerie was the first production Spark run after signature
images became mandatory. It selected the perceptually appropriate Inventor and
passed every deterministic CAD, manual, Factory, and archive gate, but still
spent 7,957,133 gross input tokens over 22 minutes 59 seconds. Make used
3,451,567 input tokens and Release used 4,505,566.

Private aggregate telemetry showed that Release began with roughly 105,000
tokens of effective context and ended around 161,000. More than 98% of Release
input was cached context reported again across native tool cycles. The same
session continuity is valuable, but carrying its entire tool-heavy history into
every later cycle is not. Release also produced four complete manual render
rounds for a one-piece toy.

The required signature sheet remained semantically weak: it showed multiple
object rotations rather than proving the promised shadow outcome. Deterministic
image checks correctly cannot judge that distinction. More generated copy and
manual polish cannot repair geometry whose signature experience is unclear.

## Decision

New Codex Spark runs freeze `references/spark-economics-v2.md`. The one
Wish-wide session keeps low reasoning effort and sets Codex's official
`model_auto_compact_token_limit` to 64,000 tokens. Compaction summarizes native
history in place; it does not create a new session, stage, Goal, or authority
boundary. Exact workspace bytes, immutable stage packets, sealed contracts, and
host checkpoints remain authoritative.

The runtime policy hash binds the compaction limit. Codex CLI 0.150.0 or newer
is required only for a v2 run. A frozen v1 Spark run remains low reasoning with
no Workshop-specified compaction setting, and an older unmarked Spark run
remains high reasoning. Forge and Quest remain high reasoning without this
Spark ceiling.

New Make finalizers also require
`<cad-project>/snap/SIGNATURE-REVIEW.json`. One bounded independent native
visual critic receives only the hardest-to-fake magic, compact concept, final
hero, and final signature sheet. The canonical evidence binds both image
hashes, confirms that the held object and signature experience are readable,
and records the largest risk plus its resolution. A failed review causes a
focused geometry/render repair and re-review inside the same Make Goal. The
host validates structure, exact hashes, and affirmative proposal fields; it
does not become an aesthetic judge.

The signature sheet is outcome evidence rather than a generic turntable. Its
panels show exact before/action/after, projection outcomes, or
setup/choice/result as appropriate. Release may not rescue unclear geometry
with copy.

For a simple one-piece Spark toy with no assembly or rule system, Release starts
with a double-sided owner card. It makes one complete review packet, receives
one bounded independent edit, resolves the strongest finding in one coherent
revision, and renders once more. Evidence-only JSON edits do not trigger more
PDF renders. Longer manuals remain available when a named setup, safety, reset,
assembly, or rules need earns the space.

## Alternatives considered

### Start a new Codex session at Release

Rejected. It would break the one-session architecture and discard useful
continuity instead of compacting it through the native runtime.

### Lower deterministic gates or skip independent review

Rejected. The quality and cost goals are conjunctive; a cheap generic product
or an unverified manual does not satisfy them.

### Add a Python beauty score

Rejected. Semantic and aesthetic judgment remains native-agent work. The host
can verify exact review bytes and hashes without pretending to measure delight.

## Consequences

- Later tool cycles carry a bounded compacted history rather than an
  ever-growing verbatim session context.
- The context threshold becomes frozen session policy and same-version drift
  fails closed.
- Make pays for one focused critic before Release, where geometry is still
  repairable, and preserves that critique in the public toy archive.
- Simple manuals spend fewer layout and render cycles while retaining exact
  color, grayscale, and independent-review evidence.
- Automatic compaction can lose incidental conversational detail, so durable
  files and compact stage evidence must carry important state.

## Compatibility and migration

The v2 marker is additive. Existing materialized sessions do not acquire it.
Runtime hashing omits the compaction field when no limit is selected, preserving
the exact v1 hash shape. Frozen finalizer scripts retain their original Make
contract when resumed.

## Verification

- Runtime tests prove start and resume pass the same 64,000-token setting,
  reject unsupported Codex versions, and reject policy drift.
- Workflow tests prove v2 Spark selects low reasoning plus compaction, v1 Spark
  remains low without compaction, and Forge/unmarked Spark retain prior policy.
- Finalizer tests reject missing, false, non-canonical, or stale hash-bound
  signature review evidence.
- Deterministic Spark, Forge, and Quest end-to-end tests pass the new finalizer.
- A permanent production Spark challenger must beat Pocket Eclipse Menagerie
  on exact signature legibility and continue toward the 2,461,602 gross-input
  target without hiding an uncached-input or output regression.
