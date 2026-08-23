Verdict: PASS

# Millbind — playability re-review (round 3, second repair)

## Re-verification method

All numbers below were re-derived independently from the exported meshes in
`project/build/millbind_parts/*.stl` (all regenerated 12:15, after the
export/render batch at 12:12 — mtimes checked, not stale), not taken from
the builder's report or `params.py` comments. A small STL parser + radius-
vs-z profiler was written for this pass (triangle edges clipped to a given
z and interpolated, giving an exact `max_r(z)` envelope per piece), and used
to re-run the same class of check the round-2 review used: radial-envelope
sums between two pieces 30mm apart (`pin_pitch`), scanned across the full
axial lift/lower travel (0–28.8mm) a piece needs to clear a yard pin.

## 1–2. Crown-vs-crown, crown-vs-neighbour-tooth clearance, and axial travel — now clear

Measured `crown_d` off the mesh directly: the crown's outer radius is a flat
11.000mm from z=30.5 to z=36.0 in every one of the four `mill_gear_*`
variants (`tri`/`square`/`penta`/`hex` — the barrel and crown are identical
across all four, only the hub differs, confirmed identical radius profiles
in all four STLs). That matches the builder's number exactly.

Re-running the full lift/lower scan (0.1mm steps, 0–29mm of travel) for
every piece that can stand next to a millstone, against a fixed millstone
30mm away, isolating the crown/hub band (fixed z ≥ 30.5, i.e. excluding the
addendum tooth band where meshing gears are *supposed* to overlap by
design):

| mover, lifted/lowered beside a millstone | min clearance margin found |
|---|---|
| `crank_gear` | **+1.5mm** |
| `gear_high` | **+1.5mm** |
| `gear_tandem` | **+1.5mm** |
| `gear_low` | **+1.5mm** |
| millstone beside millstone (any hub pair) | **+1.5mm** (crown-vs-tooth); **+8.0mm** at crown-vs-crown itself (11+11=22 vs 30mm pitch) |

The single tightest number anywhere in the whole system is **+0.625mm**,
at the pre-existing tooth-cylinder boundary (root disk r=11.875 vs a
neighbour's addendum r=17.5, i.e. 11.875+17.5=29.375 against the 30mm
pitch) — this is the same geometry the round-1 crank fix already relied on
and is untouched by this round's `crown_d`/`hub_across_flats` change
(confirmed: `crank.py` was not modified, and `crank_gear`'s own root_r/
outer_r/riser dimensions measured off the mesh are bit-for-bit what the
round-1 review reported). Every value everywhere is positive; there is no
z-band, at any lift height, for any of the four mill_gear variants against
any of the four movable pieces, where the radial envelopes sum to more than
the 30mm pitch. Placement is lowering reversed, so the same clearance holds
in both directions. PLACE, SHIFT, POWER and TEST FOR A BIND's mandatory
retraction are all mechanically possible next to a millstone now, on every
yard pin, for every piece type. The fault that failed round 2 is gone.

## 3. Effects of the smaller crown/hub on playability

- **Crown as "the grinding disc": thinner, but still a distinct silhouette.**
  Comparing `mill_gear_hex`'s iso render against `gear_tandem` (same
  full-height barrel, no crown/hub) and `gear_high`/`gear_low` side by side:
  the collar-plus-post on top of a millstone is still an unmistakable,
  unique silhouette feature no supply gear has — a player will never
  mistake a millstone for a supply piece, regardless of crown size. That
  family-level distinguisher (millstone vs the three supply tiers) is
  unaffected by the resize and remains solid.
- **The furrows are cosmetically diminished, but not load-bearing.**
  `crown_furrow_depth` (1.2mm) and the groove width (2.2mm) are unchanged
  absolute values, now cut into a 22mm-diameter disc instead of 34mm. Because
  the hub sits directly on top of the crown, the *visible* crown ring (the
  part not hidden under the hub footprint) is an annulus from the hub's
  circumradius out to 11mm — 5.8mm wide for the hex hub (r=5.196), but only
  2.0mm wide for the tri hub (r=9.0, the builder's own "2.0mm margin"
  figure). On the triangular millstone specifically, that 2mm-wide visible
  ring is narrower than a single 2.2mm-wide furrow groove, so the furrow
  pattern barely registers for that one piece. No rule ever asks a player to
  read the furrows for anything — direction is read off the crank/millstone
  turning, ownership is read off the hub's flat count — so this is a
  thematic/cosmetic dent, not a state-legibility failure. Worth a note for
  the next visual pass, not a playability fault.
