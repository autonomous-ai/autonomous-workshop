---
title: Ribs, gussets and stiffening
tags: [rib, gusset, stiffening, corrugation, fillet, stress-concentration, boss, plate, stiffness, weight]
aliases: [stiffening rib, stiffener, web, cross rib, ribbed plate, grid rib, gusset plate, corner brace, knee brace, corrugated wall, root fillet, stress concentration factor, kt, notch effect]
sources:
  - http://academic.sun.ac.za/mad/catalogs/dfmguidelines/dupontgeneraldesignprinciples.pdf (DuPont General Design Principles, Module I, pp. 11–13 moulding rules and Fig. 3.07, pp. 27–29 ribs and bidirectional ribbing, p. 22 SCF)
  - https://www.swcpu.com/blog/ribs-and-gussets/ (rib and gusset proportions, spacing, draft, base radius)
  - https://www.protolabs.com/resources/design-tips/design-stronger-molded-parts/ (ribs and gussets ≤ 60 % of nominal wall)
  - https://en.wikipedia.org/wiki/Design_of_plastic_components (rib 50–60 % of wall, height ≤ 3 × wall, spacing ≥ 2 × wall; via search excerpt)
  - Roark's Formulas for Stress and Strain, ch. 6 (stress concentration factors)
  - https://www.insdag.com/assets/frontend/trmpdf/Chapter7.pdf (outstand buckling coefficient 0.425)
related: [beam-and-plate-stiffness, printed-threads-and-bosses, wall-thickness-and-hollowing, fdm-minimum-feature-sizes, feature-recipes, overhangs-and-print-orientation, fdm-first-layer-and-warping, layer-anisotropy, lightweighting-and-lattices]
updated: 2026-09-23
---

# Ribs, gussets and stiffening

A rib is second moment of area bought with the least material: a thin web
standing on a wall puts material far from the neutral axis, where
[[beam-and-plate-stiffness#depth-beats-width-and-material-belongs-at-the-surface]]
says it pays. A gusset is a rib that ties two faces at a corner. The
moulding guides' proportions exist mostly to avoid sink and warp; for FDM
some of them stop mattering and a printing limit takes their place.

## Moulded rib proportions, and which survive FDM

| rule (moulding) | value | reason | FDM |
|---|---|---|---|
| rib thickness | 50–60 % of the wall (DuPont ½–⅔; SWC 60–75 %, 50 % cosmetic; Protolabs ≤ 60 %) | sink opposite the rib, voids at the junction | **drop it.** No sink in FDM. Size the rib to whole extrusion lines, at least 2, 3 if it carries load |
| rib height | ≤ 3 × wall | fill, ejection, sticking | keep a height limit, for **buckling and print wobble** instead |
| rib spacing | ≥ 2 × wall; SWC: no closer than the rib height | cooling, mould steel | keep it: a narrow slot between ribs is a hard-to-print gap ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]) |
| root fillet | 0.25–0.5 × wall (DuPont r = 0.5 T; min 0.25–0.5 mm) | stress concentration and flow | keep the fillet, for strength |
| draft | 0.25–1° | ejection | drop it |

