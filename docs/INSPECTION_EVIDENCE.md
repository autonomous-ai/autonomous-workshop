# Product bytes and inspection evidence

A Workshop `Inspection` can bind two content-addressed artifacts:

```text
product root --seal--> artifact_manifest -------> received product
                         | artifact_sha256                |
                         |                                |
inspection root --seal--> evidence_manifest               |
                         | evidence_artifact_sha256        |
                         +---------- Inspection -----------+
                                      |
                                      v
                           Runtime Inspect event
```

The product manifest owns files that a customer receives, including CAD source,
STEP, STL, rules, and other product assets. The evidence manifest owns review,
playtest, inspection, and validator files. Every `InspectionResult` still names
the exact product `artifact_sha256`, while its `evidence_ref` and
`evidence_sha256` must resolve in the selected evidence manifest. A CAD release
uses the same split: part paths resolve in the product manifest and CAD evidence
paths resolve in the evidence manifest.

This lets an inventor keep the received product free of review files without
losing the audit link. On the Inspect transition, Runtime records the product identity as the event's
artifact and the evidence identity as `payload.inspection_evidence_sha256`.
Serializing later must preserve the product identity; it does not add review
files to the product artifact.

For compatibility, omit `evidence_manifest` when evidence intentionally lives
inside the product artifact. Workshop then uses `artifact_manifest` for both
roles. Runtime stores identities, not evidence bytes, so the inventor must
retain the evidence artifact in its own durable storage.

The normal Workbench path accepts this split directly:

```python
evidence_manifest = seal_artifact(
    inspection_root, created_at="content-addressed"
)
inspection = workbench.inspect(
    made, evidence_manifest=evidence_manifest
)
```

An Inspection may contain failed results; they are useful remake feedback.
Only results named in the target stage's `required_inspection_ids` must pass to
advance. Runtime stores the full result list plus that required subset so an
optional failure cannot be mistaken for an approval or silently discarded.
