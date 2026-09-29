---
title: Joint catalogue
tags: [joint, fit, hinge, pin, key, keyed, phase, slide, snap, detent, retention, revolute, prismatic]
aliases: [kinematic pair, pivot, hinge pin, clevis, keyway, d-shaft, dovetail, living hinge, clip, tolerance]
sources:
  - skills/cad/scripts/cadfits.py (fit classes and print-in-place gaps)
  - Bayer MaterialScience, Snap-Fit Joints for Plastics (cantilever strain)
  - skills/cad/references/motion-manifests.md
  - "experience: printed joints that passed every geometry gate and could not be assembled or phased"
related: [shafts-and-bearings, mechanism-design, mechanism-verification, hinges-and-pin-joints, print-in-place-mechanisms, linear-guides-and-slides, latches-detents-and-ratchets]
updated: 2026-09-23
---

# Joint catalogue

Every mechanism is joints between rigid bodies. Choose the joint first, then
its fit, then the two motion conditions it owes. Numbers assume a calibrated
0.4 mm-nozzle FDM printer; the clearances themselves live in
`skills/cad/scripts/cadfits.py` and are never retyped.

## Two fit classes per project

Declare them once at the top of the parameter block and derive every mate
from them:

```python
import cadfits

RUN = "slip"    # turning / sliding joints: bearings, bores, slots, forks  (0.20 per side)
SEAT = "snug"   # static pressed joints: keyed sockets, pin sockets        (0.10 per side)

SHAFT_D = 6.0                                      # [orig]
BEARING_BORE_D = cadfits.slot_for(SHAFT_D, RUN)    # 6.40 journal
KEY_SOCKET_D = cadfits.slot_for(SHAFT_D, SEAT)     # 6.20 part fixed on the shaft
```

A joint that moves uses `RUN`; a joint that must not move uses `SEAT`
(friction) or `press` (interference, not removable by hand). `free` (0.40) is
for long slides and tall Z spans that print less accurately. A mate that moves
and is printed in one job with its partner uses `cadfits.print_in_place_gap()`
instead — see below.

## Revolute joints

Things that turn.

| form | build | when | notes |
|---|---|---|---|
| **axle in bore** | shaft `D`, bore `slot_for(D, RUN)` | any continuous rotation | length ≥ 1.5 D of bearing per support, or the part wobbles; two supports spaced apart beat one long bore ([[shafts-and-bearings]]) |
| **shoulder pin** | pin `D` with integral head; `slot_for(D, RUN)` through the moving part, `slot_for(D, SEAT)` blind socket in the fixed part | link pivots, leg pivots | one part, no loose cap; the head retains the moving part, the snug socket retains the pin (record friction retention as a limitation) |
| **pin through clevis** | pin in two cheeks, moving eye between; eye gap = eye thickness + 2 × RUN clearance | a hinge carrying load both sides | clevis carries the moment; retention by head + cap, cross-pin, or press in one cheek |
| **print-in-place hinge** | knuckles printed together, gap `print_in_place_gap()` per face (xy 0.30, z 0.50 at 0.2 layers) | lids, flexible chains, articulated toys | cone-ended pins print without support; plate-level gaps need the 0.5 mm bottom chamfer; only a print proves it frees |
| **snap-in axle** | axle end with a split, barbed nose through the bore | wheels, caps a child assembles | the split halves must deflect ≥ barb height; PLA: barb 0.3–0.5 mm, split length ≥ 4 × barb; record compliance as unverified |
| **ball joint** | ball `D`, socket `slot_for(D, "free")` with a lip over the equator | posable figures, 3-axis swings | a printed socket closing over > 0.5 D needs a split or it cannot assemble; friction ball joints need a test coupon |

**Horizontal bores print as teardrops.** The ceiling of a round hole whose
axis lies in the bed plane is an overhang; cut a 45° teardrop point or a
truncated teardrop where the wall is thin. A teardrop bore is still sized
from the round diameter.

**Axial retention is its own joint.** A turning part must also be stopped
along the axis: head, collar, shoulder on the shaft, the next part in the
stack, or the housing wall. Every axial stop is a `blocked` condition.

