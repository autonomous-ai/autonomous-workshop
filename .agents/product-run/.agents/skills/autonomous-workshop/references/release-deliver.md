# Release and Deliver contracts

Read `STAGE.json`. It binds the exact Made product, passing Playtest contract
and evidence, selected Inventor custom agent and Taste hashes, universal
blueprint, Release package root, and current checkpoint. Verify those bytes
before acting.

## Release Goal and validation loop

Read `.agents/skills/manual-design/SKILL.md`, then create one native Codex Goal
for this Release attempt. Its objective is to produce the exact printable
in-box manual and bounded product facts traceable to the sealed product and
passing Playtest evidence. Its stopping condition is a successful `release`
finalizer for the current checkpoint.

While pursuing the Goal:

1. **Observe:** Inspect the exact Made tree, passing Playtest checks and
   evidence, Wish, selected Taste, universal blueprint, and every proposed
   customer fact. Separate supported product guidance from claims about future
   publication, manufacture, delivery, or physical performance.
2. **Act:** Assemble `artifacts/release/package` with canonical `MANUAL.pdf`,
   evidence-bound `product.json`, and optional editable manual source. The PDF
   is the customer artifact: cover inventory, setup, guided first use, complete
   operation or rules, scoring where relevant, troubleshooting, pack-away,
   care, and safety. Keep slicer settings, calibration, provenance, internal
   evidence, and builder notes outside the customer manual.
3. **Evaluate:** Validate every claim against exact evidence and hashes. Render
   every PDF page, inspect it at intended print size and in grayscale, confirm
   that all essential meaning survives without color, and check that a new
   owner can begin without a phone or website. Use an independent native
   fact-checker or visual editor subagent where useful. Run deterministic
   package validation after meaningful changes.
4. **Improve:** Remove unsupported language, resolve contradictions, repair
   hierarchy or cramped layout, clarify missing actions, rerender, and continue
   until both the manual and bounded metadata are internally consistent.

Codex owns the fact-check, design, render, review, and revise loop. Python may
validate PDF structure, schemas, hashes, and claim bindings; it does not write
the manual, score beauty, or control the improvement loop.

The package must include a non-empty, self-contained `MANUAL.pdf` and canonical
schema-v4 `product.json`. That JSON object has exactly these ten fields and no
others:

- `schema_version`: integer `4`;
- `kind`: string `workshop.release-package`;
- `status`: string `manual-ready`;
- `title`: the exact Made product title;
- `summary`: concise supported product description;
- `what_arrives`: non-empty list of included-item descriptions;
- `limitations`: list of supported limitations, which may be empty;
- `product_artifact_sha256`: exact Made product artifact hash;
- `playtest_evidence_artifact_sha256`: exact passing evidence artifact hash;
- `claims`: the exact non-empty claims mapping from Playtest.

Do not invent claims of manufacture, physical fit, human response,
publication, delivery, or certification. The PDF may contain embedded fonts,
vector art, and product-derived raster images; it must not depend on external
resources, scripts, launch actions, attachments, credentials, or receipts.
`MANUAL.pdf` is authoritative customer guidance. Optional source or accessible
text companions must not contradict it.

Do not create or edit `artifacts/release/VERIFICATION.json`. It is optional
host-owned, public-safe enrichment written only after the host independently
accepts the exact Release package. The current host can emit only **Digitally
Verified**; **Physically Verified** requires a future trusted host receipt that
proves the exact released bytes were built and checked. Missing verification
never blocks Release.

Website copy limits are not manual design constraints and must not make a valid
local Release fail. Keep `product.json` concise and factual. The host may later
transport its exact supported subset, model bytes, and `MANUAL.pdf` through an
authorized adapter; it must not rewrite the sealed manual.

Run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package
```

The deterministic finalizer writes `artifacts/release/release.json` and the
compact outcome. Complete the Release Goal only after it succeeds, then return
to the host. The host validates and seals the exact manual, metadata, and
product bytes. That local gate advances independently of any Factory effect.

## Deliver is a host effect boundary

Do not create a native Goal for Deliver. Stop truthfully after the host accepts
Release. Codex may summarize what future production, hands-on QA, manual
printing, packing, and carrier evidence would be needed, but it must not buy,
manufacture, publish, ship, or access credentials.

The current Workshop has no Deliver effect adapter or Delivered contract. The
host returns a durable waiting checkpoint after Release. A future, separately
reviewed host integration may advance only from authenticated production, QA,
packing, and carrier receipts bound to these exact hashes. A plan, page, label
draft, or unconfirmed request is not delivery.
