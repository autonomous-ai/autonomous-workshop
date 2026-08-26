# Exact CAD previews

`render_product.py` turns the exact native GLB into deterministic review
images. It uses the exported triangles, occurrence transforms, node labels,
and source materials. Production-finish views recolor board triangles above the
exact Z8.20 boundary warm brass/gold and keep everything at or below it
midnight, matching `validation/finish-plan.json`. This display operation changes
no triangle, transform, or bound. It does not use the mood image and does not
claim that the finish has been physically executed.

The native GLB is Y-up and stores CAD coordinates as `(X, Z, -Y)`. The renderer
restores them exactly as `(GLB X, -GLB Z, GLB Y)` before any camera or review
transform. Its self-check also projects the canonical corner centers: Stone is
south/−Y with h1/light on screen-right, and Steel is north/+Y with a8/light on
screen-right. Every receipt records this right-handed coordinate contract.

Generate the GLB with the same Python interpreter used for the CAD skill, then
render it with the local Python that provides NumPy, Pillow, and trimesh:

```sh
PROJECT="inventors/alice/toys/manhattan-nocturne/project"

$CAD_PY src/workshop/make/skills/cad/scripts/export \
  "$PROJECT/manhattan_nocturne.step.py" \
  --glb "$PWD/$PROJECT/exports/manhattan-nocturne.glb"

python3 "$PROJECT/render_product.py" \
  --input "$PROJECT/exports/manhattan-nocturne.glb" \
  --out "$PROJECT/product-media/cad-preview"
```

The renderer freezes nineteen review recipes in seven groups:

1. mirrored Stone and Steel hero views with the required production finish;
2. production-finish top, both player obliques, and a south-border board crop;
3. one clearly marked depth-edge board diagnostic plus a raw top inventory;
4. front, rear, and top neutral lineups of all twelve side/rank variants;
5. front, rear, and upper-body-only neutral side-code comparisons for all six roles;
6. neutral Manhattan identity on the finished board, one raw one-material
   engineering view, and one clearly marked depth diagnostic; and
7. neutral full-start recognition on the finished board from both player seats.

Every camera direction is a frozen literal vector. Acceptance views never use
synthetic depth edges; the two diagnostic filenames and receipts say
`diagnostic` and are ineligible as beauty or acceptance evidence. Neutral views
replace only the display material, preserve exact triangles and source-material
hashes, and contain no rank or side labels that leak the expected answer to a
Player. Review layouts apply only rigid transforms and never claim packing or
assembly.

Every PNG has a sibling `.render.json` receipt containing:

- the exact GLB and renderer hashes;
- all selected node labels, original GLB transforms, deterministic review
  transforms, source/display material colors, and source/display bounds;
- a hash for every node record and one hash sealing the ordered scene-node set;
- the resolved camera, projection, output size, and triangle counts;
- any semantic-camera fallback warnings; and
- whether the exact Z8.20 production-finish display was applied, including the
  source-material hash, classified face counts, finish colors, and an explicit
  `geometry_changed: false`; and
- explicit `concept_art: false`, `physical_print: false`, and
  `printability_proof: false` boundaries, plus
  `physical_finish_execution_verified: false` and whether the view is eligible
  as a product beauty render.

Review layouts apply only rigid transforms to the exact source triangles. The
receipts state the selection and placement recipe; the renderer never generates
or edits product geometry.

Board parity is evaluated in the required production finish because that finish
is part of the product. `06b-board-inventory-engineering-raw.png` deliberately
retains the source one-material board for geometry audit; it is not allowed to
substitute for the finished-board usability views. The two depth diagnostics
remain ineligible for beauty or acceptance evidence.

The images belong under `project/product-media/cad-preview/`. Mood and visual
target imagery remains under `art-direction/`; neither may be presented as a
photograph or physical manufacturing evidence.