Pinned and print-in-place hinges, stops and hold-open torque:
[[hinges-and-pin-joints]]; everything printed already assembled:
[[print-in-place-mechanisms]].

## Keyed joints

Things fixed on a turning shaft.

- **Single flat** (D-shaft): the only printable key that fits **one way round**.
  Flat depth ≈ 1/6 D (1.0 on a 6.0 shaft). Socket flat =
  `D/2 - depth + mating_clearance(SEAT)`.
- **Double-D**: fits two ways, 180° apart. Wrong for any part whose phase
  matters (crank pairs, cams, gear teeth that must line up): a phased part on
  a double-D fits 180° out as happily as in phase.
- **Hex**: six ways; fine for a knob, wrong for a phased part.
- **Pin through shaft**: strong and phase-exact, but a separate part to retain.

Phase is a parameter. Record which way the flat faces relative to the crank
pin or tooth, and assert it in the part builder rather than trusting the
assembly.

## Prismatic joints

Things that slide.

| form | build | notes |
|---|---|---|
| **pin in slot** | slot width `slot_for(pin, RUN)`, length = travel + pin D + 2 × overtravel | overtravel ≥ 1 mm each end: `assert stroke + 2 * overtravel <= slot_len - pin_d` |
| **rail / T-slot** | rail printed flat, slot `slot_for(rail, "free")` for lengths > 40 mm | guided length ≥ 2 × the slide width or it racks and jams |
| **dovetail** | 60° flanks, male derived from female with `peg_for` | slides one way and is captured in the other two — both are conditions |
| **guided rod** | round rod through two bushings | the rod's own length between bushings ≥ 2.5 × its travel for smooth motion |

A slide driven off-centre racks; drive it along its axis or lengthen the
guide.

Why a short guide binds, drawers, and bought linear guides:
[[linear-guides-and-slides]].

## Latching and holding

- **Detent**: a bump (0.3–0.5 mm) into a notch; the rigid sweep reads it as a
  collision, so give the condition an explicit `maxOverlapMm3` allowance equal
  to the bump band and say so in the description.
- **Snap hook / cantilever**: deflection `y`, beam length `L`, thickness `t`:
  strain ≈ 1.5 t y / L²; keep ≤ 2 % for PLA, ≤ 4 % for PETG. Print the beam
  in the XY plane, never along Z.
- **Bayonet / quarter turn**: an L-slot; the blocked direction is axial with
  the pin in the short leg.
- **Captured by the next part**: legitimate, and exactly what the `retention`
  chain exists for — the next part must itself be proven held.

Detent force, ratchet geometry and latch types are calculated in
[[latches-detents-and-ratchets]].

## The two conditions every joint owes

| joint | `clear` (assembles along) | `blocked` (must not) |
|---|---|---|
| axle in bore | along the axle, from the open side | the other axial direction, radial |
| shoulder pin | out along its axis (friction retention noted) | the moving part along the pin axis, stopped by the head |
| pin in slot | along the slot for the whole stroke | across the slot |
| dovetail | along the tail | lift-off normal to the base |
| snap / detent | along the insertion, with the declared bump allowance | the reverse, beyond the bump |
| gear on keyed shaft | along the shaft | rotation relative to the shaft (a rotation sweep, `expect: blocked`) |

Each is one `linear_motion_collision` (or a rotation sweep); the schema and
retention rules are in `skills/cad/references/motion-manifests.md`, and how to
derive them from the kinematics is in [[mechanism-verification]].

Joints that bend instead of slide: [[flexures-and-living-hinges]]. Joining
two shafts: [[shaft-couplings]].

## Rules that are easy to break

- A bore closed on both ends cannot receive a part wider than it at both ends:
  a shaft with a hook on one side and a pinion on the other cannot be
  installed. Check the insertion path of every captured shaft *before* adding
  the features on both sides of it; an open fork plus a keeper is the fix.
- Keep designed running gaps ≥ 0.2 mm everywhere; less fuses or grinds.
- A thin part in a slot or a fork: fork gap = part thickness + 2 × RUN
  clearance, not the part thickness.
- Edges touching the bed get a chamfer, not a fillet — a bed-side fillet is an
  overhang.
