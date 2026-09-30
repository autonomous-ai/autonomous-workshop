---
title: Battery compartments in toys
tags: [battery, compartment, toy-safety, astm-f963, en-62115, coin-cell, captive-screw, polarity]
aliases: [battery door, battery cover, reese's law, button cell safety, toy standard, childproof battery]
sources:
  - https://www.awen-hollek.com/post/battery-toy-compliance-62115-f963-emc
  - https://www.qima.com/consumer-products/lab-testing/astm-f963-23-toy-safety-standard
  - https://www.intertek.com/toys-childrens-products/us-astm-f963-for-toys/
  - https://www.jjrlab.com/news/astm-f963-23-lithium-ion-battery-requirements-for-toys.html
related: [battery-cells-and-packs, lipo-cells-and-housing, electronics-enclosure-design, joints]
updated: 2026-09-23
---

# Battery compartments in toys

A toy's battery door is a safety part, because swallowed coin and button
cells injure children. Toy standards (ASTM F963 in the US, EN 62115 for
electric toys in Europe) set how the door must close. This page summarises
the design consequences. It is not a compliance statement: a toy sold to
children is certified by a lab against the current edition.

## Access: a tool, or two independent actions

Two accepted ways to keep a child out of a compartment:

- **Tool-required**: a common household tool (screwdriver or coin) opens it.
  ASTM F963 also allows a specialty drive (Torx, hex) if the tool comes with
  the toy and the instructions tell the adult to store it securely.
- **Two-action**: two independent, simultaneous movements (press-and-slide,
  dual latches).

For coin and button cells (the US rule aligned with "Reese's Law") this is
mandatory: "Magnets, friction, or 'strong snaps' are not enough." A plain snap
lid over a CR2032 is a design defect, whatever the age grade.

## Captive fasteners

Both standards require the door screw to stay with the door: an under-head
collar, a mushroom shoulder, a tether, or a heat-staked retainer. It must not
fall out under pull tests or after use-and-abuse cycles. In CAD:

- the door hole carries the screw on a reduced neck or a retaining collar, so
  the screw can turn and back out of the boss but not leave the door;
- the boss in the body takes the thread: a self-tapping boss or a heat-set
  insert ([[electronics-enclosure-design]]);
- the retention is a `blocked` motion condition. The screw pulled along its
  axis with the door open must stop at the door ([[joints#the-two-conditions-every-joint-owes]]).

## Polarity and wrong insertion

"Key the sled so cells only fit one way, emboss polarity marks, and add
reverse-polarity protection on the PCB when feasible." Emboss or deboss the
`+`/`−` marks and the cell outline in the compartment floor. A printed mark
survives where a sticker falls off.

## Abuse the door must survive

Use-and-abuse testing (drop, torque, tension) is applied to the toy and then
the battery must still be inaccessible. Design so that:

- the door hinge or tongue is not a thin printed feature across layer lines
  ([[overhangs-and-print-orientation]]);
- the screw boss has a wall at least one hole diameter thick around the hole
  ([[electronics-enclosure-design]]);
- cells are held by the holder's contacts and ribs, not by the door, so a
  drop does not push the door open from inside.

## Rechargeable cells in toys

Toys with lithium rechargeable batteries carry extra requirements in recent
editions (ASTM F963-23 added lithium-ion battery provisions): the charging
circuit, protection and marking. Use a protected cell with a proper charger
board ([[lipo-cells-and-housing]]), and treat certification as out of scope
for CAD. Record it as an open item.

## Checklist

- [ ] access needs a tool or two simultaneous actions; coin cells always
- [ ] the door screw is captive (a `blocked` condition proves it)
- [ ] the compartment is keyed for polarity and marked `+`/`−`
- [ ] the holder, not the door, holds the cells
- [ ] certification against the current edition recorded as open
