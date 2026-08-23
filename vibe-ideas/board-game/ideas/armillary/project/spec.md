# Armillary — draft build spec

Source of truth: `board-game/ideas/armillary/idea.json` + `brief.json` +
`brief.md`. This file is a short pointer, not a restatement.

A bronze-instrument press-your-luck game: a drum plinth (`plinth_ring`) holds
ten face-down tile wells on an 80mm-radius ring; three flush-stacked rotating
discs (`mask_disc_a/b/c`) mask the wells with six windows each, so only wells
where all three windows align are reachable. Tiles (`star_tile` / `moon_tile`
/ `void_tile`) are geometrically IDENTICAL round pucks with a knurled back
knob — only the 1.2mm face relief (star / crescent / eclipse) differs, and it
faces DOWN into the well, unreadable from any angle. A `reserve_column`
obelisk stores the spare stack; four `score_rail` bars (one per seat) catch
banked tiles standing on edge.

## Draft-mode scope

Fast, visually honest geometry: every bill component present as a separately
named assembly child, correct proportions, no gate-chasing. The one
non-negotiable carried from the brief into this draft: `star_tile`,
`moon_tile` and `void_tile` share one identical blank (body + knob) — the
only geometry that differs between the three parts is the 1.2mm relief boss
inside a shared recessed pocket on the underside face, so the outline,
thickness, rim and back stay bit-for-bit identical across all three families
regardless of which motif is applied.

## Radial position discipline

`blocks.shared_positions` is a rectangular grid generator and does not apply
here. The one hand-rolled radial list (`features/ring.py`, built once from
`cadlib.layout.circle_points`) is the SOLE source for: the plinth's ten well
centers, all three discs' six-window subsets (indices into the same list),
the zenith-well indices, the plinth's index-groove positions, and each disc's
witness-notch angle. No second copy of the trig exists anywhere in this
project.
