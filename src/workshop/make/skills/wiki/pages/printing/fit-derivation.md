---
title: Deriving fits and clearances
tags: [fit, clearance, tolerance, mate, cadfits, envelope, derivation, audit]
aliases: [mating dimension, running gap, clearance fit, press fit, slip fit, hole and pin sizing]
sources:
  - skills/cad/scripts/cadfits.py (FDM clearance table, peg_for, slot_for)
  - skills/cad/references/parameters.md
  - "experience: hand-sized mates whose audits restated their own arithmetic, and a retainer gap derived from the pin instead of its head"
related: [joints, printed-part-count, wall-thickness-and-hollowing, mechanism-verification, tolerance-stack-up, post-processing-and-finishing, thermal-expansion-and-hybrid-parts]
updated: 2026-09-23
---

# Deriving fits and clearances

Two mating dimensions typed independently drift apart until the parts jam or
fall out. Derive one from the other, apply the clearance in exactly one place,
and derive the gap from the feature that actually decides it.

## The FDM clearance table

Per side, from `cadfits`: `press -0.05`, `snug 0.10`, `slip 0.20`, `free 0.40`.
`peg_for(bore, cls)` gives the male from the female; `slot_for(pin, cls)` the
female from the male. Which class each joint uses is in [[joints#two-fit-classes-per-project]].

## Write the mate as a derivation

A mating pair sized by hand — `hole = PIN_D + 2 * PIN_CLEAR` in one file, the
pin in another — cannot be audited afterwards, because the only check available
restates the arithmetic:

```python
assert math.isclose((PIN_D + 2 * PIN_CLEAR) - PIN_D, 2 * PIN_CLEAR)   # 2C == 2C
```

That reduces to `True` and passes whatever the geometry does. Instead:

- derive the second half through `cadfits` (`stem = cadfits.peg_for(SEAT_BORE_D, "slip")`,
  `bore = cadfits.slot_for(PIN_D, 0.15)`);
- have the project's fit audit recompute module-level results *independently*
  and band-check every per-side clearance;
- grep the library for the `± 2 * SOME_CLEAR` idiom so a hand-written mate
  cannot come back.

Both derived forms fail when broken on purpose; the hand-written ones could not.
The same trap applies anywhere a check is written after the value it checks:
solve the output from the constraint (a flute count from the web it must leave)
rather than asserting the constraint on a typed value.

Migrating an existing project to derived mates must not move any geometry:
fingerprint every entry's volume, body count and bbox from source before and
after, and diff.

When three or more dimensions set the gap, sum them: [[tolerance-stack-up]].

A finish coat changes a mate by twice its thickness on a diameter
([[post-processing-and-finishing]]); a metal part in a plastic one changes it
with temperature ([[thermal-expansion-and-hybrid-parts]]).

## Clearance comes off the largest feature, not the nearest one

A running gap is derived like any other mate, and the derivation picks a
dimension. Pick the wrong one and the arithmetic is flawless about the wrong
part. A cross pin retaining a gear:

```python
GEAR_PIN_Z = GEAR_HUB_TOP + RETAINER_GAP + RETAINER_PIN_D / 2.0   # wrong
```

reads correctly, derives from a real diameter, and clears the hub by exactly
the gap it names — with the Ø8 head on that Ø3 pin hanging 2 mm *into* the
pointer sweeping underneath it. The shaft is the feature nearest the hub; the
head is the feature that decides.

```python
RETAINER_SWEEP_D = max(RETAINER_PIN_D, RETAINER_HEAD_D)
GEAR_PIN_Z = GEAR_HUB_TOP + RETAINER_GAP + RETAINER_SWEEP_D / 2.0
```

The `max` is the whole fix, and it is worth writing even where the two are
equal today, because it says which envelope the gap is against. Whenever a
clearance is derived from a part that has a head, a collar, a flange, a boss or
a chamfered end, derive it from that part's *envelope* at the radius in
question.

Then check the float the choice costs: raising the pin by half the head's
excess opens the retention gap by the same amount, and shrinking the head is
usually cheaper than accepting it — 8 mm to 5 mm here took the gear's axial
float from 3.0 mm back to 1.5 while leaving 0.8 mm of shoulder over the hole
the head has to stop against.

Neither a single-pose clash check nor a sweep that omits the retainer can see
this: the moving part is only under the head for part of a turn. It needs a
coupled motion sweep with the retainer named as an obstacle
([[mechanism-verification#4-what-the-manifest-must-contain]]).

Why printed holes come out small, and how to compensate for it separately from the design clearance: [[fdm-hole-accuracy]].
