---
title: Switches, limit switches and reed sensors
tags: [switch, slide-switch, tactile, micro-switch, limit-switch, reed-switch, magnet, button]
aliases: [power switch, push button, tact switch, snap action switch, end stop, home switch, magnetic switch]
sources:
  - https://www.sohantech.com/slide-switch_12d00g3-product/
  - https://einstronic.com/product/pcb-slide-switch-ss12d00g4/
  - https://components.omron.com/us-en/products/switches/B3F
  - https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf
  - https://www.sparkfun.com/products/97
  - https://www.adafruit.com/product/375
related: [power-path-design, stepper-motors, electronics-enclosure-design, joints, buttons-knobs-and-front-panels]
updated: 2026-10-07
---

# Switches, limit switches and reed sensors

A switch is a mechanical part as much as an electrical one. The model must
give it a seat, an actuator path with overtravel, and a finger or cam that
reaches it. Take its body and hole pattern from its STEP (`$step-parts`,
`cadmount`); the figures here are for choosing.

## Kinds and ratings

| switch | typical part | size | rating | use |
|---|---|---|---|---|
| **mini slide switch** (SPDT) | SS12D00 family | ~8.7 × 3.7 × 11.7 mm (L × W × H, SS12D00G); body 8 × 4 × 3.8 mm for G3; 2.54 mm pin pitch, 3 mm knob | 0.5 A at 50 V DC, > 100,000 cycles | power on/off for small battery toys |
| **tactile switch** | Omron B3F, 6 × 6 mm class (12 × 12 also) | 6 × 6 mm body, ±0.4 mm tolerance on Omron drawings | small-signal (SparkFun's mini pushbutton: 50 mA) | user buttons read by a microcontroller |
| **micro (snap-action) switch** | Omron D2F ultra-subminiature | 6.5 × 12.8 × 5.8 mm body, two mounting holes at 6.5 ± 0.15 mm pitch | up to 3 A (D2F; low-current variants 0.1 A) | limit and home switches, lid detection |
| **reed switch** (magnetic contact) | encapsulated door sensor | 29 × 15.2 × 9 mm per half (Adafruit 375) | 100 mA, 200 V DC max; normally open | contactless position sensing, hidden switches |

A slide switch rated 0.5 A is fine for LEDs and a microcontroller. For
motors, check the stall current against the rating ([[small-dc-motors]]), or
let the switch control a driver's enable line instead of carrying the motor
current.

## Designing the actuation

- **Slide switch**: the printed slot for the knob is the knob travel plus
  clearance, so the slot must not be the stop. Let the switch's own detents
  end the travel, or the user forces the switch past them. A printed
  extension cap over a 3 mm knob needs a snug fit from `cadfits`.
- **Tactile switch behind a printed button**: the printed plunger must press
  the switch before the plunger bottoms out, and must not preload it at rest.
  Design a positive gap at rest, a travel larger than the gap, and a hard stop
  in the printed guide that protects the switch from being crushed.
- **Micro switch as a limit or home switch**: the cam or finger reaches the
  operating position, then continues a little into the overtravel without
  hitting the body. A mechanism that can overshoot the overtravel breaks the
  switch; a lever variant widens the window. Model the actuation as a motion
  condition: the finger reaches the plunger (contact expected) at the end of
  travel, and never passes through the switch body.
- **Reed switch and magnet**: activation is by distance (Adafruit's
  encapsulated pair: 15 mm max). Glass-bodied reed switches are fragile: pot
  or pocket them in a closed printed channel, never under a screw. Magnets in
  moving printed parts go in closed pockets (press-fit plus a cap, or paused
  print), since glue joints fail.

Cap-over-tactile-switch stack and flexure buttons:
[[buttons-knobs-and-front-panels]].

## Wiring and debouncing

- A switch into a microcontroller input needs a pull-up or pull-down (often
  internal). Mechanical contacts bounce, so debounce in firmware.
- A power switch belongs on the battery's positive lead, before the
  regulator and the charger's load path (unless a charger board specifies
  otherwise) ([[power-path-design]]).

## Leave soldered terminals in the open

A pocket cut as the component's own prism slots every terminal and frame tab
into the printed wall: the walls between them come out 0.3-0.5 mm thick, and
an iron cannot reach the joints without melting them. Cut the wall in front of
the body away down to just under the terminals and let the side walls and the
actuator's window locate the body.

## Panel mounting notes

- Panel cut-outs for switches and connectors need clearance for FDM
  tolerance ([[electronics-enclosure-design#connector-and-port-openings]]).
- A switch is pushed and pulled by fingers. Carry that force into a printed
  boss or a PCB screwed to the housing, not into solder joints alone.

Bushing-mount cutouts, anti-rotation and thick printed walls:
[[buttons-knobs-and-front-panels]].
