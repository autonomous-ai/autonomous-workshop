# Revision C, review round 2 — reveal, and requirement-by-requirement comparison

Same critic. The brief was revealed at the start of this round, so **nothing here
is a naive read** and it is not offered as one. Round 1's blind transcript is
sealed and was not edited afterwards.

The critic was given: what the object is; that this is a correction of an
existing archive; that two defects were to be fixed and nothing else permitted to
move; that the counters are frozen byte-for-byte; and that two known defects were
scoped out by the commissioner and must NOT be fixed. It was then given ten
positive and nine negative requirements and asked for a separate MATCHES/FAILS
verdict on each with named frame evidence, told not to merge them and not to pass
one on the strength of another.

## Fresh observations, recorded before comparison

> The single biggest thing I got wrong is the mount. Knowing to look for a yoke,
> the plan view resolves it exactly: at y=780 in roof/slit-plan_el90 the slit
> interior reads 6.01 mm of open air, a 4.07 mm solid, 9.9 mm of tube, a 4.07 mm
> solid, 6.01 mm of open air — **two arms, not one fin**. In the oblique frames
> the near arm simply eclipses the far one… Second correction: the eight sun
> marks are genuinely radial tapered wedges, not un-rotated square blocks…
> Third: knowing the tray is 190 mm and the grid 176 mm… the cells land at
> 21.95 mm — the board is dimensionally right.

## Verdicts

Every positive requirement P1–P9 and every negative requirement N1–N7 and N9
returned **MATCHES**, each on a named frame with a measured number. The
load-bearing ones:

- **P1 / N1 — two arms straddling the tube, not a lone fin.** "Two separate
  solids inside the slit, 549–572 px and 628–651 px (4.07 mm each), one on each
  side of the tube, and their centres (560.5 and 639.5) mirror exactly about the
  slit centre at 600."
- **P2 / N2 — equal clear air, both sides.** "The slit walls sit at 515 and 685
  px and the arms start at 549 and end at 651, giving 34 px = 6.01 mm of clear
  air on each side — equal to the pixel."
- **P3 — 10 mm gap, centred.** "A gap of 56 px = 9.90 mm, centred at 600.0 px
  which is the slit's own centreline."
- **P4 — both arms carry the tube.** "The tube overlaps 2.5 mm of each arm's
  4.07 mm width — equal both sides — and no parting line appears between tube and
  arm, so it reads as one fused solid."
- **P5 / N3 — mirror symmetry.** "An edge-detection sweep of roof/slit-plan_el90
  finds every geometric edge with a mirror partner about x=600 within one pixel
  (0.18 mm) at nine heights — dome silhouette, slit walls, both arms, tube, and
  the arm feet."
- **P6 / P7 — the chequerboard.** "Sampling all 64 cell centres in
  board/empty-plan_el90 returns exactly 32 dark cells in perfect alternation,
  each centred on its cell, with rank 1 reading X.X.X.X. — a1 dark, h1 light."
- **P8 — flush inlays.** "A 2 mm step would project as ~12.5 px of vertical face
  at that elevation and scale, and there is nothing remotely like it, so the
  inlays finish flush."
- **N4 — not a difference you hunt for.** "The dark cells are RGB (97,111,153)
  against a (221,229,232) field — a gross colour contrast, not an outline or an
  engraved step."
- **N6 — bare plate margin.** "A pixel sweep of the entire roof plate outside the
  dome returns uniform plate colour with zero non-plate pixels… no railing, rib,
  decoration, notch, cut-out or hole."

**D1 and D2, the two scoped-out defects, were both confirmed visible** and were
not scored as failures: the perimeter reveal "plainly, in iso.png", and the
gravity-seated condition of the inlays "every inlay joint is a plain flush line
with no retention feature of any kind."

## Two FAILS, both traced to the Manager's wording

P10 ("the Sun mark is an unbroken ball…") and N8 ("no dish, cone, annular rebate,
plateau or halo") came back FAILS, and the critic pointed out, correctly, that as
written **they contradict each other**: N8 forbids the annular rebate that P10
requires. Both were paraphrases the Manager imported from the archive's own prose
rather than requirements the brief contains. The brief does not describe the
counters; it freezes them by sha256 and forbids touching them. Both requirements
were restated in round 3 as the brief states them and re-put to the critic.

## The Manager's classification of the fifteen blind defects, checked by the critic

Of the fifteen defects raised blind, the critic classified twelve as concerning
frozen geometry this revision was forbidden to touch, one as D1, and three as
touching the changed work. Of those three it **withdrew two outright** as
misreads of its own:

> 12. "Mount is a single flat fin, no fork" — and flatly wrong. It is a symmetric
> two-arm yoke. **Withdrawn in full**; this was the defect being corrected and it
> is corrected.

> 2. "Unresolved pedestal at the foot of the slit" — largely my error. The "gap
> on one side" I flagged is the mandated 6 mm clearance and it is present on both
> sides; the block is the yoke's foot, symmetric to the pixel. **Not blocking.**

It also withdrew its blind complaint that the chequer's diagonals were broken:

> With a 1.0 mm chamfer and a 0.23 mm joint per side, diagonally adjacent dark
> squares are interrupted by roughly 1.4 mm of light at the crossing, on a 22 mm
> square. I called that "the diagonals are visually broken." At 4.5% of a cell
> that is not a defect and I was overstating it. I withdraw that.

And its blind reading of the inlay pockets as 0.15–0.2 mm deep:

> The thing I measured and called "a 0.15–0.2 mm shallow pocket" cannot have been
> a pocket wall at all; it was the parting line between two flush parts of
> different colour. My blind defect 8 was wrong on the mechanism, and the correct
> reading supports flushness rather than undermining it.

Its one surviving finding against this revision's own evidence was real and was
repaired: `board/populated-plan_el90.png` at 1200 px was byte-identical to the
carried-forward `playing/top_el90.png` and added nothing. **Both board plan
frames were re-rendered at 1800 px. No geometry changed with that repair** — the
part STEPs, `snap/iso.png` and `snap/signature.png` are byte-identical to the
ones read blind — and the critic re-read the new frames in round 3.
