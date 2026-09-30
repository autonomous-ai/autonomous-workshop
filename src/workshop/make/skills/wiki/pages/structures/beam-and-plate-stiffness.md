---
title: Beam and plate stiffness
tags: [beam, plate, stiffness, deflection, second-moment, section, torsion, buckling, safety-factor, bracket]
aliases: [moment of inertia, area moment, second moment of area, section modulus, cantilever deflection, plate deflection, torsion constant, euler buckling, column buckling, local buckling, bracket sizing, arm sizing, sag]
sources:
  - Roark's Formulas for Stress and Strain, ch. 8 (beams), ch. 10 (torsion, thin-walled closed sections), ch. 11 (flat plates), ch. 15 (elastic stability)
  - Shigley's Mechanical Engineering Design, ch. 4 (deflection and stiffness, Euler columns)
  - https://www.engineeringtoolbox.com/cantilever-beams-d_1848.html (cantilever δ = F L³/3EI, q L⁴/8EI)
  - https://en.wikipedia.org/wiki/Deflection_(engineering) (simply supported cases)
  - https://en.wikipedia.org/wiki/Torsion_constant (thin open section J = U t³/3)
  - https://en.wikipedia.org/wiki/Euler%27s_critical_load (P = π² E I / (K L)², K per end condition)
  - http://academic.sun.ac.za/mad/catalogs/dfmguidelines/dupontgeneraldesignprinciples.pdf (DuPont General Design Principles, Module I, ch. 4 and Tables 4.03, 4.05, 4.06; safety factors p. 22)
  - https://eng.libretexts.org/Under_Construction/Aerospace_Structures_(Johnson)/11:_Buckling_of_columns_and_plates/11.01:_Compression_buckling_of_thin_rectangular_plates (plate buckling σcr)
  - https://www.insdag.com/assets/frontend/trmpdf/Chapter7.pdf (buckling coefficient k = 4 internal, 0.425 outstand)
related: [shafts-and-bearings, snap-fit-design, layer-anisotropy, creep-and-stress-relaxation, filament-properties, perimeters-infill-and-strength, fdm-print-orientation-for-strength, wall-thickness-and-hollowing, noise-and-vibration, lightweighting-and-lattices]
updated: 2026-09-23
---

# Beam and plate stiffness

A printed arm, bracket, lid or frame almost always bends too far before it
breaks, so size it for deflection first and check stress second. Every
structural member reduces to one of four cases on this page: a beam in
bending, a plate under pressure, a section in torsion, or a column in
compression. [[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]]
applies the beam case to shafts; [[ribs-and-stiffening]] is how to buy the
second moment of area cheaply.

## Beam deflection: the four cases

Euler–Bernoulli beam, modulus E, second moment of area I, length (span) L:

| case | max deflection | where | max moment |
|---|---|---|---|
| cantilever, end load F | `F L³ / (3 E I)` | free end | `F L` at the root |
| cantilever, uniform load q (N/mm) | `q L⁴ / (8 E I)` | free end | `q L² / 2` at the root |
| simply supported, centre load F | `F L³ / (48 E I)` | mid-span | `F L / 4` |
| simply supported, uniform load q | `5 q L⁴ / (384 E I)` | mid-span | `q L² / 8` |
| both ends fixed, centre load F | `F L³ / (192 E I)` | mid-span | `F L / 8` |

Bending stress at the outer fibre: `σ = M c / I = M / Z`, c the distance
from the neutral axis to that fibre. A cantilever deflects 16 × a simply
supported beam of the same span under the same load; supporting the free end
is usually the cheapest stiffness there is. Deflection goes with **L³**:
halving the reach of an arm makes it 8 × stiffer.

## Second moment of area of common sections

Bending about the horizontal axis through the centroid; B, H outer width and
height, t wall, tw web, tf flange:

```text
rectangle            I = b h³ / 12
round rod            I = π d⁴ / 64
round tube           I = π (D⁴ − d⁴) / 64
rectangular tube     I = (B H³ − (B − 2t)(H − 2t)³) / 12
I-beam (symmetric)   I = (B H³ − (B − tw)(H − 2 tf)³) / 12
C-channel, web vertical, bending about the strong axis: same as the I-beam
T and L sections     centroid first:  ȳ = Σ Aᵢ yᵢ / Σ Aᵢ
                     I = Σ (Iᵢ + Aᵢ (yᵢ − ȳ)²)          (parallel-axis theorem)
```

