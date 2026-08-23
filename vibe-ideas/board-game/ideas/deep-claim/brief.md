# Deep Claim — build brief

One part family, nine named parts: a single carved stone slab (`assay_board`)
and eight puck variants (4 owner marks x {large, small}). No tiling — the
slab is 190 x 190 x 34mm, comfortably under the 246 x 246 x 251mm bed.

## Parts

### `assay_board` (qty 1, board, 190mm diameter x 34mm thick)

A round slab, six identical two-stage bores drilled on a ring at 62mm radius
from the board center, evenly spaced every 60deg. Adjacent bore centers are
62mm apart; adjacent shelf rims (34mm diameter each) leave 28mm of solid
stone between them — plenty of structural margin.

Each bore, top to bottom:

| Stage | Diameter | Depth |
|---|---|---|
| Shelf chamber | 34mm | 6mm |
| Throat | 18mm | 4mm |
| Floor chamber (closed bottom) | 22mm | 11mm |

Total bore depth 21mm, leaving 13mm of solid slab under every floor chamber
— sturdy, and comfortably clear of the 34mm total thickness.

Surface treatment: 1mm-deep radial vein relief lines between the six bores;
a 0.8mm-deep witness collar around each shelf rim so a plugged shelf reads
differently from an open one at a glance; a 1mm x 45deg chamfer on the shelf
rim itself (a printability addition, not in idea.json) so a puck doesn't
have to ride over a sharp printed edge going in.

Print flat, bottom face down, bore openings facing up. Every internal step
(shelf-to-throat, throat-to-floor) is a horizontal ring bridging over the
void beneath it, largest span 9mm radius at the throat-to-shelf transition —
a flat bridge, not an angled overhang, and well inside FDM bridging limits.
No supports anywhere on this part.

### `disc_large_mark{3,4,5,6}` (qty 3 each, loose_piece, 28mm dia x 9mm tall)

Broad puck. Drops into a bore's 34mm-diameter, 6mm-deep shelf chamber and
catches on the ledge where the chamber narrows to the 18mm throat — 28mm is
10mm bigger than the 18mm throat, so the catch is robust to print tolerance
in either direction. Seated, the puck sits 3mm **proud** of the slab's top
face (9mm tall in a 6mm-deep pocket). This also happens to be exactly what
idea.json's own hero shot describes ("pucks sitting proud at shelf level"),
so the depth number is firming up something the idea had already committed
to in prose, not inventing a new look.

Top face carries 3/4/5/6 raised pyramid studs (owner mark), 1.2mm proud —
identical across all four owner variants except stud count, so the four
marks are told apart by touch, not by size. All four share one shelf-seat
geometry on the board.

Print flat, stud face up, no supports.

### `disc_small_mark{3,4,5,6}` (qty 3 each, loose_piece, 14mm dia x 8mm tall)

Slim puck. Passes freely through a bore's 18mm-diameter, 4mm-deep throat
(2mm clearance per side) whenever that bore's shelf is still open, then
drops the rest of the way to rest on the closed floor chamber (22mm dia x
11mm deep). Seated, the puck's top face sits roughly 13mm below the slab's
top face, reachable only through the 18mm throat above it.

Top face carries 3/4/5/6 raised pyramid studs, 1.2mm proud, matching the
same-numbered `disc_large` owner. All four share one throat/floor-seat
geometry on the board.

Print flat, stud face up, no supports.

## Interfaces

Two `seats` interfaces, both against `assay_board`, one representative disc
per pair standing in for all four owner marks (identical bbox, differ only
by stud count):

1. **`disc_large_mark3` seats into `assay_board`** (shelf). The board owns
   the numbers: shelf diameter 34mm, shelf depth 6mm, throat diameter 18mm.
   `disc_large`'s 28mm diameter derives its fit from those — it must clear
   the shelf diameter (3mm clearance per side, well past the 0.4mm minimum
   drop-in clearance) and must NOT clear the throat diameter (28mm vs
   18mm, a 10mm margin, so the catch never depends on print tolerance).
   Depth (6mm) is sized so the 9mm-tall puck ends up 3mm proud of the rim —
   both graspable and matching the idea's own "sitting proud" language.

2. **`disc_small_mark3` seats into `assay_board`** (throat + floor). The
   board owns the throat diameter (18mm, the same number the first
   interface uses as its "must not fit" threshold) and the floor depth
   (11mm). `disc_small`'s 14mm diameter derives its fit from the throat
   (2mm clearance per side). This interface is deliberately **not** also
   declared as an `ergonomics_check` `recesses` entry: that check's
   retrieval formula assumes a single-depth pocket, and would compare the
   piece's height against the pocket depth and the pocket's own width for
   finger room. Here the real limiting aperture for a retrieving finger is
   the 18mm throat 2mm above the piece, not the 22mm floor chamber it
   actually sits in — and the only way to satisfy that formula's finger-room
   fallback would be to widen the throat past 38mm, which would also let a
   28mm `disc_large` fall straight through it, destroying the size gate the
   whole game is built on. No rule in idea.json ever asks a player to
   retrieve a seated piece mid-game, so this is being treated as an
   intentional one-way placement (see `unstated_in_spec`), not a gap that
   was quietly worked around.

Both interfaces are diameter-driven, not depth-driven: the deterministic
routing the idea calls for (broad catches, slim passes) depends only on
34mm-shelf > 28mm-disc_large > 18mm-throat > 14mm-disc_small, all four of
which are load-bearing numbers taken directly from idea.json unchanged. The
two depth numbers I did touch (shelf depth 6mm, and the throat depth 4mm I
had to invent outright) affect only how deep a piece sits, never which
piece can reach which chamber.

## Print plan

- `min_wall_mm`: 1.6
- Single tile for `assay_board` — 190mm diameter is well under the 246mm
  bed limit, no splitting needed.
- No supports anywhere: the board's internal bore steps are flat bridges,
  not angled overhangs, and both puck families print flat with their studs
  face-up.

## Unstated in spec

See `brief.json`'s `unstated_in_spec` array for the authoritative list; in
short:

1. Shelf depth cut from idea.json's approximate "~12mm" to 6mm — the
   original number left a 9mm-tall puck sitting 3mm *below* the rim of a
   34mm-wide pocket, which fails ergonomics_check's retrieval formula
   outright (under both the 2mm minimum-protrusion and 12mm finger-room
   thresholds). 6mm instead puts the puck 3mm *proud* of the rim, which is
   also literally what idea.json's hero shot already says happens.
2. Throat depth (4mm) — idea.json states the throat's diameter but never
   its depth. Chosen to read as a real constriction while keeping total
   bore depth (21mm) safely inside the 34mm slab.
3. No retrieval provision stated for a seated `disc_small` (13mm deep,
   behind an 18mm throat). Not invented — treated as an intentional
   one-way placement per the rules text, and flagged rather than silently
   dropped from the ergonomics check.
4. A 1mm x 45deg lead-in chamfer on the shelf rim, not in idea.json — pure
   printability, keeps a puck from catching a sharp printed edge going in.
