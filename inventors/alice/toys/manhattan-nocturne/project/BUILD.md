# Build, validate, render, and slice

Run from the repository root. The CAD interpreter is the local Python 3.12
environment with the pinned `skills/cad/requirements.txt` installed.

```sh
CAD_PY="$PWD/.venv-cad/bin/python"
PROJECT="inventors/alice/toys/manhattan-nocturne/project"
```

## 1. Open one bounded CAD run

```sh
"$CAD_PY" skills/cad/scripts/with_budget \
  --start --total 30m --label manhattan-nocturne
```

## 2. Quick combined preview

```sh
"$CAD_PY" skills/cad/scripts/with_budget --step 8m -- \
  "$CAD_PY" skills/cad/scripts/verify_project "$PROJECT" \
  --quick --fresh --preview-tolerance 0.1
```

## 3. Final STEP/STL/GLB and geometry gate

```sh
"$CAD_PY" skills/cad/scripts/with_budget --step 20m -- \
  "$CAD_PY" skills/cad/scripts/verify_project "$PROJECT" \
  --fresh --exports --strict-fit --bed 256x256x256 --verbose
```

This verifies the layout, generates the combined assembly and every part entry
in one request, writes STEP, validates every B-rep, checks assembly interference,
runs the project fit/parameter audit, exports GLB/STL, and validates each mesh.
Project-specific inventory, dimensions, placement, stability proxies, and
quantity-aware bed packing still run separately through `measure/check_fit.py`.

## 4. Verify the real finish contract

```sh
"$CAD_PY" "$PROJECT/validation/check_finish.py"
```

This read-only gate hashes all 27 canonical STEP/STL artifacts, verifies the
continuous midnight base ends at Z8.20, proves that only 32 isolated light pads
continue to Z9.00, and requires warm brass/gold above that boundary. It accepts
one BOARD-only layer-height material change or one masked post-print top
finish. It does not claim that either method has been physically executed.

No shallow texture is added: the exact bevel provides light response and each
25.0 mm top remains a flat landing for a D22.5 piece base.

## 5. Exact-CAD previews

```sh
"$CAD_PY" skills/cad/scripts/export \
  "$PROJECT/manhattan_nocturne.step.py" \
  --glb "$PWD/$PROJECT/exports/manhattan-nocturne.glb"

python3 "$PROJECT/render_product.py" \
  --input "$PROJECT/exports/manhattan-nocturne.glb" \
  --out "$PROJECT/product-media/cad-preview" \
  --width 1600 --height 900 --supersample 2
```

Every preview is derived from the exact colored CAD assembly and carries a
receipt. Mood art under `../art-direction/` is never substituted for this gate.

## 6. OrcaSlicer 2.3.2

Use the official OrcaSlicer 2.3.2 CLI. The exact three P2S profiles are copied
under `validation/orca-profiles/` and must remain content-hashed.

```sh
ORCASLICER_CLI="${ORCASLICER_CLI:?point to OrcaSlicer 2.3.2}"

"$CAD_PY" "$PROJECT/validation/slice_product.py" \
  --orca "$ORCASLICER_CLI" \
  --cad-python "$CAD_PY"
```

The product-specific runner exports all thirteen unique STL files at the pinned
fine-mesh tolerances, checks every mesh, and runs the current CAD skill's
`check_thickness --nozzle 0.4` wall gate before slicing anything. It then
slices every unique entry and submits all 32 pieces together to prove that Orca
can arrange and slice the complete inventory on one P2S plate. It writes parsed
time, material, support, warning, profile, validation-tool, STL, wall-report,
and G-code hashes into `validation/slicer-receipt.json`. A CLI exit code without
parsed measurements is held, not passed. The large temporary G-code is hashed
for the receipt and discarded; it is reproducible from the sealed STL and
profiles.

## What this cannot prove

Digital validation and slicing do not prove a successful physical print,
surface finish, warp resistance, tactile feel, tipping behavior, durability, or
human delight. Those stay held for Deliver and later Reviews.
