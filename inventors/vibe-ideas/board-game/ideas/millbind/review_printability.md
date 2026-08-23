Verdict: PASS

Lens: does this actually print. `gate.json`'s numbers (63/63 watertight, one body
each, in-envelope, overhang/bridge under threshold, PASS) are taken as given and
are not re-argued. This is a re-check after the round-1 repair; the previous FAIL
was `crank_gear`'s floating arm.

## The `crank_gear` FAIL is cleared

The repair is real, not cosmetic. Measured off the rebuilt solid
(`project/build/millbind_parts/crank_gear.stl`, z-extent 0..91mm, 674 facets),
every downward-facing facet in the part, aggregated by z-band and by overhang
angle from vertical:

| z band | overhang from vertical | area |
|---|---|---|
| 0.00 (bed face) | 90deg | 379.2mm2 |
| 0.00..1.00 (tooth flanks) | 1.4-7.4deg | 54.1mm2 |
| 1.00 (tooth undersides) | 90deg | 204.3mm2 |
| 31.00 (blind-bore roof) | 90deg | 57.2mm2 |
| 49.00..55.00 (riser-2 cone) | **42.8deg** | 752.2mm2 |
| 55.00..58.00 (cap wall) | 1.3-3.7deg | 141.0mm2 |
| 58.00 (gusset corner slivers) | 90deg | **7.1mm2** |
| 58.00..69.00 (gusset outboard face) | **43.7deg** | 212.9mm2 |

Nothing else. Read against the round-1 finding, every objection is answered:

- **No cantilever anywhere.** The old part had ~135mm2 of flat underside
  starting in mid-air at z=30 with the knob's whole footprint over it. There is
  now no downward-facing facet at all between z=1 and z=31, and none above z=58
  except 7.1mm2. Riser 1 is a plain `root_r` (11.875mm) cylinder extruded off
  the barrel top, and `build_barrel` makes the barrel a full-height `root_r`
  cylinder with teeth cut into the z=1..29 band — so riser 1 continues the exact
  same circle it stands on. Zero-width step, not a ledge.
- **Both tapers are under the limit, with margin.** Riser 2 lofts 11.875 ->
  17.5mm over 6mm: 42.8deg from vertical. The gusset runs the cap edge (17.5mm)
  out to the knob's outer edge (28mm) over 11mm: 43.7deg. Both measured off the
  mesh, not read off the source comment. A 43-44deg wall is inside every stock
  slicer's 45deg support threshold and inside what actually prints clean — this
  is a genuine no-support part, which is what the customer expects on opening
  the file.
- **The one residual overhang is 1.5mm and harmless.** The gusset's bottom face
  is a 3.5 x 14mm rectangle at z=58 spanning x=14..17.5; the cap under it is a
  17.5mm-radius circle, so the two rear corners poke past the arc. Maximum
  protrusion 1.46mm at y=+/-7, 7.1mm2 across both corners. A 1.5mm unsupported
  lip anchored along its whole inner edge is a non-event — the perimeter is
  carried at both ends.
- **The knob is now fully carried.** Knob footprint is x=14..28; the gusset's
  top face at z=69 is a 14 x 14mm square spanning exactly x=14..28, y=+/-7. The
  knob circle is inscribed in it. Solid material under 100% of the knob.
- **The gate is now scoring the orientation that will actually be used.** Round
  1's `Y-90` (part on its side) was the search finding a paper win on a
  non-orientation. It now reports `as-modelled`, 5.25% overhang, upright — the
  only way this piece prints, and the number belongs to it.

## New-height checks on the 91mm crank — all clear

- **Structural.** `bore_through` cuts only to z=31, so the entire riser above
  the pin is solid, unbored. Worst realistic hand load — 20N sideways at the
  knob, ~50mm above the riser root — puts about 0.8MPa on the riser's weakest
  section (23.75mm solid minus the 8.6mm bore, Z ~ 1290mm3). PLA layer adhesion
  is 20-40MPa. Twenty-plus times margin on the piece that gets turned every
  round. Layer adhesion on a tall vertical print is not a concern here.
- **Toppling / adhesion.** Bed contact is 379mm2 (the root annulus; the teeth
  start 1mm up, so they do not touch), carrying 91mm and 37cm3. Centre of mass
  is offset only ~2.6mm in +x — the gusset and knob are ~13% of the volume — so
  it sits deep inside the footprint and will not lean. But 91mm on a 24mm-dia
  footprint is 3.8:1, so **print this one with a brim**; that is the single
  print-setting note for the part, not a geometry problem.
- **Print time.** ~37cm3 and 91mm tall, so on the order of 3-4h. It is one
  piece out of 63 and by a wide margin the box's centrepiece. Acceptable.

## Non-blocking, but fix before the files ship

**The exported artifacts and the review renders are stale.** `project/build/`
holds the repaired build (11:48), but the top-level publish copies are from the
11:17 run, before the crank repair:

- `project/millbind_parts/crank_gear.stl` — z-extent 0..55mm, 652 facets. That
  is the **pre-repair part with the floating arm**.
- `project/millbind.stl` / `.step` — same stale run.
- `project/millbind_review/crank_gear.png` — silhouette aspect 1.19 (55mm build);
  the repaired part is 2.0. The render shows the old cantilever.

The repaired geometry is correct and is what the gate hashed and built, so this
is a publish-step ordering artifact, not a design defect — the same pattern
appears under `armillary/project/`. But anyone who prints from the top-level
`millbind_parts/` today gets the version that fails. Re-run the export/render
step so the shipped STLs and the grids match `build/`.

## Nothing else regressed

Only `parts/crank.py`, the `crank_*` block of `params.py`, `validation.py` and
`fit_checks.py` were touched. `board.py`, `gears.py`, `millstone.py` and
`misc.py` are untouched, and every non-crank row in `gate.json` is unchanged in
orientation, overhang and bbox. The round-1 assessments therefore stand
unaltered, including:

- **`gear_high` (x7) still must be flipped teeth-down in the print guide.** The
  gate agrees (`flip-X-180`); the shipped `print_plan` still says smooth-column
  down, which puts a 9.5mm annular ledge floating at z=20 and forces supports.
  Documentation fix, but it does need making.
- Millstone crowns (r=17 over 17.5mm tooth tips, 1mm gap) and the barrel's 1mm
  untoothed lead-in rims are 1mm steps, not overhangs. Fine.
- `yard_board` is a solid 12mm slab, not a thin plate — not a warp case.
- `sack_spindle` (8.5mm rod, 7.3:1) remains the most fragile piece and remains
  acceptable; print the four together so the tips cool properly.
- 63 pieces but 12 distinct shapes, and the high-count families (`grain_pellet`
  x28, `gear_low` x14) are the robust ones. Losing one does not kill the game.
