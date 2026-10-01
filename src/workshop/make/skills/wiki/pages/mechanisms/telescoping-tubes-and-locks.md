---
title: Telescoping tubes and their locks
tags: [telescoping, tube, overlap, wobble, lock, collet, clamp, button, stop, anti-rotation]
aliases: [telescopic tube, telescoping pole, telescopic pole, extension pole, extendable pole, telescopic mast, telescopic leg, nested tubes, sliding tube, extendable handle, tripod leg, twist lock leg, collar twist lock, flip lock, lever lock, cam lever clamp, cam clamp collar, quick release collar, spring button, snap button, valco button, push button lock, v-spring button, spring clip button, collet lock, friction collet, paint pole lock, internal cam lock, eccentric expander, expanding plug lock, thumb screw collar, set screw collar, detent ladder, adjustment holes, minimum insertion, telescoping sword, collapsible sword, print-in-place telescope, selfie stick, monopod, trekking pole, walking pole, telescopic antenna, telescoping handle]
sources:
  - https://www.chiefdelphi.com/t/telescoping-tubes-overlap/428351 (overlap 30 % of length by old rule, 20 % aggressive, 1/4-1/5 of each stage; tip slop = bearing slop x extension / overlap)
  - https://www.law.cornell.edu/cfr/text/16/1512.6 (quill stem insertion mark at least 2.5 x stem diameter; strength kept one diameter below it)
  - https://patents.google.com/patent/US4076437A/en (paint-pole eccentric locking cam with idler cam and splines; earlier eccentric collars slipped when contaminated)
  - https://www.ulanzi.com/blogs/knowledges/twist-vs-lever-locks-travel-tripod-guide (twist collar compresses a C-ring collet; flip locks are external cam levers; grit and cam-tension failures)
  - https://antcomposites.com/telescoping-carbon-fiber-tube/ (lock families; longer overlap is stiffer but shortens the reach)
  - https://www.valcocleve.com/valco_product/part-no-B-134-single-end-bent-spring-leg-snap-button/ (0.25 in head, 0.39 in head height, 0.55-1.0 in tube ID)
  - https://www.amazon.com/Valco-Fasteners-Pickleball-Paddleboarding-Volleyball/dp/B0DLL3T47S (hole 1-2 drill sizes over the button head; a large hole loosens the hold; via search excerpt)
  - https://patents.google.com/patent/US7611398 (toy blade of frusto-conical tubes; each tube's proximal end frictionally engages the next one's distal end)
  - https://en.wikipedia.org/wiki/Machine_taper (self-holding Morse taper about 1.49 deg; steep tapers self-release)
  - https://tribology.rs/journals/2024/2024-1/9-1546.pdf (printed PLA and PETG on steel, dry: static friction 9 N and 8 N at 30 N load)
  - Meriam and Kraige, Engineering Mechanics - Statics, ch. 6 (friction on wedges)
related: [linear-guides-and-slides, joints, latches-detents-and-ratchets, bayonet-and-twist-locks, shaft-couplings, printed-threads, lead-screws, straight-line-and-toggle-linkages, print-in-place-mechanisms, layer-anisotropy, creep-and-stress-relaxation, toy-safety-constraints, push-pins-and-clip-fasteners, shaft-hub-connections]
updated: 2026-10-01
---

# Telescoping tubes and their locks

