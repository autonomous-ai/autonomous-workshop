# ADR 0053: Pin the Inventor a `workshop start` run builds and publishes with

- Status: Accepted
- Date: 2026-09-07
- Owners: CLI, workflow, and Release maintainers

## Context

`workshop start <inventor>` has always read as "this Inventor builds". It
validated the named Inventor, opened that Inventor's browser login, and
sealed the daydream under that Inventor's name. But the run itself never
knew. `wish_from_daydream` wrote `inventor_id` into the Wish context, nothing
read it, and the run materialized the whole Inventor roster, so Match ranked
every Inventor and could bind any of them. The brief only asked, in prose,
that Match bind the dreamer.

`workshop wish` had the same gap from the other side. A typed brief prefixed
"Ferro Line:" is still a free choice for Match; the microduck-windup run
(2026-09-06) bound `bob`, and because Bob had no credential file Release
would have published under the host-wide fallback account rather than the
Ferro Line account the operator had logged in. There was no flag on either
command to say which Inventor must build and publish a typed brief.

## Decision

The Wish context key `inventor_id` means "this Inventor, and no other".
`start_native_run` reads it from the Wish context and passes it to
`AgentRun.create` as `required_inventor_id`, which materializes only that
Inventor's custom agent and skills (the same host pin `workshop wish
--inventor` uses). The roster the run seals therefore has one entry, the
Match assignment contract already requires the ranking to cover the roster
exactly, and Release already publishes with the selected Inventor's
credential, so the pin reaches publication without a new gate. The key is
part of the hashed Wish, so it is immutable for the run and shown in every
checkpoint. A Wish without the key keeps the full roster.

`workshop start <inventor>` gains `--wish BRIEF`, `--ref IMAGE` (up to eight,
`--wish` only), and `--max-rounds N`. `--wish` skips the daydream, seals the
typed brief as the Wish with the named Inventor in its context, and runs
once. `--wish` and `--idea` are exclusive. Daydream builds under `start`
carry the same context and are pinned the same way; `workshop wish` without
`--inventor` remains the open-roster path.

## Consequences

- `workshop start ferro-line --wish "..."` builds the brief as Ferro Line and
  publishes with Ferro Line's credential file, or waits with a concrete need
  when that file is missing; it can no longer drift to another Inventor and
  another account.
- A required Inventor absent from the source root fails run creation with
  `Inventor source root has no Inventor <id>` before any workspace exists.
- Daydream builds now seal a one-Inventor roster. Match still runs, but its
  ranking is the dreamer alone; the prose request in the brief is now
  redundant and kept for readers.
- Runs created before this change keep their sealed rosters; the pin applies
  only to new runs.
