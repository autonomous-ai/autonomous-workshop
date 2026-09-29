---
title: Tolerance stack-up
tags: [tolerance, stack-up, worst-case, rss, statistical, loop, sensitivity, mean-shift, clearance, assembly]
aliases: [tolerance stack, tolerance chain, dimension chain, dimensional loop, loop diagram, worst case analysis, root sum square, root sum squared, statistical tolerancing, benderizing, stack analysis, gap analysis]
sources:
  - https://faculty.washington.edu/fscholz/Reports/isstech-95-030.pdf (F. Scholz, Tolerance Stack Analysis Methods, Boeing ISSTECH-95-030: arithmetic and RSS stacking, sensitivity coefficients, Bender 1.5, inflation factors, mean shifts)
  - https://www.fiveflute.com/guide/introduction-to-root-sum-squared-rss-tolerance-analysis/ (T = 3σ, 99.7 %, ±1.5σ mean shift practice)
  - https://metricmech.com/articles/tolerance-stackup-worked-example (loop signs; tolerances always add; convert to equal-bilateral first)
  - https://www.smlease.com/entries/tolerance/tolerance-stackup-analysis/ (dimensional chain, σ = T/3 per part)
  - https://ficientdesign.com/tolerance-stack-up-analysis/ (when worst case vs RSS; systematic errors shift the mean)
related: [fit-derivation, fdm-hole-accuracy, fdm-design-rule-tables, iso-2768-general-tolerances, iso-286-fits, gdt-basics, seating-bought-parts]
updated: 2026-09-23
---

# Tolerance stack-up

A clearance that is right at nominal can still close, or open too far, once
every part in the chain is off by its tolerance. A stack-up adds those
errors along the chain of dimensions that sets one gap and asks whether the
gap stays inside its limits. [[fit-derivation]] derives one mate between two
parts; a stack is needed as soon as three or more dimensions, or two or more
parts, set the gap.

## The loop diagram

1. **Name the gap** and its requirement: `G_min ≤ G ≤ G_max` (a slide that
   must not bind, a lid that must close, a board that must not rattle).
2. **Walk the loop** from one face of the gap to the other through the
   parts that touch each other, one vector per dimension, and back to the
   start.
3. **Sign each link**: a dimension whose increase opens the gap is +1, one
   that closes it is −1. The nominal gap is the signed sum.
4. **Tolerances always add**, whatever the sign of their dimension
   (MetricMech). The sign decides the nominal, not the spread.
5. **Convert every dimension to equal-bilateral form first**: `10 +0.2/−0`
   becomes `10.1 ± 0.1`. Stacking unequal limits directly drifts the
   arithmetic.

## Which dimensions belong in the chain

