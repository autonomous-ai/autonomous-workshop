---
title: Noise and vibration in printed mechanisms
tags: [noise, vibration, resonance, isolation, gear, fan, pwm, rattle, damping]
aliases: [gear whine, gear noise, rattle, buzz, hum, squeak, motor whine, pwm whine, vibration damper, stepper damper, rubber grommet, anti-vibration mount, natural frequency, transmissibility, quiet mechanism, nvh]
sources:
  - https://gearsolutions.com/features/noise-reduction-in-plastic-gears/ (contact ratio, helix angle for integer face contact ratio, tip relief, crowning, non-hunting ratios for plastic, sliding ratio < 3.0)
  - https://www.stagnoligears.com/en/motor-gears/noise-reduction-plastic-gears/ (POM–POM noisiest; plastic on steel quiet; lubricated POM pair quiet)
  - https://khkgears.net/new/gear_knowledge/gear_technical_reference/design-of-plastic-gears.html (plastic gears need more backlash than metal)
  - Shigley's Mechanical Engineering Design, ch. 13 (helical gears: axial pitch and face contact ratio)
  - Rao, Mechanical Vibrations, ch. 2–3 (natural frequency, cantilever effective mass 33/140, transmissibility)
  - https://en.wikipedia.org/wiki/Euler%E2%80%93Bernoulli_beam_theory (cantilever ω1 = 3.516/L² · √(EI/μ))
  - https://accendoreliability.com/machine-vibration-isolation-theory-and-practice/ (T = 1 at f/fn = √2; practical ratio ≥ 3; rubber ζ ≈ 0.2, steel springs ≈ 0.02)
  - https://en.wikipedia.org/wiki/Vibration_isolation (more damping, less high-frequency isolation)
  - https://www.linengineering.com/products/value-add/accessories/nema17-damper (shaft inertia damper: settling 0.5 s → 0.05 s)
  - https://www.omc-stepperonline.com/nema-17-vibration-damper (rubber-sandwich motor mount damper; 5–10 dB on printer X/Y axes via search excerpt)
  - https://www.cnckitchen.com/blog/reduce-your-3d-printing-noise-with-a-concrete-paver (67.7 dB → below 56 dB with a paver on soft foam)
  - https://forum.pololu.com/t/pwm-frequency-and-noise/4636 (Arduino default 490 Hz audible; via search excerpt)
  - https://www.progressiveautomations.com/blogs/how-to/why-is-my-dc-motor-whining-at-a-lower-pwm-frequency (16–20 kHz PWM ends most whine; more H-bridge switching loss)
  - https://www.punker.com/en/fan-technology-guide/basics-of-acoustics/fan-acoustics/ (L_W ∝ 50 log u + 20 log D; quietest near best efficiency)
  - https://blog.igus.eu/squeaking-plain-bearings-how-to-reduce-noise/ (stick-slip squeak, too-smooth shafts, Ra 0.2–0.4 µm, excess clearance rattles)
  - https://hometheaterhifi.com/technical/primers/speaker-design-keeping-the-amount-of-driver-and-enclosure-resonance-to-a-minimum/ (curved or braced panels, damping; via search excerpt)
related: [gears, small-dc-motors, stepper-motors, motor-drivers-and-flyback, shafts-and-bearings, friction-wear-and-lubricants, beam-and-plate-stiffness, ribs-and-stiffening, thermal-design-for-enclosures, springs]
updated: 2026-09-23
---

# Noise and vibration in printed mechanisms

A printed mechanism is loud for four reasons: its gears mesh with errors,
its motors shake a light stiff shell that radiates like a loudspeaker,
something is loose and rattles, or a drive frequency sits on a structural
resonance. Find the source first — each has its own cure — then fix it in
the source geometry. Read this when a moving product must be quiet, or when a
motor, fan or gear train goes into a printed housing.

## Name the excitation frequencies first

Every cure below compares a structure's natural frequency with what drives
it. List them in the spec:

