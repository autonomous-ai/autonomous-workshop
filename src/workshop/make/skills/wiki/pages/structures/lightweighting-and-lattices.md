---
title: Lightweighting, pockets and lattices
tags: [lightweighting, pocket, lattice, honeycomb, sandwich, specific-stiffness, topology-optimization, infill]
aliases: [lightening hole, lightening pocket, weight reduction, mass reduction, gyroid, tpms, triply periodic minimal surface, strut lattice, octet truss, honeycomb core, sandwich panel, generative design, topology optimisation, cut-out, skeletonise]
sources:
  - Gibson and Ashby, Cellular Solids, 2nd ed., ch. 5 (honeycombs), ch. 7 (foams: E*/Es ∝ (ρ*/ρs)² bending-dominated)
  - Ashby, Materials Selection in Mechanical Design, ch. 5 (material indices E/ρ, E^1/2/ρ, E^1/3/ρ)
  - https://eclass.aegean.gr/modules/document/file.php/511165/projects/foams_lattices.pdf (Ashby 2006, Phil. Trans. R. Soc. A 364; stretch slope 1, bending slope 2, factor 10 at ρ = 0.1; via search excerpt, PDF not text-extractable here)
  - https://en.wikipedia.org/wiki/Sandwich_theory (D ≈ f (2h + f)² / 2 · E_face for thin faces, stiff faces over a soft core)
  - https://pdf.nauticexpo.com/pdf/hexcel-composites/honeycomb/20367-5902.html (Hexcel: 2t core 7 × stiffer at +3 % weight, 4t 37 × at +6 %; via search excerpt)
  - https://ficientdesign.com/i-beam-web-holes-neutral-axis/ (web holes on the neutral axis, d ≤ 2/3 web depth, spacing ≥ 3 d, away from supports)
  - https://2024.help.altair.com/2024.1/hwsolvers/os/topics/solvers/os/mfg_topology_opt_intro_c.htm (OptiStruct MINDIM 3–12 × element size)
  - https://www.researchgate.net/publication/226681416_Checkerboard_and_minimum_member_size_control_in_topology_optimization (checkerboards are an FEA artefact; via search excerpt)
  - https://help.prusa3d.com/article/infill-patterns_177130 (gyroid: equal strength in all directions; lightning: supports top surfaces only)
  - .venv/lib/python3.12/site-packages/build123d/__init__.py (build123d 0.11.1; lattice, pocket and triangle-face cost measured with it, reproducible)
related: [beam-and-plate-stiffness, ribs-and-stiffening, perimeters-infill-and-strength, wall-thickness-and-hollowing, print-time-and-material-estimation, text-patterns-and-surface-detail, boolean-pitfalls, unmeshable-faces, filament-properties, fdm-minimum-feature-sizes]
updated: 2026-09-23
---

# Lightweighting, pockets and lattices

