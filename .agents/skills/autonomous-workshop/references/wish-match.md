# Wish and Match contracts

The host supplies a run identity, native session identity, absolute workspace,
durable checkpoint, capability limits, and current authorization scope. Verify
them before acting. Keep substantive results in the workspace; return only
compact paths, hashes, gate evidence, needs, and a proposed transition.

## Wish

**Input:** The person's words and explicitly supplied constraints/context.

**Codex work:** Preserve intent. Ask for information only when the missing
choice would materially change the product; otherwise make reversible design
assumptions visible in the workspace. Never place Wish text in a filesystem
identifier.

**Artifact and gate:** A bounded, versioned Wish record with an opaque run id.
The host validates the record before Match. A normalized Wish must not add
authority or silently weaken an explicit constraint.

## Match

**Input:** The sealed Wish plus the immutable inventor personas at
`catalog/inventors/<id>/inventor.json` and `catalog/inventors/<id>/TASTE.md`.
These exact files are run inputs; do not invoke an Inventor profile, import
Inventor code, or search outside this catalog for an executable worker.

**Codex work:** Inspect eligible inventors, compare the Wish with their stated
taste and capabilities, and write a concise ranking rationale. Use native
search only if the Match contract calls for current outside facts; record its
provenance.

**Artifact and gate:** One immutable assignment binding the exact Wish to one
eligible inventor/Taste revision, with evidence for the selection. The host
checks identities, hashes, eligibility, and one-shot assignment semantics.
Match does not begin Invent or perform an external effect.
