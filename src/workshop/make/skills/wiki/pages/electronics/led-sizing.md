---
title: Sizing indicator LEDs and addressable pixels
tags: [led, resistor, forward-voltage, neopixel, ws2812, current, indicator]
aliases: [current limiting resistor, led resistor, addressable led, rgb pixel, through-hole led]
sources:
  - https://learn.sparkfun.com/tutorials/resistors/all
  - https://learn.sparkfun.com/tutorials/light-emitting-diodes-leds/all
  - https://components101.com/diodes/5mm-round-led
  - https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels
  - https://jlcpcb.com/blog/led-sizes-explained
related: [lighting-design, power-path-design, electrical-component-selection, battery-cells-and-packs]
updated: 2026-09-23
---

# Sizing indicator LEDs and addressable pixels

An LED is a current-driven part: the supply sets nothing until a resistor (or
a constant-current driver) sets the current. Size the current first, then the
resistor, then its power. For lamps that are the point of the model, and for
anything a datasheet must prove, go on to [[lighting-design]].

## Forward voltage by colour

Typical ranges for plain 5 mm indicator LEDs (components101 table; any given
part's datasheet overrides it):

| colour | forward voltage Vf |
|---|---|
| red | 1.63–2.03 V |
| yellow | 2.10–2.18 V |
| green | 1.9–4.0 V (older GaP green is low, InGaN green high) |
| blue | 2.48–3.7 V |
| white | 3.2–3.6 V |

A blue or white LED needs more than 3 V. It will not light reliably from one
CR2032 under load, or from two alkaline cells as they sag
([[battery-cells-and-packs]]).

## Current

- A standard 5 mm indicator is rated about 20 mA continuous, 30 mA maximum;
  SparkFun's basic red is brightest at 20 mA and recommended at 16–18 mA
  for stable operation, with 30 mA only in short bursts.
- An indicator that is looked at, not a lamp, is usually bright enough at
  2–10 mA. Lower current is longer battery life.
- A microcontroller pin has its own limit (an Uno I/O pin is 40 mA absolute
  maximum, a Nano's is stated as 20 mA; [[microcontroller-boards]]), so an
  LED on a pin is sized to the pin, not to the LED.

## The resistor

```text
R = (Vs - Vf) / I            P = I² R
```

Worked (SparkFun): red LED, Vf ≈ 1.8 V, 9 V battery, 10 mA →
`R = (9 - 1.8) / 0.010 = 720 Ω`, use the nearest standard value (680 or
750 Ω); `P = 0.010² × 720 = 0.072 W`, so a common 1/4 W resistor has ample
margin.

```python
R = (V_SUPPLY - VF) / I_LED
P = I_LED**2 * R
assert V_SUPPLY - VF >= 0.5, "too little headroom: current will swing with the battery"
assert P <= 0.5 * RESISTOR_WATTS
```

LEDs in series share one resistor if `Vs` exceeds the sum of their forward
voltages with margin (SparkFun's two 2.4 V LEDs on 5 V leave 0.2 V for the
resistor, which is too little to regulate anything). LEDs in parallel each
need their own resistor: forward voltages differ, and the lowest one hogs the
current.

## Polarity

The anode (+) has the longer lead; the cathode side of a round LED carries a
flat on the flange. Model the flat into a panel socket if orientation must be
kept after assembly.

## Package sizes

Through-hole LEDs are named by body diameter (3, 5, 8, 10 mm). The flange at
the base of a 5 mm LED makes it about 6 mm across, and the lead pitch is
2.54 mm for all common sizes (JLCPCB size guide). Exact body height, flange
and lead length vary by maker: take the seat from the part's STEP through
`$step-parts` and `cadmount`, never from these nominal numbers.

## Addressable pixels (WS2812 / NeoPixel)

- **Current**: up to 60 mA per pixel at full white (red + green + blue on).
  Adafruit's planning figure for mixed animation is 20 mA per pixel; size a
  supply that must never brown out at 60 mA per pixel.
- **Supply sizing**: `amps = pixels × 0.020` (typical) or `× 0.060` (worst
  case). "Extra amps = good, extra volts = bad."
- **Reservoir capacitor**: 500–1000 µF, rated 6.3 V or higher, across + and −
  at the strip, against glitches from sudden brightness changes.
- **Voltage**: most are 5 V parts; lower voltage is tolerated with dimming.
- **Data level**: the data input needs at least 70 % of the pixel supply. A
  3.3 V board driving 5 V pixels is out of spec: run the pixels from a 3.7 V
  LiPo or add a level shifter ([[logic-level-interfacing]]).

```python
I_PIXELS_MAX = N_PIXELS * 0.060
assert SUPPLY_AMPS >= I_PIXELS_MAX or FIRMWARE_BRIGHTNESS_CAP, "pixels can exceed the supply"
```

A 60-pixel strip at full white is 3.6 A: more than any USB port or small
regulator supplies. Either cap the brightness in firmware and record the cap,
or size the supply and wiring for it ([[wire-gauge-and-connectors]]).
