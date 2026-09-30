---
title: Designing power paths and wiring
tags: [power, wiring, voltage, current, protection, battery, wire, strain-relief, circuit, electrical]
aliases: [power boundary, source to return path, wire routing, stall current, fuse, inlet, wiring harness, cable envelope]
sources:
  - skills/electromechanical-integration/SKILL.md
  - skills/electromechanical-integration/references/power-manifest.md
  - skills/electromechanical-integration/scripts/check_power
related: [electrical-component-selection, lighting-design, energy-drive, battery-cells-and-packs, wire-gauge-and-connectors, motor-drivers-and-flyback]
updated: 2026-09-23
---

# Designing power paths and wiring

A mounted electrical part is not a powered product. Trace every functional
load from its source and back, and reserve real CAD space for every carried
component and every wire route. Mechanical drive sizing is in [[energy-drive]].

## The product boundary

State whether power is **onboard** (the product carries its source) or
**external**. Inventory every functional electrical load, and name the source,
protection, switching/control, connectors, conductors and return path that
cross the boundary. An external supply still needs a modelled inlet or lead.

## One complete path per independently rated branch

- Each path begins and returns at its source and contains protection (or a
  sourced justification for none), switching/control, interconnects,
  conductors, and exactly **one** actuator or other load.
- **Voltage containment:** check the full source-voltage range, not the
  nominal, against every inline component. The source interval must fit
  inside every non-wire component's rated interval.
- **Current capacity:** size continuous *and* peak capacity against the load's
  worst case. For an actuator that means running and stall/start current. For
  a general load, continuous and peak current. Every source, protection,
  switch, controller, connector, inlet and wire on the path must meet both.
- **Parallel lights get separate paths** unless they are one
  manufacturer-rated module or strip. Use a separate path for each source, or
  for each independently protected actuator circuit.
- **Protection and control are decisions.** Each is either present, with a
  component on the path, or not required, with a written justification and
  evidence. A consistency checker verifies that the decision is declared, not
  that it is correct.

## Wires are solids

- A wire route is geometry: insulation diameter, bend room, connector
  insertion/removal space and service loops. A centerline or a wiring diagram
  alone is not a collision check.
- Every route needs strain relief, a positive clearance envelope, and service
  access.
- Holders, hatches, channels, clips, strain relief, visible lenses, bezels and
  diffusers are product geometry, and they appear in the render. A bought
  battery, a hidden controller or a flexible loom may be a validation-only
  envelope: kept out of the render, but still placed in the assembly for
  clash measurement.
- Use catalog STEP where it exists. Otherwise use a sourced, documented
  envelope, labelled as an envelope rather than as vendor geometry.

## What no rigid-geometry check certifies

Declared ratings being consistent does not certify a circuit, battery pack,
thermal design, EMI behaviour, optical compliance or physical prototype.
Seated clash is a geometry question, insertion and retention are motion
questions, and physical fit is answered only by a coupon with the exact
hardware ([[removable-lamp-interfaces#physical-fit-needs-a-real-hardware-coupon]]).
Never report "physically fits" from CAD alone.

Powered work is incomplete while any of these is open: a missing rating, an
unresolved protection decision, an absent carried mount, an unmodelled wire
route, an unidentified visible optic, an unresolved removable mate, or an
unrecorded catalog search.
