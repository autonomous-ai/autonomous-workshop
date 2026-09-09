Let `workshop wish --ref IMAGE` attach up to eight PNG, JPEG, or WebP reference
images to a Wish. The host validates each file, binds it by size and SHA-256 in
`WISH.json`, materializes it read-only under `wish-references/`, re-verifies it
at every checkpoint, lists it in every `STAGE.json`, and ships its bytes in the
public toy archive only when the exact Wish wording is disclosed.
