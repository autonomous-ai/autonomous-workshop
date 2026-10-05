---
title: Hinge types
tags: [hinge, door, lid, pivot, cam, four-bar, offset, concealed, spring]
aliases: [butt hinge, mortise hinge, continuous hinge, piano hinge, lift-off hinge, flag hinge, loose joint hinge, rising butt hinge, rise and fall hinge, helical hinge, cam rise hinge, gravity hinge, self-closing hinge, pivot hinge, centre-hung pivot, center hung pivot, offset pivot, concealed hinge, european hinge, euro hinge, cup hinge, 35 mm hinge, cabinet hinge, invisible hinge, soss hinge, barrel hinge, double action hinge, double-acting hinge, saloon door hinge, cafe door hinge, spring hinge, gooseneck hinge, cranked hinge, offset hinge, swing clear hinge, strap hinge, T hinge, tee hinge, gate hinge, four-bar hinge, multi-link hinge, lift-up lid hinge, torque hinge, hinge types]
sources:
  - https://en.wikipedia.org/wiki/Hinge (butt/mortise, continuous, flag, pivot, concealed cup, spring, self-closing and swing-clear definitions)
  - https://www.cookebrothers.co.uk/latest-news/2025/09/30/benefits-of-rising-butt-hinges/ (helical knuckle lifts the door a few millimetres; gravity closes it; handed)
  - https://patents.google.com/patent/US3748688A/en (gravity cam hinge: bottom and top dwells, cam symmetrical about the closed position, low-friction nylon)
  - https://www.fritsjurgens.com/inspiration/blog/what-is-a-pivot-hinge (pivot carries the door's weight to the floor; can be double-acting)
  - https://www.sizemarker.com/blog/cabinet-hinge-boring-dimensions (35 mm cup, 13 mm deep, 3–7 mm from the door edge, 45 mm screw centres; overlay set by boring, plate and model)
  - https://patents.google.com/patent/US4332053A/en (the concealed cup hinge is a four-bar linkage)
  - https://www.hardwaresource.com/a/blog/post/all-about-soss-invisible-hinges (invisible when closed; moving pivot stays inside; deep full mortise; ½ in minimum material)
  - https://www.soss.com/product/model-216-invisible-hinge/ (opens a full 180°)
  - https://www.hardwaresource.com/products/double-action-barrel-spring-hinge (180° either way, returns to centre; three hinges on heavy doors)
  - https://monroeengineering.com/blog/what-are-double-action-spring-door-hinges/ (two barrels, a wire spring in each)
  - https://www.americanlocksets.com/swing-clear-hinges-guide (an offset leaf moves the door out of the opening, recovering about its thickness)
  - https://www.suffolklatchcompany.com/blogs/news/t-hinges-complete-faq-for-hand-forged-and-standard-styles (strap reaches just over halfway across the door; two hinges; surface mounted)
  - https://docs.motiongen.io/docs/geometry-constructions-for-mechanism-design/three-position-synthesis (pivots on perpendicular bisectors; branch and toggle defects)
related: [hinges-and-pin-joints, joints, linkages, lead-screws, springs, counterweights-and-gravity-balance, print-in-place-mechanisms, flexures-and-living-hinges, rod-ends-and-clevises, latches-detents-and-ratchets, cams-intermittent, overhangs-and-print-orientation]
updated: 2026-10-01
---

# Hinge types

A catalogue of hinge forms: the axis each one gives, when it is the right
one, and how it prints. Pin and knuckle sizing, retention, stops and
hold-open friction for all of them are on [[hinges-and-pin-joints]].

## Choosing a hinge type

