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

The renderer freezes seven review views:

1. low three-quarter hero from the Stone side;
2. matching hero from the Steel side;
3. orthographic starting inventory and exact square-depth proof;
4. all six rank families from both sides in one neutral-material lineup;
5. a neutral side-coding macro comparing bishops and queens;
6. a clean board plus one of every canonical side/rank variant; and
7. the complete starting position under one neutral review material.

Hero cameras resolve the army side from node labels containing `stone` or
`steel`; if those labels are absent the renderer records a warning and uses the
frozen fallback camera.

Views 4, 5, and 7 are recognition evidence inputs, not product beauty renders.
They intentionally replace the display material with one neutral gray while
preserving the exact GLB material in the receipt. They contain no rank or side
labels that would leak the expected answer to a Player. View 6 is an
engineering review layout. It repositions one exact occurrence of each
canonical piece beside the exact board; it is not a packing or assembly claim.

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
