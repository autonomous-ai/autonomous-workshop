# Millbind — build brief

A hexagonal yard bristling with 37 pins carries real, physically meshing
gears at two tooth heights. One crank drives whatever it can reach; four
millstones try to end up turning clockwise; an odd loop of gears physically
jams by hand, which is the game's own legality test. Everything below is a
translation of `idea.json`'s numbers into printable millimetres — see
`brief.json`'s `unstated_in_spec` for every place idea.json didn't give a
number and I had to choose one.

## Parts

**yard_board** (board, 1x, single tile, 230 x 200 x 42mm) — the hexagonal
mill floor. 12mm slab + 30mm pin height stacked = 42mm overall. 37 pins
(8mm dia x 30mm tall) on a triangular lattice at exactly 30mm spacing —
centre, then rings of 6, 12 and 18 — because 30mm is also every gear's
pitch-circle diameter, so adjacent pins mesh correctly by construction.
yard_board OWNS the 8mm pin diameter and the 30mm pin spacing; nothing else
in the brief restates either number. The 18 outer-ring pins carry a 1.2mm
raised sill (the only pins a millstone or the crank may stand on); 1mm
plank ribs texture the floor between pins. Fits the P2S bed as one piece.

**gear_low** (loose piece, 14x, 35 x 35 x 10mm) — a squat toothed puck.
12 teeth on the shared 30mm pitch circle, teeth starting right at the
floor. 8.6mm bore, three lightening holes for grip. Engages only the
bottom 10mm of a 30mm pin — 20mm of bare pin stands exposed above it,
which is exactly the zone a neighbouring gear_high's teeth occupy.

**gear_high** (loose piece, 7x, 35 x 35 x 30mm) — the same tooth ring
carried at the top of a plain smooth column, so it reads as a lamppost:
teeth up, bare shaft below. Spans the full 30mm pin with no stub exposed.
Same 8.6mm bore as gear_low. Column diameter (16mm) is my own choice —
idea.json gives none.

**gear_tandem** (loose piece, 3x, 35 x 35 x 30mm) — a full barrel of teeth
the whole pin height, the only supply piece that meshes with both tiers
and can therefore weld — or seize — the two halves of the yard together.
Same 8.6mm bore.

**mill_gear_tri / _square / _penta / _hex** (loose piece, 1x each,
35 x 35 x 48mm) — a full-height barrel like gear_tandem, crowned by a
34mm/6mm furrowed grinding disc (1.2mm-deep radial furrows) and a prism
hub (tri/square/penta/hex flats, ~16mm across x 12mm tall) that is a
player's whole identity — read by counting flats, never by colour. Told
apart from each other by hub shape alone; everything else is identical.

**crank_gear** (loose piece, 1x, 46 x 35 x 55mm) — the only power in the
box. Full-height barrel, solid cap, an offset arm carrying a 14mm knurled
knob standing 22mm proud, and a 1.2mm raised direction arrow — the only
piece with an arm, and the only piece with a direction mark. The arm
should be modelled as a solid gusset from the barrel wall up to the
knob base (see print_plan) so it self-supports; there's also a real,
flagged tension between a graspable arm and a 30mm pin grid the crank
relocates on every round (see `unstated_in_spec`).

**grain_pellet** (loose piece, 28x, 15 x 15 x 5mm) — a smooth, untoothed
15mm-diameter domed washer with a 9mm hole, deliberately impossible to
mistake for a gear. Threads onto a sack_spindle.

**sack_spindle** (container, 1 per player / 4x, 40 x 40 x 70mm) — a 40mm
round base (8mm tall, my own figure) under an 8.5mm rod standing 62mm
tall. Capacity checks out against idea.json's own numbers exactly: 12
pellets x 5mm = 60mm, leaving the stated 2mm of rod clear for a thumbnail
pinch on the top pellet.

**granary_bin** (container, 1x, 70 x 50 x 25mm) — an open bin with a
thumb scallop and 1mm chevron relief on the front, holding the loose
grain_pellet supply within reach of every seat.

## Interfaces

- **Pin/bore, partial engagement** — gear_low's 8.6mm bore over
  yard_board's 8mm pin, engaging only the low gear's own 10mm body
  (0.3mm clearance per side). yard_board owns the pin diameter; every
  bore below derives from it.
- **Pin/bore, full engagement** — gear_high, gear_tandem, all four
  mill_gear variants and crank_gear all share the same 8.6mm bore, now
  engaging the pin's entire 30mm length. Same 0.3mm/side clearance,
  flagged as tighter than this pipeline's usual 0.4mm minimum but kept
  because both 8.6mm and 8mm are idea.json's own explicit figures — see
  the note on idea.json's own internal 8.6mm-vs-"0.5mm generous" mismatch
  in `unstated_in_spec`. Every one of these pieces is lifted and
  relocated repeatedly during play, so this is a working slip joint, not
  a one-time press fit.
- **Tooth-to-tooth mesh** — the mechanism the whole game runs on. Every
  gear shares one 12-tooth/30mm-pitch/~35mm-OD profile, and yard_board's
  30mm pin spacing exactly equals that pitch circle, so any two pieces on
  adjacent pins mesh correctly by construction. Same-tier pieces
  (low-low, high-high) mesh; any full-height piece meshes with anything
  neighbouring it regardless of tier. Backlash (0.4mm total, 0.2mm per
  flank) is my own figure — idea.json only asks for "generous backlash."
- **Rod/hole, threaded stack** — grain_pellet's 9mm hole over
  sack_spindle's 8.5mm rod (0.25mm/side, both idea.json's own stated
  figures, flagged as tight but kept as stated).
- **Stack** — up to 12 grain_pellet stack on one rod. The rod's own 8.5mm
  shaft running through every pellet is what keeps the stack from
  toppling, regardless of the stack's own height-to-base ratio.

## Print plan

Everything prints without supports. yard_board prints floor-down, pins
and reliefs building straight up from the top face. Every gear, millstone
and the crank print axis-vertical, barrel-bottom down — their natural
table-resting orientation is identical to their mounted orientation on a
pin, so nothing needs reorienting between "sits on the table" and "sits
on a pin." The one detail that needs deliberate routing: crank_gear's
offset arm should be modelled as a solid gusset from the barrel wall up
to the knob base, not a thin free-floating bar, so it self-supports.
grain_pellet, sack_spindle and granary_bin are all straightforward
flat/vertical prints.

Use `add_piece_family` for every multi-copy family (14x gear_low, 7x
gear_high, 3x gear_tandem, 28x grain_pellet, 4x sack_spindle) — each copy
must land as a separately named assembly child. Generate yard_board's
37-point triangular lattice once (via `shared_positions` or an equivalent
hand-rolled generator) and reuse it for the pins, the 18 sill rings, and
the plank-rib layout — never regenerate that trig twice. `seated_pair`
doesn't apply directly (it targets press-fit pockets, not a repeatedly
lifted rotating bore-over-post), but every bore here follows its
discipline anyway: yard_board owns the pin diameter and spacing, every
other part's bore derives its clearance from those two numbers alone.

No part exceeds the 246 x 246 x 251mm P2S bed; yard_board (the largest
footprint at 230 x 200mm) is a single tile, and no `joins`/tiling is
needed anywhere in this brief.

## Gate

`ergonomics_check.py board-game/ideas/millbind/brief.json` — **ERGO PASS,
0 findings.**
