# ADR 0078: Claude Code runs share the product token allowance

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-09-30
- Owners: Claude Code adapter (`runtime/claude.py`), product token ledger
  (`workflow/token_budget.py`), Workshop host (`workflow/native_run.py`)
- Builds on: ADR 0049 (product-wide token budget), ADR 0017 (portable
  Workshop Managers)
- Amends: ADR 0049's rule that only Codex runs carry a product token
  allowance. New Claude Code runs only.

## Context

Run `wish-20260930-021102-9a5a6b7f` (Spark, Claude Code, Opus 5.5, medium)
was stopped by its owner after about 2.5 hours, still in its first Make turn.
Its root session had made 170 model requests and read 79M tokens from cache.
That spend was not limited: `workshop wish` refused `--max-tokens` for any
Manager other than Codex, and the host kept no ledger for a Claude run, so
the default 30M cap the operator expected did not exist.

Codex usage is read back from rollout files on disk. Claude Code writes no
equivalent the host can bind to, but its `stream-json` output carries each
request's usage as it happens. The input counters are exact per request. The
output count is the value when the block streamed, so it can undercount. The
terminal `result` event's `modelUsage` is the invocation's exact total.
Subagent requests appear only with `--forward-subagent-text`.

## Decision

A new Claude Code run freezes the same product token allowance as a Codex run:
`--max-tokens` (default 30,000,000) at `workshop wish`, and `resume
--max-tokens` changes only the limit.

The adapter meters while the turn streams:

- It passes `--forward-subagent-text` whenever a budget is attached.
- It counts each request once, by message id, keeping its latest usage.
- The terminal `modelUsage` can raise each counter, never lower it.
- It reports the running total to the host after every request and once
  more when the invocation ends, however it ends.

The host records each `--print` invocation as one observed thread of the
existing ledger, with source `claude-native-stream-v1`. A ledger never
switches between the Codex and Claude sources. When the total reaches the
cap, the host kills the turn, writes `token-budget-stop.json` and keeps the
session resumable, exactly as for Codex. Unavailable or regressing usage
stops the turn the same way.

A Claude run created before this decision has no ledger file and keeps its
unbudgeted policy on resume. It cannot adopt a cap later, because its
earlier spend was never recorded.

## Consequences

- A Claude run now stops at its allowance instead of spending without limit.
- The host can stop a turn only when an event arrives. A long tool call
  streams nothing, but it also spends no tokens, so the overshoot is bounded
  by the requests in flight when the cap is crossed.
- Per-request output is an undercount until the result arrives. Input
  dominates cost in these runs, so the running total stays close.
- Grok Build still has no allowance.
