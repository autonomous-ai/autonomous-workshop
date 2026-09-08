# Make and Playtest (retained pointer)

This file is retained only because frozen historical runs bind its path in
their materialized input manifest. It is no longer linked from `SKILL.md` and
is not the current specification.

- Make: [make.md](make.md) is authoritative, including the build-group
  (`make-group`) interface, the proof-turn commands, the `product.json`
  title/summary rules, and the `make-revision` route.
- Playtest: [playtest.md](playtest.md) is authoritative, including the check
  and feedback shapes, `product_artifact_sha256` binding, vault lead answers,
  and score reads.

Where this file's earlier text disagreed with those references, those
references and the host-written `STAGE.json` take precedence.

## Playtest Goal and independent evidence loop

This section restates, for frozen runs bound to this file, the Playtest
contract that [playtest.md](playtest.md) now owns. It applies only when
`STAGE.json.stage` is `playtest`.

For every required check id `<check-id>`, write its canonical configuration to
`<evidence_root>/configs/<check-id>.json`: a strict JSON object with
`schema_version: 1`, the exact `check_id`, and the current Made
product-manifest hash under `product_artifact_sha256` (the legacy
`artifact_sha256` key is still accepted; when both are present they must
agree). When `seed` is present it must be an integer.

Write one authored JSON source with exactly `checks`, `feedback`, and
`verdict`. Every check is a strict object with exactly these eight fields:
`check_id`, `passed`, `evaluator`, `evaluator_version`, `config_ref`,
`evidence_ref`, `observed_at`, and `observations`. `feedback` is an array.
Every item is a strict object with exactly these seven
fields: `code`, `area`, `severity`, `finding`, `change`, `evidence_refs`, and
`invalidates`. `verdict` is exactly `pass`, `improve`, or `block`. Vault lead
answers, score reads, invalidation boundaries, and the finalizer command are
as described in [playtest.md](playtest.md).
