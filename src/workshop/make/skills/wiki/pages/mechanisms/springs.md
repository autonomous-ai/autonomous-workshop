---
title: Springs
tags: [spring, compression-spring, torsion-spring, extension-spring, spring-rate, wahl, buckling, spring-index]
aliases: [coil spring, helical spring, spring constant, spring stiffness, wire spring, spring design]
sources:
  - https://www.mechanixcalc.com/guides/compression-spring-design (rate, active and total coils, solid length, Wahl stress, allowable 0.5 Rm, G values, index 6-12)
  - https://mechsimulator.com/blog/articles/spring-design-helical-spring-calculator-guide/ (index 4-12, torsion moment formula, G values)
  - Shigley's Mechanical Engineering Design, ch. 10 lecture slides, https://www.philadelphia.edu.jo/academics/mgogazeh/uploads/DESIGN%202%20CH10.pdf (10.8 torsion constant, set removal 10-30 %, coil ID shrinks under load)
  - https://extrudesign.com/buckling-of-compression-springs/ (free length > 4 D buckles, guide rod or tube, buckling factors)
  - https://designofmachinery.com/wp-content/uploads/2018/11/Ch144edp802.pdf (Norton: aspect ratio > 4 may buckle, fixed-fixed vs fixed-free)
  - https://en.wikipedia.org/wiki/Spring_(device) (Hooke's law, oscillation period)
related: [energy-drive, flexures-and-living-hinges, cams-intermittent, joints, sweeps-and-helices, counterweights-and-gravity-balance]
updated: 2026-09-23
---

# Springs

A spring stores energy as elastic deflection. Buy metal springs for anything
cyclic or precise, and seat them with `cadmount`. A printed plastic spring
creeps and loses force ([[energy-drive#sources]]). The formulas below size
either kind and set the seat the spring needs.

Modelling a coil or any helical sweep in build123d: [[sweeps-and-helices]].

## Helical compression spring

`d` wire diameter, `D` mean coil diameter, `n` active coils, `G` shear
modulus:

```text
rate            k = G d⁴ / (8 D³ n)            F = k · x   (Hooke)
spring index    C = D / d
Wahl factor     K = (4C − 1)/(4C − 4) + 0.615/C
peak shear      τ = K · 8 F D / (π d³)
```

- `d` enters to the fourth power: doubling `d` makes the spring 16× stiffer,
  and doubling `D` makes it 8× softer.
- **Index**: keep `4 ≤ C ≤ 12`; practical designs target 6–12 and most
  production springs fall between 6 and 9. Below 4 the wire is hard to coil
  and stress concentrations spike; above 12 the spring tangles and buckles.
  At `C = 10`, `K ≈ 1.145`. Omitting `K` understates peak stress by roughly
  10–30 %.
- **Coils and solid length**: squared-and-ground ends add two inactive coils,
  `Nt = n + 2`, and solid length `Ls = Nt · d`. Unground ends give
  `(Nt + 1) · d`. The spring may never be compressed to solid in service;
  leave travel before solid.
- **Allowable stress**: about `0.5 · Rm` of the wire's tensile strength, with
  static safety ≥ 1.3. `G` ≈ 80–81.5 GPa for spring and music steel,
  69–73 GPa for stainless, 41 GPa for phosphor bronze.
- **Set removal**: a spring made long and pressed solid once sets 10–30 % of
  its free length and gains useful residual stress. It is not recommended for
  springs in fatigue.

```python
C = D_MEAN / D_WIRE
assert 4 <= C <= 12, f"spring index {C:.1f} out of range"
k = G * D_WIRE**4 / (8 * D_MEAN**3 * N_ACTIVE)
assert L_WORK_MIN > (N_ACTIVE + 2) * D_WIRE, "spring goes solid in service"
```

## Buckling

A compression spring whose free length is more than about **4 × its mean
diameter** behaves like a column and can buckle at a low load. Ends clamped
parallel (fixed–fixed) resist buckling far better than a free, tipping end.
One table gives a buckling factor of 0.53 for built-in ends against 0.11 for
hinged ends at `L/D = 5`. Cures: put the spring over a guide rod or inside a
tube, sized from `cadfits` with room for the coil to grow in diameter as it
compresses. The guide adds friction.

## Torsion spring

The coil wire is loaded in **bending**, not torsion. With `E` Young's modulus:

```text
moment per radian   M/θ = E d⁴ / (64 D n)
rate per turn       k'  = E d⁴ / (10.8 D n)     10.2 theoretical, 10.8 corrects for arbor friction
```

A wound-up torsion spring's coil diameter **shrinks**. The arbor (pin)
through it must stay clear of the reduced inside diameter at full wind, or the
spring locks on the pin.

## Extension spring

The same rate formula applies, but an extension spring is wound with initial
tension, so it does not start to extend until that preload is overcome. Its
hooks are the usual failure point. Anchor the hooks on posts, not in sharp
holes, and give the spring a stop so it cannot be stretched past its
elastic range.

A zero-free-length spring that balances an arm at every angle:
[[counterweights-and-gravity-balance]].

## Dynamics

A mass `m` on a spring oscillates with period `T = 2π √(m / k)`. That sets a
bounce frequency for a follower held down by a spring
([[cams-intermittent#keeping-the-follower-on-the-cam]]): drive the cam well
below it or the follower floats.

## Checks

- Asserts: index, not solid in service, stress below allowable with the Wahl
  factor, and L/D ≤ 4 or a guide present.
- Seat: pocket or post from `cadfits`, a catalog spring's STEP under `ref/`
  with a mount row.
- Open items: actual rate after assembly and preload are forces. A rigid gate
  never checks them, so record them.