Take material out only where it carries no stress, and remember that a printed
part is already a lattice: perimeters around sparse infill. Most "lightweight
lattice" ideas are best left to the slicer; CAD lightweighting is for pockets,
holes and sandwich sections you can reason about with a formula. Hollowing a
solid is [[wall-thickness-and-hollowing#hollowing-is-worth-less-than-the-volume-it-removes]];
buying stiffness with ribs is [[ribs-and-stiffening]].

## Specific stiffness: the material index decides nothing inside one material

`E/ρ` ranks materials for a tie; a beam of fixed shape but free size ranks by
`E^1/2/ρ`, a plate of free thickness by `E^1/3/ρ` (Ashby ch. 5). From
[[filament-properties#printed-specimen-properties-one-supplier-one-test-method]]:

| material | E X-Y MPa | ρ g/cm³ | E/ρ | E^1/3/ρ |
|---|---|---|---|---|
| PLA | 3427 | 1.17 | 2929 | 12.9 |
| PETG | 2117 | 1.25 | 1694 | 10.3 |
| PA6-CF, dry | 7453 | 1.17 | 6370 | 16.7 |

Removing material from one part does not change its `E/ρ`. What it changes is
**where** the remaining material sits: mass saved at the neutral axis costs
almost no stiffness, mass saved at the surface costs it cubically. That is the
whole of lightweighting.

## Lattices lose stiffness faster than they lose mass

Gibson–Ashby scaling, relative density `ρr = ρ*/ρs`:

```text
bending-dominated (foam, gyroid, most open cells)  E*/Es ∝ ρr²
stretch-dominated (triangulated, octet truss)       E*/Es ∝ ρr
```

At `ρr = 0.1` a bending-dominated lattice is about 10 × less stiff than a
stretch-dominated one (Ashby 2006), and a solid of the same mass is stiffer
than either **in direct load**. A lattice earns its place only as the core that
holds two stiff skins apart, where its job is shear, not bending. A printed
part with perimeters and infill is exactly that sandwich already
([[perimeters-infill-and-strength#perimeters-beat-infill-for-the-same-weight]]).

## Sandwich panels: separate the skins

For thin faces of thickness `f` on a core of thickness `c`, with stiff faces
over a soft core, the bending stiffness per unit width is

```text
D ≈ E_face · f · (c + f)² / 2          (face self-bending and core bending neglected)
```

Split a solid plate of thickness `t` into two `t/2` skins and move them apart:

| total depth | I relative to solid t | extra mass |
|---|---|---|
| t (solid) | 1 | — |
| 2t | ((2t)³ − t³)/t³ = 7 | core only |
| 4t | ((4t)³ − (3t)³)/t³ = 37 | core only |

Hexcel quotes the same 7 × and 37 × with a honeycomb core adding about 3 % and
6 % weight. A printed plate is this shape when it has enough top/bottom
layers and sparse infill between them: set the skin count in the slicer, do
not model the honeycomb. Model a CAD sandwich only when the core must be
visible, or the part is resin/SLS with no infill.

Sandwich failure modes to design against: core shear (core too sparse over a
short span), face wrinkling or dimpling (skin too thin for the cell span it bridges;
prove the cell size on a print), and local crushing under a point load (put a solid insert or boss there,
[[ribs-and-stiffening#gussets-on-bosses-brackets-and-corners]]).

## Holes on the neutral axis: web lightening

A hole of diameter `d` centred on the neutral axis of a web of depth `h`,
thickness `b`:

```text
I_net = b (h³ − d³) / 12            area removed = b · d
d = h/2  →  I drops 12.5 %, area drops 50 % at that section
d = 2h/3 →  I drops 30 %, area drops 67 %
```

Rules from beam practice (steel, applied as a starting point for plastic):

- Centre holes on the neutral axis, `d ≤ 2/3 h`.
- Keep them out of high-shear zones: near supports, under point loads, near a
  fixed root. Mid-span is best.
- Spacing ≥ 3 d between holes; ligament to the flange ≥ d/2.
- Fillet every corner of a non-circular cut-out; a sharp corner is a crack
  starter ([[ribs-and-stiffening#fillets-and-stress-concentration]]).

The same logic places pockets in a bracket: remove the triangle between the
load path and the support, keep the flanges and the two load-carrying legs.
That is a truss; triangulated openings behave stretch-dominated.

## A pocket in a printed part can add mass

A pocket turns sparse infill into solid perimeter along its walls. Pocket of
area `A`, wall perimeter `P`, depth `d`, infill fraction `φ`, shell thickness
`w` (perimeters × line width):

```text
saved   ≈ φ · A · d                  (infill no longer printed)
added   ≈ (1 − φ) · P · w · d        (infill region becomes shell)
worth it only when  A / P > w (1 − φ) / φ
```

At `φ = 0.15`, `w = 1.2 mm` (three 0.4 mm lines): `A/P > 6.8 mm`. A round hole
has `A/P = r/2`, so holes under about **27 mm diameter add mass** in that
region. Through-holes also remove top/bottom skins over `A`, which helps; blind
pockets do not. Small lightening holes in a printed part are cosmetic, not
structural, and they cost print time (more perimeters). Estimate with
[[print-time-and-material-estimation#mass-from-the-model-the-shell-plus-a-fraction-of-the-core]].

## Topology optimisation is a hint, not a result

This toolchain does not run topology optimisation. When a published or
supplied optimised shape is available, read it as a load-path diagram:

- Members it keeps are the load paths; rebuild them as straight struts, webs
  and flanges with named dimensions.
- Thin members and checkerboard patches are artefacts of the element size
  (OptiStruct recommends a minimum member of 3–12 × element size). Do not copy
  members thinner than the printable wall ([[fdm-minimum-feature-sizes]]).
- The optimiser solved one load case; add every other load (drop, handling,
  screw clamp) before trusting a removed region.
- Organic blends from the optimiser are loft/fillet traps
  ([[loft-pitfalls]]); a prismatic truss of the same topology is buildable and
  checkable with [[beam-and-plate-stiffness]].

## Lattices and TPMS in B-rep: measured cost

build123d 0.11.1 on this machine, reproducible with the snippets in the
source note:

| geometry | faces | build / boolean | tessellate | STEP |
|---|---|---|---|---|
| strut lattice 2×2×2 cells (27 Ø1.2 rods, fused) | 66 | 1.0 s | 0.4 s | 0.67 MB |
| strut lattice 3×3×3 (48 rods) | 144 | 2.6 s | 1.2 s | 1.9 MB |
| strut lattice 4×4×4 (75 rods) | 288 | 5.1 s | 2.5 s | 4.1 MB |
| hex pockets in a 4 mm plate, 5×5 | 181 | 0.12 s | — | 0.57 MB |
| hex pockets 10×10 | 706 | 0.8 s | — | 2.3 MB |
| hex pockets 20×20 | 2806 | 8.4 s | — | 9.5 MB |
| sphere as 2022 planar triangles | 2022 | 1.2 s | — | 4.8 MB |
| sphere as 8002 planar triangles | 8002 | 5.1 s | — | 19.7 MB |

- A strut lattice's STEP grows faster than its face count: every rod–rod
  intersection is a B-spline edge. Fuse time roughly doubles per extra cell
  along each axis; a 10 × 10 × 10 lattice is out of reach for an iterative run.
- build123d has no implicit-surface or TPMS primitive. A gyroid can enter a
  B-rep only as a mesh of planar triangles, at about **2.4 KB of STEP per
  triangle**. Illustratively, 1000 triangles per cell in a 10 × 10 × 10
  block is 10⁶ triangles, about 2.4 GB of STEP. That is a mesh wearing a
  STEP extension, not CAD.
- Every face is one more a later boolean carries and the mesher can decline
  ([[text-patterns-and-surface-detail#knurling-and-texture-are-face-count-bombs]],
  [[unmeshable-faces]]). Cut all pockets in one list boolean
  ([[boolean-pitfalls#multi-tool-booleans]]), last in the feature order.

## Let the slicer build the lattice

For FDM, slicer infill is the right lattice almost always: gyroid infill is
near-isotropic and costs no CAD faces; density can be raised locally with a
modifier region; the STEP stays small. Model a lattice only when it is **seen**
(a visible grille, a designed cosmetic pattern), when the cell must meet a
dimension (airflow area, a sieve), or when the process has no infill (resin,
SLS). Lightning infill supports top skins only and carries no load: never
choose it for a structural part. Write the infill pattern and density the
stiffness claim depends on into the spec.

## Cosmetic cut-outs versus structural ones

| | cosmetic / functional pattern | structural lightening |
|---|---|---|
| purpose | look, ventilation, grip, see-through | mass or print time |
| where | anywhere the load allows | neutral axis, low-shear zones |
| sized by | pitch ≥ 2 line widths, open area | `d ≤ 2/3 h`, spacing ≥ 3 d, `A/P` break-even |
| cost | faces; add last | stiffness; check the section |

A cosmetic grille across a load path is structural whether you meant it or
not: check the ligament between openings as a wall
([[wall-thickness-and-hollowing#a-repeated-features-count-is-a-wall]]).

## Checks

```python
assert d_hole <= 2 / 3 * web_h, "lightening hole too large for the web"
assert pitch >= 3 * d_hole, "lightening holes too close"
assert abs(hole_z - neutral_axis_z) < 0.1 * web_h, "hole off the neutral axis"
I_net = b * (web_h**3 - d_hole**3) / 12
assert I_net >= I_required, "lightened web under the required stiffness"
# printed pocket must save more infill than it adds in shell
assert pocket_area / pocket_perim > shell_w * (1 - infill) / infill or COSMETIC
assert len(part.faces()) <= face_budget, "lattice/pattern over the face budget"
assert not lattice_in_cad or process in ("resin", "sls") or LATTICE_IS_VISIBLE
```
