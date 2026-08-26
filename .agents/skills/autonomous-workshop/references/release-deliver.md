# Release and Deliver contracts

Read `STAGE.json`. It binds the exact Made product, passing Playtest contract
and evidence, selected Taste, lane blueprint, Release package root, and current
checkpoint. Verify those bytes before acting.

## Release

**Input:** The exact sealed Made product, passing Playtest evidence, Wish,
Taste, blueprint, and evidence-backed product facts.

**Codex work:** Assemble the complete factual package at
`artifacts/release/package`: `MANUAL.md`, canonical `product.json`,
evidence-bound claims, page metadata, attribution, and any additional
non-media factual files. Preserve mechanics, rules, components, limitations,
care, and safety. Keep Factory-owned copy and media explicitly pending. Do not
invent claims of manufacture, human response, publication, delivery, or
delight.

**Artifact and gate:** The package must include substantive UTF-8 `MANUAL.md`
and canonical `product.json` with `kind=workshop.release-package`,
`status=facts-ready`, exact product/evidence hashes, exact Playtest claims, and
`factory_enrichment` pending. Do not place credentials, receipts, images,
video, `story_blocks`, or `use_case` in this local package. Run:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package
```

The finalizer writes `artifacts/release/release.json` and the compact outcome.
The host validates and seals the entire package before any Factory effect.

## Deliver

**Input:** Exact Made and Release hashes and the current Release receipt.

**Codex work:** Stop truthfully at the Deliver boundary. Codex may summarize
what future production, hands-on QA, packing, and carrier evidence would be
needed, but it must not buy, manufacture, publish, ship, or access credentials.

**Artifact and gate:** The current Workshop has no Deliver effect adapter or
Delivered Python contract. The host returns a durable waiting checkpoint after
Release. A future, separately reviewed capability may advance only from
authenticated production, QA, packing, and carrier receipts bound to these
exact hashes. A plan, page, label draft, or unconfirmed request is not delivery.
