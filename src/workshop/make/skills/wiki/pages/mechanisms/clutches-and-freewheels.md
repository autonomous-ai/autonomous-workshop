---
title: Clutches, freewheels and torque limiters
tags: [clutch, freewheel, one-way, sprag, torque-limiter, slip-clutch, ball-detent, shear-pin, overload, dog, jaw, shift-fork]
aliases: [one-way clutch, overrunning clutch, sprag clutch, roller clutch, one-way bearing, slip clutch, friction clutch, overload clutch, safety clutch, dog clutch, jaw clutch, claw clutch, claw coupling, positive clutch, toothed clutch, face clutch, square jaw clutch, spiral jaw clutch, sawtooth clutch, dog ring, dog teeth, sliding dog, back-cut dogs, undercut dogs, shift fork, selector fork, shifter yoke, sliding collar, gear selector, synchromesh, synchronizer]
sources:
  - https://en.wikipedia.org/wiki/Freewheel (saw-tooth ratchet discs, roller type, pawls and clicking, uses)
  - https://en.wikipedia.org/wiki/Torque_limiter (friction plate, ball detent, shear pin, magnetic, pawl and spring)
  - https://en.wikipedia.org/wiki/Dog_clutch (interlocking teeth, no slip, shock at unequal speeds, synchromesh matches speeds first)
  - https://mechanicalinfo.wordpress.com/2011/11/02/types-of-clutches/ (square jaws not engaged in motion; spiral jaws one direction, engaged in motion; sliding half on a feather key)
  - https://www.firgelliauto.com/blogs/mechanisms/clutch-form (tangential load per jaw T/(r n), axial separation (T/r) tan alpha)
  - https://www.firgelliauto.com/blogs/mechanisms/sliding-clutch-box (back-taper 2-5 deg; 50-100 rpm engagement difference in steel boxes; 30-45 deg tip chamfer; fork-to-groove 0.2-0.4 mm)
  - https://www.hpacademy.com/blog/tech-nugget-how-a-dog-engagement-gearbox-works (back-cut dogs held engaged by torque; a torque interruption lets them out)
  - https://rallysportmag.com/gearboxes-in-rallying-a-technical-overview/ (six large dogs; wider gaps give more backlash and a larger chance to engage)
related: [cams-intermittent, energy-drive, gears, springs, latches-detents-and-ratchets, shaft-hub-connections, shaft-couplings, linear-guides-and-slides, layer-anisotropy, filament-properties]
updated: 2026-10-01
---

# Clutches, freewheels and torque limiters

Three different jobs, often confused:

