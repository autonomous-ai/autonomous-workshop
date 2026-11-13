---
title: A closed ring on an open hook
tags: [hook, crook, hanging, ring, retention, pin, detent]
aliases: [lantern ring falls off, ring slides off hook, pinned ring, shepherd's crook hanger]
sources:
  - measured in CAD sweeps (rotation_motion_collision) on a printed crook and ring; no external source
related: [key-rings-and-charm-hardware, screws-into-plastic, wall-mounting-and-hanging]
updated: 2026-11-10
---

# A closed ring on an open hook

## Why it falls off: gravity alone, near the free end

A printed closed ring hung over the free end of an open crook or J-hook is
held only by gravity in the hook's lowest point. Measure the distance from
that point to the hook's free end along the bar's bearing face: when it is a
few millimetres (a crook curled about 300° whose end stops 20° past the
bottom), a swing of about 35° or a sideways nudge of 2-4 mm carries the ring
off, with almost no lift. A drop of cyanoacrylate does not fix it: CA does
not fill a free-fit gap of 0.4-2 mm, so the bond is a few point contacts.

## Fixes that keep the install path

The ring went on along a path, and every fix has to keep that path:

- **A stop between the ring and the free end** (a stud, a pin across the bar,
  a ball on the tip) needs bar length the ring does not leave, and lengthening
  the tip raises the swing the ring needs to go on. Sweep that install swing
  with `check_motion` against the arm before choosing it; a lantern under the
  ring met the arm at 45°.
- **Thickening the whole ring** has the same cost: a thicker ring needs a
  bigger swing to clear the end.
- **Pin the ring to the bar** after it is on: a boss on the ring's side wall,
  outside the bar's width, takes a small self-tapping screw (or a printed pin
  with glue) through a clearance hole into a pilot in the bar
  ([[screws-into-plastic]]). The ring and its install path stay as they were;
  once the pin is in, the ring cannot swing, slide, lift or pull off. Prove
  both: the install swing `clear` without the pin, each escape `blocked`
  with it.
- **A seat notch** under the ring is only a detent: the ring's own clearance
  over the bar lets it lift out of any notch shallower than that clearance
  plus the notch depth, so it buys a few millimetres of lift.

- **Strengthen the ring only below the bar.** A pinned ring no longer swings
  away from a knock, so its legs bend across the layer lines (the ring prints
  upright). Deepening the legs below the spring line is free, because they sit
  beside the bar's width. The arch over a curved crook must keep its depth:
  the bar's inner face rises toward the ring's faces, so a deeper arch either
  collides with the bar when seated or, once raised to clear it, no longer
  passes the open end. Check the arch's own bending, and test-print when the
  margin is under 2×. (R28 revision 3: legs 3 → 6 mm, 36 → 9 MPa; the arch
  stayed 3 mm, at about 16 MPa against 20.)
