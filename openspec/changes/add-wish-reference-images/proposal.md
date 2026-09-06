## Why

A Wish is text only. When the person already holds the decisive evidence as pictures (a HAER elevation sheet, a photo of the object to reconstruct, a sketch of the mechanism), the only way to hand it to a run today is to describe it in words and hope the agent finds the same file on the Internet. The Make skill set already reads images well (`image-to-cad` turns a reference into a tagged build spec and `check_likeness` scores a model's silhouette against it), but nothing carries a person's image into the run, binds it, or accounts for it in the public archive.

## What Changes

- **Wish contract.** `Wish` gains an optional ordered `references` list. Each entry names one image (`ref-NN-<slug>.<ext>`), its media type, byte size, pixel size, and SHA-256. An image-less Wish keeps byte-identical canonical JSON, so every existing Wish hash is unchanged.
- **CLI.** `workshop wish --ref IMAGE` (repeatable, up to eight) reads PNG, JPEG, or WebP files, validates them with Pillow without decoding pixels, names them in the order given, and hands the bytes to the host.
- **Run host.** The bytes are materialized read-only under `wish-references/` as immutable run inputs with their own byte budget, re-verified at every checkpoint against the declarations in `WISH.json`, marked read-only for the Codex and Grok sandboxes, and listed as `wish_references` in every `STAGE.json`.
- **Agent guidance.** The product-run constitution and the workflow skill tell the agent where the images are, that they are the primary visual evidence, and that `image-to-cad` is the way to read them.
- **Public archive.** `wish/wish.json` always lists reference metadata; the image bytes are written under `wish/references/` only when the exact Wish wording is disclosed.

## Non-goals

No image is generated, judged, or scored by the host. The reference is the person's input, not evidence: the Make gate still judges the real sealed mesh, and no reference reaches the Factory listing.

## Capabilities

### New Capabilities

- `workshop/wish-reference-images`: reference images attached to a Wish, bound and materialized by the host, disclosed with the Wish.

## Impact

- `src/workshop/wish/contracts.py`, new `src/workshop/wish/references.py`: contract and loader.
- `src/workshop/workflow/agent_run.py`, `native_run.py`: materialization, budgets, verification, stage packet.
- `src/workshop/runtime/codex.py`, `grok.py`: read-only sandbox rules.
- `src/cli/main.py`: `--ref`.
- `src/workshop/release/public_archive.py`: metadata and gated bytes.
- `.agents/product-run/AGENTS.md`, workflow skill `references/wish-match.md`: agent guidance.
