# Make

Owns mechanical and 3D creation, CAD verification, maker provenance, Make
contracts, and the Workshop's single locked skill tree in `skills/`.

Public API: `workshop.make`.

Make declares its replaceable model, CAD build, verification, and evaluation
ports in `workshop.make.ports`; integration packages only implement or
compatibly re-export them.

The locked MVP geometry vocabulary is 2–12 printable boxes or vertical
cylinders. Every part declares `top_grooves_mm`; cylinders leave it empty, while
boxes may use up to eight non-overlapping, full-local-Y subtractive top grooves
for concept-required integral tactile seams. Groove center and width run along
local X; each cut retains at least 0.8 mm at both X edges and below its floor,
preserving the part's external bounds.
