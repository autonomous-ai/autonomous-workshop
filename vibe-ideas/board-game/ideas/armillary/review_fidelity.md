Verdict: FAIL The reference/ folder that should hold the owner-approved draft is empty, and independent evidence (git diff / idea.json history) shows the object now built is a wholesale replacement of a different, previously-existing design, so nothing establishes that the owner ever saw and approved this silhouette.

# Fidelity review — armillary

## The reference problem

`reference/` contains zero files. There is no owner-approved draft render for
this idea, of any design, at any point in its history that is recoverable
from this directory. My lens exists to check "is this the object the owner
said yes to" by comparing current renders against that folder view by view.
With nothing in it, that comparison cannot be performed — not "passes
trivially," cannot be performed at all.

The builder's stated workaround — using `project/armillary_review/` (the
current build's own renders) as a stand-in for the missing reference, and
reporting "no geometry edits this turn" as reassurance that the silhouette is
unchanged — does not close this gap, for two reasons:

1. Comparing the build's renders against the build's own renders is
   self-referential. It can catch a builder who broke their own geometry
   mid-turn; it cannot show a human ever agreed to the shape in the first
   place.
2. "No geometry edits this turn" is not the same claim as "unchanged from
   what the owner approved." I checked this independently rather than take
   it on the builder's word, per the brief for this review.

## What the git working tree actually shows

`git diff` / `git status` against HEAD in this directory is not a quiet
diff. It shows a **total part-vocabulary replacement**, not incidental
polish:

- Deleted (tracked, previously built): `armillary_parts/plinth_axle.*`,
  `armillary_parts/tier_disc_a/b/c.*`, `armillary_parts/marker_peg_tri/
  square/penta/hex_0[1-4].*` (16 peg files), `armillary_parts/probe_pin.*`,
  and the corresponding `project/parts/plinth_axle.py`,
  `project/parts/tier_disc.py`, `project/parts/marker_peg.py`,
  `project/parts/probe_pin.py` source files, plus every matching PNG in
  `armillary_review/`.
- Added (untracked, new): `armillary_parts/plinth_ring.*`,
  `mask_disc_a/b/c.*`, `star_tile_01-12.*`, `moon_tile_01-10.*`,
  `void_tile_01-08.*`, `reserve_column.*`, `score_rail_tri/square/
  penta/hex.*`, and `project/parts/plinth_ring.py`, `mask_disc` logic in
  `blocks.py`/`features/ring.py`, `parts/tile.py`, `parts/reserve_column.py`,
  `parts/score_rail.py`.
- `idea.json`'s `concept` field itself changed mechanism: the committed
  version describes "gamble a shared probe pin down into a socket... seats
  flush... or perches visibly on top of whichever disc blocked it, plant a
  peg"; the working-tree version describes "reach through and pull tiles one
  at a time... a star or moon joins your catch, an eclipse ends your turn."
  These are not two renders of the same game — they are two different games.
- `brief.md`'s parts list confirms this: it no longer mentions
  `plinth_axle`, `tier_disc`, `marker_peg`, or `probe_pin` at all; it
  describes `plinth_ring`, `mask_disc_a/b/c`, `star_tile`/`moon_tile`/
  `void_tile`, `reserve_column`, `score_rail` instead.

Whatever draft renders an owner might have looked at and approved at any
earlier gate for this idea would necessarily have shown the probe-pin/socket
object (the one now deleted from `armillary_parts/` and `armillary_review/`),
not the mask-disc/tile-well object that is now in `project/` and described
in the current `brief.md`/`idea.json`. `reference/` being empty is
consistent with this: whoever reworked the concept cleared the stale
reference images along with the stale geometry, but no new reference set was
ever produced and signed off before the build proceeded. That is exactly the
gap this lens is supposed to catch.

## What I can say about internal consistency (not the same as fidelity)

For completeness, and to be clear about what this verdict is *not* about: the
current build appears internally consistent with the *current*
`brief.md`/`idea.json` text. Looking at
`project/armillary_review/_assembled.png` (iso hero shot), I see a squat
disc-drum (plinth_ring + flush-stacked mask discs reading as one cylinder),
a square tapering obelisk beside it (reserve_column), four flat bars around
it (score_rail x4), and a small cluster of round-knobbed studs (tiles) —
which matches the brief's `hero_shot`/`silhouette` language for the *new*
design. `plinth_ring.png` (front/top/iso views) shows a drum with a central
axle post and a ring of eight-ish sunken wells, matching the brief's
`plinth_ring` description. `reserve_column.png` (front/back/right views)
shows a square tapering obelisk with a full-height slot on one face,
matching the brief's `reserve_column` description. If the question were "did
the builder execute the current brief faithfully," the answer looks like
yes on this spot check. But that is not this lens's question — this lens
asks whether the built object is what the owner said yes to, and there is no
artifact anywhere in this idea's directory that shows the owner ever said
yes to the mask-disc/tile-well object.

## Bottom line

I am not flagging a silhouette drift I can point to frame-by-frame, because
there is no reference frame to point to. I am flagging that the visual
contract this lens is supposed to enforce does not exist for the object
that was actually built, and that the git history shows a plausible reason
why: the design underneath this idea was substantially reworked at some
point and the reference set was never regenerated/approved for the new
version. That is a fail condition for "is this the object the owner said
yes to" — the only honest answer available is "unknown, and the record that
would resolve it is missing."
