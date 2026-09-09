# ADR 0050: Give Spark Make enough working memory to stop repeating itself

- Status: Accepted
- Date: 2026-09-09
- Owners: Runtime and Workflow maintainers
- Relates to: ADR 0019 (Spark economics), ADR 0021 (Spark compaction), ADR 0023 (Spark v3), ADR 0046 (budgeted Spark turns), ADR 0049 (product-wide token budget)
- Supersedes for new runs: Spark v3's 64,000-token compaction ceiling

## Context

Spark's compaction ceiling has been 64,000 tokens since ADR 0021 chose it to
cut spend. Measured against real runs it now does the opposite on any product
that does not fit in one window.

Four Spark runs on 2026-09-08 separate cleanly into two groups. The two that
finished did their whole Make in **one** native turn and cost 6.7M and 8.6M
tokens. The two that did not finish cost 15.8M and 18.0M tokens across 27 and 2
stage attempts.

The discriminator is not the input-to-output ratio. Every run here is
input-dominated, because each tool call re-sends the whole session: the two
stuck runs sit at 112:1 and 133:1, and the *finished* 6.7M run is higher still
at 144:1. Ratio measures tool-call granularity, not waste. What separates the
groups is total spend, attempt count, and how much of the work was done twice.

Compaction count is where they part. Per-request input climbs from roughly
37,000 to roughly 71,000 tokens and resets: six times in the finished run,
sixteen times in one hundred minutes in the stuck one. About 35,000 tokens of
every window are fixed overhead — base instructions, `AGENTS.md`, the stage
packet, and the previous compaction summary — so a complex Make gets roughly
35,000 tokens of actual working room per cycle. Six resets a Goal can absorb;
sixteen it cannot.

What the run does with the cycles it has left is the cost. The first stuck run
called `stage_proposal.py need --stage make` nineteen times with identical
arguments and re-read `STAGE.json` through inline Python eleven more. Both runs
repeatedly `sed`-ed disjoint ranges out of the 2,288-line `verify_project`
source — lines 280-370, 1060-1195, 1125-1215, 2150-2295 — to rediscover a tool
contract they had already read. This is not exploration. It is a Goal
reconstructing state that compaction dropped, then reaching the same conclusion
and attempting the same repair.

Compaction was chosen as an economy. On a complex product it is the mechanism
that makes the run expensive.

## Decision

New Codex Spark runs freeze `references/spark-economics-v4.md`. It is v3 with
one value changed: the automatic context-compaction ceiling rises from 64,000
to 256,000 tokens, the ceiling Forge and Quest have used since ADR 0038.

Everything else in the frozen profile is unchanged and deliberately so. Spark
keeps low reasoning effort, the 20-minute budgeted native turn boundary from
ADR 0046, the same work order, the same review schema, and every deterministic
CAD, manual, and publication gate. Runs frozen at v1, v2, or v3 keep their
historical ceiling on resume; the host selects the newest marker present rather
than branching on an older file's existence, because a v4 run materializes the
preserved v1-v3 references too.

The wider ceiling is working memory, not a licence to read more. The v4 marker
says so explicitly: exact workspace bytes, `STAGE.json`, sealed contracts and
concise review evidence remain the durable memory, independent reads stay
batched, and the full verifier is still not an iteration loop.

## Alternatives considered

### Keep 64k and instruct the agent to re-read less

Rejected. v3 already carries that instruction, in the paragraph beginning
"Treat exact workspace bytes ... as durable memory". Both stuck runs had it in
context and still re-read, because an instruction cannot be followed by a turn
that no longer remembers it. The failure is capacity, not compliance.

### Raise the ceiling and also raise reasoning effort to medium

Rejected for this change. Two variables move two results and neither can be
attributed. Reasoning effort is already selectable per run through
`manager_reasoning_effort`, so it can be measured separately against the same
ceiling.

### Cap Make's share of the product token budget instead

Rejected as a substitute, retained as separate work. A stage cap stops a
runaway sooner; it does not make the run finish. Both stuck runs would still
have failed, only earlier and more cheaply.

