# Terminal Release contract

Read `STAGE.json`. It binds the exact Made product, selected Inventor custom
agent and Taste hashes, universal blueprint, Release package root, and current
checkpoint. Verify those bytes before acting.

## Release Goal and validation loop

Read `.agents/skills/manual-design/SKILL.md`, then create one native Codex Goal
for this Release attempt. Its objective is to produce the exact printable
in-box manual and bounded product facts traceable to the sealed product and,
when present, the exact passing Playtest. Its stopping condition is a successful
`release` finalizer for the current checkpoint.

Release starts from the sealed Made contract, product metadata, artifact
manifest, final verification, and exact presentation render. Read CAD source or
additional model files only when one customer instruction or claim cannot be
resolved from those compact authorities. Do not rebuild, redesign, or rerun
Make's accepted verification inside Release; the host owns the final CAD guard.

While pursuing the Goal:

1. **Observe:** Inspect the exact Made tree, Wish, selected Taste, universal
   blueprint, and every proposed
   customer fact. Separate supported product guidance from claims about future
   publication, manufacture, delivery, or physical performance.
2. **Act:** Assemble `artifacts/release/package` with canonical `MANUAL.pdf`,
   `product.json`, canonical `MANUAL-DESIGN.json` when listed by
   `required_package_files`, the effort-required Playtest omission file when
   listed there, and optional editable manual source. The PDF
   is the customer artifact: cover inventory, setup, guided first use, complete
   operation or rules, scoring where relevant, troubleshooting, pack-away,
   care, and safety. Keep slicer settings, calibration, provenance, internal
   evidence, and builder notes outside the customer manual.
3. **Evaluate:** Validate every product claim against exact Made bytes and
   hashes. Render
   every PDF page, inspect it at intended print size and in grayscale, confirm
   that all essential meaning survives without color, and check that a new
   owner can begin without a phone or website. For current runs, use an
   independent native visual-editor subagent on the first complete render,
   resolve at least one concrete finding, and bind the review in
   `MANUAL-DESIGN.json`. Run deterministic package validation after meaningful
   changes.
4. **Improve:** Remove unsupported language, resolve contradictions, repair
   hierarchy or cramped layout, clarify missing actions, rerender, and continue
   until both the manual and bounded metadata are internally consistent.

Produce the smallest complete manual first, render all of it in one batch, then
make one coherent revision that resolves the required independent review and
the largest first-owner problem together. Rerender after that revision. Avoid
page-by-page drafting, repeated font or layout experiments, and extra review
passes that do not answer a concrete finding.

For a simple one-piece Spark toy with no assembly or rule system, start with a
double-sided owner card. Add pages only for a named clarity or safety need that
cannot fit. Use ASCII customer text unless exact font coverage is already
verified, drawing special symbols as vectors. After the final review render,
write the hash-bound `MANUAL-DESIGN.json`; changing only that evidence file does
not require another PDF render.

Codex owns the fact-check, design, render, review, and revise loop. Python may
validate PDF structure, schemas, hashes, and claim bindings; it does not write
the manual, score beauty, or control the improvement loop.

For Spark and Forge, the package includes canonical `PLAYTEST-NOT-RUN.json`
and schema-v5 `product.json`. That JSON has exactly these eleven fields:

- `schema_version`: integer `5`;
- `kind`: string `workshop.release-package`;
- `status`: string `manual-ready`;
- `title`: the exact Made product title;
- `summary`: concise supported product description;

Both reach a shopper unchanged, so write them as customer copy:

- The title is a name someone would say out loud: one to four words, no
  dimensions, no part counts, no sentences, no slug, no repeated category
  ("Chess Set" twice on one shelf helps nobody). "Horn Tip" and "Ember Knock"
  are names; "185 Mm Tall" and "210mm retro-futuristic helical dice tower with
  a funnel hopper" are not.
- The summary says what it is and what it does, in the words a buyer uses.
- Never put Workshop vocabulary in customer copy. The words Wish, Taste,
  Inventor id, Goal, Make, Release, Playtest, Spark, Forge, Quest, artifact,
  gate, and finalizer are internal. A shopper reading "the mechanism is the
  Wish" learns nothing.
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

For Quest, `STAGE.json` instead contains exact `playtested` and
`playtested_artifact` inputs and uses schema-v4 `product.json`. Omit
`playtest_status` and the omission file. Bind
`playtest_evidence_artifact_sha256` to the sealed evidence manifest and build
`claims` from every exact Playtest check: pass status, evidence class, bounded
claims, evidence reference and hash, evaluator, and evaluator version. Do not
broaden those claims or imply physical evidence when the cited class is
digital.

Do not invent claims of manufacture, physical fit, human response,
publication, delivery, or certification. The PDF may contain embedded fonts,
vector art, and product-derived raster images; it must not depend on external
resources, scripts, launch actions, attachments, credentials, or receipts.
`MANUAL.pdf` is authoritative customer guidance. Optional source or accessible
text companions must not contradict it.

Do not create or edit `artifacts/release/VERIFICATION.json`. The host may derive
that optional projection after a passing Quest Release; it is never agent gate
evidence and does not rewrite the sealed package.

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
