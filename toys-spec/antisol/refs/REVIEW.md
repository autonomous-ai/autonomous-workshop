# Antisol reference images — self-review

## The one that is not fixed, and is not fixable by prompting

**The size ladder does not read.** Mercury should be a small ball on a wide plate
(40% of the disc) and Jupiter should nearly fill its disc (79%). In the delivered
set they look much the same, because the model collapses every piece to roughly a
three-quarter ratio and will not be talked out of it — measured across three
different framings at 95–104% against a 41% target.

This was solved by compositing and then deliberately un-solved, because the
composite destroyed the seat collar (`NOTES.md`). Collar over ladder is the
creator's call, taken with the trade-off stated.

**The consequence to expect:** the likeness gate is a hard 0.90 IoU silhouette
floor per view. On the small planets — Mercury, Mars, Venus, Earth — Make will
build a globe roughly half the width these references show, so those four pieces
in both armies are the likely places the run stalls. The spec's numbers are
authoritative and hash-bound; the images are the gate's contract; here they
disagree and the disagreement is recorded rather than hidden.

The exact per-piece ratios in this set are **not measured**. Two attempts to
recover them from the alpha mask were written and both were wrong, and inventing
a third number that has not been checked would be worse than saying so.

## Passes

- **The surfaces look like the planets.** Mercury cratered two-tone grey; Mars
  rust with dark albedo regions and a white cap; Venus a pale banded cloud ball;
  Earth's continents; Neptune deep blue with a dark storm and wisps; Uranus flat
  pale cyan; Saturn belted with rings; Jupiter belted with the Great Red Spot.
  This was the creator's first and strongest stated requirement and the earlier
  hand-drawn polygons did not meet it.
- **Parity inversion reads.** Earth's ice cap sits up-right on Sol and up-left on
  Anti; Mars likewise; Saturn's ring dips right on Sol and left on Anti. Here the
  two armies are separate generations rather than one flipped image, so the
  mirror is approximate, not exact.
- **The seat collar is present on every piece**, which is the reason this set was
  chosen over the composited one.
- **Ownership reads at thumbnail size:** white discs against black discs.
- **Rank reads:** the seven-segment numerals 1–8 are legible and correct on both
  armies, dark on white and white on black.
- **The four non-piece geometries** each read as their role.

## Weak, recorded rather than iterated past

1. **Neptune (`05`/`13`) shows no clear axial lean.** The spec puts it at 28
   degrees. Its dark spot and streaks carry identity, but its side is carried by
   the disc alone rather than by all three cues.
2. **Uranus (`06`/`14`) is nearly identical between the armies.** The vertical
   band correctly states the 97.77-degree obliquity, but the globe is close to
   featureless and close to symmetric, so the mirror is not visible on it. Disc
   colour carries ownership here.
3. **Disc proportions vary slightly between images**, because each disc was
   generated independently. The gate normalises height per piece, so this costs
   nothing at the gate, but the set is not perfectly uniform as a family.
4. **Saturn's ring still projects further than the spec's Ø32.00 allows.** The
   spec keeps the ring inside the Ø34.00 disc — a decision taken deliberately in
   section 16 — and the generated art draws a more generous ring. Make builds
   from the spec's number, not the picture.

## Fixed during the run

- **The corona (`17`)** first came back as four traffic cones on a plinth. It is
  the signature component, so it was regenerated as curved tapering flames with
  the back pair tall and the front pair short. Accepted on the second attempt.
- **Mercury's numeral** first generated as a 7 instead of a 1. Correct now.
- **A stem artefact** growing out of Earth's north pole, killed by an explicit
  negative clause in the presentation text.

## Second pass — the board and the belt

Reviewed after the pieces were accepted.

- **`ref-18-board-panel.png` deleted.** It drew the recessed board and read as a
  muffin tray: sixty-three circles, no grid. The fault was in the spec, not in
  the render, so the spec changed — the field is now flat with a 1.20 mm cut
  grid groove, following `toys/mara-masque-dustlight-crossing`, and depth is
  reserved for trap, den and belt. No replacement image: the board is carried by
  `antisol.md` section 5 plus the named in-repo precedent. The four panels are
  consequently the only parts outside the IoU ≥ 0.90 gate, which is recorded in
  section 16 rather than hidden.
- **`ref-19-belt-inlay.png` replaced by `ref-18-belt-cell.png`.** One tile per
  cell, one central Ø26.00 landing pad in a faceted rubble field, 90°-symmetric.
  Reads correctly: a square tile, one pad, rubble to the edges. The 2x2 slab it
  replaces erased the cell grid under the water.
- **`ref-20-orbit-tray.png` renumbered to `ref-19`.** Unchanged image.

(Superseded by the third pass below: the set is back to 20.)

What the board change bought, and what it cost, in one line each: it removed 63
wells and one whole tolerance chain, it moved the belt from two geometries to
one, it added eight printed parts, and it left the board ungated.

## Third pass — the corona is the trap

- **`ref-18-corona-cell.png` — accepted, first attempt.** Square tile, sunburst
  of flames engraved from the centre, two tongues at the two corners of one
  edge. Reads as a corona from directly above, which is the angle a board is
  actually read from. **One discrepancy to carry:** the generated flames are
  raised, the spec says engraved 0.40 mm deep. Engraved is correct — raised
  relief under a Ø34.00 disc would make a trapped piece rock — so Make builds
  from the spec's number, not from the picture. Same class of thing as Saturn's
  ring.
- **`ref-17-sun-den-star.png` — taken at the round cap, not fully solved.**
  Three attempts; all three drew the two flares as inward-curving bull horns.
  The third has the bases outside the plinth footprint and the pair splaying
  into a V, which matches the spec's 12° outward lean and the 23.40 mm base
  placement, but the tips still hook inward. The spec's §7.2 wording is
  unambiguous about the lean, so the fault is contained. If the built part reads
  as horns at the first visual round, the fix is the spec's lean angle, not the
  image.
- **The board still has no reference image**, unchanged from the second pass,
  and the four panels remain the only parts outside the IoU ≥ 0.90 gate.

Set is **20 images, `ref-01`…`ref-20`**, contiguous, 10.03 MiB.

What the remapping bought: the trap stopped being a renamed noun and became a
component with a colour, a part and a picture; the den plug lost a geometry; and
§7's own opening admission — *"there is no room for a ring around the den"* —
stopped being true, because the ring was on the board all along.