## Consequences

- A complex Spark Make can hold its stage packet, sealed concept, tool
  contracts and passed-check record across one turn instead of rebuilding them
  every ten requests.
- Peak per-request input rises.
- **Total product spend rose, and the saving this ADR predicted did not
  appear.** Measured 2026-09-09 on the same "millenium puzzle from yugioh"
  Wish as the 8,579,481-token v3 baseline that finished Make and reached
  Release: a v4 run spent 20,027,671 tokens and stopped at the budget cap
  without sealing Make, and a v4 "death note" run spent 14,771,051 and finished
  its geometry, review and final CAD checks but was blocked at packaging. The
  compaction goal was met exactly — zero compactions against the baseline's
  seven — so the prediction failed on cost, not on mechanism.
- Part of the reason is visible in the same rollouts and is not compaction, but
  it is not what it first looked like. Collection calls — `write_stdin` with
  empty input, used to gather a command the agent had yielded away from after a
  second — rose with the window: 21% of tool calls in the v3 baseline, 34% in
  the v4 death note run, 42% (57 of 136) in the v4 puzzle run. They are **not**
  empty: every one of the 57 and 34 returned real output, a median of 905 and
  2,781 characters. What makes them expensive is arithmetic, not emptiness.
  Running a command to completion costs one call; yielding early and collecting
  later costs two, and only gathering several commands per collection pays for
  the difference. Measured, collections gathered 1.33 and 1.26 sources on
  average, and 67% and 76% gathered exactly one. So roughly 38 and 26 calls —
  on the order of 4.5M tokens in the puzzle run at its context size — went on a
  second call for commands a single blocking call would have finished. A wider
  ceiling makes each of those cost more. The two changes are therefore coupled,
  and this ADR's economics cannot be judged until that pattern changes.
- The comparison is not clean in the other direction either. The v4 runs also
  fetched and visually inspected reference images and used the image-derived
  path (ADR 0051), work the v3 baseline never did — and the v3 baseline did not
  produce a product that resembles its target. Part of the increase buys a
  likeness the baseline lacked.
- Instruction was tried against that pattern and **did not change it**, at
  three increasing strengths: a note in the CAD tool reference, the same note
  carrying the measured durations, and finally a rule in the host stage prompt
  that the host injects on every turn, stating the two-calls-versus-one
  arithmetic and the measured fact that commands batched into one call already
  run concurrently (two eight-second commands returned together after 10.2
  seconds, not 16). Under all three, `gen` and `verify_project` were still
  launched with a one-second yield. All three were reverted; the pattern is
  documented here rather than instructed against. What remains untried is
  enforcement — a `PreToolUse` hook can refuse a short yield, though it cannot
  rewrite one, because Codex exposes `updatedInput` only on the
  `PermissionRequest` event that `--ask-for-approval never` prevents.
- So this ADR stands as: the compaction mechanism works, the cost went up, and
  the largest single component of a run's spend is a pattern instruction cannot
  reach.
- Simple products are unaffected: they already completed Make inside one 64k
  window and will not approach the new ceiling.
- Frozen v1, v2 and v3 runs resume with their original ceiling, and the private
  Codex runtime-policy hash still fails closed if a resumed session's ceiling
  changes.

## Verification

- Workflow tests prove a v4 Spark checkpoint selects the 256,000-token ceiling
  while v3, v2, v1, Forge, Quest and unmarked runs retain their prior ceiling,
  and that a v4 checkpoint carrying the preserved v1-v3 references still
  selects v4.
- A test proves v4 keeps the 20-minute budgeted turn boundary and that
  budget wrapping does not alter the compaction ceiling.
- The economics claim was tested on 2026-09-09 and **failed**; the measured
  totals are recorded under Consequences. Compaction counts confirm the
  mechanism works. Three attempts to instruct the collection pattern away were
  measured and none changed it; any future claim of saving must come from a run
  measured after something that actually changes it, against the same Wish.
