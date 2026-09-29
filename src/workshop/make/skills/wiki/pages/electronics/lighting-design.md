---
title: Designing functional lights
tags: [lighting, led, lamp, lens, diffuser, light-pipe, driver, optics, electrical]
aliases: [led design, status light, beacon, strobe, headlight, light strip, backlight, illuminated control, navigation light]
sources:
  - skills/electromechanical-integration/references/lighting-discovery.md
  - https://gitlab.com/kicad/libraries/kicad-packages3D (current KiCad 3D package library)
related: [electrical-component-selection, power-path-design, removable-lamp-interfaces, led-sizing, buttons-knobs-and-front-panels, thermal-design-for-enclosures]
updated: 2026-09-23
---

# Designing functional lights

Applies whenever a design contains a functional LED, lamp, beacon, strobe,
headlight, light strip, illuminated control, light pipe or backlight. The
search sequence across catalogs stays in
`skills/electromechanical-integration/references/lighting-discovery.md`.

## A visible light is four objects

1. the emitter or bought light module;
2. its driver/controller and connector;
3. the lens, light pipe or diffuser that owns the visible exterior;
4. the printed seat, bezel, wire channel and service feature.

One coloured primitive does not complete all four. Inventory each light:

| Field | Record |
|---|---|
| function | position/navigation, head/landing/work, brake/indicator, beacon/strobe, status, decorative/ambient, backlight, IR/UV, or an explicit project term |
| position | part, face and assembly pose |
| colour | observed/requested colour; wavelength only from a datasheet |
| behaviour | steady, dimmed, blink, pulse, strobe pattern, addressable animation |
| optical direction | viewing direction, beam/viewing angle if sourced, and which surface is luminous |
| implementation | discrete LED, addressable pixel, strip, COB/module, lamp, light pipe, or unresolved |
| evidence | `[observed]`, `[inferred]` or `[assumed]` for image-derived work |

A lens colour and glow in a render can identify function, never an exact
manufacturer part number. Treat compliance terms like "navigation light" or
"warning beacon" as a design convention until an applicable standard and its
photometric requirements are explicitly in scope.

## Facts that must come from the manufacturer

Before selecting, obtain as applicable:

- accepted supply or forward-voltage range;
- continuous current and worst-case pulse/peak current;
- whether a resistor, constant-current driver, level shifter or controller is
  required;
- wavelength/colour, luminous intensity or flux, viewing/beam angle, and
  maximum duty cycle, when these affect the requested function;
- package drawing, emitting-surface datum, lead/connector orientation, bend
  limits and thermal constraints.

If a required rating cannot be sourced, leave compatibility unresolved. Never
fill it with a value from a similar-looking part or from an open-hardware
analogy. A CAD service's model is mechanical evidence only; electrical and
optical facts still come from the manufacturer or a standard.

## What a generic package model proves

KiCad-style package geometry is useful for PCB rendering, board-envelope
checks and a documented generic stand-in. It is **not** evidence that a lamp
mates with a socket, and it does not authorise a drilled hole, a bayonet path
or a twist-lock receiver. Unless the model traces to the exact selected MPN and
drawing revision, label it a validation envelope, and take mating dimensions
from the lamp/socket manufacturer or a measured exact sample. Resolve any model
found by function or package back to an exact MPN, and compare the
package/drawing revision before using it. Never substitute a visually similar
LED or module.

The old GitHub `KiCad/kicad-packages3D` is an archived snapshot that points to
the GitLab repository. Pin new provenance to the current library, not to the
archived default branch.

## Selection order

Select against the whole product, in this order:

1. the exact requested function, colour and behaviour;
2. full source-voltage compatibility and worst-case current;
3. the exact lamp MPN, its exact mating socket/contact system, geometry, and a
   serviceable assembly path;
4. optical direction and the visible optic;
5. driver heat, wire bend, connector access and replacement access.

## In the model

Visible lenses, bezels and diffusers belong in the combined assembly and in
likeness renders. Hidden emitters, drivers and looms may be validation-only,
but each still gets a mount and an obstacle list for clash checking. Model the
full route from controller to emitter, including insulation diameter, bend
room, connector insertion/removal and strain relief
([[power-path-design#wires-are-solids]]). A removable lamp is a separate design
problem: [[removable-lamp-interfaces]].

Light pipes from an LED to the panel: [[buttons-knobs-and-front-panels]]; heat
from the light source: [[thermal-design-for-enclosures]].
