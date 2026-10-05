# Make

Consumes the exact sealed Invent result and owns mechanical and 3D creation,
CAD verification, maker provenance, Make contracts, and the Workshop's single
locked skill tree in `skills/`.

Public API: `workshop.make`.

Reusable Codex-native creation capabilities live once in `skills/`. The host
materializes their exact locked bytes into each private product run; Inventors
use those shared capabilities without copying or wrapping them in Python.

The `cad`, `design-reference`, `electromechanical-integration`,
`image-to-cad`, `product-design`, `step-parts`, and `wiki` skills are reviewed
snapshots of `autonomous-ai/autonomous-product-to-cad`. `LOCK.json` binds
their canonical trees to an exact upstream revision, while `PROVENANCE.md`
records local path adaptations and the distinct license status of each
upstream tree.

`make-round` and `print-details` are authored in this repository and locked
under its URL. `print-details` is a library of printable decorative detail
(rivets, bosses, low domes, bands, rims, pipe ribs, inset panels, lancet
windows, grille slits, teardrop bores) and blunt free edges (`blunt_tip`,
`rib_end`) whose features refuse sizes below the wiki's print limits; its
`--self-check` runs the real `check_thickness` and `check_overhang` on every
feature. It tags each feature it makes, and the two gates name the tagged
feature nearest each failing region (issue #82, a Workshop-local change to
the vendored `cad` tree recorded in `PROVENANCE.md`).

The locked MVP geometry vocabulary is 2–12 printable boxes or vertical
cylinders. Every part declares `top_grooves_mm`; cylinders leave it empty, while
boxes may use up to eight non-overlapping, full-local-Y subtractive top grooves
for design-required integral tactile seams. Groove center and width run along
local X; each cut retains at least 0.8 mm at both X edges and below its floor,
preserving the part's external bounds.
