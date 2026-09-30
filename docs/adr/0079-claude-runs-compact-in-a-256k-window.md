# ADR 0079: Claude Code runs compact in a 256k window

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-09-30
- Owners: Claude Code adapter (`runtime/claude.py`), Workshop host
  (`workflow/native_run.py`, `workflow/effort.py`), product-run references
  (`context-compaction-v1.md`)
- Builds on: ADR 0021 (compacted Spark context), ADR 0051 (192k deep
  ceiling), ADR 0078 (Claude product token allowance)

## Context

Run `wish-20260930-021102-9a5a6b7f` ran Claude Code Opus 5.5 with a 1M
context window and no compaction setting. Its root context reached 721k tokens
without compacting once, and averaged 470k over 170 requests. Every request
re-reads the whole context from cache, so cached input was about 70% of the
run's cost. About 485k of the final context was retained thinking from
earlier requests.

Codex runs have compacted at a frozen ceiling since ADR 0021, 192k for new
Spark and deep runs. Claude Code offers the same control as `--autocompact`,
a window from 100k to 1M tokens, but the adapter never passed it.

The operator first asked for 256k on both Managers. ADR 0051 had lowered
Codex from 256k to 192k because 256k sits above 90% of Astra's 258,400-token
window: compaction never fired, and turns failed above about 210k. The
operator then chose 256k for Claude only.

## Decision

New runs materialize the marker `references/context-compaction-v1.md`. A
Claude Code run that carries it passes `--autocompact 256000` on every turn.
The window is recorded in the session checkpoint, like the model, and resume
refuses a different or missing window.

Codex ceilings do not change, marker or not.

Runs frozen without the marker keep their policy on resume: an older Claude
run keeps Claude Code's default window.

## Consequences

- A Claude root context stays below roughly 256k, so the cost of each request
  is bounded by the window, not by how long the run has been going.
- Claude Code compacts a little short of the window to leave room for the
  summary.
- A compaction drops detail, so durable state has to live in the run's notes
  and artifacts. The marker says so to the Manager.
- Retained thinking still fills the window. Whether the window should be
  smaller is left to measurement on a live run.
