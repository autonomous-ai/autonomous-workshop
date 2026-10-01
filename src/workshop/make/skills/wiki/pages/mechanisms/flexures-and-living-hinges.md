---
title: Flexures, living hinges and compliant mechanisms
tags: [flexure, living-hinge, compliant-mechanism, prbm, bistable, fatigue, strain, pivot, torsion, tpu]
aliases: [flexure hinge, flexure bearing, integral hinge, pseudo-rigid-body model, compliant joint, notch hinge, leaf spring hinge, flexure pivot, flexural pivot, cross-spring pivot, cross spring pivot, cross-strip pivot, cross-axis flexural pivot, crossed leaf pivot, free-flex pivot, Bendix flex pivot, cartwheel hinge, cartwheel flexure, butterfly pivot, butterfly flexure, LET joint, lamina emergent torsional joint, lamina emergent mechanism, split-tube flexure, split tube hinge, Q-joint, quadrilateral joint, four-bar flexure, remote centre pivot, virtual pivot, circular notch hinge, Paros-Weisbord, spiral flexure, spiral arm flexure bearing, helical flexure, ortho-planar spring, compliant ortho-planar spring, TPU hinge, TPU flexure, printed flexure joint, compliant gripper finger]
sources:
  - https://en.wikipedia.org/wiki/Compliant_mechanism (definition, advantages, no continuous rotation, fatigue, PRBM)
  - https://en.wikipedia.org/wiki/Flexure_bearing (no friction or lubrication, limited range, fatigue)
  - https://github.com/Kartik17/Compliant-Mechanism/blob/master/README.md (PRBM gamma 0.85, K_theta 2.65, k = K_theta E I / l, S_y/E)
  - "Howell and Midha pseudo-rigid-body model: small-length flexural pivot K = E I / L (search summary of the literature)"
  - https://stuff.mit.edu/afs/athena/course/2/2.75/resources/random/Living%20Hinge%20Design.pdf (polypropylene living hinge design, thickness, land, cold drawing, tearing)
  - https://www.firgelliauto.com/blogs/mechanisms/living-hinge (strain formula, material strain limits)
  - https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/ (printed hinge thickness and cycle counts by process)
  - https://www.jpe-innovations.com/precision-point/cross-spring-pivot/ (cross-spring K = 8(1 − 3a + 3a²) EI/L, 2EI/L at mid-crossing, θ = 2σL/(Et), buckling 8π²EI/L², Haberland crossing)
  - https://precenglab.riteh.uniri.hr/wp-content/uploads/2016/10/Optimised-Cross-Spring-Pivot-Configurations-with-Minimised-Parasitic-Shifts-and-Stiffness-Variations-Investigated-via-Nonlinear-FEA.pdf (Markovic and Zelenika 2016: cartwheel up to 8 x less shift at about 4 x stiffness and stress; butterfly a further 4 x; crossing at 0.1–0.13 L)
  - https://esmats.eu/esmatspapers/pastpapers/pdfs/2003/heneindroz.pdf (Henein et al. 2003, butterfly pivot: four pivots in series sharing one axis, 20–30 deg strokes, 65 x less centre shift than a cross-spring pivot)
  - https://www.precisionmechatronicslab.com/wp-content/uploads/2017/11/Yong_Review.pdf (Yong et al. 2008: Paros–Weisbord simplified circular-notch compliance and its t/R validity)
  - https://patents.google.com/patent/US9157497B1/en (LET joint: torsion bars in a sheet, k_eq, Roark torsion constant, w > t)
  - https://patents.google.com/patent/US6585445B1/en (split-tube flexure: axis on the wall opposite the slit, t < 0.15 R, 150 deg, off-axis stiffness 3–4 orders higher)
  - https://patents.google.com/patent/US20040021123A1/en (compliant ortho-planar spring: platform moves without rotating, odd leg counts more stable, σ_max = 3 δ E c / L²)
  - https://www.jmsse.in/files/321haribhau%20et.%20al.pdf (spiral-arm flexure bearing: high radial, low axial stiffness; peak stress at the slot ends)
  - https://arxiv.org/pdf/2401.16463 (one-shot TPU hand: PLA failed by plastic deformation; 10,000 grasps at about 75 N; TPU 95A 26 MPa, 85A 12 MPa)
  - https://arxiv.org/pdf/2207.00721 (monolithic compliant delta in TPU 95A, PP or PLA: 0.41 mm living hinges, two orthogonal hinges as a universal joint)
  - https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0336401 (printed TPU 95A joints: raster angle sets stiffness, density sets damping)
  - https://arxiv.org/pdf/2203.07130 (printed notch flexures: isotropic model 5 % off in one direction, 68–74 % in another)
  - Norton, Design of Machinery, ch. 6 (four-bar instant centre at the crossing of the two side links)
  - "Howell, Quadrilateral joints (Q-joints) in compliant mechanisms, 10th World Congress on TMM (title only; via search summary)"
