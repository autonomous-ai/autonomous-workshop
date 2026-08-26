# Wish and Match contracts

## Wish

**Input:** The person's words and explicitly supplied constraints/context.

**Codex work:** Preserve intent. Ask for information only when the missing
choice would materially change the product; otherwise make reversible design
assumptions visible in the workspace. Never place Wish text in a filesystem
identifier.

**Artifact and gate:** The host creates and validates the canonical Wish before
the first native turn. Do not rewrite `WISH.json` or propose the Wish gate. A
normalized interpretation must not add authority or silently weaken an
explicit constraint.

## Match

Read the Match `STAGE.json`. Its inputs bind the sealed Wish plus the immutable
inventor personas at
`catalog/inventors/<id>/inventor.json` and `catalog/inventors/<id>/TASTE.md`.
An entry may also expose host-declared, hash-bound Inventor resources such as
inventor-owned Codex skill trees with `SKILL.md`, scripts, references, assets,
or deterministic domain tools. Use only resources declared by that exact
eligible catalog entry; do not search outside the catalog for an executable
worker.

**Codex work:** Inspect eligible inventors, compare the Wish with their stated
taste and capabilities, and write a concise ranking rationale. Use native
search only if the Match contract calls for current outside facts; record its
provenance.

You are the Workshop Manager. Where useful, use native dynamic subagents for
bounded candidate-fit analysis. Brief each one from the exact materialized
candidate bytes and treat its answer as input, not a vote or gate. You must
synthesize the complete ranking and selected Inventor. Use the materialized
project-scoped custom-agent roster; do not launch another Codex process or run
candidate agents through Python.

Write one authored JSON source with exactly `selected_inventor_id` and
`ranking`. Every ranking item must be evidence-based and refer to an eligible
catalog entry. Then run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . match --source <match-source.json>
```

The finalizer writes the canonical `artifacts/match/assignment.json` and
`agent-outcome.json`. The host checks identities, hashes, eligibility, the
complete ranking, and one-shot assignment semantics. Match does not begin
Invent or perform an external effect.
