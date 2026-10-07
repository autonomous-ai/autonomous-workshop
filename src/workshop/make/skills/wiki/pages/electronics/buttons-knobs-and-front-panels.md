---
title: Buttons, knobs and front panels
tags: [button, tactile, knob, encoder, potentiometer, light-pipe, display, bezel, panel, cutout, legend]
aliases: [push button cap, button plunger, tact switch cap, key top, flexure button, printed button, d-shaft knob, knurled shaft, rotary encoder knob, pot knob, oled window, lcd bezel, display window, viewing area, active area, light guide, panel cutout, panel mount, front panel, control panel]
sources:
  - https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf (Omron B3F tactile switch datasheet, Cat. No. A070-E1-08)
  - https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf (Bourns PEC11R 12 mm encoder: shaft, bushing, torque, push switch)
  - https://www.led-professional.com/media/illumination-application-guide.pdf/@@download/file/Illumination%20Application%20Guide.pdf (Bivar Illumination Application Guide, 2022)
  - https://vcc.co/light-pipe-design-guide/ (VCC light pipe design guide)
  - https://newhavendisplay.com/blog/how-to-mount-a-tft-display/ (bezel and gasket clearances, flex tail bend radius)
  - https://goldenmorninglcd.com/oled-display-module/0.96-inch-128x64-ssd1306-gme12864-11/ (0.96 in 128 × 64 OLED panel: outline, active area, pixel pitch)
  - MIL-STD-1472F, Figures 8 and 12 (push buttons and knobs)
related: [switches-and-reed-sensors, handheld-ergonomics, electronics-enclosure-design, snap-fit-design, flexures-and-living-hinges, lighting-design, led-sizing, fdm-minimum-feature-sizes, fit-derivation, seating-bought-parts]
updated: 2026-09-23
---

# Buttons, knobs and front panels

