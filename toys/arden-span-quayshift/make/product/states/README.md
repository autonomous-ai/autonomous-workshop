# Exact state sources

These STEP states are generated from the same quayshift_lib.py assembly builder as the canonical assembly. No substitute geometry is used. Reproduction calls:

- layout1: assemble(0, (92,92))
- layout2: assemble(1, (60,92))
- layout3: assemble(2, (124,156))

The canonical assembly calls assemble(1) with the ferry at C1. All positions use the board coordinate system and the same floor datum. The state sheet compares three rebuilt towns from the complete delivered inventory. Ferry positions are on their verified paths.

The supplied render_product tool validates distinguishable exact states, but its rendering intentionally assigns two colors by face normals and does not preserve the authored material palette. Canonical color images therefore use render_review on each exact STEP, at the same isometric camera, with a simple three-panel composition. Its source is the exact state STEP, not an illustration. Source/STEP agreement is checked separately from appearance.
