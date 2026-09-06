## 1. Contract and loader

- [x] 1.1 Add `WishReference` and the optional ordered `Wish.references` list with name, media-type, size, pixel, count, and total-byte limits; an empty list is omitted from the canonical document so existing Wish hashes are unchanged. Tests in `tests/wish/test_contracts.py`.
- [x] 1.2 Add `workshop.wish.references.load_wish_references` (Pillow header read only, PNG/JPEG/WebP, no animation, duplicate and size rejection, `ref-NN-<slug>` naming). Tests in `tests/wish/test_references.py`.

## 2. Run host

- [x] 2.1 `AgentRun.create` accepts `wish_reference_files`, requires them to match the Wish exactly, materializes them read-only under `wish-references/`, locks the directory, and budgets them separately from constitution and skill bytes.
- [x] 2.2 Every checkpoint re-verifies that the declared references are present with their exact bytes and that nothing undeclared sits under `wish-references/`.
- [x] 2.3 `start_native_run` passes the bytes through; `STAGE.json` lists `wish_references` when present. Codex and Grok treat the directory as read-only.

## 3. CLI, archive, guidance

- [x] 3.1 `workshop wish --ref IMAGE` (repeatable) and a "References:" banner line; a bad file fails before any workspace exists.
- [x] 3.2 The public archive lists reference metadata always and writes `wish/references/<name>` only with exact Wish disclosure.
- [x] 3.3 Constitution and `wish-match.md` guidance; docs and `changes/wish-reference-images.added.md`.
