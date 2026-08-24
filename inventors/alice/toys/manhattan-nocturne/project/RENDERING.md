# Exact CAD previews

`render_product.py` turns the colored native GLB into deterministic review
images. It uses the exported triangles, occurrence transforms, node labels,
and GLB material colors. It does not use the mood image and does not generate
or alter geometry.

Generate the GLB with the same Python interpreter used for the CAD skill, then
render it with the local Python that provides NumPy, Pillow, and trimesh:

```sh
PROJECT="inventors/alice/toys/manhattan-nocturne/project"

$CAD_PY skills/cad/scripts/export \
  "$PROJECT/manhattan_nocturne.step.py" \
  --glb "$PWD/$PROJECT/exports/manhattan-nocturne.glb"

python3 "$PROJECT/render_product.py" \
  --input "$PROJECT/exports/manhattan-nocturne.glb" \
  --out "$PROJECT/product-media/cad-preview"
```

The renderer freezes nineteen review recipes in seven groups:

1. mirrored raw Stone and Steel hero views;
2. raw top, both raw obliques, and a south-border board crop;
3. one clearly marked depth-edge board diagnostic plus a raw top inventory;
4. front, rear, and top neutral lineups of all twelve side/rank variants;
5. front, rear, and upper-body-only neutral side-code comparisons for all six roles;
6. neutral Manhattan identity, raw engineering, and clearly marked depth diagnostic views; and
7. neutral full-start recognition from both player seats.

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
- explicit `concept_art: false`, `physical_print: false`, and
  `printability_proof: false` boundaries, plus whether the view is eligible as
  a product beauty render.

Review layouts apply only rigid transforms to the exact source triangles. The
receipts state the selection and placement recipe; the renderer never generates
or edits product geometry.

The images belong under `project/product-media/cad-preview/`. Mood and visual
target imagery remains under `art-direction/`; neither may be presented as a
photograph or physical manufacturing evidence.
