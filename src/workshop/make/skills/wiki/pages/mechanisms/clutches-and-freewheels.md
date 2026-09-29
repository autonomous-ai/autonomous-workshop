---
title: Clutches, freewheels and torque limiters
tags: [clutch, freewheel, one-way, sprag, torque-limiter, slip-clutch, ball-detent, shear-pin, overload]
aliases: [one-way clutch, overrunning clutch, sprag clutch, roller clutch, one-way bearing, slip clutch, friction clutch, overload clutch, safety clutch]
sources:
  - https://en.wikipedia.org/wiki/Freewheel (saw-tooth ratchet discs, roller type, pawls and clicking, uses)
  - https://en.wikipedia.org/wiki/Torque_limiter (friction plate, ball detent, shear pin, magnetic, pawl and spring)
related: [cams-intermittent, energy-drive, gears, springs, latches-detents-and-ratchets]
updated: 2026-09-23
---

# Clutches, freewheels and torque limiters

Three different jobs, often confused:

| job | device | toy example |
|---|---|---|
| drive one way, coast the other | **freewheel / one-way clutch** | a wind-up or pull-back car that coasts; a crank that should not spin back |
| slip instead of breaking when overloaded | **torque limiter / slip clutch** | a child forcing a geared arm; a motor stalled against a stop |
| connect and disconnect on demand | engaged clutch | a toy that can be switched between hand and motor drive |

## Freewheels (one-way)

- **Ratchet and pawl**: two or more spring-loaded pawls on a toothed ring, or
  two saw-tooth discs spring-pressed together. Simple and printable. It clicks
  at a rate proportional to the speed difference. Its backlash is up to one
  tooth, so more teeth or more staggered pawls give quicker engagement. The
  tooth and pawl geometry are on [[cams-intermittent#ratchet-and-pawl]].
- **Roller (ramp) clutch**: spring-loaded rollers wedge between a ramp and a
  cylinder in one direction and roll free in the other. It is silent with
  near-zero engagement angle. Buy it as a one-way bearing (`$step-parts`);
  printed ramps wear.
- **Sprag clutch**: tilted sprags wedge between two races. Like the roller
  clutch it is bought, not printed.

Uses beyond toys show the purpose: a bicycle's coasting hub, an engine
starter that must not be over-spun by the engine, a helicopter rotor that
autorotates.

## Torque limiters

| type | how it releases | resets |
|---|---|---|
| **friction plate / slip clutch** | plates slip above a set torque (spring or nut preload) | continuously, by itself |
| **ball detent** | spring-loaded balls leave their detents | at the next detent, by itself; the adjustable clutch on a cordless drill |
| **pawl and spring** | a spring-held pawl leaves its notch | automatically or by hand |
| **shear pin** | a sacrificial pin breaks | replace the pin |
| magnetic (synchronous, particle, hysteresis) | magnets slip | by itself |

For printed toys the practical choices are a **detent clutch**, with printed
bumps on a flexing arm or a spring pressing a ball into dimples, and a
**friction clutch**, with a spring-loaded felt or rubber washer. Put the
limiter between the motor or crank and the first stage that a child can
jam. Its slip torque must sit below the weakest printed tooth's failure
torque and above the running torque.

```python
assert RUNNING_TORQUE < SLIP_TORQUE < WEAKEST_STAGE_TORQUE, "limiter does not protect the train"
```

The ball-detent holding force formula is in [[latches-detents-and-ratchets]].

## Checks

- Asserts: the slip-torque band above; freewheel direction matches the drive
  direction ([[energy-drive#drive-direction]]).
- Motion: a freewheel owes a rotation sweep `clear` in the coasting direction
  and `blocked` in the driving direction with the pawl engaged. The pawl's
  pivot belongs in the retention chain.
- Open items: slip torque, detent force and wear are forces and life, which
  no rigid gate measures. Record them and plan a test coupon.