- **One link per part.** Each part contributes the single dimension between
  the two interfaces where the loop enters and leaves it. A part that
  appears through two dimensions is dimensioned from the wrong datum:
  re-dimension it between its functional faces ([[gdt-basics#datums]]), which
  shortens the chain and removes a tolerance.
- **Contact decides.** Follow the faces that actually touch under the load
  that closes the gap (gravity, a spring, a screw). A part with play in the
  loop contributes its play as a link too.
- **Geometric tolerances enter as links.** A flatness, position or
  perpendicularity zone contributes ± half its width to the gap direction.
  Where none is stated, [[iso-2768-general-tolerances]] gives the default.
- **Bought parts from the datasheet**, at their datasheet tolerance
  ([[iso-286-fits#what-this-means-for-printed-parts]]); printed parts from the
  process ([[tolerance-stack-up#where-the-fdm-process-tolerance-comes-from]]).

## Sensitivity coefficients

When a dimension does not lie along the gap, or the gap is a function of it,
linearise: `G ≈ G0 + Σ aᵢ (Xᵢ − Xᵢ0)` with `aᵢ = ∂G/∂Xᵢ` (Scholz). A plain
end-to-end chain has `aᵢ = ±1`. Common others:

| link | aᵢ |
|---|---|
| a diameter in a radial clearance | ±0.5 |
| a length at angle θ to the gap direction | ±cos θ |
| a lever arm r setting a tip position through angle φ | ±φ (rad) for r, ±r for φ |

Every formula below takes `|aᵢ| Tᵢ`, not `Tᵢ`.

## Worst case and RSS

With Tᵢ the ± tolerance of link i:

```text
worst case (arithmetic)   T_wc   = Σ |aᵢ| Tᵢ
RSS (statistical)         T_rss  = sqrt( Σ (aᵢ Tᵢ)² )
Bender's inflation        T_b    = 1.5 · T_rss
inflated RSS              T_c    = sqrt( Σ (cᵢ aᵢ Tᵢ)² )
mean shift + RSS          T_ms   = Σ ηᵢ |aᵢ| Tᵢ + sqrt( Σ ((1 − ηᵢ) cᵢ aᵢ Tᵢ)² )
```

- **Worst case** is a guarantee: every assembly works, even when every
  part sits at its limit together. Use it for few links, low volume, and
  anything that must never fail.
- **RSS** assumes each link is normal, centred on nominal, independent,
  and that `Tᵢ = 3σᵢ`; then about 99.7 % of assemblies fall inside
  `± T_rss` (Five Flute). It pays only with many links: the gain over worst
  case grows like √n.
- **Bender's 1.5** corrects for suppliers who quote ±2σ as their tolerance.
  Scholz notes that for two links it is more conservative than worst case.
- **Inflation factor cᵢ** for a link that is not normal (Scholz, Fig. 6):
  normal 1, triangular 1.225, **uniform 1.732**, elliptical 1.5. Use the
  uniform value for a process you have no data for: its parts can sit
  anywhere in the band.
- **Mean shift.** A systematic error (tool wear, temperature, a printer's
  flow or XY offset) moves the mean, not the spread, and RSS does not
  average it away (Ficient). Stack the shift, a fraction ηᵢ of Tᵢ,
  arithmetically and the rest statistically (Mansoor's form, via Scholz).
  A common practice shifts critical links by 1.5σ, η = 0.5 (Five Flute).

## Where the FDM process tolerance comes from

In order of preference:

1. **Measured on the printer that will print the part**: print a coupon with
   the feature (outside width, hole, slot, Z height), measure several, and
   take `Tᵢ = 3σ` about the mean. Put the mean error into the model as a
   compensation (the fit classes and hole rules do exactly this), and only
   the spread into the stack.
2. **The fit classes**, where the link is a printed mate: `cadfits`' per-side
   clearances are what a tuned printer needs for that class to work
   ([[fit-derivation#the-fdm-clearance-table]]), so they are the budget the
   rest of the stack must not eat.
3. **A service's published tolerance** from [[fdm-design-rule-tables]]:
   Hubs ±0.5 % with a ±0.5 mm floor, an industrial service ±0.3 % with
   ±0.25 mm. These are worst-case bands for unknown machines, wide enough to
   swallow any slip fit on their own.

FDM error is not centred and not independent: holes print small
([[fdm-hole-accuracy#why-a-vertical-hole-comes-out-small]]), outside
dimensions grow with over-extrusion, the first layer spreads, and every
part from one printer carries the same offset. Over-extrusion shrinks a hole
and grows the peg that fits it, so the two errors add in the clearance
rather than cancel. Treat printer offsets as a mean shift (η), and a
dimension with no data as uniform (c = 1.732).

## Worked example: a module in a printed box

Axial gap above a bought module that must not be clamped by the lid. Box
inner depth A = 25.00, printed spacer B = 5.00, module C = 14.00 ± 0.20
(datasheet), lid lip D = 5.00. Printed links ± 0.25 (the industrial floor).
Loop: `G = A − B − C − D = 1.00` nominal.

| method | ± T | G_min |
|---|---|---|
| worst case | 0.95 | 0.05 |
| RSS | 0.48 | 0.52 |
| RSS × 1.5 (Bender) | 0.72 | 0.28 |
| RSS, printed links uniform | 0.78 | 0.22 |
| η = 0.3 on printed links, uniform | 0.79 | 0.21 |

Variance shares under plain RSS: each printed link 27 %, the module 18 %.
Spend tolerance on the largest contributor first: the three printed links
together are 82 % of the variance, and one of them (the spacer) can usually
be deleted by dimensioning the module's seat from the box floor directly.
With four links and a printing process nobody measured, the defensible
answer is worst case or the uniform-with-shift line, not bare RSS.

## Write it as an assert

The stack lives in the parameter block next to the dimensions it reads, so
it re-runs when any of them changes:

```python
import math
# (sign or sensitivity, nominal, ± tol, c inflation, eta mean-shift)
LOOP = [(+1, BOX_INNER_D, T_PRINT, 1.732, 0.3),
        (-1, SPACER_H,    T_PRINT, 1.732, 0.3),
        (-1, MODULE_H,    MODULE_TOL, 1.0, 0.0),     # datasheet
        (-1, LID_LIP_H,   T_PRINT, 1.732, 0.3)]
G0  = sum(a * x for a, x, *_ in LOOP)
Twc = sum(abs(a) * t for a, _, t, _, _ in LOOP)
Tms = (sum(e * abs(a) * t for a, _, t, _, e in LOOP)
       + math.sqrt(sum(((1 - e) * c * a * t) ** 2 for a, _, t, c, e in LOOP)))
T = Twc if len(LOOP) <= 3 or MUST_NEVER_FAIL else Tms
assert G0 - T >= GAP_MIN, f"gap closes to {G0 - T:.2f} mm"
assert G0 + T <= GAP_MAX, f"gap opens to {G0 + T:.2f} mm"
```

Derive the nominal of the last link from the loop rather than typing it
(`LID_LIP_H = BOX_INNER_D - SPACER_H - MODULE_H - GAP_NOM`), for the same
reason [[fit-derivation#write-the-mate-as-a-derivation]] derives the second
half of a mate; the tolerance assert is then the part that can fail.

## Checks

```python
assert all(t > 0 for _, _, t, _, _ in LOOP), "a link with zero tolerance was not measured"
assert G0 - Twc >= GAP_MIN or len(LOOP) > 3, "few links: worst case must hold"
assert G0 - T >= GAP_MIN and G0 + T <= GAP_MAX, "stack leaves the gap band"
```