| source | frequency |
|---|---|
| shaft imbalance | `f = n / 60` (n in rpm) |
| gear mesh | `f_mesh = z · n / 60` for either gear of the pair |
| stepper | full-step rate `= steps_per_rev · rev/s`; its resonance band is low speed |
| DC motor PWM | the PWM frequency (an Arduino's default, about 490 Hz on most pins, is audible) |
| fan blade pass | `blades · n / 60` |

Illustration: a 130-size motor at 9,000 rpm is 150 Hz; its 10-tooth pinion
meshes at 1.5 kHz, where the ear is sensitive.

## Resonance: keep natural frequencies away from the drive

A part that behaves like a mass `m` on a stiffness `k` has

```text
f_n = (1 / 2π) · √(k / m)
cantilever with tip mass     k = 3 E I / L³,   m = m_tip + (33/140) · m_beam
uniform cantilever alone     f_1 = (3.516 / 2π) · √(E I / (μ L⁴))       μ = mass per length
from static sag δ under g    f_n = (1 / 2π) · √(g / δ) ≈ 15.8 / √(δ [mm])  Hz
```

Illustration: a PLA bracket (E ≈ 3.5 GPa), 60 mm long, 10 mm wide, 3 mm
thick in the bending direction, carrying a 30 g motor at its tip:
k ≈ 1.09 N/mm, f_n ≈ 30 Hz. Doubling the thickness to 6 mm raises k eight
times and f_n to 86 Hz ([[beam-and-plate-stiffness#depth-beats-width-and-material-belongs-at-the-surface]]).

- Response is amplified near `f / f_n = 1` and suppressed well above it.
  Keep each structural `f_n` **above** the highest steady excitation by a
  clear margin (stiffen: depth, ribs, closed sections, shorter spans —
  [[ribs-and-stiffening]]), or deliberately **far below** it on an isolator
  (next section). A motor that spins up passes through every frequency below
  its running speed: it must not dwell there.
- Adding mass lowers `f_n` and lowers the response to a given force above
  resonance; it helps a panel already above its drive, and hurts one just
  below it.
- Damping only matters near resonance: TPU, foam, felt or a constrained
  layer take the peak off; they do little far from it.

## Isolating a motor from the shell

An isolator is a soft spring under the motor. It works only above its own
natural frequency:

```text
undamped transmissibility   T = 1 / |1 − r²|,   r = f_drive / f_n
damped                      T = √((1 + (2ζr)²) / ((1 − r²)² + (2ζr)²))
T = 1 at r = √2; isolation only above it; aim for r ≥ 3
```

At r = 3, an undamped mount transmits 12.5 %, a rubber one (ζ ≈ 0.2) about
19 % — damping calms the resonance but costs isolation above it.

- **Rubber grommets or sleeves** around the motor's screws, with no hard
  path left: the screw must not clamp metal to plastic through the grommet.
  Leave a gap round the motor body; a motor that touches the shell anywhere
  is not isolated.
- **Stepper mount dampers** (two plates joined by rubber) are reported to
  cut 3D printer axis noise by about 5–10 dB. They add compliance: a belt
  or gear pulling on the motor now deflects it, so check tension and mesh
  under load ([[belts-and-pulleys#tension]]).
- **Shaft inertia dampers** are a different part: they damp the stepper
  rotor's ring-down after each step (one vendor: settling 0.5 s → 0.05 s).
- A **flexible coupling** between motor and load breaks the path through the
  shaft ([[shaft-couplings]]).
- Driver settings matter as much as mounts: microstepping and quiet-mode
  stepper drivers remove most step noise ([[stepper-motors]]).
- The whole product on a desk makes the desk the loudspeaker. Soft feet
  under a heavy base help: a 3D printer measured 67.7 dB on its felt feet
  and below 56 dB on a concrete paver over soft foam. Give products that
  vibrate soft feet at the polygon corners
  ([[stability-and-tipping#a-base-that-rocks-is-not-a-polygon]]).

## Gear noise

Gear noise is transmission error — the output not following the input
exactly — excited at the mesh frequency.

- **Contact ratio above 1.0 in the worst centre-distance case**, and higher
  is quieter: more teeth share the load and the hand-over is smoother. More,
  smaller teeth at the same centre distance raise it; so does a lower
  pressure angle (deeper teeth). Printed teeth set a floor on module
  ([[gears#printed-tooth-choices]]).
- **Helical or herringbone** teeth engage gradually along the face. The
  quietest helix gives a face contact ratio near a whole number:
  `ε_β = b · sin β / (π m_n)`. At m_n = 1, β = 20°: ε_β = 1 needs
  b ≈ 9.2 mm. Herringbone cancels the axial thrust a single helix puts on
  the bearings.
- **Tip relief and crowning** keep a slightly misaligned or deflected tooth
  from striking its mate at the tip or the face edge. Relief no larger than
  deflection plus profile error.
- **Non-hunting ratio for plastic** (e.g. 12:24): the same teeth meet every
  turn, so a printed tooth error wears in rather than wandering.
- **Material pairing:** in one supplier's tests, **POM on POM was the
  noisiest pair** and the most sensitive to torque changes; plastic on steel
  was quiet, and a lubricated POM pair was quiet. A PLA–PLA printed pair has
  layer steps on every flank; a nylon, PETG or POM gear against a
  different plastic or a steel pinion runs quieter. Check any grease against
  the plastic ([[friction-wear-and-lubricants#lubricants-check-the-base-oil-against-the-plastic]]).
- **Backlash rattle:** a lightly loaded or reversing train knocks across its
  backlash. Plastic needs more backlash than metal (thermal and moisture
  growth), so do not remove it: keep the load one direction (a light spring,
  a drag, gravity) so the teeth stay on one flank.
- **Stiff shafts and housings.** A deflecting shaft or a flexing gearbox
  wall changes the centre distance under load, which is transmission error
  ([[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]]).

## Bearings, bushings and squeak

- Plain bearings squeak by **stick-slip**, worst when shaft and bore are both
  very smooth and dry; igus recommends shaft Ra 0.2–0.4 µm and a little
  grease at assembly. Too much clearance rattles.
- PLA on PLA squeaks and wears; a steel shaft in a PETG or nylon bore, or a
  bought bushing, runs quieter ([[shafts-and-bearings#bushing-or-ball-bearing]]).
- Polymers damp where metal rings: igus reports its plastic bearings run
  quieter than metal ones. A ball bearing at motor speed can still be the
  quietest choice; seat it square in a `snug` seat rather than a crushing
  press ([[seating-bought-parts]]).

## Rattles and panel buzz

- **Nothing loose.** Every wire, battery, weight and lid either preloaded or
  padded: foam or felt under a battery door, a clip or tie for the wires,
  ballast potted or packed ([[counterweights-and-gravity-balance#ballast-pockets-and-dense-fills]]),
  a slight interference on a lid seam. A rattle is a clearance that sees
  vibration.
- **Stiffen large flat panels.** A flat printed wall is a soundboard. Ribs,
  a curve or a crowned face raise its `f_n`
  ([[beam-and-plate-stiffness#plates-under-uniform-pressure]]); a bonded
  damping patch or a foam lining takes the peak off.
- **Decouple the source from the panel:** mount motors, speakers and fans
  through a gasket or grommets, not straight into a large wall.

## Fans

```text
sound power  L_W = const + 50 · log10(u2/u1) + 20 · log10(D2/D1)     u = tip speed
```

Tip speed dominates: 20 % slower is about 4.8 dB quieter. For the same
airflow, a larger fan turning slower is quieter than a small fast one, and
any fan is quietest near its best-efficiency point, not throttled against a
blocked vent. Give it free inlet space and a smooth path
([[thermal-design-for-enclosures#fans-airflow-from-power-and-δt]] sizes the
airflow).

## PWM whine

A DC motor driven by PWM in the audible band sings at that frequency: the
current ripple makes torque ripple. Running PWM at 16–20 kHz or above ends
most whine; the H-bridge then switches more often and runs hotter, so check
the driver's maximum PWM frequency and its heat
([[motor-drivers-and-flyback#choosing-an-h-bridge]]). A servo that hums while
holding is fighting its load or its deadband — lower the load
([[arm-and-gripper-sizing]]) rather than isolating it.

## Checks

```python
f_n = (1 / (2 * math.pi)) * math.sqrt(k / m)
for f_drive in excitation_frequencies:           # shaft, mesh, step, PWM, blade pass
    r = f_drive / f_n
    assert r <= 0.5 or r >= 3, f"{f_drive:.0f} Hz within resonance band of a {f_n:.0f} Hz part"
assert pwm_hz >= 16_000 or not quiet_required, "audible PWM frequency"
assert contact_ratio_min > 1.0, "gear contact ratio below 1 at the largest centre distance"
```

Open items: what actually sounds loud is measured, not modelled. Record the
excitation table and the chosen cures; a CAD gate checks none of them.
