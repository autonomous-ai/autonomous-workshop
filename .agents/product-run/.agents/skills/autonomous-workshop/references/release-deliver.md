# Terminal Release contract

Read `STAGE.json`. It binds the exact Made product, selected Inventor custom
agent and Taste hashes, universal blueprint, Release package root, and current
checkpoint. Verify those bytes before acting.

## Release Goal and validation loop

Read `.agents/skills/manual-design/SKILL.md`, then create one native Codex Goal
for this Release attempt. Its objective is to produce the exact printable
in-box manual and bounded product facts traceable to the sealed product, while
truthfully recording that Playtest was not run. Its stopping condition is a
successful `release` finalizer for the current checkpoint.

While pursuing the Goal:

1. **Observe:** Inspect the exact Made tree, Wish, selected Taste, universal
   blueprint, and every proposed
   customer fact. Separate supported product guidance from claims about future
   publication, manufacture, delivery, or physical performance.
2. **Act:** Assemble `artifacts/release/package` with canonical `MANUAL.pdf`,
   `product.json`, canonical `PLAYTEST-NOT-RUN.json`, and optional editable
   manual source. The PDF
   is the customer artifact: cover inventory, setup, guided first use, complete
   operation or rules, scoring where relevant, troubleshooting, pack-away,
   care, and safety. Keep slicer settings, calibration, provenance, internal
   evidence, and builder notes outside the customer manual.
3. **Evaluate:** Validate every product claim against exact Made bytes and
   hashes. Render
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

The package must include a non-empty, self-contained `MANUAL.pdf`, canonical
`PLAYTEST-NOT-RUN.json`, and canonical schema-v5 `product.json`. That JSON
object has exactly these eleven fields and no others:

- `schema_version`: integer `5`;
- `kind`: string `workshop.release-package`;
- `status`: string `manual-ready`;
- `title`: the exact Made product title;
- `summary`: concise supported product description;
- `what_arrives`: non-empty list of included-item descriptions;
- `limitations`: list of supported limitations, which may be empty;
- `product_artifact_sha256`: exact Made product artifact hash;
- `playtest_status`: exact string `not-run`;
- `playtest_evidence_artifact_sha256`: exact hash of canonical
  `PLAYTEST-NOT-RUN.json`;
- `claims`: exactly the required `playtest` omission mapping, with status
  `not-run`, an empty claims list, and the omission file reference and hash.

Generate the omission file with exactly the schema documented by the current
`release_contract` in `STAGE.json`; do not improvise its wording or treat it as
evidence that a test occurred.

Do not invent claims of manufacture, physical fit, human response,
publication, delivery, or certification. The PDF may contain embedded fonts,
vector art, and product-derived raster images; it must not depend on external
resources, scripts, launch actions, attachments, credentials, or receipts.
`MANUAL.pdf` is authoritative customer guidance. Optional source or accessible
text companions must not contradict it.

Do not create or edit `artifacts/release/VERIFICATION.json`. The direct path
does not emit one because Playtest was not run. A future verified Playtest or
physical receipt may introduce separate evidence without rewriting this
truthful Release.

Website copy limits are not manual design constraints. Keep `product.json`
concise and factual so the host can transport its exact supported subset,
model bytes, and `MANUAL.pdf` through the required Release adapter without
rewriting the sealed manual. If Factory cannot accept or verify the exact
handoff, Release waits or fails closed; Codex must not change truthful product
content merely to fit a remote marketing field.

Run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package
```

The deterministic finalizer writes `artifacts/release/release.json` and the
compact outcome. Complete the Release Goal only after it succeeds, then return
to the host. The host reruns the current full-tier CAD gate, validates the
exact manual and package, publishes the ready-to-print CAD plus `MANUAL.pdf`,
and requires authenticated public hash readback before Release completes.
Missing credentials or a transient or ambiguous server result leaves Release
waiting; the host reconciles its durable effect ledger before retrying.

Do not create Goals for Printing, Deliver, or Review. Those are
Operations-owned stages after the executable Workshop lifecycle. Codex may
state truthful limitations, but it must not buy, manufacture, publish, ship,
access credentials, or claim physical completion.
