# ADR 0036: Reserve the proof runway for product bytes

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0035's `deep-economics-v7` profile

## Context

The identical Three-Sky Seed production Quest tested deep-v7 through the
regular CLI in an untouched persistent Codex session. Invent passed after its
20-minute initial turn and 5m45s medium recovery. Both eight-minute Make proof
turns then expired with no product source, CAD, render, or marker. The run
stopped safely without Playtest, publication, or GitHub product claim.

The root tool timeline makes the failure deterministic:

| Time | Make action |
|---|---|
| 08:51:04 | read root `AGENTS.md` |
| 08:52:57 | read the Workshop skill |
| 08:54:34 | read the Make reference |
| 08:55:52 | read Manager and Stage packets |
| 08:58:14 | inspect the completed Invent Goal; first boundary ends |
| 08:59:14 | create the Make Goal |
| 09:01:55 | inspect an empty product tree and Wish |
| 09:04:20 | spawn the early critic |
| 09:06:28 | create an empty proof directory; second boundary ends |

V7's instruction to use separate bounded reads directly caused the first
failure. Recovery then treated Goal inspection, empty-tree inspection, critic
coordination, and directory creation as separate reasoning cycles. Each native
cycle took roughly one to two and a half minutes even though the shell work was
instant. No CAD command ran, so cache isolation and CAD entrypoints were not
the failure.

Local native-session diagnostics reported:

| Root stage / turn | Input | Cached input | Uncached input | Output | Reasoning output |
|---|---:|---:|---:|---:|---:|
| Invent initial | 344,365 | 290,048 | 54,317 | 3,075 | 392 |
| Invent recovery | 166,486 | 125,184 | 41,302 | 4,368 | 149 |
| Make proof | 119,610 | 93,952 | 25,658 | 781 | 154 |
| Make proof recovery | 107,084 | 77,824 | 29,260 | 888 | 94 |
| **Root total** | **737,545** | **587,008** | **150,537** | **9,112** | **789** |

This was about 18% less root input and 36% less output than v6, but it produced
fewer durable Make bytes. Lower failed-run spend without a product is a false
economy.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v8.md`.

- Invent, final Make, Playtest, Release, 24k compaction, and the eight-turn CLI
  cap retain their v7 settings.
- Early Make receives one 16-minute medium proof runway instead of two planned
  eight-minute fragments. The existing bounded recoverable-turn mechanism
  remains, but recovery is not the planned place to begin source.
- The Manager creates or continues the Make Goal immediately without a
  preparatory `get_goal` call.
- Mandatory root, Workshop, Make, Stage, and sealed-concept reads are batched
  into one bounded tool action. Separate stable reads are forbidden.
- The next file action authors the proof source and parent directories
  together. Empty-tree inspection and empty-directory creation are not
  progress.
- The broad CAD skill stays deferred. Generate, export, and render remain one
  exact `$WORKSHOP_PYTHON` foreground batch with a private run cache.
- The root directly inspects the early images and may repair once. Early proof
  is a direction falsifier, not a gate, so it does not spawn a child critic.
  The independent hash-bound blind critic remains mandatory during final Make.
- The checkpoint-bound marker still has no lifecycle or gate authority.
- No CAD, Playtest, manual, publication, or GitHub requirement changes.

## Consequences

- The proof budget is longer per turn but is aimed at fewer native reasoning
  cycles and fewer total tokens than two setup-only turns.
- A failed v8 run has a larger single-turn time ceiling; durable source and CAD
  timestamps reveal whether the runway earns that cost.
- Removing duplicate early child critique saves coordination while retaining
  independent judgment at the authoritative final review.
- V8 adds no Python planner, prompt loop, model judge, retry engine, or effect
  path. Codex still authors and evaluates the product.
- Cross-effort economics remain unproven until fresh Spark, Forge, and Quest
  products complete, publish, preserve their GitHub snapshots, and pass the
  qualitative comparison.

## Compatibility and verification

Deep-v7 and every older profile remain recognized with their exact prompts,
timeouts, and hashes. New profile tests require v8's 16-minute boundary,
batched read, immediate source action, absence of early critic, final critic,
and v7 frozen compatibility. The real CAD batch and private-cache acceptance
test remains mandatory. Full deterministic tests pass before the next
production run.
