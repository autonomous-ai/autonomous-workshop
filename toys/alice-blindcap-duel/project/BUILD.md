# Build, slice, review, and prepare the private draft

These commands are the release path for this frozen project. Run them from the repository root with `uv` available on `PATH`. The coupon is mandatory, all production and coupon STLs must pass the real OrcaSlicer gate, and `physical_fit_verified` remains `false` until the printed coupon is tested. Generated production meshes, STEP files, slicer sidecars, and intermediate renders remain ignored; only the two canonical review covers and six curated `product-media` images are tracked.

## 1. Generate the first-print coupon set

```sh
UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/uv-cache}" \
uv run --offline --no-project \
  --with 'cadquery<2.8' --with trimesh --with pygltflib \
  --with numpy --with manifold3d --with pillow --with matplotlib \
  --with networkx \
  python board-game/ideas/blindcap-duel/project/fit_coupons.py \
  --out board-game/ideas/blindcap-duel/project/coupons
```

The exact coupon inventory is nine printable STL/STEP pairs, two STEP reference assemblies, and `validation.json`. Print the socket, all four species, both owner probes, and the male/female dovetail pair before the production set.

## 2. Run the full candidate gate with OrcaSlicer

Slicing is mandatory. The three frozen profiles are part of the gate fingerprint.

```sh
ORCASLICER_CLI="${ORCASLICER_CLI:?Set ORCASLICER_CLI to the OrcaSlicer CLI executable}" \
ORCA_PROFILE="$PWD/board-game/ideas/blindcap-duel/project/validation/orca-profiles/p2s-machine-standard.json;$PWD/board-game/ideas/blindcap-duel/project/validation/orca-profiles/p2s-process-standard.json;$PWD/board-game/ideas/blindcap-duel/project/validation/orca-profiles/pla-basic-standard.json" \
UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/uv-cache}" \
uv run --offline --no-project \
  --with 'cadquery<2.8' --with trimesh --with pygltflib \
  --with numpy --with manifold3d --with pillow --with matplotlib \
  --with networkx \
  python board-game/tools/gate.py \
  board-game/ideas/blindcap-duel/project \
  --bill board-game/ideas/blindcap-duel/project/bill.json \
  --brief board-game/ideas/blindcap-duel/project/brief.json \
  --promote-package-artifacts
```

Stop unless `project/gate.json` reports `pass: true`, empty `fails` and `unmeasured`, 28 placed/expected production occurrences, clean swept interference, 15 exact family STEP files, 28 exact occurrence STL files, all production and coupon slices clean, and complete source/CAD/bill/motion/brief/slicer/profile hashes.

## 3. Review the fresh build and install only the two canonical covers

Render from the sidecar produced by that gate, not from an older root export:

```sh
UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/uv-cache}" \
uv run --offline --no-project \
  --with 'cadquery<2.8' --with trimesh --with pygltflib \
  --with numpy --with manifold3d --with pillow --with matplotlib \
  --with networkx \
  python cadcode/scripts/review \
  board-game/ideas/blindcap-duel/project/build \
  --stem blindcap-duel
```

Visually inspect the generated review sidecar. Then place exactly these two files in `project/blindcap-duel_review/` and no others:

```sh
mkdir -p board-game/ideas/blindcap-duel/project/blindcap-duel_review
cp board-game/ideas/blindcap-duel/project/build/blindcap-duel_review/_assembled.png \
  board-game/ideas/blindcap-duel/project/blindcap-duel_review/_assembled.png
cp board-game/ideas/blindcap-duel/project/build/blindcap-duel_review/_qa.png \
  board-game/ideas/blindcap-duel/project/blindcap-duel_review/_qa.png
```

The importer requires `_assembled.png` at 900 × 900 and the native final renderer output `_qa.png` at 2251 × 2270. Do not copy per-part or section renders into the canonical review directory or crop/resave either reviewed image.

## 4. Run the final integrity gate, then freeze

Repeat the full OrcaSlicer command from step 2 after the canonical covers and all text/media are final. This second clean pass is the release gate. After it passes, do not edit, regenerate, reformat, or copy anything inside `project/`; any change invalidates the bound evidence and requires another final gate.

## 5. Prepare the deterministic private-draft archive offline

Run only after the final gate and freeze:

```sh
python3 board-game/tools/import_private_draft.py prepare \
  --project board-game/ideas/blindcap-duel/project \
  --page-manifest board-game/ideas/blindcap-duel/content/factory-page.json \
  --title 'Blindcap: Duel' \
  --prompt 'Invent Blindcap: Duel: an original two-player physical deduction game where mushroom pieces share a species-neutral silhouette but carry visible owner marks, passive printed tunnel codes reveal public high/low clues through probes, and players crown connected groves before harvest.' \
  --output "${TMPDIR:-/tmp}/blindcap-duel.factory.zip"
```

Record the printed ZIP SHA-256. Preparation is offline and does not create a Factory record. The separate one-shot `import` command is only for Blindcap's first private draft; public publication remains a manual human action.

After the `blindcap-duel` design exists, every improvement must update that exact design and current history. Never run another create/import operation for Blindcap, never accept a different slug or design ID, and never retry an ambiguous revision write. Reconcile the existing design first; if an exact idempotent private-revision path is unavailable, hold the improvement locally instead of creating a duplicate game.

## Physical acceptance before any public listing

Low (3.0mm proud) and high (about 28mm; 27.628906mm digital reference) must be obvious from both seats. The two parallel routes must not cross-talk. Every D-keyed variant must insert and lift without damaging force. At harvest, record the four public tiebreak counts, withdraw every probe completely to 34mm proud, then lift and invert each mushroom cap-down in its original cell. Digital checks and clean slices do not substitute for this test.
