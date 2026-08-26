# Invent contract

Read `STAGE.json`. It binds the exact Wish, Match assignment, selected
`.codex/agents/<inventor-id>.toml` file and hashes, universal blueprint,
canonical output path, and current checkpoint. Verify those bytes before
acting. The blueprint is an open-ended shared contract, not a product
classification.

## Invent Goal and improvement loop

Create one native Codex Goal for this Invent attempt. Its objective is to
research, explore, judge, and specify the strongest feasible concept for the
Wish through the selected Inventor's exact Taste and method. Its stopping
condition is a successful `invent` finalizer for the current checkpoint.

Use the selected project-scoped custom agent for specialist work. The root
Workshop Manager reviews and synthesizes its output and remains responsible
for the one stage proposal.

While pursuing the Goal:

1. **Observe:** Read the Wish, assignment, selected custom-agent instructions,
   relevant skill resources, and any exact upstream evidence. Identify what
   needs factual research and what needs creative exploration.
2. **Act:** Use Codex-native search, browsing, file tools, and specialist
   subagents to research supported facts and explore materially different
   concepts. Save source provenance beside the claims it supports. Use the
   Inventor's declared skills and deterministic craft tools when relevant.
3. **Evaluate:** Compare concepts against the Wish, full Taste, novelty,
   coherent play, mechanical feasibility, printability, and inspectability.
   Ask independent native subagents to judge bounded questions when subjective
   tradeoffs matter; synthesize their evidence rather than averaging votes.
4. **Improve:** Address the largest weakness, challenge unsupported
   assumptions, and refine or replace the concept. Repeat research or review
   only when it can resolve a concrete gap.

Codex owns the research strategy, concept generation, judging, and iteration.
Do not implement deep research, candidate fan-out, model judging, scoring,
reward, or repair loops in Python. Deterministic scripts may inspect facts or
artifacts but do not decide what to invent.

Do not claim geometry, safety, movement, fit, printability, or player response
that has not been checked. Make assumptions and unresolved risks explicit so
Make and Playtest can verify them.

## Artifact and gate

Write one authored JSON source with exactly `concept` and `research`, then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json>
```

The deterministic finalizer binds the chosen concept to the exact assignment
and writes `artifacts/invent/invented.json` plus `agent-outcome.json`. It does
not research, judge, assign a quality score, or run the improvement loop.
Complete the Invent Goal only after the command succeeds, then return to the
host. The host validates the exact contract and hashes before checkpointing
Make.
