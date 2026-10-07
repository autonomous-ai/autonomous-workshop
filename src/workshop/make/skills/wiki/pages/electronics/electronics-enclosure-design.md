---
title: Designing printed enclosures for electronics
tags: [enclosure, standoff, boss, pcb, clearance, port, ventilation, strain-relief, lid]
aliases: [electronics housing, project box, pcb mount, screw boss, usb cutout, cable gland]
sources:
  - https://www.hubs.com/knowledge-base/enclosure-design-3d-printing-step-step-guide/
  - https://zbotic.in/3d-printed-electronics-enclosures-design-tips-for-makers/
  - https://www.allaboutcircuits.com/industry-articles/six-steps-for-designing-a-custom-3d-printed-electronics-enclosure/
  - https://www.3d-demand.com/blog/3d-printed-enclosures-electronics-guide
related: [microcontroller-boards, wire-gauge-and-connectors, lipo-cells-and-housing, toy-battery-compartments, wall-thickness-and-hollowing, seating-bought-parts, thermal-design-for-enclosures, buttons-knobs-and-front-panels, sealing-and-ingress-protection]
updated: 2026-10-02
---

# Designing printed enclosures for electronics

An enclosure holds boards, cells and wires in known places, lets cables,
buttons and sensors through, sheds heat, and opens for service. The starting
numbers below are from enclosure design guides. Every bought part's position
still comes from its STEP ([[seating-bought-parts]]), and every mate from
`cadfits`.

## Exterior redesign with retained electronics

When the brief explicitly limits work to the exterior and preserves firmware,
freeze the existing display, touch/control and connector contracts before
choosing a new silhouette. A circular display does not require a circular
housing. Do not select a replacement development board merely because its
screen has the same nominal size: pin assignments and peripherals can change
the firmware contract.

An inert display illustration and standard fasteners in a concept assembly
do not establish functional integration or closure retention. State which
component clearances were actually checked, and keep full PCB mounting,
acoustic paths, cable overmould access, thermal behaviour and closure strength
as explicit unverified items until their geometry and applicable gates exist.
An original complete-device assembly includes its old housing; fitting that
whole assembly is a different claim from seating a retained LCD or board.

## Walls and clearances

- **Walls about 2 mm** as a starting point for FDM enclosures (Hubs); check
  against the nozzle rule in [[wall-thickness-and-hollowing]].
- **0.5 mm clearance around internal components** and between PCB edges and
  walls, for shrinkage, warp and printer tolerance (Hubs, AllAboutCircuits).
  Add room for the wiring that must pass between them.
- Round the inside corners: fillets reduce stress concentrations at the
  wall joints.

## Standoffs and board mounting

- Put bosses exactly on the board's hole pattern, read from the board's
  STEP, never typed from a drawing.
- **M2.5 boss** starting point (enclosure guides): about 5 mm outside
  diameter; a ~2.1 mm hole for a thread-forming screw or 2.5 mm for
  clearance; tall enough to lift the board 3–5 mm (or 5–8 mm) off the floor,
  clearing through-hole pins and underside parts and letting air pass.
- **Wall around a threaded hole at least one hole diameter** (Hubs: a 5 mm
  wall for an M5 screw).
- **Hole sizing** (Hubs): clearance hole = screw diameter + 0.25 mm; a
  self-tapping hole = diameter − 0.25 mm. The repository's fit table
  (`cadfits`) is authoritative where it covers the case
  ([[fit-derivation]]).
- For boards opened and closed repeatedly, use heat-set inserts or captive
  nuts rather than threads cut in plastic. Snap-fits suit single-assembly
  prototypes (Hubs).

## Connector and port openings

- **USB, barrel jacks, switches**: at least 0.5 mm clearance per side for FDM
  (0.3 mm for SLA/SLS) around the connector body itself (3d-demand), and
  about **2 mm all round the port opening** for the cable's overmould, since
  a cutout that only exposes the port blocks bulky plugs (AllAboutCircuits;
  Hubs gives 1 mm per side).
- Place the board so the connector face sits at the wall datum, with the
  plug's mating depth measured from its STEP.
- Buttons and LEDs through the wall need plungers or light pipes positioned
  from the component's STEP, with a hard stop that protects the part
  ([[switches-and-reed-sensors]]).

Button caps, knobs, light pipes, display windows and panel cutouts:
[[buttons-knobs-and-front-panels]].

## Strain relief

Any cable that can be pulled or flexed needs a strain relief so the force
goes into the enclosure, not into solder joints or board connectors: a
printed clamp, a tortuous path, a cable tie anchor or a grommet. Moving
cables need a service loop ([[wire-gauge-and-connectors]]).

## Heat and ventilation

- Motor drivers, regulators and servos under load get warm. PLA softens at
  moderate temperatures, so keep hot parts off PLA walls or give them air.
- Vents: slots low and high on opposite walls give a convection path. Size
  them small enough to keep fingers out of a toy.
- A lithium cell must not sit against a heat source
  ([[lipo-cells-and-housing]]).

The calculation — heat budget, junction temperature, box temperature rise,
vent area, fan flow: [[thermal-design-for-enclosures]].

## Closing it

| closure | use |
|---|---|
| screws into inserts or captive nuts | opened repeatedly; battery doors in toys must use captive screws ([[toy-battery-compartments]]) |
| snap-fits | assembled once, or lids opened rarely |
| living hinge + snap | integrated lid for flexible materials; fatigue-limited in PLA |

Design the assembly order: boards and harness in first, lid last. Check that
no screw tip, boss or rib lands on a cell, a connector or a component when
the lid closes; a motion or assembly sweep makes that visible
([[mechanism-verification#4-what-the-manifest-must-contain]]).

Gaskets, O-rings, cable glands, vents and IP ratings:
[[sealing-and-ingress-protection]].
