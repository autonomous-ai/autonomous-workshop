---
title: Arm and gripper sizing
tags: [robot-arm, gripper, servo, torque, payload, backlash, friction, end-effector]
aliases: [robot arm, robotic arm, desktop arm, joint torque, shoulder torque, claw, gripper jaw, parallel gripper, fin ray, finray, underactuated finger, grip force, payload budget]
sources:
  - https://www.firgelliauto.com/blogs/engineering-calculators/robot-arm-payload-calculator-joint-torque (τ = Σ m g d cos θ; "double or triple your static torque estimate")
  - https://automaticaddison.com/how-to-determine-what-torque-you-need-for-your-servo-motors/ (τ = I α + m g (r/2) cos θ, horizontal worst case)
  - https://www.robotis.us/robotis-blog/torque-ratings/ (continuous torque ≈ 20 % of stall for servos rated in stall torque; via search excerpt, page no longer served)
  - https://www.agi-automation.com/design-guidelines-for-pneumatic-gripper/ (Fg = w g S / (μ nf), S = 3–4, higher when fast; formula via search excerpt)
  - https://www.mmscience.eu/journal/issues/december-2021/articles/analysis-of-increasing-the-friction-force-of-the-robot-jaws-by-adding-3d-printed-flexible-inserts/download (Suder et al., MM Science Journal 2021, Tables 3–4)
  - https://arxiv.org/pdf/2301.08431 (Hartisch & Haninger, compliant fin-ray gripper, sec. 3)
  - https://www.eng.yale.edu/grablab/pubs/ma_icra2013.pdf (Ma & Dollar, open-source underactuated hand; via search excerpt)
  - https://la.disneyresearch.com/wp-content/uploads/A-Passively-Safe-and-Gravity-Counterbalanced-Anthropomorphic-Robot-Arm-Paper.pdf (actuators grounded at the base, counterbalance; via search excerpt)
related: [hobby-servos, small-dc-motors, stepper-motors, belts-and-pulleys, linkages, flexures-and-living-hinges, mass-properties-and-measurement, beam-and-plate-stiffness, stability-and-tipping, gears]
updated: 2026-09-23
---

# Arm and gripper sizing

A small arm is a chain of levers whose shoulder carries everything outboard of
it. Size it from the tip back: payload and gripper first, then each joint's
torque with every downstream mass at full horizontal reach, then the
actuator with a margin to its **stall** torque. Read this before choosing
servos or link lengths for any arm, boom, claw or gripper.
[[counterweights-and-gravity-balance]] holds the ways to take the gravity
load off the actuators.

## Static joint torque at full reach

Worst case is the arm stretched horizontal: every `cos θ` is 1. For joint `i`,
sum over every mass outboard of it — links at their centre of mass, the
actuators they carry, the gripper and the payload:

```text
τ_i = g · Σ_j m_j · d_ij · cos θ_j        d_ij = horizontal distance joint i → mass j
link of length L, uniform:  d = L / 2 from its own joint
actuator at the next joint: d = full link length (it is a point mass there)
```

Worked illustration (numbers invented to show scale): shoulder link 120 mm,
30 g; a 9 g micro servo at the elbow; forearm 100 mm, 20 g; gripper with its
servo 25 g and a 20 g payload at 220 mm.

```text
τ_shoulder = 9.81 · (0.030·0.060 + 0.009·0.120 + 0.020·0.170 + 0.045·0.220)
           = 0.159 N·m = 1.62 kg·cm
```

That is 90 % of an SG90's 1.8 kg·cm stall ([[hobby-servos#common-models-towerpro-figures]]):
it would lift once, then overheat or strip. An MG996R (9.4 kg·cm) runs it at
17 %. The payload and the gripper at the tip are 61 % of the total: **tip
mass is paid for twice** — once in torque, once in the heavier actuators it
forces on every joint inboard.

## Dynamic term

