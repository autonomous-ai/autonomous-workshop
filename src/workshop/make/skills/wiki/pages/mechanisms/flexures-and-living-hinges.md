---
title: Flexures, living hinges and compliant mechanisms
tags: [flexure, living-hinge, compliant-mechanism, prbm, bistable, fatigue, strain]
aliases: [flexure hinge, flexure bearing, integral hinge, pseudo-rigid-body model, compliant joint, notch hinge, leaf spring hinge]
sources:
  - https://en.wikipedia.org/wiki/Compliant_mechanism (definition, advantages, no continuous rotation, fatigue, PRBM)
  - https://en.wikipedia.org/wiki/Flexure_bearing (no friction or lubrication, limited range, fatigue)
  - https://github.com/Kartik17/Compliant-Mechanism/blob/master/README.md (PRBM gamma 0.85, K_theta 2.65, k = K_theta E I / l, S_y/E)
  - "Howell and Midha pseudo-rigid-body model: small-length flexural pivot K = E I / L (search summary of the literature)"
  - https://stuff.mit.edu/afs/athena/course/2/2.75/resources/random/Living%20Hinge%20Design.pdf (polypropylene living hinge design, thickness, land, cold drawing, tearing)
  - https://www.firgelliauto.com/blogs/mechanisms/living-hinge (strain formula, material strain limits)
  - https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/ (printed hinge thickness and cycle counts by process)
related: [joints, springs, cams-intermittent, mechanism-design, hinges-and-pin-joints, fluid-fittings-and-pneumatics]
updated: 2026-09-23
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
| **cross-axis / cartwheel** | two crossing leaves; larger angle with less axis drift | rotary stages, compliant walkers |

Pressure-driven compliant actuators: [[fluid-fittings-and-pneumatics]].

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
