# Product bytes and Playtest evidence

Workshop Playtest binds every verdict to the exact Make it tested. Product
files and evidence files are separate content-addressed artifacts:

```text
product root  --seal--> artifact_manifest
                              | artifact_sha256
                              v
                         [ Playtest ] ------> Feedback or pass
                              ^
                              | evidence_artifact_sha256
playtest root --seal--> evidence_manifest
```

The product manifest owns what the customer may receive: rules, source, STEP,
per-part meshes, assembly information, and other product assets. The evidence
manifest owns simulator traces, evaluator output, CAD measurements, slicer
reports, physical-test records, human-playtest observations, and supporting
media.

Keeping them separate prevents internal review files from silently entering the
customer product while preserving a complete audit link.

## Exact binding

Every `PlaytestResult` names:

- one playtest ID;
- pass or fail;
- the exact product `artifact_sha256`;
- a non-empty evidence record;
- an evaluator and exact non-floating version;
- the evaluator configuration hash;
- observation time;
- a safe evidence path and the SHA-256 of that file.

The evidence path must resolve with the declared hash inside the sealed
evidence manifest. A CAD release follows the same split: CAD source, STEP, and
mesh paths resolve in the product manifest; CAD observations resolve in the
evidence manifest.

Changing the product after Make, changing an evidence file after Playtest, or
attaching evidence from another revision invalidates the boundary. Re-running
Make creates a new immutable round and requires new Playtest evidence.

## Routing provenance is not product evidence

Before Make, the Workshop Manager searches the catalog's compact Taste
descriptions, records a shortlist, compares one exact Wish with each finalist's
exact `TASTE.md`, and creates one assignment. That assignment binds the catalog
snapshot, retrieval receipt, complete finalist ranking and Taste hashes, chosen
inventor, entry point, and trusted Playtest-round allowance. It proves which
request-scoped decision was made and why; changing relevant catalog metadata,
a finalist Taste, or the selected manifest invalidates dispatch.

A routing decision does **not** prove that the product matches Taste, works,
prints, delights anyone, or deserves release. The semantic fit score is an
independent-model prediction only when its evaluator provenance supports that
claim. It cannot substitute for artifact-bound CAD, slicer, physical,
simulation, or human evidence, and Instructions must not present “the Manager chose
this inventor” as product approval.

The assignment is one-shot. Reassignment creates a new routing record; it does
not bless artifacts or Playtest evidence produced under the old Taste. A future
continuous-intake adapter may create many independent assignments, but uptime
and scheduling add no evidence class and do not weaken any Playtest gate.

## Normal Workbench path

Seal the Playtest workspace independently, then pass that manifest to the
canonical method:

```python
evidence_manifest = seal_artifact(
    playtest_root,
    created_at="content-addressed",
)
playtest = workbench.playtest(
    made,
    evidence_manifest=evidence_manifest,
)
```

For compatibility, omitting `evidence_manifest` means the evidence intentionally
lives inside the product artifact. New production paths should normally keep
the roots separate. Runtime stores their identities, not the evidence bytes, so
the operator must retain both sealed artifacts durably.

## Failed evidence is useful, not approval

A `Playtest` may contain failed results. They become actionable `Feedback` for
the next Make round. A pass exists only when every required result for the
exact artifact passes the pinned policy.

Missing, stale, malformed, timed-out, unsupported, or hash-mismatched evidence
is not a pass. An optional failure remains visible and cannot be silently
discarded or presented as approval. Same-model self-confidence cannot satisfy
an independent gate.

## Evidence class limits

The evidence class determines what Instructions may claim:

