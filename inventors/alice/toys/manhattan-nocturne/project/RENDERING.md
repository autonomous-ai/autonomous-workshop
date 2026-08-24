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

The initial renderer freezes three views: a low three-quarter hero from each
army and an orthographic inventory view. Hero cameras resolve the army side
from node labels containing `stone` or `steel`; if those labels are absent the
renderer records a warning and uses the frozen fallback camera.

Every PNG has a sibling `.render.json` receipt containing:

- the exact GLB and renderer hashes;
- all selected node labels, transforms, material colors, and bounds;
- the resolved camera, projection, output size, and triangle counts;
- any semantic-camera fallback warnings; and
- explicit `concept_art: false`, `physical_print: false`, and
  `printability_proof: false` boundaries.

The images belong under `project/product-media/cad-preview/`. Mood and visual
target imagery remains under `art-direction/`; neither may be presented as a
photograph or physical manufacturing evidence.
