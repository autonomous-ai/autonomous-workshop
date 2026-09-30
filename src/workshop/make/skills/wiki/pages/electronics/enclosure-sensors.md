---
title: Sensors that look out of an enclosure
tags: [sensor, ultrasonic, hc-sr04, pir, infrared, ir-receiver, tsop38238, window]
aliases: [distance sensor, motion sensor, remote control receiver, sonar module, presence sensor]
sources:
  - https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf
  - https://www.adafruit.com/product/189
  - https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor/overview
  - https://www.adafruit.com/product/157
related: [microcontroller-boards, logic-level-interfacing, electronics-enclosure-design, switches-and-reed-sensors, sealing-and-ingress-protection]
updated: 2026-09-23
---

# Sensors that look out of an enclosure

A sensor that measures the world through a housing needs an opening shaped
for what it senses: a sound path, an unobstructed lens, an IR window.
Placing it behind a solid wall is the commonest failure, and no geometry gate
catches it.

## Ultrasonic distance: HC-SR04

- 45.7 × 20.5 × 15.5 mm module, two round transducers (SparkFun datasheet).
- 5 V, ~15 mA, 40 kHz; range 2–400 cm; 15° measuring cone; trigger with a
  10 µs pulse; `distance_cm = (echo_µs / 2) / 29.1`.
- **Echo is a 5 V output**: a 3.3 V board needs a divider on it
  ([[logic-level-interfacing]]).
- Design: both transducer cans must face out through open holes at least
  their diameter, flush with or proud of the wall. A recessed opening
  deeper than a few millimetres, or a wall edge inside the 15° cone,
  returns false echoes. Hold the module by its PCB holes, not by the cans.

## Passive infrared motion: PIR

- Adafruit 189: PCB 24.03 × 32.34 mm, 24.66 mm tall with the lens; two
  mounting holes Ø2 mm at 28 mm spacing; 5.87 g.
- 5–12 V in (5 V is ideal), digital 3.3 V output; about 7 m and 110° × 70°
  detection (Adafruit's guide; 120° cone on the product page); delay and
  sensitivity trimmers.
- Design: the Fresnel dome must be fully exposed. IR does not pass through
  ordinary printed plastic. Leave access to the two trimmers if tuning is
  expected, and avoid pointing it at the toy's own moving parts or a heat
  source.

## Infrared remote receiver: TSOP38238

- 5.20 × 6.98 × 7.86 mm package; 38 kHz carrier; 3–5 V; pins: 1 output,
  2 ground, 3 supply (Adafruit 157). Outputs the raw demodulated signal.
- Design: a small window or hole in front of the dome. The window can be a
  thin section of the right material, but plain opaque PLA blocks it: prove
  a printed window with a test before relying on it.

## General rules

- Put the sensor's datum (the face that must be flush) on a wall datum. Make
  the module's PCB holes the mount, with standoffs from the enclosure page
  ([[electronics-enclosure-design#standoffs-and-board-mounting]]).
- Seal the gap around a sensor window only if the sensor tolerates it;
  ultrasonic cans should not touch the housing, which transmits the ping.
- Keep motor and PWM wiring away from sensor lines ([[small-dc-motors#electrical-noise]]).

Sealing the gap around a sensor window: [[sealing-and-ingress-protection]].
