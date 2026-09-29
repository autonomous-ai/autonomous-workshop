---
title: Ergonomics of handheld objects and controls
tags: [ergonomics, grip, handle, button, knob, anthropometry, clearance, hand]
aliases: [grip diameter, handle size, push button size, knob size, finger clearance, human factors, mil-std-1472]
sources:
  - https://www.ccohs.ca/oshanswers/ergonomics/handtools/tooldesign.html
  - https://www.denix.osd.mil/soh/denix-files/sites/21/2016/03/02_MIL-STD-1472F-Human-Engineering.pdf
  - https://hf.tc.faa.gov/hfds/download-hfds/hfds_pdfs/App_B_Tech_Ops_Anthropometrics.pdf
related: [body-dimensions-for-scale, scale-anchors, toy-safety-constraints, form-and-finish-heuristics, buttons-knobs-and-front-panels]
updated: 2026-09-23
---

# Ergonomics of handheld objects and controls

When a photo gives no dimension but the object is held, pressed or turned,
the hand sets the size. These published ranges size a grip, a button or a
finger opening, and they double as a sanity check on a scale read from a
photo: a handle measured at 15 mm or 70 mm across is probably a scaling
error ([[scale-anchors]]).

## Handles and grips

Canadian Centre for Occupational Health and Safety (CCOHS), hand-tool design:

| feature | range | recommended |
|---|---|---|
| power-grip handle diameter (whole hand wraps it) | 30–50 mm | 40 mm, cylindrical or elliptical section |
| precision-grip handle diameter (fingertips) | 8–16 mm | 12 mm |
| handle length | ≥ 100 mm (shorter presses into the palm) | 120 mm |
| span of a two-handled gripping tool | 65–90 mm for maximum grip force | above 100 mm is hard for some users |
| tool mass, one hand | ≤ 1.4 kg; ≤ 0.4 kg for precision tools | ≤ 2.3 kg when held away from the body |

Bent handles suit force applied horizontally and straight handles suit force
applied vertically. A trigger long enough for two or three fingers is better
than a one-finger trigger.

## Push buttons

MIL-STD-1472F, Figure 12:

| | fingertip, bare | fingertip, gloved | thumb | palm |
|---|---|---|---|---|
| diameter min | 10 mm | 19 mm | 19 mm (25 gloved) | 40 mm (50 gloved) |
| diameter max | 25 mm | — | 25 mm | 70 mm |
| travel min / max | 2 / 6 mm | 2 / 6 mm | 3 / 38 mm | 3 / 38 mm |
| actuation force | 2.8–11 N (single finger) | | 2.8–23 N | 2.8–23 N |

Spacing between button edges: single finger ≥ 13 mm (50 mm preferred) bare,
≥ 25 mm gloved; sequential presses by different fingers ≥ 6 mm (13
preferred); thumb or palm ≥ 25 mm (150 preferred). Make the top concave to
seat the finger, or give it high friction; give positive feedback (a snap, a
click or a light); guard a button that must not be pressed by accident.

The mechanical stack under a button: [[buttons-knobs-and-front-panels]].

## Knobs

MIL-STD-1472F, Figure 8:

| grasp | diameter | height |
|---|---|---|
| fingertip | 10–100 mm | 13–25 mm |
| thumb and finger encircling | 25–75 mm | 13–25 mm |
| palm | 38–75 mm | length ≥ 75 mm |

Edge-to-edge separation between knobs: 25 mm minimum and 50 mm optimum for
one hand, 50 mm minimum and 125 mm optimum for two hands at once. When knob
diameter is the coding cue, diameters must differ by at least 13 mm.

## Finger access and clearance

MIL-STD-1472F, Figure 39: a push button needs a 32 mm diameter opening for a
bare finger to reach it to the first joint, 38 mm gloved. A two-finger twist
needs the object plus 50 mm bare, plus 65 mm gloved.

For openings a finger passes through, compare with the finger breadth at the
middle joint: men 19–23 mm, women 16–21 mm (5th–95th,
[[body-dimensions-for-scale]]). Size the opening to the 95th percentile man.
For toys, the finger-entrapment rules in [[toy-safety-constraints]] take
precedence.

## Applying it

- Put the governing ergonomic number in the parameter block with its source
  and assert the model against it (`assert 30 <= GRIP_D <= 50`).
- The ranges are for adult users. For a child's object, scale down and check
  the toy rules.
- Everything a hand touches gets a fillet, not a sharp edge
  ([[form-and-finish-heuristics]]).
