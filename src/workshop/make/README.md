# Make

Consumes the exact sealed Invent result and owns mechanical and 3D creation,
CAD verification, maker provenance, Make contracts, and the Workshop's single
locked skill tree in `skills/`.

Public API: `workshop.make`.

Reusable Codex-native creation capabilities live once in `skills/`. The host
materializes their exact locked bytes into each private product run; Inventors
use those shared capabilities without copying or wrapping them in Python.

The `cad`, `design-reference`, `image-to-cad`, and `step-parts` skills are
reviewed snapshots of `autonomous-ai/autonomous-product-to-cad`. `LOCK.json` binds
their canonical trees to an exact upstream revision, while `PROVENANCE.md`
records local path adaptations and the distinct license status of each
upstream tree.

The locked MVP geometry vocabulary is 2–12 printable boxes or vertical
cylinders. Every part declares `top_grooves_mm`; cylinders leave it empty, while
boxes may use up to eight non-overlapping, full-local-Y subtractive top grooves
for design-required integral tactile seams. Groove center and width run along
local X; each cut retains at least 0.8 mm at both X edges and below its floor,
preserving the part's external bounds.