| type | what it does | use when | prints as |
|---|---|---|---|
| **butt** | two leaves, alternating knuckles, axis at the joint line | doors and lids hung on an edge | print-in-place flat, or pinned |
| **continuous / piano** | one knuckle row along the whole edge | long lids, fold-flat panels | print-in-place flat; many short knuckles |
| **strap / T** | long leaf screwed to the face | heavy, wide or planked doors and gates | flat; the strap is a beam |
| **lift-off / flag** | pin fixed in one leaf, the other drops over it | parts that must come off without tools | two parts; pin printed lying down |
| **rising butt** | helical knuckle faces lift the leaf as it opens | doors that should close by their weight | cam knuckles, axis vertical |
| **self-closing cam** | a cam with dwells returns the leaf | gates, toy doors, flaps that spring back | cam faces printed facing up |
| **pivot** | pins top and bottom on the leaf's own axis | heavy doors, frameless panels, double swing | two pegs; bottom one takes the weight |
| **spring / double-action** | spring barrels, return to closed | swing doors, self-closing flaps | spring bought, or replaced by a cam |
| **offset / swing-clear / gooseneck** | cranked leaf moves the axis | a door that must leave its opening clear | flat; the crank is a lever |
| **concealed cup (European)** | four-bar arm in a 35 mm cup | cabinet doors | buy it; print the bore and plate holes |
| **invisible (Soss)** | link stack hidden in mortises | flush lids and doors, 180° | link plates on pins in two pockets |
| **four-bar lid** | the lid is a coupler, not a rotor | a lid that must lift up and back | links printed flat on pins |
| **torque / friction** | friction holds any angle | lids and screens that stay put | [[hinges-and-pin-joints#friction-and-hold-open-hinges]] |

## Butt, continuous, strap and T hinges

- **Butt.** Any hinge set into the door and the frame. The two leaves sit
  in shallow pockets (mortises), so the closed gap is only the knuckle
  clearance. An odd number of alternating knuckles; the axis sits at the
  joint line, a little proud of the faces so the leaves fold flat.
- **Continuous (piano).** The same knuckle row runs the whole edge, so the
  load and the stiffness are spread along it and the leaves cannot twist.
  Printed in place, every knuckle face is an axial gap that may fuse. More
  knuckles mean more gaps: keep them long enough that each gap gets its
  `print_in_place_gap()` ([[hinges-and-pin-joints#print-in-place-hinges]]).
- **Strap and T.** Surface-mounted, with a long strap on the door and a
  short leaf (T) or a second strap on the frame. The strap reaches just
  over halfway across the door, and two hinges carry it. It spreads the
  screw load over a planked door that a butt hinge would tear out of.

**The pair carries a couple.** A door of weight `W` whose centre of mass is
`x` from the axis, hung on two hinges `s` apart, loads them with
`H = W · x / s` horizontally: the top hinge pulls, the bottom one pushes.
Put the hinges as far apart as the door allows. The top hinge's fasteners
are in pull-out.

## Lift-off and pivot hinges

- **Lift-off (flag).** A pin fixed in the frame leaf points up; the door
  leaf's knuckle drops over it. The door comes off by lifting it, so it
  needs lift clearance above it of at least the pin engagement. Handed: the
  pin leaf goes on the frame, pin up. Print the pin leaf with
  the pin lying on the bed (D-flat down) so its strands run along the pin.
- **Pivot.** Two pins on the leaf's own axis, one top and one bottom, set in
  from the edge (offset) or at mid-width (centre-hung). The bottom pivot takes
  the weight down to the floor and the top one only locates, so the frame
  takes no hanging moment. A pivot door can be made double-acting. The bottom
  pivot is a thrust bearing: friction torque `μ · W · r_eff`, so end the
  pin in a dome or on a steel ball to make `r_eff` small. A printed leaf
  with two pegs goes in by flexing one wall by the peg engagement (size it
  as a snap: [[snap-fit-design#cantilever]]) or down a slot closed later.

## Rising butt and self-closing cam hinges

A rising butt has helical faces between its knuckles. Opening, the leaf
climbs the helix and rises `h` (a few millimetres on a room door); released,
its weight runs it back down. A cam hinge does the same with a ramp between
two dwells: a bottom dwell holds it closed, a top dwell holds it open. A cam
symmetrical about the closed position closes from either side.

```text
lead angle        tan λ = h / (r_m · θ_open)      r_m mean cam radius, θ_open in radians
closes itself     λ > φ,  φ = atan μ               (otherwise the helix is self-locking)
closing torque    T = W_c · r_m · tan(λ − φ)       W_c weight on the cam
```

This is the screw's lowering torque with its sign reversed
([[lead-screws#self-locking]]). Illustration: `r_m = 5`, a 90° swing and
`λ = 30°` give `h = 5 · 1.571 · 0.577 = 4.5 mm`. A printed pair has a high,
uncertain μ, so take φ from the high end and leave margin. The knuckle pin's
own friction also opposes closing.

- Relieve the leaf's top edge on the hinge side by `h`, or leave `h` of
  clearance above it, or it jams on the frame as it rises.
- Rising hinges are handed: one for clockwise, one for anticlockwise.
- **Printing.** Print each knuckle with its cam face up: a downward-facing
  ramp is an overhang at λ from horizontal. With the axis vertical a helix
  prints as radial terraces, one per layer, and the follower climbs them
  like stairs. Use the finest layers on the cam, and let a rounded follower
  ride a ramp rather than mating two full faces.

Spring-assisted versions: [[#spring-and-double-action-hinges]].

## Spring and double-action hinges

- **Spring hinge.** A torsion spring in the barrel closes the leaf. Its
  torque is linear in angle while gravity follows cos θ, so it matches at two
  angles at best ([[counterweights-and-gravity-balance#torsion-and-coil-springs-at-a-hinge]]).
  Size the spring with [[springs#torsion-spring]].
- **Double-action.** Two spring barrels, one for each direction. The door
  opens 180° either way and returns to centre; two hinges on a light door,
  three on a heavy one. Printed, a symmetrical gravity cam does the same job
  with no spring to buy (above), or a flexure spring can
  ([[flexures-and-living-hinges]]).

## Offset, gooseneck and swing-clear hinges

A cranked leaf moves the axis away from the door's edge. Take a door of
thickness `t` swinging 90°. Let the axis stand `b` out from its swing-side
face and `s` back from the jamb line, away from the opening. The door then
intrudes into the opening by

```text
intrusion = t + b − s          (≤ 0 means the opening is fully clear)
```

A plain butt hinge has `s ≈ 0`, so the door eats its own thickness of the
opening. A swing-clear hinge cranks the axis back by about `t`. A gooseneck
or cranked strap moves the axis round a frame member or an overlay lip; the
crank is a lever arm, so check its bending. The jamb stop and the frame
return must clear the swept edge, which is a `clear` rotation sweep.

## Concealed hinges: European cup and invisible

- **European cup hinge.** The door takes a 35 mm cup bored about 13 mm deep,
  its edge 3–7 mm from the door edge, with fixing screws on 45 mm centres. A
  mounting plate goes on the cabinet side. The arm is a four-bar linkage: as
  the door opens it moves out and away, so its edge clears the side.
  Overlay depends on the boring distance, the plate height and the hinge
  model; read it from that model's chart. Buy the hinge
  (`$step-parts`); print only the 35 mm bore (inside face up, so the cup is
  a blind pocket opening upward) and the plate's screw holes.
- **Invisible (Soss).** A stack of links pivoted in two bodies, each fully
  mortised into one edge. Nothing shows when closed, it opens 180°, and the
  moving pivot stays inside the hinge until it is fully open, so there is no
  pinch point behind. It needs depth: the smallest wants ½ in material. A
  printed version is link plates on pins, printed flat, in a pocket in each
  part.

## Four-bar hinges that move a lid clear

When no single axis puts the lid where it must go (lift up and back over a
box, stay inside the cabinet's footprint, clear a neighbouring lid), make
the lid the coupler of a four-bar ([[linkages#four-bar]]).

1. Draw the lid closed and open. Pick two points `A`, `B` on the lid.
2. **Two positions:** a fixed pivot can be anywhere on the perpendicular
   bisector of `A1A2`, the other anywhere on that of `B1B2`. Choose them to
   fit inside the box and keep links short.
3. **Three positions:** each fixed pivot is the centre of the circle through
   `A1 A2 A3` (and `B1 B2 B3`), unique for the chosen points.
4. Solve the linkage over the whole travel. It must reach every position on
   one branch without passing a toggle. A toggle near closed is useful: the
   lid then holds itself shut over centre ([[linkages#dead-centres]]).

Print the links flat with pins through them, one four-bar at each end of
the lid. The lid ties the pair together; a third fights the other two
through print error ([[exact-constraint-and-kinematic-mounts]]).

## Failure classes

| symptom | cause | rule |
|---|---|---|
| top hinge screws pull out, door sags | hinge couple `W x / s` on close hinges | spread the hinges; strap or T for heavy leaves |
| piano hinge fused at one knuckle | many short axial gaps | fewer, longer knuckles, each with its own gap |
| rising or cam hinge stays open | `λ ≤ φ`, terraced ramp, or pin friction | steeper helix; fine layers; rounded follower |
| rising door jams at the head | no relief for the rise | relieve the top edge by `h` |
| pivot door hard to turn | flat thrust face at large radius | dome or ball at the bottom pivot |
| door narrows the opening | axis at the edge | swing-clear crank, `s ≥ t + b` |
| four-bar lid stops short or flips | toggle or branch change inside the travel | solve the full travel; one branch |

## Checks

```python
import math
H = DOOR_W * DOOR_XCG / HINGE_SPACING
assert H <= HINGE_PULL_OUT, "top hinge fasteners pull out"
lam = math.atan(RISE / (CAM_R * math.radians(SWING_DEG)))
assert lam > math.atan(MU_HIGH) + math.radians(5), "cam hinge will not close itself"
assert HEAD_CLEARANCE >= RISE, "rising leaf jams on the frame"
assert DOOR_T + AXIS_OUT - AXIS_BACK <= 0 or not MUST_CLEAR_OPENING, "door intrudes into the opening"
assert LIFT_CLEARANCE >= PIN_ENGAGEMENT, "lift-off hinge cannot be lifted off"
assert ONE_BRANCH and NO_TOGGLE_IN_TRAVEL, "four-bar lid does not reach every pose"
```
