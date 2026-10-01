---
title: Toy safety as design constraints
tags: [toy, safety, small-parts, choking, magnet, sharp-edge, finger-entrapment, age-grading]
aliases: [small parts cylinder, choke tube, astm f963, en 71-1, 16 cfr 1501, cpsc, choking hazard, flux index]
sources:
  - https://www.cpsc.gov/s3fs-public/Small-Parts-16-C-F-R-Part-1501-English.pdf
  - https://www.tradeaiders.com/toys-for-under-3-years-using-the-small-parts-cylinder-to-prevent-choking-hazards.html
  - https://www.law.cornell.edu/cfr/text/16/1501.2
  - https://www.law.cornell.edu/cfr/text/16/1501.4
  - https://www.law.cornell.edu/cfr/text/16/1500.19
  - https://www.law.cornell.edu/cfr/text/16/1500.48
  - https://www.law.cornell.edu/cfr/text/16/1500.52
  - https://www.law.cornell.edu/cfr/text/16/1500.53
  - https://law.resource.org/pub/eu/toys/en.71.1.2014.html
  - https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Magnets
related: [handheld-ergonomics, printed-part-count, automata-patterns, joints, stability-and-tipping, scissor-and-pantograph-linkages, posable-figure-joints]
updated: 2026-10-01
---

# Toy safety as design constraints

A printed toy is judged by the rules a toy must meet. This page turns the
most-quoted US (16 CFR, ASTM F963) and EU (EN 71-1) mechanical rules into
geometry constraints to design against. It is not a compliance statement:
consult the current standard before claiming a toy complies, and say in the
spec which rules were designed to and which were not checked.

## Who the toy is for decides everything

US 16 CFR 1501.2 decides whether a product is intended for children under 3
by three factors: the maker's stated age (label, packaging), how it is
marketed, and whether it is commonly recognised as for under-3s. Squeeze
toys, teethers, push-pull toys, blocks and stacking sets, bath toys, and baby
dolls are listed examples. State the intended age in the spec before
designing. EN 71-1 has extra rules for under 36 months, under 18 months, and
children too young to sit unaided.

## Small parts — the choke test

- A **small part** is anything that fits, without compressing and in any
  orientation, entirely into the small parts cylinder: **31.7 mm (1.25 in)
  inside diameter**, **57.1 mm (2.25 in)** deep, with a slanted bottom whose
  depth runs from 25.4 mm (1 in) to 57.1 mm. The cylinder approximates the
  fully expanded throat of a child under three. EN 71-1 uses the same
  cylinder.
- **Under 3**: toys that are or release small parts are banned — including
  pieces that break off during the use-and-abuse tests. Exemptions include
  balloons, books, crayons, chalk, modelling clay and paint sets.
- **3 to 6 years**: toys with small parts must carry a choking-hazard warning.
- **Small ball**: a ball that passes under its own weight through a
  **44.4 mm (1.75 in)** hole. Marbles and small balls carry warnings (toys
  containing them, for ages 3 to 8); latex balloons always carry one.

Design consequences: for a toy that might reach under-3s, every part —
including any part a child can pry off (a wheel, a pin, a printed eye) — must
not fit the cylinder: make it larger than 31.7 mm across in some direction
it cannot be turned out of, or make it captive. Assert it in the parameter
block.

## Use and abuse tests (what "breaks off" means)

Before the cylinder test, toys are dropped, twisted, pulled and squeezed:

| age | drop | torque | tension | compression |
|---|---|---|---|---|
| 18–36 months (16 CFR 1500.52) | 4 × from 0.92 m (3 ft) | 3 in·lb (0.34 N·m) | 15 lb (67 N) | 25 lb (111 N) |
| 36–96 months (16 CFR 1500.53) | 4 × from 3 ft | 4 in·lb (0.45 N·m) | 15 lb | 30 lb (133 N) |

(N and N·m converted from the pound values.) A press-fit or snap-fit part a
child can grip must hold 67 N pulled straight out. A friction-fitted printed
pin usually won't, so capture it ([[joints#latching-and-holding]]). This is
not something a rigid sweep can check; record it as an open item.

## Sharp points and edges

- US sharp-point test (16 CFR 1500.48), for children under 8: an accessible
  point is sharp if it enters a 1.02 × 1.15 mm slot and moves the sensing head
  0.12 mm further against 2.2 N, under an applied 4.45 N. Accessibility is
  judged with probe A (up to 3 years) or probe B (3–8 years). Sharp *metal or
  glass* edges have their own test (1500.49).
- EN 71-1 treats an edge as the junction of two surfaces longer than 2.0 mm,
  and requires metal edges free of burrs.
- For printed plastic: fillet or chamfer every exposed edge and point, and
  never leave a sharp tip on a thin printed feature that can snap off to a
  point.

## Finger entrapment and springs (EN 71-1)

- **Hinges, winding keys, scooters, moving parts**: if a gap admits a
  **5 mm** rod it must also admit a **12 mm** rod. Gaps between 5 and 12 mm
  trap fingers.
- **Scissor actions in folding toys**: keep 12 mm or more clearance between
  the moving parts ([[scissor-and-pantograph-linkages]]).
- **Springs** (spiral, extension, compression): the gap between turns must be
  more than **3 mm** (compression springs, at rest), or the spring must be
  inaccessible.

Apply these to every moving joint of a printed mechanism a child can reach:
linkages, gear meshes, crank arms against the frame. Either close the gap
below 5 mm, open it to 12 mm or more, or enclose it.

Two that are easy to miss on a wheeled toy: a wheel whose face has
through-windows turns a millimetre from the chassis, so each window is a
shear against the frame — make the windows blind pockets; and a slot or well
under the chassis that admits a 5 mm rod needs a cover plate once whatever
runs in it is assembled. Neighbouring tyres on one side are a nip: keep
their gap under 5 mm.

## Magnets

A magnet that fits the small parts cylinder and has a **flux index of
50 kG²mm² (0.5 T²mm²)** or more is hazardous (ASTM F963, EN 71-1). US toys follow ASTM F963 through 16 CFR
1250, and non-toy magnet products follow 16 CFR 1262. A printed toy with
embedded magnets must make them unable to come out after abuse testing, or
use magnets below the threshold.

## Other numeric limits in EN 71-1

- Projectile kinetic energy: rigid ≤ 0.08 J, resilient ≤ 0.5 J.
- Yo-yo ball cord initial length ≤ 370 mm.
- Enclosures a child can enter need ventilation: ≥ 1300 mm² total, or 650 mm²
  per opening with openings 150 mm apart.
- Sound: close-to-ear toys 60–70 dB(A), hand-held or table-top 80–90 dB(A),
  peak 110 dB(C).

The EN 71-1 stability slopes and how to design for them:
[[stability-and-tipping]].

## What to write in the spec

The intended age, the rules designed to, the part-by-part small-part check
(which parts are captive, which are larger than the cylinder), the moving
gaps and how each avoids 5–12 mm, magnets if any, and what was not checked —
use-and-abuse strength and chemical/material rules are never verified by
geometry.