The user touches the front panel, not the switch. Every control is two
parts: a bought element whose body, hole pattern and datum come from its
STEP ([[seating-bought-parts]], `$step-parts`), and a printed interface — a
cap, a flexure, a knob, a light pipe, a window — whose one job is to carry a
finger's motion or an LED's light to that element with the element's own
numbers. The figures below are for choosing; the datasheet is authoritative.
Sizes and spacing for fingers are in [[handheld-ergonomics#push-buttons]]
and [[handheld-ergonomics#knobs]].

## What a tactile switch gives you

Omron B3F, 6 × 6 mm class (the part most breakouts use):

| item | value |
|---|---|
| body | 6 × 6 mm, ±0.4 mm general tolerance |
| plunger | about 3.5 mm dia.; heights 4.3, 5.0, 7.0, 7.3 (projected), 9.5 mm |
| operating force OF | 0.98 ± 0.29, 1.47 ± 0.49, 2.55 ± 0.69, 4.9 ± 1.47 N |
| pretravel PT | 0.25 +0.2 / −0.1 mm (0.15–0.45 mm) |
| life | 1,000,000 ops at 0.98 N … 50,000 ops at 4.9 N |
| rating | 1–50 mA at 3–24 V DC |

A tactile switch travels about a quarter of a millimetre and then bottoms
out. Ergonomic push-button travel is 2–6 mm for a fingertip (MIL-STD-1472F).
A button that should feel like a button needs its travel from the printed
part, not the switch. Stiffer switches last fewer cycles.

## A cap over a tactile switch

Stack along the press axis: rest gap `g0` between cap and plunger, the
switch pretravel, then the cap's hard stop on the housing.

```text
travel to stop   s = g0 + PT_max + ot         ot: small overtravel, the switch dome absorbs it
never preload    g0 > 0 at the worst tolerance stack
always actuate   s  > g0 + PT_max
finger force     F = OF_max (+ spring or flexure force at s)
```

- Derive `g0` and the guide bore from `cadfits` (a `slip` guide,
  [[fit-derivation]]): a free cap rattles and tilts on a 3.5 mm plunger.
- The tolerance stack across cap, housing and board standoffs is larger
  than the 0.15–0.45 mm pretravel. Either set the switch height by a rigid
  datum (board clamped to bosses on the same part as the stop), or put the
  compliance in the cap (next section) so the stop position does not have to
  be exact.
- Retain the cap with a flange inside the wall, so a pull cannot remove it,
  and key a non-round cap against rotation.
- A long cap (length > about 2 × its guide length) wedges when pressed off
  centre; lengthen the guide, not the cap.
- The finger load at the stop goes into the housing. The switch sees only
  its own travel.

## Printed flexure buttons

A cantilever cut from the case wall by a U-shaped slot is a button with no
extra part: its tip carries a nub over the tactile plunger, and its
stiffness adds the travel and feel the switch lacks. It is a snap-fit beam
that never unhooks, so the snap-fit formulas apply
([[snap-fit-design#cantilever]]):

```text
deflection at the nub   y = g0 + PT_max + ot
root strain             ε = 1.5 h y / L²          keep ≤ repeated-use strain limit
arm stiffness           k = E b h³ / (4 L³)       rectangular, constant section
finger force            F = k · y + OF_max
```

- Illustrative: `h = 1.2 mm`, `L = 15 mm`, `y = 0.7 mm` → `ε = 0.56 %`.
  Repeated flexing wants the lower, cyclic limit from
  [[flexure-materials-and-snap-strain#snap-fit-strain]] and
  [[printed-fatigue]].
- Print the arm so its length runs along the layers
  ([[layer-anisotropy]]); a wall button on a vertical wall already does.
- The slot is a gap the printer must keep open: at least the minimum gap in
  [[fdm-minimum-feature-sizes#features-pins-and-gaps]].
- A flexure arm relaxes under a constant preload, so it must not rest on
  the plunger ([[creep-and-stress-relaxation]]). Flexure types and life:
  [[flexures-and-living-hinges]].

## Knobs on encoders and potentiometers

Bourns PEC11R (a common 12 mm encoder):

| item | value |
|---|---|
| shaft | 6.0 ± 0.1 mm dia. |
| D-flat | flat at 4.5 +0 / −0.05 mm across |
| knurled option | 18 teeth |
| bushing | M7 × 0.75 thread, nut and flat washer supplied |
| mounting torque | 10.2 kgf·cm max (about 1 N·m) |
| detent torque | 30–90 gf·cm |
| push switch | travel 0.5 ± 0.3 mm, force 610 ± 306 gf |

- **D-bore knob**: derive the bore and flat from the shaft with `cadfits`,
  a `snug` or `press` class; the flat carries the torque. Print the bore
  axis vertical so the D is round and true ([[fdm-hole-accuracy]]).
- **Knurled shaft**: a plain bore sized a press fit on the tooth tips, or a
  split collet; the teeth cut their own grooves. Remove and refit reduces grip.
- **Set screw**: a grub screw into the flat through a nut trap
  ([[nut-traps-and-captive-nuts]]) makes a knob serviceable.
- Leave a gap between knob skirt and panel so it does not rub, and a knob
  depth that stops short of the nut, or the knob bottoms before it seats.
- A push-switch encoder is also a button: the knob must travel the push
  stroke without striking the panel.
- Other pots and encoders use other bushings (1/4 in, other metric sizes)
  and shaft lengths. Read the datasheet.

## Panel cutouts for bushing-mount parts

A toggle, pot, encoder or jack clamps the panel between a shoulder and a
nut on a threaded bushing:

```text
panel hole      = bushing major dia. + clearance       (cadfits, slip or free)
panel thickness ≤ threaded length − nut height − washer − 1 thread
anti-rotation   a keyway, flat or locating tab: the panel needs its slot or hole
```

- A printed wall is often thicker than the bushing allows. Spot-face it
  from inside (a counterbore down to a thin land) rather than thinning the
  whole wall.
- Many miniature toggle switches use a 1/4-40 bushing (6.35 mm major
  diameter); the PEC11R uses M7 × 0.75. Take hole, thickness range and tab
  position from the datasheet or the STEP, never from this page.
- The nut is tightened from outside with a socket: leave wrench clearance
  around it, and room for the knob, cap or finger
  ([[handheld-ergonomics#finger-access-and-clearance]]).
- A nut on plastic loosens as the plastic creeps. A washer spreads the
  load; mounting torque on a printed panel stays well under the part's
  maximum.
- USB, barrel jacks and other board-edge connectors:
  [[electronics-enclosure-design#connector-and-port-openings]].

## Light pipes

A light pipe carries an LED's light to the panel by total internal
reflection. Bought pipes are acrylic or polycarbonate (critical angles about
42° and 39°). Rules from Bivar and VCC:

| rule | value |
|---|---|
| pipe diameter | wider than the LED; the wider the LED's viewing angle, the wider and closer the pipe |
| LED-to-pipe gap | about 0.5 mm (Bivar); 0.05 in (1.27 mm) at most (VCC) |
| rigid pipe length | about 76 mm or less (Bivar); 1.2–2.0 in by style (VCC) |
| curved rigid pipe | bend radius ≥ 2 × pipe diameter |
| flexible pipe | bend radius ≥ 10 × fibre diameter (1 mm fibre → 10 mm) |
| inner corners | radius ≥ 0.5 mm |
| transmission | about 80–90 % in a good design (VCC) |

- A panel-mounted pipe floats over the LED and leaks light at the gap
  ("light bleed"): false indications and colour mixing between neighbouring
  LEDs. Put an opaque wall between adjacent pipes, and seat the panel so the
  pipe is centred on the LED within the gap's tolerance.
- Printed transparent filament scatters at every layer line: it is a
  diffuser, not a pipe. Use it for a short window directly over the LED; for
  anything longer, use a bought pipe or a clear rod.
- Thin light-coloured printed walls glow when an LED is behind them. Use
  an opaque (dark) colour or a thicker wall around each light.
- LED current and colour: [[led-sizing]]; lights as a system:
  [[lighting-design]].

## Display windows and bezels

A display module has three rectangles: the **module** (PCB) outline, the
**viewing area** (the glass you can see), and the **active area** (the
pixels). A 0.96 in 128 × 64 OLED panel, for example, is 26.7 × 19.26 mm of
glass with a 21.74 × 10.86 mm active area at 0.17 mm pixel pitch; the PCB
around it is larger and varies by vendor, so read its STEP.

Newhaven Display's clearances:

```text
bezel edge  ≥ 0.8 mm outside the viewable area     (cosmetic)
bezel edge  ≥ 1.0 mm outside the active area       (touch panels: no false touches)
gasket      inner edge ≥ 1.0 mm from viewable area; outer edge ≥ 0.5 mm inside the display edge
spacing     set by rigid housing features; a gasket seals, it does not locate
flex tail   bend radius 2–3 mm
```

- **Opening size**: the opening sits between the active area and the
  viewing area, positioned from the module's STEP (the glass is rarely
  centred on the PCB).
- **Parallax**: a bezel face a distance `t` in front of the pixels hides a
  strip `t · tan θ` of them at viewing angle θ. Widen the opening by that on
  each side, or chamfer the opening's edge.
- **Cover window**: a clear acrylic or glass window sits in a pocket
  behind the bezel. Make the pocket the window size plus a `slip` clearance
  (`cadfits`), deep enough for the window's thickness tolerance, and retain
  the window with a lip, not glue on the viewing area.
- **Never clamp the glass**: support the module by its PCB holes or edges
  on standoffs, with the glass clear of the bezel by a small gap. A breakout
  whose glass is only taped to the PCB is fragile at the flex tail.

A glass plate flush with the shell over a module, in a thin hollow wall, has a
stack of its own: [[flush-display-plate-stack]].

## Labels and legends

- Legends on a printed panel: raised or cut text sized from
  [[fdm-minimum-feature-sizes#text-logos-and-surface-details]]; a
  vertical wall takes smaller text than a top face.
- A two-colour legend (colour change at a layer) reads better than relief
  at small sizes: [[fdm-multi-material-design]].
- Put the legend where the finger does not cover it: above a button,
  around a knob's travel arc, with a pointer on the knob.

## Checks

```python
assert g0 > 0, "button cap preloads the tactile switch at rest"
assert stop_travel > g0 + PT_MAX, "cap reaches its stop before the switch actuates"
assert 1.5 * h_arm * y_nub / L_arm**2 <= EPS_CYCLIC, "flexure button over its cyclic strain"
assert panel_t <= bushing_thread_len - nut_h - washer_t - pitch, "panel too thick for the bushing"
assert pipe_gap <= 1.27 and pipe_d > led_d, "light pipe loses the LED's light"
assert window_w >= active_w + 2 * bezel_t * math.tan(math.radians(view_deg)), "bezel hides pixels"
```
