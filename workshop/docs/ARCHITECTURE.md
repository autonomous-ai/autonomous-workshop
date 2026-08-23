# Workshop architecture

Workshop separates an inventor's creative identity from machinery every
inventor needs.

## One promise, two views

Customer view:

```text
WISH  ------------------------- WAIT ---------------------->  RECEIVE
```

Developer view:

```text
MAKE  ------------>  INSPECT  ------------>  PACK  ------------>  SEND
```

The developer stages explain implementation. They are not a customer progress
feed, and `Wait` is not an engine stage. `Receive` is the customer handoff; the
Box is the physical outcome, not a ZIP file or queue record.

## Alice as the example

```text
              Alice owns                         Workshop owns

       +----------------------+       +--------------------------------+
       | TASTE.md             |       | Workbench + making skills     |
Wish ->| workflow and prompts |------>| Inspection + exact evidence   |
       | niche-specific bar   |       | Pack + Sender + Doors         |
       +----------------------+       | Clockwork underneath          |
                                      +---------------+----------------+
                                                      |
                                                      v
                                                   Receive
                                                    (Box)
```

To build Ada instead, copy neither Alice's state machine nor its runtime. Add
`inventors/ada/`, define Ada's Taste and workflow, then compose the same
Workshop contracts.

The dependency direction is one-way:

```text
inventors/alice  --->  inventor_workshop  --->  qualified Doors

inventor_workshop  -X->  inventors/alice
```

Workshop never imports an inventor. An outside service never becomes a second
source of local truth merely because it returned HTTP 200.

## The four backstage stages

### Make

`Wish` is bounded intent. `Taste` is loaded from the inventor root and bound by
exact bytes. `Workbench.make()` uses the model and CAD Doors. It
owns the budget and fresh workspace boundary, but it does not run the separate
Inspect stage.

The result is `MakeResult`: concept identity, CAD build, and artifact manifest.
Its canonical CAD release is absent and its `inspections` tuple is empty until
the legacy combined `create()` compatibility path is used.

`MakerMark` sits beside that result and records how one candidate run was made:
exact tool and version, live/fixture/offline/replay mode, authentication, Taste
and input hashes, the exact output artifact hash, agent-call count, actual
versus synthetic cost, timestamps, and limitations. Non-live modes can never authenticate or report actual cost;
live mode can never report synthetic cost. The mark is provenance only—not an
Inspection or a production-readiness claim.

### Inspect

`Workbench.inspect(made)` invokes the CAD Inspection Door and domain Inspection
Door, then returns an artifact-bound `Inspection` carrying the validated CAD
release. An `InspectionResult` names:

- an inspection id;
- pass/fail;
- exact artifact SHA-256;
- evaluator identity, pinned version, and configuration SHA-256;
- evidence path and evidence SHA-256;
- UTC observation time.

`Inspection` additionally proves that each evidence path and hash exists in a
sealed evidence manifest. By default that is the product's own
`ArtifactManifest`; a product-only Pack can instead use
`Workbench.inspect(made, evidence_manifest=sealed_review_evidence)`. Part paths
remain bound to the product manifest while review and validator paths resolve
in the selected evidence manifest. Canonical `Workflow.advance()` requires
this bundle for any transition with required checks. Detached evaluator claims
cannot cross that boundary.

Passed and failed results are both durable feedback. Only the ids required by
the target stage license a transition and therefore must pass pinned policy and
freshness checks. Optional failures stay in the event's `inspections` list;
`required_inspection_ids` records which subset actually approved the move.

A CAD result carries two independent hashes. Its `evidence_sha256` is the
digest of the report file named by `evidence_ref`; that file must be present in
the selected sealed evidence manifest. Its structured evidence also names
`cad_release_sha256`, the digest of the validated `CadReleaseBundle`. Requiring
those two hashes to equal would make an artifact-bound report circular, so the
Workshop validates each identity at its own boundary.

```text
product bytes ----- SHA-256 ----+
                                |
evidence file ----- SHA-256 ----+--> Inspection --> checked transition
                                |
evidence manifest - SHA-256 ----+
```

### Pack

`pack_artifact()` builds one deterministic `PackedArtifact` outside the source
tree. Ordering, timestamps, permissions, ZIP form, inventory, file limits, and
secret patterns are checked. `inspect_pack()` reads the exact Pack bytes once
and returns both Pack and artifact identities.

The canonical state change is
`Workflow.advance(..., "pack", ..., packed=packed)`. Workflow re-inspects the
structured Pack, requires its artifact SHA-256 to equal the product already
accepted by Inspect, and records its `pack_sha256` in Clockwork's hash-chained
transition event. A caller-authored hash alone cannot cross this boundary.

The Pack is backstage transport. It is never called the customer's Box.

### Send

`Sender` writes a durable intent before an effect. A `ShopDoor` or
`DeliveryDoor` owns authentication and transport. A `Stamp` records trustworthy
outside evidence bound to exact Pack and artifact hashes.

Timeouts, redirects, malformed success bodies, unexpected statuses, and
uncertain readbacks remain ambiguous. Sender holds them for reconciliation; it
does not blindly retry a possibly completed non-idempotent effect.

A shop is optional:

```text
Pack --> DeliveryDoor --> Stamp --> printing + delivery --> Box

Pack --> ShopDoor --> Stamp --> later DeliveryDoor --> Box
```

## Clockwork

Clockwork is durable machinery, not the inventor's mind.

It supplies:

- SQLite state and transactions;
- revision-fenced workflow transitions;
- hash-chained events;
- bounded leases;
- budget reservation and spend accounting;
- durable send intents;
- record-before-send effect tokens;
- ambiguous-effect reconciliation.

Accurate security terms stay literal: artifact, SHA-256, lease, budget,
idempotency, draft, live, audit, and payment receipt.

## Doors

A Door is always qualified. A bare, all-purpose adapter hides too much.

| Door | Boundary |
|---|---|
| `ModelDoor` | model/agent execution |
| `CadDoor` | artifact construction |
| `CadInspectionDoor` | geometry and manufacturing verification |
| `InspectionDoor` | form, safety, play, novelty, or domain evaluation |
| `ShopDoor` | optional storefront effect and readback |
| `DeliveryDoor` | printer, fulfillment, or carrier handoff |

Secrets stay with the concrete Door and out of Packs, events, manifests, and
inventor source.

## Repository boundary

```text
inventors/<id>/
  TASTE.md              human-owned creative constitution
  inventor.json         identity and used Workshop features
  README.md             thesis, operation, limits
  src/ or harness/      inventor-owned workflow
  tests/                inventor checks

workshop/
  src/inventor_workshop/
    make.py             Wish -> MakeResult
    maker_mark.py       exact creation provenance
    inspection.py       artifact-bound evidence
    pack.py             reproducible exact bytes
    send.py             Doors, durable send, Stamps
    clockwork.py        workflow + durable machinery
    taste.py            exact creative constitution
  skills/               versioned making knowledge
  schemas/              manifest and Stamp contracts
```

Compatibility modules such as `creation.py`, `launch.py`, and former package
names exist only to read old deployments. New inventor code imports the files
shown above.

## Extension rules

An inventor may:

- add stages and stricter inspections;
- choose any models, CAD engines, printers, or providers behind Doors;
- add niche skills and reward hypotheses;
- retain stronger local machinery while adapting at a Workshop boundary.

It may not:

- edit `TASTE.md` autonomously;
- treat missing evidence as pass;
- detach evidence from artifact bytes;
- bypass leases, budgets, or a durable effect fence;
- infer external success from a local flag or HTTP status;
- claim a `workshop_feature` its runtime does not actually use.
