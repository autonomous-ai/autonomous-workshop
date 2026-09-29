---
title: Logic levels between 3.3 V and 5 V parts
tags: [logic-level, 3v3, 5v, level-shifter, voltage-divider, gpio, ttl, cmos]
aliases: [level shifting, level converter, 3.3v to 5v, 5v tolerant, voltage translation]
sources:
  - https://learn.sparkfun.com/tutorials/logic-levels/all
  - https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels
  - https://www.adafruit.com/product/4864
related: [microcontroller-boards, led-sizing, motor-drivers-and-flyback]
updated: 2026-09-23
---

# Logic levels between 3.3 V and 5 V parts

Most modern boards (RP2040, ESP32, XIAO) are 3.3 V. Many hobby modules and
the classic Arduinos are 5 V. The two directions are not symmetric.

## Thresholds

5 V TTL (SparkFun): an input reads HIGH above VIH = 2.0 V and LOW below
VIL = 0.8 V; an output gives at least VOH = 2.7 V high and at most VOL = 0.4 V
low. The band between 0.8 and 2.0 V is undefined. 3.3 V CMOS levels are
similar in shape but scaled to the lower supply.

## 3.3 V driving 5 V: usually fine

A 3.3 V output (≥ 2.4 V high) clears a 5 V TTL input's 2.0 V threshold.
**Exceptions** are 5 V parts with CMOS-style thresholds. WS2812 pixels need
the data line at ≥ 70 % of their supply (3.5 V at 5 V), so a 3.3 V board is
out of spec there ([[led-sizing#addressable-pixels-ws2812-neopixel]]).

## 5 V driving 3.3 V: damage

"Any voltages above 3.6V will cause permanent damage" to many 3.3 V chips. The
Pico datasheet makes the same point: its GPIO are not 5 V tolerant. A 5 V
sensor's output (for example an HC-SR04 echo, [[enclosure-sensors]]) into a
3.3 V pin needs one of:

| fix | how | limits |
|---|---|---|
| resistor divider | 1 kΩ from the 5 V signal, 2 kΩ to ground, tap to the 3.3 V input (5 × 2/3 = 3.3 V) | one direction, slow edges; fine for sensors and serial RX |
| bidirectional MOSFET level converter | commercial breakout | I²C and other open-drain buses |
| level-shifter IC (e.g. TXS0108E) | multi-channel | push-pull buses, check the datasheet speed |

## In the model

A level shifter or divider is a small board or a pair of resistors: give it a
place on the carrier or in the harness, and write which signals it serves in
the wiring table. The divider also sets which side of the harness is 5 V.
Label it so nobody swaps a connector.