Accelerating the arm adds `τ = I α` about the joint, with `I` about the joint
axis ([[mass-properties-and-measurement#inertia-about-the-centre-of-mass-density-1]]
gives it about the CoM; add `m d²`):

```text
I_joint = Σ (I_cm,j + m_j d_j²)     uniform rod about its end: m L² / 3
α       = 4 Δθ / t²                  triangular speed profile: accelerate half, brake half
```

In the illustration, `I ≈ 3.0e-3 kg·m²`. A 60° move in 0.3 s gives
α = 46.5 rad/s² and `I α ≈ 0.14 N·m` — as large as the gravity term. A
hobby servo drives at full speed to its target, so its real α is higher
still. Either slow the command profile in firmware (ramp the setpoint) or
budget the sum.

## Actuator margin: size against stall

- Hobby servos are rated at **stall**. Stall is the torque at which they stop
  and draw maximum current, not a working point.
- For servos rated only in stall torque, ROBOTIS estimates continuous torque
  at about **20 % of stall**. The FIRGELLI guide says to double or triple the
  static estimate, more if things move fast or stop often.
- Rule here: **static holding torque ≤ 20 % of stall, static + dynamic peak ≤
  50 % of stall** at the lowest supply voltage the battery reaches. An arm
  that holds a pose all day is a continuous load; one that moves and rests
  on a stop is not.
- A DC gearmotor or stepper follows the same logic against its rated
  (continuous) torque, not stall or holding torque
  ([[small-dc-motors#sizing-rules]], [[stepper-motors]]).
- Stall current sizes the supply for every joint that can stall at once
  ([[hobby-servos#power-the-servo-is-the-biggest-load]]).

## Taking torque off the shoulder

In order of effectiveness:

1. **Lighten the tip.** Shorter reach, lighter gripper, a micro servo at the
   wrist. Every gram there counts at full reach.
2. **Move actuators toward the base.** Put the elbow motor at the shoulder
   and drive the elbow through a parallelogram link, a belt or a cable
   ([[linkages#four-bar]], [[belts-and-pulleys]]). The elbow motor's mass then
   sits at d ≈ 0 for the shoulder. Arms that ground all actuators at the base
   also free room there for counterbalance springs or masses.
3. **Counterbalance** the static load with a counterweight or a
   zero-free-length spring ([[counterweights-and-gravity-balance]]). The motor
   then supplies only I α and friction; the counterweight adds inertia, the
   spring does not.
4. **Gear down** the joint: output torque × ratio × efficiency
   ([[energy-drive#ratio-budget]]). A self-locking worm holds a pose with no
   current but cannot be back-driven ([[worm-gear-efficiency]]).

Support the load beside the actuator, not through it: a micro servo's output
shaft is supported over a few millimetres inside its case. Put the joint on a
printed pin or a bearing on the far side and let the servo only turn it
([[hobby-servos#horns-and-splines]], [[shafts-and-bearings]]).

## Gripper types

| type | how | force | choose when |
|---|---|---|---|
| **pivoting claw** | one servo turns one or two jaws on pins, often through meshing gear sectors | varies with jaw angle and contact radius: `F = τ / r_contact` | toys and demos; pads meet the object at an angle |
| **parallel jaw, rack-and-pinion** | a pinion drives two racks in opposite directions | one pinion, two jaws: `F_jaw = τ / (2 r_pitch)`, constant over stroke | objects of varying width; flat pads stay parallel |
| **parallel jaw, linkage** | a four-bar parallelogram per finger keeps the pad parallel while it swings | changes with linkage angle; highest near toggle | compact, no sliding rack; pads move on an arc |
| **lead-screw jaw** | screw drives a nut carrying the jaws | high force, self-locking, slow ([[lead-screws]]) | holds without power |
| **underactuated / tendon fingers** | one tendon or link drives several joints; springs or flexures return them; fingers wrap until each link touches | adaptive, low | irregular objects; one motor for many joints |
| **fin-ray compliant finger** | a flexible triangular finger with cross ribs bends *toward* the pushing object and wraps it | low, adaptive | fragile or irregular objects; soft printed material |

Notes:

- A rack-and-pinion or linkage jaw is a slide or a four-bar and owes a
  `clear` and a `blocked` condition like any joint
  ([[joints#the-two-conditions-every-joint-owes]]). Put a hard stop at the
  open and closed ends so a servo commanded past the object stalls against
  the object, not against its own gears.
- The fin-ray work above printed the ribs as slicer infill lines in a solid
  finger with one wall and no top or bottom skin. This repository's
  deliverable is STEP, which carries no slicer settings, so **model the ribs
  as geometry** in source. Their study used PLA+ and PETG and found the
  friction of both **insufficient for a stable grasp**: add a soft pad.
- Underactuated printed fingers (Yale OpenHand) use cast elastomer flexure
  joints because printed FDM joints lacked robustness; see
  [[flexures-and-living-hinges]] for printed alternatives.

## Grip force from friction

A friction grip holds the object by `μ` times the squeeze. With `n` contact
faces (two for a two-jaw gripper), mass `m`, the largest acceleration of the
arm `a`, and a safety factor `S`:

```text
F_jaw ≥ m · (g + a) · S / (n · μ)
```

The automation guideline takes `S` = 3–4 for normal moves and more for fast
ones. A form-fit grip — a V-notch, a pocket or a lip around the object —
does not depend on μ and is always more secure; use one whenever the object
shape is known.

Measured friction (Suder et al., steel-cased motor pulled out of a two-jaw
gripper, μ from `F_pull = 2 · F_grip · μ`):

| jaw surface | μ at 15 N | 35 N | 50 N grip |
|---|---|---|---|
| original rigid jaws | 0.21 | 0.17 | 0.15 |
| TPU 30D inserts, knurled | 0.72 | 0.69 | 0.79 |
| TPU 30D inserts, smooth | 0.61 | 0.46 | 0.60 |
| TPE 88 inserts, knurled | 0.51 | 0.35 | 0.31 |
| TPE 88 inserts, smooth | 0.39 | 0.34 | 0.25 |

Rules from it: soft printed pads roughly triple μ over hard plastic; a
knurled or ribbed pad beat a smooth one in every case; μ moves with grip
force, so design on the lowest value in the range. Make pads replaceable
inserts — they wear — and seat them in a pocket with a lip so they cannot
peel ([[fdm-multi-material-design]] for a printed-in-place soft layer).

## Backlash and sag at the end effector

Angular play at each joint becomes a position error at the tip, multiplied by
the distance from that joint to the tip:

```text
δ_tip ≈ Σ_i θ_play,i [rad] · R_i  +  Σ link deflections
```

With an illustrative 0.5° of play at the shoulder and 220 mm reach,
δ = 0.0087 × 220 = 1.9 mm — before the elbow and wrist add theirs. Hobby
servo gear trains and printed gear stages both have play
([[gears#printed-tooth-choices]]); measure the servo you have. Gravity keeps
a horizontal arm loaded to one side of its backlash; an arm that passes
through vertical, or a counterbalanced one, crosses its backlash and jumps.

Link bending adds to it: a printed link is a cantilever,
`δ = F L³ / (3 E I)` for a tip load ([[beam-and-plate-stiffness#beam-deflection-the-four-cases]]).
Close the section (a box or tube) so the link does not also twist under an
off-axis grip.

## Arm on a base

A reaching arm moves the combined centre of mass out over the base edge.
Check tipping with the arm at full reach, loaded, in the direction of the
narrowest base ([[stability-and-tipping#support-polygon-and-centre-of-mass]]).

## Checks

```python
g = 9.81
tau_static = g * sum(m * d for m, d in masses_outboard_of_shoulder)   # full horizontal reach
I_joint = sum(I_cm + m * d**2 for m, d, I_cm in bodies_outboard)
alpha = 4 * move_angle / move_time**2
tau_peak = tau_static + I_joint * alpha
assert tau_static <= 0.20 * stall_torque_at_min_voltage, "holding load above 20 % of stall"
assert tau_peak <= 0.5 * stall_torque_at_min_voltage, "peak joint torque above half of stall"
F_needed = payload * (g + a_max) * S / (n_faces * mu_min)
assert F_jaw_min >= F_needed, f"grip {F_jaw_min:.1f} N below the {F_needed:.1f} N friction needs"
assert sum(play * R for play, R in joints_play_and_reach) <= tip_tolerance, "tip backlash over budget"
```

Open items a CAD gate never closes: real μ of the chosen pad on the real
object, servo play, and whether the arm resonates at its speed
([[noise-and-vibration]]). Record them.