| job | device | toy example |
|---|---|---|
| drive one way, coast the other | **freewheel / one-way clutch** | a wind-up or pull-back car that coasts; a crank that should not spin back |
| slip instead of breaking when overloaded | **torque limiter / slip clutch** | a child forcing a geared arm; a motor stalled against a stop |
| connect and disconnect on demand | **dog (jaw) clutch** ([[#dog-clutches-and-jaw-clutches]]) or friction clutch | a toy that can be switched between hand and motor drive |

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

## Dog clutches and jaw clutches

A dog (jaw, claw) clutch couples two coaxial parts by teeth on their facing
ends. One half slides axially on a feather key, spline or D-flat
([[shaft-hub-connections]]) and is moved by a shift fork. It never slips, so
it engages with a shock when the halves turn at different speeds; a
synchromesh matches the speeds first. The permanent, unshifted version with
an elastomer spider is the jaw coupling ([[shaft-couplings]]).

| tooth form | drives | engages | use |
|---|---|---|---|
| **square jaw** | both ways | at rest or barely turning | a hand/motor selector switched while stopped |
| **back-cut square** (faces undercut 2–5°) | both ways | at rest; torque then pulls it in | a dog that must not jump out under load; a torque dip lets it out |
| **spiral jaw** (one face square, one helical) | one way | in motion, still with a shock | engaging a turning drive in one direction |
| **sawtooth** (one face square, one ramp), spring-loaded | one way; rides over the other way | always | a freewheel ([[#freewheels-one-way]]) |
| **sloped or chamfered flanks**, spring-loaded | both ways up to a torque | always | a torque limiter ([[#torque-limiters]]) |

**Flank force.** With n dogs sharing the load at mean radius r_m and the
loaded flank at angle α from the axis (α < 0 for a back-cut):

```text
tangential, per dog    F_t = T / (r_m · n)
axial push-out         F_a = (T / r_m) · (tan α − μ) / (1 + μ tan α)     (derived; ≤ 0 holds itself)
```

A square face (α = 0) has no push-out in theory, but deflection and wear tilt
it and vibration walks it out; a back-cut holds by geometry; any positive
flank needs the fork, detent or spring to supply `F_a`
([[latches-detents-and-ratchets#detent-holding-force]]).

**Engagement window** (derived). n dogs of angular width β leave each mating
dog a gap `θ_g = 2π/n − 2β`. At relative speed ω the gap passes in `θ_g/ω`,
and the sliding half must enter its minimum overlap `h_min` in that time:
`v_shift ≥ h_min · ω / θ_g`. Fewer, narrower dogs give a longer window: a
rally dog box uses six large dogs and wide gaps, accepting the backlash for
the chance to engage. Steel practice keeps the speed difference to about
50–100 rpm; a printed square-jaw clutch engages at rest.

**Shift fork and groove.**

- The collar carries a circumferential groove; the fork's two pads sit in it
  on a diameter through the axis, so the push acts on the axis and the collar
  does not cock. A one-sided push binds when the pad radius over the collar's
  guided length exceeds `1/(2μ)` ([[linear-guides-and-slides#the-binding-ratio]]).
- Groove width `slot_for(PAD_T, RUN)`; steel practice gives 0.2–0.4 mm fork
  clearance.
- **A detent holds the shift rod or lever**, not the collar, at each position
  (engaged, neutral, the other gear), so the fork floats centred and rubs only
  while shifting. The detent also resists any `F_a` the flanks make.
- Travel = engagement depth + disengaged clearance (`RUN` at least) + detent
  overtravel.

**Printable tooth proportions.**

- Print each half axis vertical with the teeth **face up**: the drive faces
  are perimeter walls, and a ramp or chamfer faces upward and prints as fine
  steps. Teeth printed face down overhang.
- A face-up dog is a short post in Z, and the drive force bends it with
  tension **across the layers** at its root. With dog height h (axial),
  thickness w along the circumference and radial width b:
  `σ = 6 F_t h / (b w²)`, checked against the interlayer strength, not the
  X-Y value ([[filament-properties#a-second-supplier-disagrees-and-why-that-matters]],
  [[layer-anisotropy]]). Keep `h ≤ w` and put the dogs on the largest radius
  the part allows.
- A small tip chamfer (steel practice 30–45°) stops tip-to-tip landing. A
  large one is a ramp that pushes the dog out.
- Printed dogs are weaker and coarser than steel ones: use the fewest, largest
  dogs the backlash allows, and count on fewer than all n sharing the load.

```python
F_t = T_DESIGN / (R_MEAN * N_DOGS_SHARING)
assert 6 * F_t * DOG_H / (DOG_B * DOG_W**2) <= SIGMA_Z / SF, "dog root breaks across the layers"
push = (T_DESIGN / R_MEAN) * (math.tan(ALPHA) - MU) / (1 + MU * math.tan(ALPHA))
assert push <= F_DETENT, "dogs walk out of engagement"
assert DOG_H <= DOG_W, "dog too tall for a face-up print"
```

## Checks

- Asserts: the slip-torque band above; freewheel direction matches the drive
  direction ([[energy-drive#drive-direction]]).
- Motion: a freewheel owes a rotation sweep `clear` in the coasting direction
  and `blocked` in the driving direction with the pawl engaged. The pawl's
  pivot belongs in the retention chain. A dog clutch owes the collar's slide
  `clear` along the shaft, and a rotation sweep `blocked` while engaged and
  `clear` when disengaged.
- Open items: slip torque, detent force and wear are forces and life, which
  no rigid gate measures. Record them and plan a test coupon.