| Evidence class | Supports | Cannot establish |
|---|---|---|
| AI simulation | executable rules, termination, traces, balance and pacing proxies | human understanding, delight, or desire for another play |
| Independent model review | a reproducible prediction about clarity, novelty, coolness, or Taste alignment | observed human preference or physical behavior |
| CAD/kernel measurement | dimensions, topology, clearances, interference, motion, assembly calculations | that a real print assembled or survived use |
| Slicer analysis | behavior under an exact printer, material, and profile; predicted time, material, and supports | successful printing or acceptable finish |
| Physical prototype | recorded measurements and tests for one exact print with full provenance | broad durability, safety, or delight beyond that test |
| Human playtest | observed behavior and statements from identified independent participants under a stated protocol | universal fun or demand beyond the sample |
| Production or carrier receipt | the exact production, QA, packing, handoff, or delivery event observed | any later event or unobserved product quality |

For example, “1,000 seeded games terminated” is a strong simulation claim and
still not evidence that anyone had fun.

## Category evidence

Every category must first clear the Workshop product bar:

- the result could not have been downloaded before the Wish;
- the Wish materially changes the design rather than adding decoration;
- cool, clever, striking, or satisfying beats merely cute or twee;
- personalization and design intelligence beat a generic print.

An independent model may predict that a design clears this bar, but human
behavior is required for human-preference claims.

Category-specific Playtest then adds the right gates:

- **Classics made yours (`classics-made-yours`)** uses known rules. Verify rules
  fidelity, personalization, legibility, setup, handling, physical quality,
  printing, and the exact custom edition. Do not claim familiar gameplay as a
  new invention.
- **Games that don't exist yet (`invented-games`)** needs executable AI-player
  traces to find rule errors, loops, exploits, balance risks, and pacing
  problems. Release also requires an independent human table that plays the
  exact game and wants another play. Even 1,000 simulations cannot replace
  that gate.
- **Machines that move (`moving-machines`)** needs exact motion, interference,
  wear, assembly, print, and physical-cycle evidence.
- **Science you can hold (`holdable-science`)** needs scientific accuracy plus
  exact geometry, interaction, print, and physical-observation evidence.
- **Little worlds (`little-worlds`)** needs evidence that the Wish materially
  shaped the world, plus legibility, originality, print, assembly, and observed
  human response.

Kits and numbered series are later variants. They introduce no V1 Playtest
class and are not evidence shortcuts.

## Per-Wish round allowance

`playtest_rounds` limits how many immutable Make–Playtest repair rounds one Wish
may consume. The trusted service boundary records a value from 1 through 100
before Make and passes the same value into every custom context.

It never changes the evidence policy. A smaller allowance does not remove
physical tests, human gates, or required result IDs; a larger allowance does
not turn simulation into human evidence. If the allowance ends while a required
result still fails, the run stops before Instructions and Deliver.

The number of AI games, reviewers, or physical trials inside one Playtest round
is a separate trusted budget.

## Instructions and Deliver remain bound

Instructions begins only after Playtest passes for the exact product hash. Each public
claim points back to a result's evidence class, path, hash, evaluator, and
version. Copy may be delightful, but it may not upgrade simulation to fun,
slicing to a physical print, or concept art to product proof.

Deliver rechecks both the product and Instructions manifests. Production, QA, packing,
and USPS/UPS/FedEx receipts must identify those approved bytes. A carrier label
alone is not handoff or delivery.

## Persisted compatibility

Workshop 0.5 code uses `Playtest`, `PlaytestResult`, `PlaytestPolicy`, and
`Workbench.playtest()`. Persisted records intentionally keep a few older field
names so existing state remains replayable:

- serialized `inspection_id` is the stored spelling of code-facing
  `playtest_id`;
- older transition payloads may contain `required_inspection_ids`;
- the sealed Playtest evidence hash may be stored as
  `inspection_evidence_sha256`.

The older class and method names remain aliases to the same implementation.
They are compatibility details, not a second evidence model or an additional
Workshop job.

Use [`../schemas/playtest-result.schema.json`](../schemas/playtest-result.schema.json)
for the canonical 0.5 persisted result. The older
[`../schemas/inspection-result.schema.json`](../schemas/inspection-result.schema.json)
remains available for compatibility.