A telescoping joint is a prismatic joint whose guide is the overlap between
two nested sections, so its length changes as it moves. That makes it wobble
and bind more than a fixed-length slide. This page sizes the overlap, the
stops and the anti-rotation, then compares the locks. The general binding
ratio and the slide forms are on [[linear-guides-and-slides]]; the catalogue
row is [[joints#prismatic-joints]].

## Overlap: the couple that carries the moment

Inner section of outside diameter `D` in an outer section with diametral
clearance `c`. Overlap `L_o` at full extension, extension `L_e` from the outer
mouth to a side load `W`:

```text
tilt in the clearance   θ ≈ c / L_o                      rad
tip play                δ ≈ c · L_e / L_o                sum it over the stages
mouth reaction          R_mouth = W · (L_e + L_o) / L_o
tail reaction           R_tail  = W · L_e / L_o
drag while loaded       F_f = μ (R_mouth + R_tail) = μ W (2 L_e + L_o) / L_o
```

Size the overlap from the play you accept, `L_o ≥ c · L_e / δ_max`. Worked:
`slip` on both sides gives `c = 0.4 mm`. At `L_e = 150 mm` that needs
`L_o ≥ 20 mm` for 3 mm of tip play and 60 mm for 1 mm. Published floors for
loaded metal tubes: a bicycle quill stem must stay inserted at least 2.5 ×
its diameter, by regulation. Robot elevators reserve a quarter to a fifth of
each stage, and the older rule was 30 %. Printed clearances are larger, so
the play rule usually asks for more.

**Bear at the two ends of the overlap, clear between.** The reactions act at
the outer section's mouth and the inner section's tail. Put a short bushing
at each: a collar inside the mouth and a collar on the inner section's tail.
Two short rings print rounder than a long bore, and the drag no longer
depends on the straightness of the whole tube.

## Binding while sliding

A push at angle `α` to the axis has a side component, and the bearing couple
above multiplies it. The joint slides only while

```text
tan α  <  L_o / ( μ · (2 L_e + L_o) )
```

At `μ = 0.3`, `L_e = 150` and `L_o = 40`, the push must stay within about
21° of the axis. The allowed angle shrinks as the tube extends. This is the
binding ratio of [[linear-guides-and-slides#the-binding-ratio]] with the
lever arm growing as the joint opens. Printed PLA and PETG on steel showed
static friction near 0.3 at light load, and plastic on plastic runs higher.

## Clearance, section and material

- Derive every stage from the one inside it:
  `outer_ID = cadfits.slot_for(inner_OD, RUN)`, with `"free"` for long
  printed sections ([[joints#two-fit-classes-per-project]]). With wall `t`
  and per-side clearance `c₁`, stage `k` has
  `D_k = D_0 − 2k (t + c₁)`, which limits how many stages nest.
- A tube printed standing up is round, but its layers cross the tube. Bending
  then pulls the layers apart on the tension side ([[layer-anisotropy]]).
  For a leg or pole that carries bending, buy the tubes (aluminium, carbon,
  PVC) and print the collars, bushes and locks.
- A closed section is a piston. Vent the closed end, or the trapped air
  springs it back.

## End stops that keep sections captive

- The inner section's tail collar is wider than the outer section's mouth
  bushing, so it cannot pass. The two bearing collars are also the stops.
- **The extension stop sets the minimum overlap.** Place it from `L_o`, not
  from the wanted length: when the collars touch, the overlap is the mouth
  bushing plus the tail collar, so lengthen one of them to lengthen `L_o`.
- **Assembly path.** A tail collar wider than the mouth must enter from the
  outer section's far end, or the mouth bushing is fitted after the inner
  section (pressed, glued or snapped). That bushing is then in the retention
  chain ([[joints#rules-that-are-easy-to-break]]).
- A tube flicked open hits its stop. Size the collar's shear area for the
  impact, and remember that on a vertical print the stop load runs across the
  layers.
- The collapse stop must land on a shoulder, not on a lock part or a finger.
  Collapsing tubes are a finger trap in a toy
  ([[toy-safety-constraints#finger-entrapment-and-springs-en-71-1]]).

## Anti-rotation

| form | build | notes |
|---|---|---|
| key and groove | rib on one section, groove along the other for the full stroke | prints cleanly with the axis vertical |
| flat | D-flat along the inner, matching flat in the mouth bushing | phase-exact, one way |
| non-round section | square, hex, oval or triangular tubes | keyed for free; no internal twist lock possible |
| splines | several keys | shares torque between keys |
| none (round) | — | needed by an internal cam lock |

An internal eccentric lock locks by turning one tube in the other, so it
excludes anti-rotation. A collar twist lock turns only its collar, so the
tubes may be keyed. A spring button must line up with its holes: key the
sections, or run a groove that leads the button to them.

## Locks compared

| lock | holds by | positions | release | printed? |
|---|---|---|---|---|
| **collar twist lock** (tripod) | collar thread drives a taper that squeezes a split collet (C-ring) onto the inner tube | any | turn the collar back | collar, thread and collet print; thread rules in [[printed-threads]] |
| **internal eccentric cam** (paint pole) | an eccentric plug on the inner tail wedges against the outer bore when the tubes turn | any | turn back | the cam must be dragged by the outer bore or it spins with the inner |
| **flip / lever lock** | split collar at the mouth closed by an over-centre cam lever | any | flip open | a toggle: needs overtravel and a stop ([[straight-line-and-toggle-linkages#toggle-mechanisms]]); give it a tension screw |
| **spring button** (snap button) | a sprung button in the inner pops through a hole in the outer | discrete | press flush and slide | buy the spring clip; print the holes |
| **thumb or set screw collar** | a screw presses the inner tube | any | loosen | pad or flat under the point, never bare plastic; `stdpart sizes LockCollar`, `stdpart sizes SetScrew` |
| **detent ladder** | a flexing bump on the inner into a row of notches | discrete | pull past the detent | prints; holds only the detent force |
| **O-ring drag** | an O-ring in a groove rubs the bore | any | pull | smooth damped feel, little hold; `stdpart sizes ORing` |

## Friction locks: collet, eccentric and clamp collar

Every friction lock holds `F_hold = μ · N`, where `N` is the total radial
force it builds:

```text
split collar, screw tension P (thin ring)    N ≈ 2π · P
collet drawn into a taper of half-angle α    N ≈ F_a / tan(α + φ)     F_a = axial force of the collar thread
```

The collar thread's `F_a` follows from its torque as a power screw
([[lead-screws#torque-and-efficiency]]).

- **Drag the eccentric.** An eccentric plug only wedges if the outer tube
  holds it while the inner turns. The paint-pole patent adds an idler cam
  keyed to splines in the outer pole for this. Earlier single eccentrics
  slipped once dirty. A printed eccentric needs a drag: a rubbing pad, a
  spline or a TPU sleeve.
- **Clamps creep.** A printed collet or clamp collar relaxes under constant
  squeeze and its hold falls ([[creep-and-stress-relaxation#design-rules]]).
  Use PETG or nylon over PLA, keep a tension screw, and record the hold as
  unverified.
- **Grit and wear.** Tripod makers report grit jamming twist threads and
  flip-lock cams going slack until re-tensioned.
- Use the low end of μ for hold and the high end for the user's release
  force.

## Positive locks: spring button and detent ladder

- **Hole.** Drill the outer tube one or two drill sizes over the button head
  (Valco's rule); a larger hole loosens the hold. Printed, that is
  `cadfits.slot_for(BUTTON_D, "slip")` up to `"free"`. A 0.25 in-head
  single-leaf button suits tube IDs of 0.55–1.0 in. Take the button and its
  tube range from the maker's sheet.
- **Bearing on the hole edge** is the hold. A printed wall crushes and the
  hole elongates. Check `p = F / (D_button · t_wall)` against the printed
  wall, or seat the hole in a metal or thicker printed collar.
- **Ladder.** Holes at pitch `p` leave a web of `p − D_hole` between them.
  It shears out along two planes: `τ = F / (2 · web · t_wall)`.
- **Detent ladder.** A printed flexing bump holds only its detent force
  ([[latches-detents-and-ratchets#detent-holding-force]]). Use it for
  positioning; a load-bearing leg needs a button or a pin through holes.

## Collapse force

```text
F_collapse = F_lock + F_drag + F_seal + F_detent − weight (vertical, downward)
```

- `F_lock` is zero once released; the held load must stay below
  `F_hold / SF`, or below the button's positive hold.
- `F_drag` is the bushing friction: preload plus the bending reactions
  above.
- A vertical pole whose lock slips collapses under its own load. Prefer a
  positive lock where something hangs on it.

## Printed telescoping sections

Print-in-place telescopes print all stages nested and collapsed, axis
vertical ([[print-in-place-mechanisms]]).

- **Gap.** Each radial gap is `cadfits.print_in_place_gap()["xy"]`. Every
  stage starts on the bed, so chamfer each first-layer edge by
  `print_in_place_gap()["bottom_chamfer"]`
  ([[print-in-place-mechanisms#the-bed-closes-gaps-elephants-foot]]).
- **45° cone stops.** Flare the inner stage's tail outward toward the bed and
  narrow the outer stage's mouth inward going up. Both are self-supporting
  overhangs, and they meet when extended. Radially, the order is: inner body,
  gap, mouth lip, flare, gap, outer wall. The lip overlaps the flare by more
  than the gap plus two line widths.
- **Taper stops.** A section whose wall tapers wedges at full extension, as
  the frusto-conical tubes of a toy blade do. A wedge pushed in with force
  `F_set` at half-angle `α` releases at
  `F_r = F_set · (μ cos α − sin α) / (sin α + μ cos α)`. It stays extended on
  its own only when `μ > tan α`, like a self-holding Morse taper (1.49°).
  Steeper tapers self-release. Choose α for the behaviour wanted, not for
  looks.
- **Stops load the layers.** On a vertical print the stop's axial load pulls
  the lip's layers apart. Make lips several layers thick and their cones
  long.
- **Detent.** A small bump at the stop holds a toy extended; give the rigid
  check its overlap allowance
  ([[mechanism-verification#8-allowances-are-declared-not-hidden]]).

## Failure classes

| symptom | cause | rule |
|---|---|---|
| tip wobbles | overlap short for the clearance | `c · L_e / L_o ≤ δ_max`; stop placed from `L_o` |
| sticks when pushed at an angle | bearing couple × μ exceeds the push | `tan α < L_o / (μ (2 L_e + L_o))`; bushings at both ends |
| sections pull apart | no tail collar, or a collar that passes the mouth | collar OD > mouth ID; mouth bushing in the retention chain |
| cannot assemble | tail collar and mouth bushing both fixed | one of them fitted after insertion |
| twist lock spins and never locks | eccentric not dragged by the outer bore | drag pad, idler or splines |
| creeps shorter under load | friction lock relaxed, μ lower than designed | low μ for hold; positive lock for loads |
| button will not find its hole | round sections turn | key or guide groove |
| print-in-place stages fused | first-layer squish, gap too small | bottom chamfer; `print_in_place_gap` |
| springs back after collapse | trapped air | vent the closed end |

## Checks

```python
import math
assert CLEARANCE_D * EXTENSION / OVERLAP_MIN <= TIP_PLAY_MAX, "tip wobble over the limit"
assert OVERLAP_MIN == STOP_TO_STOP, "overlap must come from where the stops meet"
assert math.tan(math.radians(PUSH_ANGLE_DEG)) < OVERLAP_MIN / (MU_HIGH * (2 * EXTENSION + OVERLAP_MIN)), "binds when pushed"
assert TAIL_COLLAR_OD > MOUTH_ID and (MOUTH_FITTED_AFTER or TAIL_FITTED_AFTER), "not captive, or not assemblable"
assert not (LOCK == "eccentric" and ANTI_ROTATION), "an internal eccentric needs the tubes to turn"
assert LOCK != "eccentric" or ECCENTRIC_DRAG, "eccentric spins with the inner tube"
assert LOCK != "button" or ANTI_ROTATION or BUTTON_GUIDE, "button cannot find its hole"
f_hold = MU_LOW * N_RADIAL
assert LOCK_POSITIVE or f_hold >= SF * W_AXIAL, "friction lock slips under the load"
taper_holds = MU_LOW > math.tan(math.radians(TAPER_HALF_DEG))
assert taper_holds == MUST_STAY_EXTENDED, "taper half-angle gives the wrong behaviour"
assert STOP_OVERLAP - GAP_XY >= 2 * LINE_W, "print-in-place lip slips past the flare"
```

Open items: hold force, collapse force and clamp relaxation are forces and
life; no rigid gate measures them. Test a printed stage pair.
