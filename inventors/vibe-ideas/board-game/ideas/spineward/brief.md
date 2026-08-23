# Spineward — build brief

A reef of 37 hexagonal pans carries up to four domed urchin shells, each a
ring of six identical sockets that a player fills with spines (movement,
reach, defence) or pearls (cargo) in any mix they like. One socket size
(6.6mm) serves both piece families; one hex-dish size seats any shell in any
of six orientations. Everything below is a translation of `idea.json`'s
numbers into printable millimetres — see `brief.json`'s `unstated_in_spec`
for every place idea.json didn't give a combinable number and I had to
choose one, and the interface notes for two tight-but-explicit tolerances I
kept rather than loosened.

## Parts

**reef_board** (board, 1x, single tile, 238 x 206 x 14mm) — the reef floor.
238mm is idea.json's own "~238mm across the flats" figure, but I read it as
the board's overall **corner-to-corner** span, not the literal flat-to-flat
distance the phrase names — that's the only reading that matches the
board's own pitch/ring geometry (34mm pitch x 3 rings + a pan's own 17.3mm
circumradius ≈ 238.6mm) and keeps idea.json's own "fits the P2S bed in one
piece" claim true (the literal flat-to-flat reading implies a 274.8mm
corner-to-corner that fails the bed at every rotation). 206mm is my derived
flat-to-flat (238 x √3/2). 37 hexagonal pans on a triangular lattice at
34mm pitch — centre, then rings of 6, 12, 18 (1+6+12+18=37) — reef_board
OWNS the 34mm pitch and the 30mm pan width; nothing else restates either.
Every pan is a 30mm-across-flats, 3mm-deep dish (1.2mm ripple floor) that
seats any urchin_shell's 29mm hex footprint at 0.5mm clearance per side,
indexed to one of six orientations, plus a 6.6mm/10mm-deep centre socket
for a pearl's shaft only (peg-only engagement — see Interfaces, not a
`recesses` seat). 19 inner pans carry a 1.2mm seed collar; the 6 outer
corner pans carry a 1.5mm landing barnacle cluster.

**urchin_shell** (loose piece, 4x / 1 per player, 29 x 29 x 34mm) — a domed
hex carapace, 29mm across the flats, 1.2mm radial dome grooves. Six
6.6mm/12mm-deep sockets on an 11mm radius, one per face — a leg, arm and
shield in whichever direction it's plugged, or a cargo slot if it holds a
pearl instead. Total height (34mm) is my own additive reading of two
figures idea.json gives separately (18mm dome + 16mm knob rise). The grip
knob's 3/4/5/6-flat prism is a player's mark for the game.

**spine** (loose piece, 24x common supply, 11 x 11 x 32mm) — a 6mm/12mm
peg fully buried flush in a shell socket, topped by an 11mm-thick wedge
quill standing 20mm proud. 32mm total height reconciles three figures
idea.json gives that don't sum on their own (12mm peg + 13mm blade ≠ 20mm
proud) — see `unstated_in_spec`. Stands vertical in its socket; the socket's
own position near one of the shell's six faces is what "points at" a
neighbour, not an angled blade.

**pearl_one_ring / pearl_two_ring / pearl_three_ring** (loose piece, 8x /
5x / 3x, 16 x 16 x 27mm each) — a 16mm knob (11mm tall) on a 6mm/16mm
shaft, identical across all three grades everywhere but the flat foot of
the shaft, which carries one, two or three 1.2mm raised rings — the only
marking in the game, and only readable foot-up in a pearl_rack.

**pearl_rack** (container, 4x / 1 per player, 135 x 34 x 22mm) — six
17mm/9mm-deep wells with a thumb scallop (a direct `cut_wells` match),
each seating any pearl grade knob-down at 0.5mm clearance, its ringed foot
finally standing proud and readable. One end carries a prism finial
matching that seat's urchin_shell knob. Six wells is a hard capacity.

**tide_pot** (container, 1x, 150 x 150 x 95mm) — a blind drum (85mm x
95mm) for the setup shake-and-blind-draw, with an open scalloped tray
(~150mm across) around its foot holding the loose spine supply. bbox uses
the tray's own width (widest feature) and the drum's own height (tallest
feature) directly.

## Interfaces

- **Seats** — urchin_shell into reef_board: 30mm hex dish over a 29mm hex
  shell, 0.5mm clearance per side, exact from idea.json's own two figures.
  Six-fold hex symmetry is what makes the TURN action (lift clear, rotate,
  reseat) work structurally.
- **Joins** — spine's 6mm/12mm peg into a shell's 6.6mm/12mm socket, full
  engagement, flush. 0.3mm/side clearance — tighter than this pipeline's
  usual 0.4mm minimum, but both numbers are idea.json's own explicit
  figures, kept as stated (flagged, not loosened).
- **Joins** — a pearl's 6mm/16mm shaft into the SAME 6.6mm/12mm shell
  socket (one bore serves both piece families by design), partial
  engagement, 4mm of shaft exposed above the socket mouth before the knob.
- **Joins** — a pearl's shaft into reef_board's 6.6mm/10mm pan-centre
  socket, partial engagement, 6mm of shaft exposed. Same flagged 0.3mm/side
  clearance.
- **Seats** — any pearl into a pearl_rack well: 17mm well over a 16mm
  knob, 0.5mm clearance, exact from idea.json's own figures. The only
  genuine "whole piece drops into a pocket" seat for a pearl anywhere in
  the brief — every other pearl engagement is shaft-only.

## Print plan

reef_board prints floor-down — pan dishes, sockets, and all three relief
features are top-face cuts, no supports. Its 37-point hex-radial lattice
needs a hand-rolled generator (`shared_positions` is rectangular-only) but
follows the same discipline: generate once, reuse for the dish cuts, the
socket cuts, and the relief overlays. urchin_shell prints socket-openings
up, no supports. spine prints peg-down, self-supporting. Every pearl grade
prints knob-down or knob-up, axisymmetric, ring relief cut into the flat
foot. pearl_rack is a direct `cut_wells` case (thumb scallop on by
default) — one call, four racks, finial swapped per seat. tide_pot prints
foot-down, tray flaring outward from the same print, no supports.

Use `add_piece_family` for every multi-copy family: 4x urchin_shell, 24x
spine, 8x pearl_one_ring, 5x pearl_two_ring, 3x pearl_three_ring, 4x
pearl_rack — each copy a separately named assembly child. `seated_pair`
doesn't apply directly to the peg/socket joints (idea.json states both
halves — 6mm nominal and 6.6mm socket — explicitly and independently
rather than one deriving from the other), but its discipline holds
everywhere else: reef_board owns the one true `recesses` dimension (the
30mm dish), and every other number in this brief derives from, or is
checked directly against, an explicitly-stated pair.

No part exceeds the 246 x 246 x 251mm P2S bed once reef_board is read
corner-to-corner (238 x 206 x 14mm — see `unstated_in_spec`); single tile,
no `joins`/dovetailing needed anywhere in this brief.

## Gate

`ergonomics_check.py board-game/ideas/spineward/brief.json` — **ERGO PASS,
0 findings.**
