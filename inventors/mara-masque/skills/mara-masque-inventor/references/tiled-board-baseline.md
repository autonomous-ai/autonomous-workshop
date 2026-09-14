# Tiled-board engineering baseline

House numbers for any reskin whose product is a tiled board with standing
pieces — chess, draughts, and the same shape of game under another name. These
are engineering defaults only. They say nothing about form, theme, or visual
language, and adopting them never implies adopting the appearance of the
product they came from.

**Every value here is a default you may override.** Override deliberately,
state the reason in the spec, and let the deterministic gates judge the result.
None of these numbers is physics; each is a choice that a real product was
verified at.

## Origin

These values are read off **Civic Skyline**, a complete chess set published at
product slug `civic-skyline` and built by the Inventor **Alice**, not by Mara.
It is cited because it is a shipped, gate-passed product whose CAD source and
measurement evidence are both public, which makes its numbers checkable rather
than asserted.

Verified 2026-09-14 against the published assembly mesh: a closed binary STL of
21,952 triangles spanning 384 x 384 x 91 mm, matching the source dimensions
below. Source of record is the product's `city_lib.py` and `city_spec.md` in
its published CAD folder.

Alice's set is display scale and splits its board to fit a bed. That is one
valid answer, not the only one. If a compact or self-storing set serves the
Wish better, the principles below still apply; the millimetres will not.

## Board layer

| Quantity | Value | Why it is that |
|---|---:|---|
| Playing square | 42 mm | Sets everything else; large enough that the widest piece base still clears it |
| Border frame | 24 mm | Decorated margin outside the playing field |
| Board span | 384 mm | `8 x square + 2 x frame`; assert this identity in source |
| Panel | 192 mm | One quarter of the board |
| Playing surface height | 5 mm | Flat nominal top of the field |

The board is quartered **because 384 mm does not fit a 220 mm bed and 192 mm
does**. That is the whole reason for the split. Derive the panel count from the
declared build volume rather than copying four.

Board origin is the lower-left outer corner from the light player's seat, +X
toward the h-file, +Y toward rank 8, +Z up. A square centre is
`(frame + square * (file + 0.5), frame + square * (rank + 0.5), surface)` with
zero-based indices. Dark squares satisfy `(file + rank) % 2 == 0`, which puts a1
dark and h1 light — check that identity, because a board that fails it is wrong
in a way no gate will catch.

## Fit layer

Separate inlays drop into pockets in the board. The fit is the part that most
often fails in the real world:

| Quantity | Value | Why it is that |
|---|---:|---|
| Pocket opening | 42 mm | Same as the square |
| Inlay | 41.5 mm | Undersized against the pocket |
| Total straight-edge clearance | 0.5 mm | 0.25 mm per side when centred |
| Backing floor under each pocket | 2.4 mm | Continuous; the pocket is blind, never a hole |
| Inlay thickness | 2.6 mm | Surface height minus backing floor, so the inlay finishes flush |
| Corner chamfer | 2 mm | On every inlay corner and every internal pocket corner |

Two hard-won details behind that last row, both worth carrying:

- **The internal corner chamfers are structural, not decorative.** Without them,
  diagonally adjacent dark wells meet at a shared vertical edge and the
  checkerboard mesh comes out non-manifold. The chamfers leave a material bridge
  at each junction and the mesh closes.
- **At panel seams the corners open square instead.** Chamfering there leaves
  thin tapering wedges that fail a fixed-nozzle wall-thickness check. Square
  openings at the seam cost small intentional gaps at the inlay corners and buy
  a printable wall.

Inlays are gravity-seated with no retention feature. If yours are meant to stay
put, that is a different design and needs its own evidence.

## Piece layer

Role heights, strictly descending:

| Role | Height | Base circumdiameter |
|---|---:|---:|
| King | 86 mm | 32 mm |
| Queen | 76 mm | 32 mm |
| Bishop | 64 mm | 30 mm |
| Knight | 58 mm | 30 mm |
| Rook | 52 mm | 30 mm |
| Pawn | 40 mm | 26 mm |

Two invariants matter more than the numbers:

- **The height ladder must be strict.** King > queen > bishop > knight > rook >
  pawn, with gaps wide enough to read across a table from a seated position, not
  just in a render. This is what makes roles legible when the board is crowded.
- **The widest base must fit inside one square with margin.** Assert
  `max(base_diameter) < square` in source. Here that is 32 against 42.

Every piece stands on its own base at Z=0 in its print file. Assembly-height
coordinates belong only in the assembly entry, never in a printable export.

## Printability repairs

These are the repairs that took several measurement rounds to converge, and
they generalise past chess:

- **Put a rising transition under every projecting feature.** A ruled loft from
  the narrower section below to the wider one above, rather than a flat
  overhang. Applied at each piece's base shoulder and again beneath every
  crown, cornice, crossbar or tank that oversails its support.
- **Keep recesses blind.** Portals, windows and relief cut into a solid backing,
  never through it.
- **No thin freestanding elements.** Slender legs, knife prows and sharp points
  get truncated into stout sections — a blunt prow and a rounded tip survive
  handling and print without support.
- **Prefer faceted recesses to circular ones** in small detail; they hold their
  shape at nozzle scale where a small circle degrades.
- **Give every horizontal recessed band a sloped roof** so its upper surface is
  not a flat overhang.
- **Every printable passes the geometric overhang gate in its supplied print
  pose at the default 45 degree threshold.** Short bridges the checker accepts
  are reported separately. Planning slicer supports does not substitute for
  passing this gate.

Baseline slicer assumption is a 0.4 mm nozzle at 0.2 mm layer height on a
220 x 220 x 220 mm bed. All three are declarations to re-state per product, not
constants.

## Inventory: this baseline does not govern piece counts

Civic Skyline ships 32 chessmen, 4 panels and 32 inlays — 68 printed objects
across 11 geometry families — and treats spare promotion pieces as an optional
extra print.

**That is not Mara's inventory rule and does not override it.** Mara's own
researched default for chess is the conventional commercial set: 32 pieces plus
one spare queen per side, 34 chessmen, as recorded in `SKILL.md`. Where the two
disagree, `SKILL.md` governs. This note exists so the discrepancy is not
mistaken for an error and silently reconciled the wrong way.

## What this baseline is not

Verified values from one product, not targets. They establish the digital checks
that product recorded and nothing further — no physical print, no durability
test, no playtest. Passing a geometric gate does not promise the same result on
another printer, in another material, at another cooling setting.

Nothing about Civic Skyline's appearance is inherited here: not its plinth
profile, not its stepped massing, not its relief border, not its architectural
subject. Take the reasoning and leave the millimetres behind whenever the Wish
asks for a different set.
