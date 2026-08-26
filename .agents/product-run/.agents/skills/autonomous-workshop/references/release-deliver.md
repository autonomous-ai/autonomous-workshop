# Release and Deliver contracts

Read `MANAGER.json` and `STAGE.json`. They bind the selected Manager and its
runtime projection, exact Made product, passing Playtest contract and evidence,
selected Inventor-agent path and Taste hashes, universal blueprint, Release
package root, and current checkpoint. Verify those bytes before acting.

## Release Goal and validation loop

Create one native Goal through the selected Manager's `/goal` control for this
Release attempt. Its objective is to produce a complete, useful manual and
page-ready customer product package whose claims and creative direction are
traceable to the sealed product and passing Playtest evidence. Its stopping
condition is a successful `release` finalizer for the current checkpoint.

While pursuing the Goal:

1. **Observe:** Inspect the exact Made tree, passing Playtest checks and
   evidence, Wish, selected Taste, universal blueprint, and every proposed
   product fact. Separate evidence-bound product storytelling from claims about
   future publication, manufacture, delivery, or physical performance.
2. **Act:** Assemble `artifacts/release/package` with substantive `MANUAL.md`,
   canonical page-ready `product.json`, evidence-bound claims, complete hero,
   cinematic, use-case, and story-block copy, visual direction, what arrives,
   limitations, attribution, and any necessary non-media factual files. Cover
   mechanics, rules, components, assembly, limitations, care, and safety.
3. **Evaluate:** Validate every claim against exact evidence and hashes, check
   the manual as a new owner's complete starting point, and inspect the package
   as the source for a product page. Use an independent native fact-checker or
   editor subagent for bounded review where useful. Run deterministic package
   validation after meaningful changes.
4. **Improve:** Remove unsupported language, resolve contradictions, clarify
   missing steps, and rerun validation until the package is internally
   consistent and evidence-complete.

The selected Manager owns the fact-check/write/review/revise loop. Python
validates exact schema, hashes, and claim bindings; it does not write copy,
judge usefulness, invent claims, or control the loop.

The package must include UTF-8 `MANUAL.md` and canonical schema-v3
`product.json` with `kind=workshop.release-package`, `status=page-ready`, exact
product/evidence hashes, exact Playtest claims, `title`, `summary`, `hero`,
`cinematic`, `use_case`, one or more `story_blocks`, `what_arrives`, and
`limitations`. Every page section contains `headline`, `body`,
`visual_direction`, and valid `evidence_refs`. Do not invent claims of
manufacture, physical fit, human response, publication, delivery, or delight.
Do not place credentials, receipts, images, audio, or video in the local
package. The selected Manager owns the complete page copy and visual direction;
Factory later transports the exact sealed page and model bytes rather than
creatively enriching them.

For the exact `use_case` and `story_blocks` copy to render on the current
Factory site, keep each `headline` to 1–40 plain-text characters, each `body`
to 180–400 plain-text characters, use no `<` or `>` characters in those
fields, and provide at most 10 story blocks. These are Factory display limits,
not prompts for Python rewriting: the host copies compatible text exactly and
fails the handoff rather than truncating or paraphrasing it. The imported
design cover fills Factory's required use-case image slot. The complete
schema-v3 page, including visual direction and evidence references, and the
exact `MANUAL.md` remain authoritative sealed files in the uploaded project.

Run:

```bash
python <skill_directory>/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package
```

Replace `<skill_directory>` with its exact `MANAGER.json` value; do not type
the angle brackets literally.

The deterministic finalizer writes `artifacts/release/release.json` and the
compact outcome. Complete the Release Goal only after it succeeds, then return
to the host. The host validates and seals the exact manual, page, and product
bytes before any Factory effect.

## Deliver is a host effect boundary

Do not create a native Goal for Deliver. Stop truthfully after the host accepts
Release. The selected Manager may summarize what future production, hands-on
QA, packing, and carrier evidence would be needed, but it must not buy,
manufacture, publish, ship, or access credentials.

The current Workshop has no Deliver effect adapter or Delivered contract. The
host returns a durable waiting checkpoint after Release. A future, separately
reviewed host integration may advance only from authenticated production, QA,
packing, and carrier receipts bound to these exact hashes. A plan, page, label
draft, or unconfirmed request is not delivery.