- **Hub as a finger grip: smaller, still functional.** 9mm across flats,
  12mm tall — `ergonomics_check.json` already passed this with no findings,
  and qualitatively it's in the same size class as an ordinary board-game
  peg (comparable to a chess-pawn neck), not a fiddly nub. Handling a single
  millstone once or twice a game at this size is not a chore.
- **Penta-vs-hex distinguishability: still the weak pair, now measurably
  tighter.** Re-measured hub circumradii off the mesh: tri 9.000mm, square
  6.364mm, penta 5.562mm, hex 5.196mm — a uniform 0.5625× scale-down of the
  round-1 figures (16.00/11.31/9.89/9.24mm), so the *relative* geometry is
  identical, but the absolute penta-vs-hex gap shrank from 0.65mm to
  0.37mm. Side-by-side render crops of the iso views confirm this
  qualitatively: tri (pyramid cap) and square (boxy top) both read
  instantly; penta and hex look close to identical at normal viewing scale
  and angle. This is unchanged in kind from round 1, and the same mitigation
  still applies and still holds: `idea.json` setup has each player pick up
  one millstone at the start ("the one you take is your mark for the whole
  game") and every reference to a millstone thereafter is either the
  owner's own piece (which they can confirm by feel — counting flats in the
  hand is reliable even when two shapes look similar at a glance) or is
  identified by which pin it sits on, not by a stranger's cross-table shape
  read. No rule requires a player to visually distinguish an opponent's
  penta millstone from an opponent's hex millstone at a glance. Genuinely
  weak, and worth tightening in a future pass (vary hub height or diameter
  with flat count, not just flat count alone, and the margin has now gotten
  worse rather than better) — but not, on its own or in combination with
  the crown shrink, a state-legibility failure that blocks play.

## 4. Everything else from rounds 1–2 — reconfirmed, unchanged

- **No dominant strategy, real decisions per turn, reachable/well-timed
  ending.** `idea.json`'s rule text is byte-identical to what round 2 quoted
  (checked the PLACE/SHIFT/POWER/DIRECTION/GRIND passages verbatim); the
  odd-loop bipartite structure, the three-gear-type decision space, and the
  24-gear supply clock are unaffected by a millstone dimension change. Not
  re-derived from scratch (out of this lens's scope on a second repair pass
  with no rules change), but nothing in this round touches them.
- **Seat bias at four players.** Still real (6 rounds don't divide by 4
  seats), unaffected by this round.
- **Floor ribs.** `parts/board.py` is untouched — same nine 4mm ribs unioned
  across the whole floor with no relief around pin footprints, confirmed by
  reading the current file. Cosmetic tilt risk, unchanged from round 1.
- **Crank direction arrow.** Re-read `parts/crank.py`: the arrow polygon is
  `[(-outer_r*0.7, -4), (-outer_r*0.7, 4), (-outer_r*0.3, 0)]`, a triangle
  whose base sits at radius 0.7×17.5=12.25mm and whose tip sits at
  0.3×17.5=5.25mm — both on the same side, differing only in radius, i.e.
  still pointing radially inward, not tangentially, despite a code comment
  now claiming "pointing tangentially." `crank.py` was not touched this
  round (unaffected by `crown_d`/`hub_across_flats`), so this is the same
  cosmetic mismatch round 1 flagged, still present, still non-blocking
  because the rule text carries the direction in words ("...the way the
  arrow on its cap points" backed up by an explicit "clockwise").
- **Renders are current, not stale.** `project/millbind_review/crank_gear.png`
  now visibly shows the tall riser+arm crank (matches the built mesh), unlike
  round 2's byte-identical stale render. All four `mill_gear_*` renders and
  the gear/crank renders used above are from the same 12:12 export batch as
  the STLs used for measurement.

## Net

The blocking fault — millstone crowns interpenetrating each other and
blocking every piece's axial travel onto/off a pin next to a millstone — is
resolved with real, independently-measured margin (0.625mm on the
pre-existing tooth-cylinder boundary, 1.5mm on the new crown/hub boundary,
8mm crown-vs-crown), confirmed across all four millstone variants and all
four things that can stand next to one. The resize's side effects are a
cosmetically thinner furrow band (not rule-relevant) and a tighter — but
still non-blocking, still mitigated by ownership-by-pickup — penta/hex hub
gap. Nothing here blocks PLACE, SHIFT, POWER, or TEST FOR A BIND.
