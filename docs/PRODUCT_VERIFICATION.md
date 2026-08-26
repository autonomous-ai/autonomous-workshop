# Product verification

Autonomous Workshop has exactly two product-verification levels:

1. **Digitally Verified**
2. **Physically Verified**

These are verification levels for a one-off Wish. They are not prototype and
mass-production tiers. Manufacture, shipment, and delivery are separate
fulfillment statuses and never raise a verification level by themselves.

Verification is an optional public projection, not a lifecycle gate. Existing
Make and Playtest gates remain authoritative. A missing, malformed, or
unwritable public verification record must not block Release, Factory
publication, or Deliver; it means only that no public badge was recorded.

## Authority

Only the trusted Workshop host may set or raise a verification level. Codex,
an Inventor subagent, product-page copy, a checked-in file, or a model-authored
Playtest observation cannot self-declare either level.

When enrichment succeeds, the host derives a versioned `VERIFICATION.json`
after reloading and validating the exact Made, passing Playtested, and Release
contracts. The public record binds their hashes. If any bound product,
evidence, product JSON, or Release bytes change, that record no longer applies
and the new revision must be verified again.

The current host can derive only **Digitally Verified**. **Physically
Verified** is reserved until a reviewed trusted-host receipt contract exists;
schema v1 rejects an attempted physical claim.

## Digitally Verified

Digitally Verified means the host accepted one exact sealed product artifact,
the required digital Playtest checks all passed for that artifact, and Release
was bound to the same product and evidence hashes.

It may support bounded claims about exact digital geometry, CAD/kernel checks,
seeded simulations, slicer predictions, and render inspection according to the
underlying evidence class. It does **not** prove that the product was printed or
built, that physical parts fit, that it is durable, or that a person enjoyed or
even handled it.

The public manifest fixes its scope to:

- `sealed-product-bytes`;
- `passing-digital-playtest-evidence`.

It also explicitly lists these unverified areas:

- `physical-build`;
- `physical-fit`;
- `durability`;
- `human-response`.

## Physically Verified

Physically Verified means a trusted host receipt proves that the exact
hash-bound released artifact was actually printed or otherwise built and then
checked hands-on. The receipt must identify the exact product artifact and
Release identity, the physical build, the check procedure and result, and an
authenticated observer or effect source. An agent statement, uploaded model,
Factory page, slicer output, photograph without authenticated binding, shipping
label, or delivery scan is insufficient.

Physical verification does not imply mass-production readiness, certification,
durability beyond the recorded checks, or customer satisfaction. If the exact
released artifact changes, the physical level resets until the new bytes are
built and checked.

No physical receipt adapter is implemented today. When one is added, it must be
a typed host-owned contract and must introduce a reviewed schema version. It
must not accept a `physical_verification` object supplied by Codex. Physical
proof may be attached later without rerunning or blocking the digital workflow.

## The public manifest

As a best-effort post-Release enrichment, the host writes the canonical
public-safe file at:

```text
artifacts/release/VERIFICATION.json
```

It is deliberately outside Codex's authored
`artifacts/release/package/` tree. This preserves the exact agent proposal while
making the verification level a host-owned projection. Schema v1 contains:

```json
{
  "checks": [
    {
      "check_id": "agent-playtest",
      "config_sha256": "<sha256>",
      "evidence_sha256": "<sha256>",
      "passed": true
    }
  ],
  "kind": "autonomous-workshop.product-verification",
  "label": "Digitally Verified",
  "level": "digitally-verified",
  "made_sha256": "<sha256>",
  "native_release_sha256": "<sha256>",
  "not_verified": [
    "physical-build",
    "physical-fit",
    "durability",
    "human-response"
  ],
  "physical_verification": null,
  "playtest_evidence_artifact_sha256": "<sha256>",
  "playtested_sha256": "<sha256>",
  "product_artifact_sha256": "<sha256>",
  "product_json_sha256": "<sha256>",
  "schema_version": 1,
  "scope": [
    "sealed-product-bytes",
    "passing-digital-playtest-evidence"
  ]
}
```

The real file uses strict canonical JSON and full SHA-256 values. Check IDs and
hashes bind the public statement without publishing free-form observations,
local paths, prompts, transcripts, identities, credentials, or raw receipts.

## GitHub, the website, and private evidence

Each destination has a different job:

- **GitHub documentation** defines these terms and the versioned contract.
- **Private run storage** keeps the full product tree, Playtest evidence,
  native-session artifacts, and host-only receipts. Raw logs and authenticated
  receipts are not committed or published.
- **A public toy snapshot** may copy the exact host-generated file to
  `toys/<inventor>-<product-slug>/VERIFICATION.json`, alongside the manual,
  product data, and printable parts. Its SHA-256 should be bound by the
  sanitized publication record.
- **The product website** renders a verification badge, scope, and “not
  verified” disclosure only when a valid manifest is present. If it is absent
  or invalid, the website shows “Verification not recorded”; it does not infer
  a level and it does not treat the product as failed. Fulfillment and delivery
  status come from separate host receipts and are displayed separately.

There is no second authoritative `EVIDENCE.md`. A website panel or readable
summary may be deterministically rendered from `VERIFICATION.json`, but if
human prose disagrees with the manifest, the manifest wins.