Stratasys Direct's view for industrial FDM is the same: bosses and ribs may
be the wall thickness, and draft is unnecessary
([[printed-threads-and-bosses#bosses-ribs-and-fillets]]).

## Rib height and thickness

In FDM the rib thickness is set by the nozzle, not the wall:

```python
import cadprint
RIB_T = cadprint.shell_wall(NOZZLE)     # 3 lines for a load-bearing rib; min_wall (2 lines) only for a stiffener
```

A rib thinner than 2 lines is dropped or gap-filled by the slicer
([[wall-thickness-and-hollowing#derive-the-wall-from-the-nozzle]]); a rib
whose thickness is not a whole number of lines gets a thin gap-fill core.

The height limit in FDM comes from two failures:

- **Local buckling of the free edge.** A rib loaded in compression along
  its free edge is an outstanding plate, buckling coefficient k = 0.425:
  `σ_cr = 0.425 π² E / (12 (1 − ν²)) · (t / h)²`
  ([[beam-and-plate-stiffness#buckling-slender-columns-and-thin-walls]]).
  At t = 1.2 mm, h = 12 mm, E = 2300 MPa this is about 9 MPa, well below
  printed PLA's strength: a tall thin rib folds before it breaks. Keep
  `h / t` at roughly 10 or less unless the free edge is in tension, or add a
  flange (a T-rib) on the free edge.
- **Printing a tall thin fin.** Like a thin vertical pin, it sways under the
  nozzle and rings ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]).

## The rib versus thicker wall calculation

Compare a 20 mm wide strip of 2 mm wall, one rib 1.2 mm thick per strip,
against a plain wall thickened to the same I (parallel-axis sum from
[[beam-and-plate-stiffness#second-moment-of-area-of-common-sections]]):

| rib t × h | I, mm⁴ | I / plain 2 mm | equal-I plain wall | ribbed mass / equal-I mass | Z at rib tip | Z of equal-I wall |
|---|---|---|---|---|---|---|
| none | 13.3 | 1 | 2.0 mm | 1 | 13.3 | 13.3 |
| 1.2 × 4 | 58 | 4.4 | 3.3 mm | 0.68 | 12.5 | 36 |
| 1.2 × 6 | 133 | 9.9 | 4.3 mm | 0.55 | 20.7 | 62 |
| 0.8 × 6 | 96 | 7.2 | 3.9 mm | 0.58 | 14.7 | 50 |
| 1.2 × 8 | 258 | 19.4 | 5.4 mm | 0.46 | 32 | 96 |

Read three rules out of it:

1. **A rib buys stiffness at half the mass or less** of the equal-stiffness
   wall once it is about 3 × the wall tall.
2. **Height beats thickness.** Taking the rib from 0.8 to 1.2 mm adds 38 %
   to I; taking it from 6 to 8 mm tall doubles I.
3. **Stiffness is not strength.** The rib's free edge is far from the neutral
   axis, so the section modulus at the tip grows much more slowly than I. A
   **short rib can weaken the part**: the 1.2 × 4 rib is 4.4 × stiffer, but
   its tip stress is higher than the plain wall's at the same moment. Check
   the tip stress, keep the free edge in compression where you can (a
   printed rib's tip in tension cracks from its surface), and watch that
   compression against local buckling.

DuPont's rule for thinner ribs: holding `rib count × rib thickness`
constant keeps the equivalent structure. Ribs 2.5 mm thick every 25 mm equal
ribs 1.25 mm thick every 12.5 mm.

## Cross-ribbing a plate

A panel's deflection goes with `span⁴ / t³`
([[beam-and-plate-stiffness#plates-under-uniform-pressure]]), so a rib that
halves the unsupported span buys up to 16 ×, and ribs in one direction only
stiffen in that direction: a one-way ribbed plate still bends freely across
the ribs, and twists. Use a grid (square, diamond, triangle) when the load or
the support is not along one axis.

DuPont's bidirectional ribbing chart (Fig. 4.08) sizes a cross-ribbed plate
with the same I as a flat plate of thickness tA. Its worked examples:

| flat tA | constraint | ribbed wall tB | overall T | rib pitch | material saved |
|---|---|---|---|---|---|
| 4.5 mm | save 40 % | 2.0 mm | 8.5 mm | ~33 mm | 40 % |
| 2.5 mm | wall ≥ 1.0 mm | 1.0 mm | 5.0 mm | 20 mm | 45 % |
| 6.5 mm | overall ≤ 10.8 mm | 3.65 mm | 10.8 mm | 37 mm | 24 % |
| 4.0 mm | 4 ribs / 100 mm | 2.0 mm | 7.0 mm | 25 mm | 32 % |

The pattern: a cross-ribbed plate about 1.7–2 × the flat plate's thickness
overall, with a wall about half as thick, matches its stiffness with a
quarter to a half less material. In FDM, check the pockets between ribs
against the overhang limit if the ribbed face prints downwards
([[overhangs-and-print-orientation]]); print the ribs standing up from the
panel.

## Corrugation and formed stiffeners

Folding the wall itself (a corrugated or beaded panel, a return lip on a free
edge) moves material away from the neutral axis the same way a rib does, at
constant wall thickness, which suits a printed shell of 2–3 perimeters. A
turned-over lip also changes a free edge (k = 0.425) into a supported one
(k = 4): the same wall resists local buckling about ten times better.
[[fdm-first-layer-and-warping#design-against-warping]] adds a manufacturing
reason: Stratasys Direct ribs thin tall walls against warping.

Separating two skins with a core: [[lightweighting-and-lattices]].

## Gussets on bosses, brackets and corners

- **Bosses**: tie a free-standing boss to the nearest wall with ribs, or
  stand it on gussets; DuPont notes a rib substantially raises a boss's
  strength ([[printed-threads-and-bosses#bosses-ribs-and-fillets]]).
  Gussets spaced around a boss stop it rocking under a screw's side load.
- **L-brackets**: a gusset across the inside corner turns the corner from a
  bending joint into a triangle. The corner of an unbraced L is the highest
  stressed point of the part and the one with the worst stress
  concentration.
- **Proportions**: moulding guides give gusset thickness 50–75 % of the
  wall and height up to about 2–3 × the wall. In FDM, thickness follows the
  rib rule above; make the gusset as long along both legs as the space
  allows, because its stiffness comes from its triangle, not its thickness.
- **Round or chamfer every gusset corner**, including the free edge where it
  meets each face.
- In build123d, root each rib or gusset into **both** faces it stiffens so
  the union is one solid ([[feature-recipes]]).

## Fillets and stress concentration

Sharp internal corners are, in DuPont's words, perhaps the leading cause of
failure of plastic parts: most plastics are notch-sensitive, and the peak
stress at a corner starts the crack. DuPont's plot for a cantilevered wall
(Fig. 3.07) gives the stress concentration factor against R/T, the fillet
radius over the wall thickness. It falls steeply from the sharp corner and
flattens past **R/T ≈ 0.5**, which is where the rule "fillet radius = half the
wall" comes from; a larger radius buys very little. Minimum radius 0.5 mm
even where the corner should look sharp.

For a hand calculation of a brittle part DuPont uses SCF 2 for a nicely
filleted design, 3 for normal, 4–6 for sharp corners
([[beam-and-plate-stiffness#safety-factors-for-printed-plastic]]).

FDM specifics:

- A fillet in the XY plane prints as a smooth curve; a fillet in a vertical
  plane is a staircase of layers, and its effective radius is only as good
  as the layer height. The layer line at the root of a vertical rib is a
  notch across the layers, the weakest direction
  ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]); give it
  a chamfer or fillet of several layers.
- For constant wall thickness around a bend, outer radius = inner radius +
  wall ([[printed-threads-and-bosses#bosses-ribs-and-fillets]]).
- A fillet smaller than about 1 mm does not print as a fillet
  ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]).

## Checks

```python
import math
assert RIB_T >= 2 * LINE_W, "rib thinner than two lines is dropped by the slicer"
assert RIB_H / RIB_T <= 10 or RIB_TIP_IN_TENSION, "tall thin rib buckles at its free edge"
assert RIB_GAP >= 2 * WALL, "slot between ribs narrower than two walls"
assert ROOT_FILLET >= 0.5 * WALL, "sharp rib root: DuPont fillet = 0.5 × wall"
I, yb = section_I([(PITCH, WALL, WALL / 2), (RIB_T, RIB_H, WALL + RIB_H / 2)])
sigma_tip = M * (WALL + RIB_H - yb) / I
assert sigma_tip * SCF <= STRENGTH / SAFETY, "rib tip overstressed: stiffness is not strength"
```
