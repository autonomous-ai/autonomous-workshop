---
title: Selecting electrical components
tags: [component, selection, motor, servo, battery, connector, led, mpn, datasheet, gate]
aliases: [choose a motor, pick a part number, hard gates, selection contract, drop-in replacement, part substitution]
sources:
  - skills/electromechanical-integration/references/component-selection.md
  - skills/electromechanical-integration/SKILL.md
related: [power-path-design, lighting-design, removable-lamp-interfaces, energy-drive]
updated: 2026-09-23
---

# Selecting electrical components

The goal is not the closest catalog name. It is an exact purchasable part whose
complete powered and physical integration is supported by evidence. This
applies to any motor, servo, solenoid, battery, converter, controller, switch,
connector, LED, lamp, light module or other carried electrical hardware. For
the mechanical side of a drive (ratio, torque budget), see
[[energy-drive#ratio-budget]].

## Start from a measurable contract

Translate the request and the approved exterior into measurable constraints
before searching. Tag each value `[observed]`, `[inferred]` or `[assumed]`, or
give an authoritative source. Never silently turn an unknown into a convenient
number. Record, as applicable:

- required output and duty (torque, speed, force, travel, optical function,
  brightness or another load-specific measure), including the worst case;
- source minimum/nominal/maximum voltage, continuous and peak demand, control
  interface, and required protection or driver;
- maximum component envelope, mounting datum, output or optical axis, fastener or
  retention strategy, and allowed mass;
- insertion and removal direction, connector mate/unmate envelope, wire bend
  room, service loop, strain relief, and access for tools or fingers;
- thermal, environmental, noise, lifetime or compliance constraints that are
  actually in scope;
- procurement constraints the user stated (region, budget, availability,
  approved manufacturers).

For an actuator, always record accepted voltage, running current, stall/start
current and control method. When an unresolved choice changes the power
boundary, the requested function or the approved exterior, it is the user's
decision. Otherwise preserve the uncertainty and show whether it changes the
selection.

## What counts as evidence

- **Authority** for ratings and dimensions is the manufacturer datasheet, the
  manufacturer product page, an applicable standard, or a measurement with a
  stated method.
- **Discovery only**: a generic family page, a distributor title, a visually
  similar STEP, or an open-hardware project. These can surface a candidate but
  cannot prove its ratings or its mating geometry.
- **Open-hardware projects teach integration patterns**: battery and
  controller placement, connectors, hatches, wire channels, strain relief,
  service access, light pipes and diffusers, assembly order. Never take their
  dimensions or electrical or photometric ratings as authority for the user's
  hardware, and never redesign the requested exterior around an analogous
  project.
- **Appearance identifies no part number.** A visible coloured lens is not
  proof of a functional light or of an exact MPN.
- Even hardware the user explicitly requires starts only as a fixed
  *candidate*. It still has to pass the same gates.

## Compare exact candidates, not families

Search exact MPNs and manufacturer aliases. For each plausible candidate,
record the manufacturer page or datasheet revision, the search outcome, the CAD
source and revision, and which values are still unresolved. Never accept the
first catalog hit. When only one candidate remains, name the nearest rejected
alternative and its first failed gate. Do not invent a candidate count when the
market genuinely offers fewer qualified parts.

## Decide in two stages: hard gates, then preferences

### Hard gates

Mark each gate `pass`, `fail` or `unresolved`, with the evidence behind it:

- **Functional:** rated output and duty cover the requested worst case.
- **Electrical:** the load and every inline component contain the full source
  range; continuous and peak capacities cover demand; the control interface is
  compatible.
- **Physical:** the exact part, plus connector, cable and service envelopes,
  fits the available space without changing the approved exterior; the
  mounting datum, output axis and insertion/removal path are usable.
- **Integration:** protection, driver/controller, mating connector, mounting,
  strain relief, service access and any required heat rejection all have
  implementable paths.
- **Evidence:** the exact MPN and relevant revision have authoritative ratings
  and a manufacturer drawing, an exact STEP, or a documented validation
  envelope.
- **Procurement:** any user-declared cost, region, lead-time or vendor rule is
  met.

A `fail` rejects the candidate. An `unresolved` blocks final selection when the
unknown could make a gate fail. **Never average a hard failure into a total
score**: a high preference score cannot compensate for a failed gate.

### Preferences

Rank only candidates that passed every applicable hard gate. Use the user's
priorities (mass, efficiency, noise, thermal margin, price, availability,
serviceability, evidence quality), and state their order or weights before
scoring. Do not present arbitrary default weights as user requirements.
Prefer useful margin over merely meeting a nominal value, but don't oversize
so far that mass, startup current, driver size or heat creates a new
integration problem.

Record the chosen MPN, why it wins, the nearest viable alternative, and what
would make that alternative preferable. This keeps a later supply
substitution from becoming an unaudited geometry change.

## A substitution reopens everything

Changing the MPN reopens the selection contract and every CAD check that
depended on it. Similar overall dimensions do not make a component a drop-in
replacement. The connector, the cable bend, the service loop, strain relief,
removal space and thermal clearance are part of the component's envelope, not
extras.
