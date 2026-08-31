# Make

Consumes the exact sealed Invent result and owns mechanical and 3D creation,
CAD verification, maker provenance, Make contracts, and the Workshop's single
locked skill tree in `skills/`.

For new marked Forge and Quest runs, Make also receives the exact sealed
Concept and sanitized image-effect identity. Schema-v2 `Made` binds both,
requires product component keys to equal the Concept brief, and rejects any
product-tree file whose bytes copy a Concept image. Spark and frozen unmarked
runs retain schema-v1 behavior. Concept imagery is design context, never CAD,
Playtest, Factory, manufacture, or delivery evidence.

Public API: `workshop.make`.

Reusable Codex-native creation capabilities live once in `skills/`. The host
materializes their exact locked bytes into each private product run; Inventors
use those shared capabilities without copying or wrapping them in Python.

The `cad`, `design-reference`, `electromechanical-integration`,
`image-to-cad`, and `step-parts` skills are reviewed snapshots of
`autonomous-ai/autonomous-product-to-cad`. `LOCK.json` binds
their canonical trees to an exact upstream revision, while `PROVENANCE.md`
records local path adaptations and the distinct license status of each
upstream tree.

The locked MVP geometry vocabulary is 2–12 printable boxes or vertical
cylinders. Every part declares `top_grooves_mm`; cylinders leave it empty, while
boxes may use up to eight non-overlapping, full-local-Y subtractive top grooves
for design-required integral tactile seams. Groove center and width run along
local X; each cut retains at least 0.8 mm at both X edges and below its floor,
preserving the part's external bounds.
