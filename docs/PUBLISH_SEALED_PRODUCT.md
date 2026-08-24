# Create one sealed product draft

`tools/publish_sealed_product.py` is the generic Workshop path from completed
Instructions to a private Factory draft. It does not run Make or Playtest, and
it has no operation that makes a draft public.

The checked-in descriptor is a small locator, not a second product record. Its
hashes bind the inventor's exact `TASTE.md`, the final Make tree, the final
Playtest evidence tree and index, and the Instructions tree. Titles, copy,
images, Wish, inventor identity, and Playtest claims are reconstructed from
those sealed roots and cross-checked before the first network request.

```json
{
  "schema_version": 1,
  "kind": "workshop.sealed-private-draft",
  "inventor_id": "alice",
  "taste_sha256": "<sha256 of inventors/alice/TASTE.md>",
  "make": {
    "root": "inventors/alice/toys/example/project",
    "manifest": "inventors/alice/toys/example/playtest/round-03/make-manifest.json",
    "artifact_sha256": "<Make artifact sha256>"
  },
  "playtest": {
    "root": "inventors/alice/toys/example/playtest/round-03",
    "evidence_artifact_sha256": "<Playtest evidence artifact sha256>",
    "index_sha256": "<sha256 of evidence-index.json>"
  },
  "instructions": {
    "root": "inventors/alice/toys/example/instructions",
    "manifest": "inventors/alice/toys/example/instructions-manifest.json",
    "artifact_sha256": "<Instructions artifact sha256>"
  }
}
```

The final Make root must contain root `wish.json`, `product.json`, and
`project.json`. The selected round must seal exactly the lane's required AI
Playtest capabilities, with every result passing and no `improve` or `block`
feedback. Instructions must contain `INSTRUCTIONS.md`, an exact `product.json`,
and distinct sealed `hero`, `play`, `detail`, `parts`, and `box` images.

Provide credentials only through the process environment:

```bash
export WORKSHOP_SHOP_TOKEN='...'
export WORKSHOP_SHOP_OWNER_ID='...'
python3 tools/publish_sealed_product.py \
  inventors/alice/toys/example/private-draft.json --verify-draft
```

The token is never a command-line argument and is never written to the durable
ledger or command output. The ignored retry ledger lives at
`.runtime/sealed-product-publication/<product-id>/workshop.sqlite3`. The first
attempt requires the canonical slug to be unused; a successful retry replays
the exact recorded draft instead of importing or uploading again.
