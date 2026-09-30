---
title: Counterweights and gravity balance
tags: [counterweight, gravity-compensation, spring, gas-spring, balance, lid, lamp, ballast]
aliases: [counterbalance, equilibrator, anglepoise, carwardine, zero free length spring, zero-length spring, spring balance, gas strut, gas spring, lift support, lid stay, balanced arm lamp, ballast pocket, steel shot]
sources:
  - French, M. J. and Widden, M. B., "The spring-and-lever balancing mechanism, George Carwardine and the Anglepoise lamp", Proc. IMechE Part C 214 (2000) 501–508 (https://eprints.lancs.ac.uk/20295/1/20295.pdf), eqs. 1, 8–10, 14, 17
  - Stabilus, Gas Springs Technical Information (https://www.betz.cz/stabilus/ke-stazeni/08_Technical_Information_EN.pdf), ch. 1.2 and 5.1–5.2 (force ratio x = F2/F1 = V1/V2, reserve factor 1.2–1.3, ~50,000 automotive cycles with < 10 % force loss)
  - https://www.suspa.com/global/products/gas-struts/faq (rod down, ~3.5 % force per 10 °C between −30 and +80 °C, no side load, friction F_out = A p − F_R, F_in = A p + F_R, 10,000–100,000 double strokes)
  - https://www.engineeringtoolbox.com/metal-alloys-densities-d_50.html (steel 7850, bismuth 9750, lead 11340, tungsten 19600 kg/m³)
  - https://en.wikipedia.org/wiki/Random_close_pack (loose random sphere packing 0.59–0.60, random close packing ~0.64)
related: [springs, hinges-and-pin-joints, stability-and-tipping, linkages, mass-properties-and-measurement, toy-safety-constraints, creep-and-stress-relaxation, magnets-and-strap-slots]
updated: 2026-09-23
---

# Counterweights and gravity balance

An arm, boom or lid that must stay where it is left needs its gravity moment
cancelled at **every** angle, not at one. There are four ways: a
counterweight, a zero-free-length spring on a lever (exact at all angles), a
gas or coil spring on a hinge (exact at one or two angles), and friction to
cover whatever is left. Read this before drawing a lamp boom, a balanced arm,
a hinged lid or a drawbridge. Sizing the actuator that remains is
[[arm-and-gripper-sizing]]; a friction hinge alone is
[[hinges-and-pin-joints#friction-and-hold-open-hinges]].

## Gravity moment

A body of mass `m` whose centre of mass is at distance `r` from the pivot,
with the line pivot→CoM at angle θ from horizontal:

```text
M_g(θ) = m · g · r · cos θ          (θ from horizontal; = m g r sin φ with φ from vertical)
```

Every balancing element must produce a moment with the same `cos θ` shape.
The CoM is the combined one of everything that swings — find it with
[[mass-properties-and-measurement#density-weighted-centre-of-mass-for-mixed-materials]].

## Counterweight

```text
m_c · r_c = Σ m_i · r_i            exact at all angles only if the counterweight's CoM
                                    lies on the line through the pivot and the load's CoM
```

- It is exact everywhere and needs no spring, but it **adds mass**: the pivot
  carries load + counterweight, and the moment of inertia grows by
  `m_c r_c²`, so the arm is slower to start and stop.
- A short counterweight arm needs a heavy weight. Illustration: a 150 g head
  at 300 mm plus a 40 g boom (CoM at 150 mm) is 0.051 kg·m. At `r_c` = 80 mm
  the counterweight is 638 g — 81 cm³ of solid steel, 135 cm³ of loose steel
  shot, 33 cm³ of tungsten.
- An off-line counterweight adds a `sin θ` error term: the arm balances at one
  angle and drifts elsewhere.

## Zero-free-length spring: the Carwardine balance

French and Widden's analysis of the Anglepoise mechanism: a load `m` at
radius `r` on an arm pivoted at A; a spring from point C on the arm (distance
`b` from A, on the far side of A from the load for the Fig. 2a layout) to
a fixed point B (distance `c` directly above or below A). Balance holds at
**every** angle if and only if

```text
spring free length l0 = 0          (tension proportional to its whole length a)
stiffness            k  = m g r / (b c)
```

With a real spring, `F = k (a − l0)`, and the balance error is

```text
ΔM(θ) = k · l0 · b · c · sin θ / a            → zero only when l0 = 0
```

Illustration: 0.2 kg at 300 mm, `b = c = 40 mm` → k = 0.37 N/mm, and at the
largest spring length (a = b + c = 80 mm) the spring pulls 29 N. Short `b`
and `c` mean stiff springs and large pivot loads: size the pins and the
anchor posts for that force, not for the lamp's weight
([[hinges-and-pin-joints#pin-and-knuckle-sizing]]).

Ways to get `l0 = 0`:

- **Initial tension.** A close-coiled extension spring wound with pre-tension
  has an effective free length `L0 − F_i / k`. Choose `F_i = k · L0` and the
  line through its force–length curve passes through zero. It only holds
  while the coils are open, so `a` must stay above the body length `L0` —
  put the spring where it is always stretched.
- **Hide the body behind a pulley or slide.** Run a cord from C over a small
  pulley at B to a spring anchored beyond it, rigged so the spring is at its
  free length when C reaches B. The spring's stretch then equals `a`. The
  pulley radius adds a small error; keep it small against `b` and `c`.
- A tension–compression spring pair (Nathan, cited in the paper) — rarely
  worth it at toy scale.

Two degrees of freedom (the desk lamp): a **parallelogram** carries the
vertical reference from the base to the elbow, so each arm's spring sees
only its own angle. Each spring is sized by the same formula with its own
`b`, `c` and the mass it carries (`k1 = m g r1 / (b1 c1)`,
`k2 = m g r2 / (b2 c2)`); with arm masses included, the numerator becomes the
sum of each mass times its radius. Exact balance with heavy arms needs each
arm's CoM **on the line through its pivots**, otherwise a `cos θ` term
returns and balance holds at one angle only. Carwardine mounted the shade
in trunnions so its CoM does not move when it is tilted; later cheaper
copies lost that and drift.

## Gas springs for lids

A gas spring is nitrogen behind a piston rod: nearly constant force that
rises slightly as it compresses.

```text
F(extended) = F1,  F(compressed) = F2 = x · F1,   x = V1 / V2   (close to 1 for a big tube)
F_out = A p − F_R   (extending)     F_in = A p + F_R   (compressing; friction F_R)
moment balance (Stabilus 5.1):  n · F1 · h_s = R · m g · x_g
   h_s  perpendicular distance from hinge to the spring's line
   x_g  horizontal distance from hinge to the lid CoM, in the position being held
   R    force reserve factor, 1.2–1.3 (more below 10 °C, less above 30 °C)
```

- The lid moment falls as `cos θ` while the spring's lever arm `h_s` changes
  with the mounting points. The result is a range where the lid needs a push
  and a range where it lifts itself or falls shut. Check the moments at
  closed, at about one third open and fully open; that is the whole design.
- Force changes about **3.5 % per 10 °C** (SUSPA, −30 to +80 °C). Size for
  the coldest room the product lives in.
- Mount **rod down** (the seal stays lubricated), with ball or eye ends so
  **no side load** reaches the rod. Both ends pivot; the travel of each
  pivot is a `clear` sweep.
- A spring whose line passes over the hinge (over-centre) as the lid closes
  holds it shut; one that never crosses holds it open. Place the anchor on
  purpose.
- Gas springs are bought parts: search `$step-parts` by stroke and extended
  length, seat both ends from the STEP with `cadmount`. Life is roughly
  10,000–100,000 double strokes.

## Torsion and coil springs at a hinge

A spring's torque is linear in angle; gravity is `cos θ`. A spring can
match gravity at two angles at best, so **a spring plus friction** is the
usual answer: the friction torque must cover the largest residual.

```text
T_spring(θ) = k_t · (θ0 − θ)                       (θ0: angle where the spring is relaxed)
T_friction ≥ max_θ | m g r cos θ − k_t (θ0 − θ) |  over the travel
```

Illustration: a lid with `m g r = 0.5 N·m` opening 0 → 90°. A spring relaxed
at 90° (θ0 = π/2) and matching at closed has k_t = 0.32 N·m/rad; the largest
residual is 0.105 N·m, near 40° open. Friction of about 21 % of the lid moment
then holds it anywhere — less than a quarter of what friction alone needs.
Size the spring itself with [[springs#torsion-spring]], and remember
printed friction relaxes ([[creep-and-stress-relaxation]]).

## Ballast pockets and dense fills

| fill | density (g/cm³) | note |
|---|---|---|
| PLA part | about 1.2 | the thing being balanced |
| steel (shot, balls, nuts, washers) | 7.85 | cheap, magnetic, rust-prone if wet |
| bismuth | 9.75 | lead-free, brittle |
| lead | 11.3 | not in toys or anything handled by children ([[toy-safety-constraints]]) |
| tungsten (putty, shot, cubes) | 19.6 | smallest pocket; expensive |

- Loose shot packs to about **0.6** of the pocket volume (random loose
  packing of spheres 0.59–0.60, shaken ~0.64):
  `V_pocket = m / (ρ · 0.6)`. Solid pieces (nuts, a cut bar) use nearly the
  whole pocket.
- Close the pocket so the fill cannot rattle or escape: drop it in during a
  print pause, or screw a lid on and fill the voids with epoxy or a
  compressible pad ([[magnets-and-strap-slots]] shows the pause-and-drop
  pocket). Loose shot rattles ([[noise-and-vibration]]).
- Put the fill where the moment needs it — as far from the pivot as the
  envelope allows — and model it as its own body so the CoM check uses its
  real density.

## Stability: balance moves the problem to the base

A balanced arm or lid still moves the whole product's CoM when it swings.
A counterweight adds mass high up on the arm; a spring moves no mass but
loads the base with its reaction. Check tipping with the arm at full reach
and at the other extreme ([[stability-and-tipping#support-polygon-and-centre-of-mass]],
[[stability-and-tipping#making-it-stand]]).

## Checks

```python
M_load = g * sum(m * r for m, r in swinging_masses)          # at horizontal
assert abs(m_c * r_c - M_load / g) <= 0.05 * M_load / g, "counterweight moment off by > 5 %"
k_zfl = m * g * r / (b * c)
assert abs(k_spring - k_zfl) / k_zfl <= 0.1 and l0_effective <= 0.05 * min(b, c), "not a zero-free-length balance"
for th in thetas:                                            # hinge spring + friction
    assert abs(m * g * r * cos(th) - k_t * (th0 - th)) <= T_friction_min, f"lid drifts at {th:.2f} rad"
assert n * F1_min_cold * h_s >= R * m * g * x_g, "gas spring cannot hold the lid open when cold"
```

Open items: real spring rate and initial tension (catalog tolerance), gas
spring force tolerance, friction after creep. A rigid-body gate checks none
of them; record them.
