# Wish and Match contracts

## Wish is a host boundary

**Input:** The person's exact words and explicitly supplied constraints or
context.

The host creates, validates, and seals the canonical Wish before the first
native turn. Do not create a native Goal for Wish, rewrite `WISH.json`, or
propose the Wish gate. Preserve intent. Ask for information only when the
missing choice would materially change the product; otherwise record
reversible assumptions without adding authority or weakening a constraint.
Never place Wish text in a filesystem identifier.

## Match uses the native Inventor roster

Read the Match `STAGE.json`. It binds the sealed Wish, universal blueprint
hash, and exact `inventor_roster` with its `roster_sha256` identity.
`.codex/agents/*.toml` is the sole identity, Taste, and skill roster: each
eligible file is hash-bound by the host and names its materialized skills under
`.agents/skills/`. Do not consult a second identity tree, search for executable
workers, or infer an Inventor that the host did not materialize.

Inventors are not preclassified product categories. Every Wish is open-ended.
Compare all eligible Inventors on the evidence in their exact custom-agent
instructions, especially their Taste, method, and distinctive product
judgment.

## Match Goal and improvement loop

Create one native Codex Goal for this Match attempt. Its objective is to rank
the entire eligible roster and select the best Inventor for the exact Wish.
Its stopping condition is a successful `match` finalizer for the current
checkpoint.

While pursuing the Goal:

1. **Observe:** Read the exact Wish and every eligible custom-agent file.
   Identify the Wish's creative tensions and the concrete Taste evidence that
   differentiates candidates.
2. **Act:** Compare the full roster. Use native subagents for bounded candidate
   fit assessments when useful, briefing each from the exact materialized
   bytes. Treat their reports as evidence, not votes or gate decisions.
3. **Evaluate:** Check that every eligible Inventor appears exactly once, the
   selected Inventor is ranked first, and every rationale distinguishes fit
   using Wish and Taste evidence. Use an independent native reviewer when the
   choice is close.
4. **Improve:** Reinspect weak comparisons, missing counterevidence, or
   overconfident claims and revise the ranking. Continue until the complete
   ranking satisfies the proof condition.

Codex owns this comparison and synthesis. No Python scorer, router, prompt
chain, judge, or retry loop selects the Inventor.

## Artifact and gate

Write one authored JSON source with exactly `selected_inventor_id` and
`ranking`. Every ranking item must be evidence-based and refer to one eligible
`.codex/agents/*.toml` Inventor. Then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . match --source <match-source.json>
```

The deterministic finalizer binds `inventor_roster_sha256`, the selected
custom-agent path, and its exact hashes; writes
`artifacts/match/assignment.json`; and writes `agent-outcome.json`. It does not
reason or choose the Inventor. Complete the Match Goal only after that command
succeeds, then return to the host. The host verifies identities, hashes, full
ranking coverage, and one-shot assignment semantics before it can checkpoint
Invent.