Compute an unsymmetric section with the parallel-axis sum rather than a
memorised formula: split it into rectangles, and the same code serves T, L,
C-about-the-weak-axis and a ribbed plate ([[ribs-and-stiffening#the-rib-versus-thicker-wall-calculation]]).

```python
def section_I(rects):            # rects: [(b, h, y_centre), ...]
    A = sum(b * h for b, h, _ in rects)
    yb = sum(b * h * y for b, h, y in rects) / A
    I = sum(b * h**3 / 12 + b * h * (y - yb)**2 for b, h, y in rects)
    return I, yb
```

## Depth beats width, and material belongs at the surface

For a rectangle, I grows with h³ and only with b. The same 40 mm² strip as a
cantilever, L = 60 mm, F = 20 N, E = 2300 MPa (printed PLA, X-Y,
[[filament-properties]]):

| section b × h | I, mm⁴ | tip deflection | root stress |
|---|---|---|---|
| 10 × 4 (flat) | 53 | 11.7 mm | 45 MPa |
| 4 × 10 (on edge) | 333 | 1.9 mm | 18 MPa |

Same material, same print time, 6 × stiffer. Put the long side of the
section in the plane of the bend.

A tube places its material far from the axis. A Ø10 rod and a Ø16 × 1.75 mm
wall tube have the same area; the tube has about 4 × the I. That is also why
a printed part's perimeters carry most of a bending load and its infill little
([[perimeters-infill-and-strength#perimeters-beat-infill-for-the-same-weight]]):
for a conservative stiffness, compute I of the perimeter shell alone, as a
tube, and treat sparse infill as absent.

Holes on the neutral axis and sandwich panels:
[[lightweighting-and-lattices]].

## Plates under uniform pressure

A flat panel (a lid, a floor, an enclosure wall someone presses) of thickness
t, short side a, long side b, uniform pressure p. Coefficient form from
DuPont Table 4.06 (Roark), ν ≈ 0.3–0.35:

```text
edges simply supported   y_max = 0.142 p a⁴ / (E t³ (1 + 2.21 (a/b)³))       centre
                         σ_max = 0.75  p a² / (t² (1 + 1.61 (a/b)³))          centre
edges clamped            y_max = 0.0284 p a⁴ / (E t³ (1 + 1.056 (a/b)⁵))      centre
                         σ_max = 0.50  p a² / (t² (1 + 0.623 (a/b)⁶))         middle of the long edge
circular, radius r:
edges simply supported   y_max = 3 p (1 − ν)(5 + ν) r⁴ / (16 E t³)
edges clamped            y_max = 3 p (1 − ν²) r⁴ / (16 E t³),  σ_max = 3 p r² / (4 t²) at the edge
```

For a square plate the coefficients reduce to 0.0442 (supported) and 0.0138
(clamped), Roark's tabulated values; a long strip tends to 0.142 and 0.0284.
Consequences:

- deflection goes with **a⁴ / t³**: halve the unsupported span and the panel
  is 16 × stiffer; double the thickness and it is 8 × stiffer. A rib that
  halves the span is cheaper than thickness ([[ribs-and-stiffening#cross-ribbing-a-plate]]);
- clamping the edges (walls moulded to the panel, not a lid resting on a
  ledge) cuts deflection by 3–5 ×;
- the formulas are small-deflection theory: once `y_max` passes about half
  of t, membrane action stiffens the plate and the linear result is
  conservative.

Worked: an 80 × 80 × 2 mm PLA lid, supported edges, 10 kPa (a palm press
spread over the lid) → 0.98 mm; clamped → 0.31 mm.

A thin panel is also a resonator: [[noise-and-vibration]].

## Torsion: close the section

Twist `θ = T L / (G K)`, G ≈ E / (2 (1 + ν)), K the torsion constant:

```text
solid round               K = π r⁴ / 2
round tube                K = π (r₀⁴ − r₁⁴) / 2 ≈ 2 π r³ t (thin)
any thin closed section   K = 4 A² / ∮ ds/t   = 4 A² t / U for uniform t   (Bredt)
any thin open section     K = U t³ / 3          (U = median-line length)
solid rectangle b ≥ a     K ≈ a³ b (1/3 − 0.21 (a/b)(1 − a⁴ / (12 b⁴)))
```

A is the area enclosed by the wall's median line. Slit a tube along its
length and K drops from `2π r³ t` to `(2/3) π r t³`, a ratio of `3 (r/t)²`:
a Ø20 × 1.2 mm tube loses about 200 × its torsional stiffness when it is cut
open. An open channel, an L or a U-shaped printed arm twists like a sheet of
paper. Anything that twists (a lever, a long arm with an offset load, a
box that racks) wants a closed section, or a lid that closes it: a box
without its lid is an open section.

## Buckling: slender columns and thin walls

A column in compression fails by buckling before it crushes once it is
slender. Euler, with the minimum I of the section:

```text
P_cr = π² E I / (K L)²
K = 2.0 fixed–free (flagpole), 1.0 pinned–pinned, 0.7 fixed–pinned, 0.5 fixed–fixed
```

A Ø4 printed PLA post 60 mm tall, fixed at the base and free at the top,
buckles at about 20 N. DuPont applies a safety factor of 3–4 to P_cr for
plastics, and uses the tangent modulus at the working stress; for a printed
part use the Z modulus if the post stands up ([[layer-anisotropy]]).

Thin walls buckle locally, as plates, under in-plane compression or shear:

```text
σ_cr = k π² E / (12 (1 − ν²)) · (t / b)²
k = 4     long plate, both long edges supported (a box wall, a tube face)
k = 0.425 one long edge free (an outstanding flange, a free rib edge)
k ≈ 7     both long edges clamped
```

A free-edged flange is about ten times weaker in local buckling than the
same plate held on both edges: turn a free edge over (a lip, a return flange)
or tie it to a neighbour wall. A tall thin rib under compression along its
free edge is exactly this case ([[ribs-and-stiffening#rib-height-and-thickness]]).

## Safety factors for printed plastic

A printed member's calculated capacity is an estimate with a wide spread.
Stack the factors explicitly rather than choosing one number:

- **Material allowable.** DuPont suggests `S = 1.5–2.0` on yield for static
  loads in moulded, isotropic parts. Printed parts start from a weaker base:
  if the stress crosses the layers, use the Z strength, about 0.3 × X-Y
  without measured data ([[layer-anisotropy#how-much-weaker-across-the-layers]]).
- **Stress concentration.** For brittle materials (elongation at break
  under 5 %) DuPont applies SCF 2 nicely filleted, 3 normal design, 4–6 sharp
  corners ([[ribs-and-stiffening#fillets-and-stress-concentration]]).
- **Sustained load.** A load that stays on creeps; use a large factor and a
  creep-resistant material ([[creep-and-stress-relaxation#design-rules]]).
  DuPont's long-term vessel example uses 3 on the 10-year stress.
- **Buckling.** 3–4 on P_cr (DuPont).
- **Stiffness.** Use the printed-specimen modulus, not the filament's, and
  lower it further for sparse infill or heat
  ([[heat-resistance-of-printed-parts]]).

The factor on stiffness is a deflection budget, not a strength margin: state
the allowed deflection (a gap that must not close, a mesh that must not
separate) and assert against it.

## Checks

```python
import math
I = B * H**3 / 12                                     # or section_I(...) for a built-up section
delta = F * L**3 / (3 * E_PRINT * I)                  # cantilever arm
assert delta <= DEFLECTION_BUDGET, f"arm sags {delta:.2f} mm"
sigma = F * L * (H / 2) / I
assert sigma * SCF <= STRENGTH / SAFETY, f"root stress {sigma:.1f} MPa"
assert H >= B or not BENDS_ABOUT_WIDTH, "section lies flat in the bend plane"
P_cr = math.pi**2 * E_PRINT * I_MIN / (K_END * L_COL)**2
assert P_cr >= 3 * P_AXIAL, "column buckles inside a factor of 3"
y = 0.142 * p * a**4 / (E_PRINT * t**3 * (1 + 2.21 * (a / b)**3))
assert y <= PANEL_BUDGET, f"panel bows {y:.2f} mm"
```
