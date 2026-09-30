---
title: Wheeled toy vehicles
tags: [wheel, vehicle, traction, rolling-resistance, differential-drive, motor-sizing, speed, caster]
aliases: [toy car, robot drive, drive wheel, wheel size, tractive effort, skid steer, differential steering, drivetrain]
sources:
  - https://en.wikipedia.org/wiki/Rolling_resistance (F = Crr N, Crr table, Crr = sqrt(z/d))
  - https://en.wikipedia.org/wiki/Traction_(engineering) (usable traction = coefficient × normal force)
  - https://en.wikipedia.org/wiki/Friction (rubber on concrete static 1.0, kinetic 0.6-0.85 dry; steel on steel; PTFE)
  - https://en.wikipedia.org/wiki/Differential_wheeled_robot (V = (vR + vL)/2, omega = (vR - vL)/b, casters)
  - https://web.mae.ufl.edu/designlab/Lab%20Assignments/EML2322L-Electric%20Motors%20and%20Drives.pdf (V = pi D N, T = F r, P = T omega, 60 % brushed efficiency, 75 % of no-load speed)
related: [energy-drive, gears, strain-wave-and-differentials, shafts-and-bearings, stability-and-tipping]
updated: 2026-09-23
---

# Wheeled toy vehicles

A driven vehicle is a chain of four numbers: the force to move, the torque at
the wheel, the wheel speed, and the motor's torque–speed curve. Size them in
that order before drawing a gearbox ([[energy-drive#ratio-budget]]).

## Force to move

```text
rolling resistance   F_rr = C_rr · N                 N = weight on the wheels
grade                F_g  = m g sin(slope)
acceleration         F_a  = m a
total tractive force F = F_rr + F_g + F_a
```

`C_rr` values: steel wheel on steel rail 0.0003–0.0004, bicycle tyres
0.0022–0.005, car tyre on concrete 0.010–0.015, sand 0.3. For a rigid wheel
on a soft surface, `C_rr ≈ √(z/d)` (`z` sinkage, `d` diameter): **bigger
wheels roll easier on carpet and sand**. On hard floors the diameter matters
little. A toy's axle friction in printed bushings usually dwarfs its rolling
resistance, so give the axles smooth bores or bearings
([[shafts-and-bearings#bushing-or-ball-bearing]]).

## Traction limits it

The wheel can push only as hard as friction allows:

```text
F_max = μ · N_drive          N_drive = weight on the driven wheels only
```

Rubber on concrete: μ ≈ 1.0 static, 0.6–0.85 sliding (dry), 0.45–0.75 wet.
Bare hard plastic slips far sooner, so give driven wheels a rubber or TPU
tyre or an O-ring. Put weight over the driven wheels. Torque beyond
`F_max × r` only spins the wheel.

```python
T_wheel = F_TOTAL * R_WHEEL
assert F_TOTAL <= MU * N_DRIVE, "wheels slip before the toy moves"
```

Tipping on slopes and while accelerating: [[stability-and-tipping]].

## Torque, speed and the motor

```text
wheel torque   T = F · r
ground speed   V = π D N          (N in rev/min → V per minute)  =  ω r
power          P = T · ω
```

- A brushed DC motor's torque falls linearly from stall to its no-load speed.
  As a first approximation take about 75 % of the rated no-load speed under
  load, and about 60 % electrical efficiency for a small brushed motor.
- A gear ratio `i` multiplies torque by `i` (times the train efficiency) and
  divides speed by `i` ([[gears#trains-and-ratio-budget]]).
- Wheel diameter trades speed for pulling force at the same motor: a larger
  wheel is faster but needs more torque for the same force.
- Check the whole chain both ways: the motor must supply `T / (i η)` at the
  wheel speed times `i`, and the wheel must not slip at that torque.

## Differential drive

Two independently driven wheels on one axis, plus a caster or skid so the
body does not tip:

```text
forward speed   V = (v_R + v_L) / 2
turn rate       ω = (v_R − v_L) / b          b = wheel track (distance between wheels)
wheel speeds    ω_R = (V + ω b / 2) / r,   ω_L = (V − ω b / 2) / r
```

Equal wheel speeds drive straight; opposite speeds spin on the spot. The robot
goes where the *difference* of the wheel speeds sends it, so two unmatched
motors make it curve. Match them, or close the loop with sensing. A car-like
single-motor layout needs steering and either a differential or a solid axle
that scrubs in turns ([[strain-wave-and-differentials#differentials]]).

## Checks

- Asserts: traction ≥ required force; motor torque at operating speed ≥
  wheel torque / (ratio × efficiency); the driven wheel's axle supported on
  two bearings with the wheel inboard.
- Motion: wheels are simple rotations. Check wheel-arch clearance at full
  steering lock or suspension travel, and the caster's full swivel, as
  sweeps ([[mechanism-verification]]).
- Open items: real floor friction, battery sag under load and the achieved
  speed must be measured; no gate predicts them.
