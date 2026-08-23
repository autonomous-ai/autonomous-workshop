# Deep Claim — draft CAD spec

One carved-stone slab (`assay_board`) with six two-stage assay bores, plus
eight puck variants (four owner marks x {broad, slim}), 3 of each = 24 loose
pucks. See `board-game/ideas/deep-claim/brief.json` / `brief.md` for the
authoritative numbers; this file only tracks the draft's modeling choices.

## assay_board

Round slab, 190mm diameter x 34mm thick, centered on Z (top face at
+17mm, bottom at -17mm so the board's own frame is symmetric). Six bores on
a 62mm-radius ring, evenly spaced 60deg apart. Each bore is cut with a single
axisymmetric revolve profile (`features/bore.py:bore_cutter`) so the shelf,
throat, and floor chamber, plus the shelf's lead-in chamfer, are one
watertight cut per bore rather than three separately-booleaned cylinders:

  top (r=0) -> chamfer flat (shelf_r+chamfer) -> down chamfer to shelf_r
  -> down to shelf floor -> step in to throat_r -> down to throat floor
  -> step out to floor_r -> down to closed floor bottom -> back to axis

Surface treatment: six radial vein-relief grooves (1mm deep) cut between
the bores; a 0.8mm-deep witness collar ring cut around each bore's rim
(`features/vein.py`, `features/collar.py`).

## disc_large / disc_small

Simple cylinders (28x9mm broad, 14x8mm slim) with 3/4/5/6 raised pyramid
studs (loft from a square base to a near-point) arranged in a small circle
on the top face, one stud ring radius for large pucks and a smaller one for
slim pucks so the studs never crowd the piece's edge.

## Demo / hero state

`assemblies/product.py` seats a representative subset of pucks in the
bores (three broad pucks catching shelves, two slim pucks resting on open
floors, one bore left empty) so the assembled render matches idea.json's own
`hero_shot` prose, and lays every remaining puck out in four owner clusters
around the board so all 24 loose pucks are visible and separately named.