related: [joints, springs, cams-intermittent, mechanism-design, hinges-and-pin-joints, fluid-fittings-and-pneumatics, rolling-contact-joints, flexure-materials-and-snap-strain, beam-and-plate-stiffness, shaft-couplings, layer-anisotropy, posable-figure-joints, arm-and-gripper-sizing]
updated: 2026-10-01
---

# Flexures, living hinges and compliant mechanisms

A compliant mechanism moves by bending its own material instead of sliding at
a joint. It has no backlash, no wear surfaces and no lubrication, and it prints
in one piece. The costs are a limited range, a restoring force, and fatigue at
the flexure. No purely compliant joint can turn continuously.

Pinned (knuckle) hinges are in [[hinges-and-pin-joints]].

## Flexure types

| flexure | behaviour | use |
|---|---|---|
| **small-length flexural pivot** (short thin web; a "living hinge" when very short) | acts like a pin at the web centre with a torsional spring | lids, clips, toy joints |
| **long leaf (cantilever) flexure** | large deflection, the pivot drifts as it bends | springs, grippers |
| **notch (circular, elliptical, corner-filleted)** | precise axis, small angle, stress concentrated in the notch | precision stages, levers |
| **cross-axis / cross-spring pivot** | two leaves crossing in an X; larger angle with less axis drift | rotary stages, compliant walkers |
| **cartwheel hinge** | the cross-spring's leaves joined where they cross, in one piece | a stiffer pivot with much less centre shift |
| **butterfly pivot** | four cross-spring pivots in series on one shared axis, each taking a quarter of the stroke | the largest angle with the least drift; complex to make |
| **quadrilateral (four-bar) pivot, Q-joint** | two leaves that do not cross; the body turns about where their lines meet, a moving virtual centre | remote-centre pivots, an axis inside air |
| **LET (lamina emergent torsion) joint** | torsion bars cut in a flat sheet; the flap rotates out of the sheet's plane | large angles from a flat print; low off-axis stiffness |
| **split-tube flexure** | a thin tube slit along its length twists; the axis lies on the wall opposite the slit | long-travel hinge (≈ 150°) with high off-axis stiffness |
| **spiral flexure (flexure bearing)** | a disc with spiral arms: soft along its axis, stiff radially; stack two | guiding a plunger or piston without sliding |
| **helical flexure (beam coupling)** | helical slots in a tube: bends, stays stiff in twist | shaft couplings ([[shaft-couplings#choosing-by-misalignment]]) |
| **compliant ortho-planar spring** | a platform joined to its base ring by legs cut in one sheet; moves out of plane without rotating | valves, buttons, springy pads |
| **TPU section** | a rubber web that springs back to its printed pose | grippers, return-to-rest limbs (below) |

Pressure-driven compliant actuators: [[fluid-fittings-and-pneumatics]].
Joints that roll on crossed bands instead of bending: [[rolling-contact-joints]].

## Stiffness of the common pivots

```text
cross-spring pivot, leaves of length L, width w, thickness t, crossing at a·L from one block, I = w t³ / 12
    K     = 8 (1 − 3a + 3a²) E I / L        crossing at mid-length (a = 0.5): K = 2 E I / L
    θ_max = 2 σ_max L / (E t)                (a = 0.5)
    F_b   = 8 π² E I / L²                    radial load that buckles the leaves
circular notch hinge (Paros–Weisbord, simplified), cut radius R, neck t, width b
    θ / M = 9 π R^½ / (2 E b t^(5/2))        within about 5 % for 0.05 ≤ t/R ≤ 0.2
LET joint (outside form), torsion bars and one bending segment
    k_eq  = 2 k_T k_B / (k_T + 2 k_B),   k_T = K G / L_T,   k_B = E I_B / L_B
split tube, radius r, wall t
    K_open = (2/3) π r t³   against K_closed = 2 π r³ t: a ratio of 3 (r/t)²
```

K for the rectangular torsion bars and the open and closed tubes is in
[[beam-and-plate-stiffness#torsion-close-the-section]]. The LET formula
assumes bar width w > t.

- **Cross-spring centre shift.** Crossing at mid-length shifts the centre
  as it turns. Crossing at about 0.13 L (0.5 − √5/6) nearly removes the
  shift, at about a third of the angular range. A cartwheel cuts the shift
  by up to 8 ×, but its stiffness and leaf stress rise about 4 ×. A butterfly
  cuts it about 4 × more, with stress about 2 × the plain pivot's, because
  the shift grows faster than the angle and each of its stages turns only a
  quarter of the stroke. A radial load near F_b makes the pivot's stiffness
  go negative.
- **Notch hinges** soften as `t^(−5/2)`. A tenth of a millimetre of print
  error on a 1 mm neck moves the stiffness by about 25 %. Prefer leaf
  flexures where the print sets the thickness.
- **Quadrilateral pivots** turn about the four-bar instant centre, where the
  two leaf lines cross. That centre can lie outside the part, and it moves
  as the joint turns ([[linkages#four-bar]]).
- **LET joints** balance out-of-plane forces only when the bars are
  symmetric about the flap. They suit a flat FDM print with the bars' length
  along the strands.
- **Split tube**: keep t < 0.15 r. The twist puts shear on the tube's cross
  sections. A tube printed upright carries that shear across every layer
  weld, so print it lying down ([[layer-anisotropy]]). At two perimeters
  (0.8 mm) the radius must be more than 5.3 mm.
- **Ortho-planar spring**: small-deflection peak stress
  `σ_max ≈ 3 δ E c / L²` (δ platform travel, c half the leg thickness, L leg
  length). Odd leg counts are more stable than even ones.
- **Spiral arms** peak in stress at the ends of the slots, so radius the
  slot ends. Unlike a helical spring, the disc has no tendency to buckle and
  is very stiff radially.

## Stiffness: the pseudo-rigid-body model

Model each flexible segment as a rigid link on a pin with a torsional spring:

```text
small-length flexural pivot     K = E I / L                     pin at the web centre
cantilever with an end force    K = γ · K_Θ · E I / l,   γ ≈ 0.85, K_Θ ≈ 2.65
                                pin at (1 − γ) l from the fixed end
I = w t³ / 12                   w width, t thickness
```

Stiffness scales with `t³`: halving the thickness makes the flexure 8×
softer.

## Strain decides life

A web of thickness `t` bent through angle `θ` over land length `L_land` bends
about a radius `R ≈ L_land / θ` (θ in radians). Peak outer-fibre strain:

```text
ε_max = t / (2R + t)
```

For a given angle, a longer land and a thinner web lower the strain. The
material index for how far a flexure can bend is `S_y / E` (yield strength
over modulus). Polypropylene and nylon are high; PLA is low: printed PLA
yields at about 25 MPa with an ultimate strength of 31 MPa in one test.

## Material limits

- **Polypropylene** living hinges survive about 40 % strain for 1M+ cycles.
  Molded PP homopolymer hinges have been flexed through 180° some 900,000
  times across −28 to 23 °C without failure. Stress whitening on the first
  flex is normal.
- **Polyethylene**: low-cycle only. **Acetal, nylon** (molded): a few thousand
  cycles at most. **ABS, polystyrene**: snap on the first or second fold.
- **Printed hinges** are far weaker than molded ones. Guidance:
  - FDM: 0.4–0.6 mm thick with at least two layers; under ~0.3 mm tears and
    over ~0.8 mm will not flex. Nylon, PP, PETG or TPU. One reference
    example lasted about 25 cycles.
  - SLS PA11/PA12: 0.3–0.8 mm thick, at least 5 mm long, about 30–50 cycles.
  - Make the hinge length about 8–12 × its thickness, meeting the rigid walls
    at right angles.
  - Orient the hinge so it bends *within* the layers (layers parallel to the
    bending plane), never across a layer line.
  - Annealing can extend life.

## Molded living-hinge rules

These rules are for molding, but they are the reference geometry.

- Start the web thin, 0.20–0.25 mm, and adjust up to at most 0.38 mm.
  Thicker webs orient poorly and flex-life drops; under 0.20 mm the web
  under-fills.
- Land length is typically 1.5 mm. Radius every corner into the web, and keep
  the hinge line straight: a hinge cannot form along a curved centreline.
- Flow must cross the hinge perpendicular to it. Flex the part a few times
  while it is still warm (cold drawing) to orient the web.
- To stop tearing at the ends under twist, thicken both ends from 0.25 to
  0.50 mm over 0.5–1.0 mm, or radius the ends. Split hinges longer than about
  150 mm into sections.

## TPU flexure joints in figures and grippers

TPU is a rubber, not a spring ([[flexure-materials-and-snap-strain#flexures-and-printed-springs]]).
A TPU joint returns to its printed pose and holds no other pose. Use it
where return-to-rest is wanted: gripper fingers that reopen, tails,
antennae, bumpers. A posable limb needs a friction joint
([[posable-figure-joints]]).

- **Modulus.** About 26 MPa for TPU 95A and 12 MPa for 85A in two papers,
  against roughly 2.3–3.4 GPa for PLA. Bending stiffness goes as E t³, so a
  TPU web with a hundredth of the modulus needs about 4.6 × the thickness to
  match a PLA web's stiffness.
- **One-shot hands.** Fingers, flexure joints and band tendons printed in
  one TPU job survived 10,000 grasps at about 75 N of tendon force with no
  plastic deformation. The same design in PLA failed by rapid plastic
  deformation in flexion. The bands were printed tied to the links by thin
  support bridges that tear on the first flexion.
- **Monolithic linkages.** A whole compliant delta parallelogram has been
  printed in TPU 95A, PP or PLA, with 0.41 mm living hinges and 4.5 mm links.
  Two orthogonal living hinges make a universal joint. Keep their offset
  near zero, or it shows up as position error. Such a print repeats well but
  is not accurate.
- **Print settings change stiffness.** For printed TPU 95A joints, raster
  angle moved stiffness the most (highest at 45°). Finer layers raised
  stiffness and damping. Infill density mostly changed damping. Fix the
  slicer profile in the spec with the geometry.
- **Isotropic formulas misjudge printed flexures.** One printed notch-flexure
  device matched its isotropic model within 5 % in one direction and missed
  by 68–74 % in another. Treat every number on this page as a starting point
  for a test coupon ([[layer-anisotropy]]).

## Bistable mechanisms

A compliant mechanism with two stable positions snaps between them: a toggle
switch or a clip that holds open. Stability comes from a stored-energy
maximum between the two states. The pseudo-rigid-body model with springs
gives the energy curve. Design the peak force to be reachable, and check that
the strain at the peak is inside the material limit above.

## Checks

- Asserts: `ε_max` below the material limit at the full design angle, web
  thickness ≥ 2 layers, and hinge length 8–12 × thickness.
- A rigid sweep cannot bend a flexure. Model the flexure as a pin plus spring
  for the kinematics, sweep that rigid model, and record flex life and
  restoring force as open items ([[mechanism-verification#9-what-nothing-here-proves]]).

```python
import math
I = LEAF_W * LEAF_T**3 / 12
K_cross = 8 * (1 - 3 * A_CROSS + 3 * A_CROSS**2) * E * I / LEAF_L
theta_max = 2 * SIGMA_ALLOW * LEAF_L / (E * LEAF_T)                 # mid-crossing pivot
assert math.radians(PIVOT_RANGE_DEG) <= theta_max, "cross-spring leaves overstressed at full angle"
assert F_RADIAL < 8 * math.pi**2 * E * I / LEAF_L**2 / SF_BUCKLE, "radial load buckles the leaves"
assert 0.05 <= NOTCH_T / NOTCH_R <= 0.2 or not USES_PAROS_WEISBORD, "notch formula outside its range"
assert SPLIT_TUBE_T < 0.15 * SPLIT_TUBE_R, "split tube too thick-walled to twist like an open section"
assert MATERIAL != "TPU" or not HOLDS_POSE, "a TPU flexure springs back; it cannot hold a pose"
```
