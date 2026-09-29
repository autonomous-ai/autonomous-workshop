---
title: Hobby servos
tags: [servo, sg90, mg90s, mg996r, pwm, spline, horn, torque, actuator, stall-current]
aliases: [rc servo, micro servo, 9g servo, servo horn, servo spline, positional servo]
sources:
  - https://www.towerpro.com.tw/product/sg90-7/
  - https://www.towerpro.com.tw/product/mg90s-3/
  - https://www.towerpro.com.tw/product/mg996r/
  - https://www.pololu.com/blog/17/servo-control-interface-in-detail
  - https://www.robotdigg.com/news/168/RC-Servo-Spline-Chart
  - https://www.arrmaforum.com/threads/servo-help.204/
related: [energy-drive, power-path-design, battery-cells-and-packs, seating-bought-parts, microcontroller-boards, arm-and-gripper-sizing]
updated: 2026-09-23
---

# Hobby servos

A hobby servo is a motor, gearbox, potentiometer and controller in one case.
It moves to an angle set by a pulse width. It is the simplest way to give a
printed model a controlled motion, and the usual source of brown-outs,
stripped horns and wobbly mounts.

## Common models (TowerPro figures)

| model | size (mm) | mass | stall torque | speed | voltage | notes |
|---|---|---|---|---|---|---|
| **SG90** | 23 × 12.2 × 29 | 9 g | 1.8 kg·cm at 4.8 V | 0.1 s/60° at 4.8 V | 4.8 V (4.8–6 V accepted) | POM plastic gears; ~0–150° travel; operating current ~0.5–2 A; dead band 1 µs |
| **MG90S** | 22.8 × 12.2 × 28.5 | 13.4 g | 1.8 kg·cm (4.8 V), 2.2 kg·cm (6.6 V) | 0.10 s/60° (4.8 V), 0.08 s/60° (6 V) | 4.8 V | metal (6061-T6) gears and shaft; same frame as SG90 |
| **MG996R** | 40.7 × 19.7 × 42.9 | 55 g | 9.4 kg·cm (4.8 V), 11 kg·cm (6 V) | 0.19 s/60° (4.8 V), 0.15 s/60° (6 V) | 4.8–6.6 V | idle 10 mA, no load 170 mA, **stall 1,400 mA** |

Vendors write torque as "kg/cm"; it means kg·cm (force × radius). Torque at a
horn hole radius r: `F = torque / r`. An SG90 at 1.8 kg·cm pushes about
0.9 kg-force at 2 cm. That is stall: design the linkage to need well under
half of it.

Clones share names and not specs. Take dimensions and the mounting-ear hole
pattern from the chosen part's STEP (`$step-parts`, `cadmount`,
[[seating-bought-parts]]), not from this table.

Torque at full reach, the dynamic term and stall margin for an arm:
[[arm-and-gripper-sizing]].

## The control signal

- Pulse every ~20 ms (50 Hz); most servos accept faster rates.
- 1.5 ms is neutral; roughly 1.0–2.0 ms gives about 90° of travel. The
  pulse-to-angle mapping is not standard between models, and pulses beyond
  the servo's range drive it into its mechanical stop, which can destroy it.
  TowerPro notes that 1–2 ms does not cover the SG90's full stated range.
- Calibrate each servo's end points in firmware and **record the mechanical
  range the linkage allows**. Firmware must never command past a hard stop
  in the mechanism.

## Power: the servo is the biggest load

- Stall current (1.4 A for an MG996R; up to ~2 A for an SG90 per TowerPro)
  flows at every start and whenever the linkage binds.
- Power servos from the battery or a dedicated regulator. A board's USB
  5 V or 3.3 V pin browns out and resets the microcontroller
  ([[power-path-design]]).
- Share ground between servo supply and controller; the signal is referenced
  to it.
- Several servos moving at once: add their stall currents, or sequence them in
  firmware and record that.

## Horns and splines

The output spline tooth count differs by brand: Futaba 25T, Hitec 24T,
JR 23T, Savox 25T (RobotDigg chart; other sources list Airtronics, Sanwa and
KO as 23T). A horn for one count does not fit another without force. Micro
servos (SG90 class) usually ship with their own small plastic horns. Their
spline is not reliably documented, so use the supplied horn.

Printed parts on a servo:

- **Screw the supplied horn to the printed arm.** A printed spline is weak and
  its fit depends on the clone.
- The horn screw into the output shaft is the axial retention; it is a
  `blocked` condition ([[joints#the-two-conditions-every-joint-owes]]).
- Support the arm's far side (or the servo's output axis) if the load is
  offset: a micro servo's output shaft is supported over a very short length
  inside its case.

## Mounting

Mount through the case ears with screws (holes from the STEP), or clamp the
case between two printed plates. Leave the cable exit and its bend radius
clear. Give the output shaft a clear path when the servo is inserted into its
pocket: servos usually go in from the side with the ears.
