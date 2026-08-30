# ADR 0024: Treat quality economics as a comparative North Star

- Status: Accepted
- Date: 2026-08-30
- Owners: Workshop, runtime, workflow, and documentation maintainers
- Relates to: ADR 0019 (Spark economics), ADR 0021 (Spark compaction), ADR 0022 (blind review), ADR 0023 (bounded Spark turns)
- Supersedes: literal `10x` quality and `0.1x` token acceptance thresholds in ADRs 0019–0023

## Context

“10x the quality at one tenth the cost” describes the desired direction: a
large experiential improvement and a large efficiency improvement at the same
time. It is not a claim that subjective toy quality has a cardinal scale, nor
that one gross-input cutoff remains economically correct across models,
caching policies, or pricing changes.

Workshop already records a token vector rather than inventing a dollar total.
Production evidence also shows why a single ratio is misleading. Cached input
dominates many resumed turns, incomplete telemetry can make totals into lower
bounds, and a cheap failed Make attempt is not comparable with a published
end-to-end run.

## Decision

Quality economics is a comparative North Star, not a deterministic lifecycle
gate. A challenger succeeds only when both sides improve:

- exact renders, product files, interaction, manual, and deterministic evidence
  earn a strong blind preference over named published baselines; and
- complete like-for-like telemetry shows material improvement across gross
  input, uncached input, output, reasoning output, elapsed time, and retries.

No token categories are added together. No current model price is embedded in
the repository. The historical 24,616,026-input Moonchase Fox run and the
earlier 2,461,602 experimental threshold remain useful reference points, but
the latter is not a pass/fail law.

Failed runs are evidence, not toys. Their complete measured attempts may guide
optimization, but only a gate-passing, published run can establish whole-run
economics and take part in the final product comparison.

## Consequences

- Optimization cannot declare victory by hitting one arbitrary token number
  with a worse or unfinished toy.
- A model, cache, or pricing change does not silently redefine success.
- Named production baselines and complete category-level telemetry remain the
  source of truth.
- “10x / 0.1x” remains useful shorthand for ambition, while documented claims
  stay exact and falsifiable.

## Verification

- `docs/QUALITY_ECONOMICS.md` reports input, cached input, derived uncached
  input, output, reasoning output, turn coverage, and elapsed time separately.
- Permanent challengers retain exact public artifacts for blind comparison.
- Failed or partially measured attempts are labeled and never used as
  end-to-end reduction claims.
