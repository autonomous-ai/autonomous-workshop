# ADR 0046: Explicit twenty-minute turns for budgeted Spark

- Status: Accepted
- Date: 2026-09-06
- Scope: Codex Spark v3 runs with the budgets-v1 capability

## Context

The Crescent run remained in Make for more than a day across explicit
resumes. An initial diagnosis incorrectly assumed Spark's launcher constant
was 1,200 seconds. Commit 63604455 had intentionally changed that constant to
3,600 seconds on September 3. A test comparing the launcher to the same
constant passed without demonstrating a twenty-minute limit.

The operator requested continuing the promised limit fix. This decision
explicitly shortens budgeted Spark's turn ceiling; it does not describe the
previous sixty-minute behavior as a malfunctioning process timer.

## Decision

For Codex Spark v3 with budgets-v1, use the minimum of 1,200 seconds, the
constructed launcher's boundary, and the remaining command/step budget.
Preserve the existing budgets capability digest as the runtime profile identity
so the same native session can resume with a shorter turn, as it already does
when command clocks run down. Preserve the selected model, reasoning effort,
compaction settings, and subprocess dependency injection.

Unbudgeted sessions retain their exact historical binding. Older Spark
profiles and other workflows do not acquire the new twenty-minute cap.
Every gate and the exact session, Goal, and workspace remain unchanged.

## Limits and verification

The full launcher construction and budget wrapper are tested together against
the literal value 1,200, including the explicit Astra/high selection. Other
fixtures cover shorter remaining budgets, repeated wrapping, shorter launcher
boundaries, historical profiles, and fake subprocess preservation. No live
model calls are needed for these tests.

This is a per-turn boundary, not a completion or lifetime-cost guarantee.
Explicit resumes grant fresh command clocks. Repeated CAD rebuilds and costly
checks require separate diagnosis; stopping a long deterministic check sooner
can itself cause replay and must not be represented as a throughput improvement.
