---
title: Launchers and projectile toys
tags: [launcher, catapult, trebuchet, projectile, rubber-band, trigger, kinetic-energy, toy, safety]
aliases: [mangonel, onager, torsion catapult, slingshot, rubber band gun, rubber band shooter, spring popper, pop-up launcher, stomp rocket, air rocket, foam dart, flick launcher, disc launcher, top launcher, sear, kinetic energy density, ked, improvised projectile, counterweight trebuchet, sling release pin, en 71-1 4.17, astm f963 4.21, projectile range]
sources:
  - https://law.resource.org/pub/eu/toys/en.71.1.2014.html (EN 71-1:2011+A3 4.17, superseded: rigid tip radius >= 2 mm, suction-cup projectile >= 57 mm, darts >= 3 cm2, 0.08 J rigid / 0.5 J resilient, arrows 0.16 J/cm2; 7.7.2 warning above 0.08 J; 8.4.2.3 60 N pull on protective parts)
  - https://stc.group/getfile/index/action/images/slug/2018-21-en71-1-2018-version (EN 71-1:2014+A1:2018 rewrote 4.17: leading parts replace tip radius, kinetic energy density replaces kinetic energy, catapults and elastic bands added in 4.17.4, improvised projectiles, 8.42 range test)
  - https://stc.group/getfile/index/action/images/name/5f582c9f13d91.pdf (STC table of ISO 8124-1:2019, EN 71-1:2014+A1:2018, ASTM F963-17: above 0.08 J a resilient leading part, warning and <= 2500 J/m2; mechanism unable to launch improvised projectiles; stored-energy projectiles not small parts (ISO, ASTM); corners 0.25 mm (ISO); ground-based toys exempt (ISO))
  - https://www.marktpuls.ch/artikel/permalink/382139 (SGS toy update: leading part checked with a 4 mm gauge; range under 300 mm excluded; balls, darts and discs are projectiles)
  - https://www.intertek.com.cn/Readingen_itemid_6742.html (ASTM F963-17 4.21.2.3: above 0.08 J by 8.14.5, KED <= 2500 J/m2 by 8.14.6)
  - https://arxiv.org/pdf/1604.00049 (latex bands: energy from the contraction curve, force falls with log hold time, 10-20 % force loss after a few hundred shots, force proportional to absolute temperature, steep curve sections add force not energy)
  - https://en.wikipedia.org/wiki/Effective_mass_(spring%E2%80%93mass_system) (uniform spring effective mass m/3)
  - https://en.wikipedia.org/wiki/Center_of_percussion (no pivot reaction; 2L/3 for a uniform rod)
  - https://en.wikipedia.org/wiki/Projectile_motion (R = v^2 sin 2theta / g, 45 deg on level ground)
  - https://arxiv.org/html/2608.09157 (optimum angle from height H = arctan(v/sqrt(v^2+2gH)), R = (v/g) sqrt(v^2+2gH))
  - https://en.wikipedia.org/wiki/Drag_coefficient (sphere C_d 0.47, drag equation)
  - https://arxiv.org/html/2502.19442v2 (measured trebuchet: 53.9 kg on 0.717 kg, arms 97.5/25 cm, sling 87 cm, about 70 % efficient, 11 % with a 68.5 g ball, ideal 73 %, optimized 91 %, climb 34-40 deg)
  - https://www.comsol.com/blogs/what-is-the-physics-behind-a-counterweight-trebuchet (M/m = 100 model, best release about 38 deg, +/-5 deg costs little, range very sensitive to sling length)
  - https://real-world-physics-problems.com/trebuchet-physics.html (Siano: counterweight 100 x payload, long arm 3.75 x short arm, sling = long arm; finger angle sets release angle)
  - https://additive-mfg.me.wisc.edu/?p=122 (printed trebuchet: arm ratios 3:1-5:1, swappable release fingers 0-25 deg in 5 deg steps)
  - https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir73-156.pdf (NBSIR 73-156 Table 1a: child push/pull on a lever, ages 2-6, averages and 5th percentiles in N)
related: [toy-safety-constraints, energy-drive, springs, latches-detents-and-ratchets, snap-fit-design, handheld-ergonomics, layer-anisotropy, shafts-and-bearings, creep-and-stress-relaxation, printed-fatigue, flexure-materials-and-snap-strain, beam-and-plate-stiffness, counterweights-and-gravity-balance, hinges-and-pin-joints, fdm-design-rule-tables]
updated: 2026-10-10
---

# Launchers and projectile toys

A launcher stores energy `E`, releases it on a trigger, and hands a fraction
`η` of it to the projectile as `KE = η·E`; the toy standards limit `KE` and
`KE` per contact area. General toy rules: [[toy-safety-constraints]].

## Stored energy: what each store gives back

- **Coil spring**, cocked to compression `x_c`, still compressed `x_e` at the
  end of the stroke: `E = ½ k (x_c² − x_e²)`. Preload left at the end of the
  stroke never reaches the projectile ([[springs#helical-compression-spring]]).
- **Rubber band**: `E` is the area under the force–draw curve taken while the
  band *contracts*, at the toy's hold time; the loading curve is distinctly
  higher and over-predicts speed. Held force falls with the log of hold time,
  latex loses 10–20 % after a few hundred shots, force scales with absolute
  temperature, and the steep end of the curve adds force but little energy.
- **Torsion skein** (mangonel, onager): `E = ∫ T dθ`, torque falling as it
  unwinds ([[energy-drive#sources]]). **Counterweight**: `E = M g H`.
- **Printed flexure** (bow, leaf) at peak stress `σ`: `U = σ² V / (18 E)`
  prismatic and tip-loaded, `σ² V / (6 E)` tapered to constant stress. PLA at
  its 10⁴-cycle stress of about 14 MPa ([[printed-fatigue#a-design-curve-for-printed-pla]])
  stores 3–9 mJ/cm³: a printed bow holds tens of millijoules, a band or a
  steel spring far more.

## Conversion: whatever moves and does not fly is lost

Every part still moving when the projectile leaves keeps energy the
projectile never gets. Refer each to the projectile's speed:

```text
m_eff = I_arm / r_p² + m_cup + m_piston + m_spring / 3   (+ the band's moving mass)
η_max = m_p / (m_p + m_eff)                                no friction, no lift
KE    = η_fric · η_max · E − m_p g Δh_p − M_arm g Δh_arm   Δh = rise in the stroke
```

`r_p`: projectile radius from the pivot; `m_spring/3`: a uniform spring's
effective mass. Worked: a solid PLA arm 120 × 12 × 6 mm (10.7 g, `I = mL²/3`)
and a 3 g cup throwing a 2.7 g ball from 110 mm: `m_eff` = 4.2 + 3 g,
`η_max` = 0.27. Half the arm inertia and a 1 g cup: 0.46; a popper's 3 g
piston and 1.5 g spring: 0.44.

- **A trebuchet beats a rigid arm**: the sling's whip leaves beam and
  counterweight nearly at rest at release. A measured tabletop machine
  delivered about 70 % of the drop energy (73 % ideal, 91 % optimized), but
  11 % with a ball ten times lighter: the beam kept the rest.
- **`KE` rises with projectile mass** at fixed `E`, so the worst case for the
  limits below is the heaviest object the launcher will hold.

## Speed and range

```text
v     = sqrt(2 KE / m_p)
R     = v² sin(2θ) / g                    level ground; best θ = 45°
θ_opt = atan(v / sqrt(v² + 2 g h))        released h above the landing
R_max = (v / g) · sqrt(v² + 2 g h)
v_t   = sqrt(2 m_p g / (ρ C_d A))         terminal speed: drag equals weight
```

Drag lowers the best angle and the range; near `v_t` the formulas are only
an upper bound. A 40 mm, 2.7 g table-tennis ball (`C_d` ≈ 0.47) has `v_t` ≈
8.6 m/s, about what 0.08 J allows it: a light-ball toy is drag-limited.
Trebuchets throw best at 34–40° of climb, ±5° costing little: tune in test.

## Trebuchet proportions

- **Counterweight : projectile** about 100 : 1 (Siano); a measured 75 : 1 ran
  at 70 %. Far lighter projectiles leave the energy in the beam.
- **Long arm : short arm** 3.75 (Siano), 3–5 on printed and tabletop machines.
- **Sling** about the long arm (0.9–1.0 ×); range is very sensitive to it.
- **Release pin** swappable, 0–25° in 5° steps, smooth and round: pin angle
  and sling length set the release angle together. A hinged counterweight
  falls straight down instead of swinging out with the beam; fill it densely
  ([[counterweights-and-gravity-balance#ballast-pockets-and-dense-fills]]).

## Projectile limits in the toy standards

EN 71-1:2014+A1:2018 rewrote clause 4.17 to match ASTM F963-17 (4.21) and
ISO 8124-1; the 0.08 J / 0.5 J caps of EN 71-1:2011 are superseded
([[toy-safety-constraints#other-numeric-limits-in-en-71-1]]).

- **Above 0.08 J** a stored-energy projectile needs a resilient leading part,
  a "do not aim at eyes or face" warning, and a kinetic energy per contact
  area (KED) of at most **2500 J/m²** (older texts: 0.16 J/cm² for arrows).
- **Catapults count**: EN 71-1 4.17.4 puts toy catapults, bands able to hold
  a projectile, and mechanisms storing energy only while held under these
  rules. Design stomp, squeeze and flick launchers to them too.
- **Improvised projectiles** (pencils, pebbles, nails): EN 71-1 and ASTM F963
  require the discharge mechanism to be unable to launch them.
- **Not a small part**: under ASTM F963-17 and ISO 8124-1 a stored-energy
  projectile must not fit the small-parts cylinder before or after abuse
  tests ([[toy-safety-constraints#small-parts-the-choke-test]]).
- **Leading parts** (a tip, edge or protrusion that could meet an eye) are
  judged with a 4 mm-diameter gauge; corners next to a rigid leading edge are
  rounded (ISO: 0.25 mm). The old 2 mm tip radius is a safe floor.
- **Suction-cup projectiles** ≥ 57 mm long; hand-thrown **darts** ≥ 3 cm² of
  resilient contact; caps survive a 60 N pull.
- **Out of scope**: a maximum range under 300 mm (EN 71-1), and ground-based
  toys launched along a track or onto a surface, such as spinning tops (ISO).
  A pop-up figure that flies 300 mm is a projectile; a rotor in free flight
  needs a ring, flexible blades or a clutch.

```text
v_max at 0.08 J = sqrt(0.16 / m_p)    1 g → 12.6 m/s, 2.7 g → 7.7, 5 g → 5.7, 10 g → 4.0
A_min           = KE / 2500 J/m²      0.08 J → 32 mm², 0.2 J → 80 mm², 0.5 J → 200 mm²
pop-up < 300 mm: (v/g)·sqrt(v² + 2 g h) < 0.3 m    → v below about 1.7 m/s
```

## Only its own projectile: geometry, not a label

- **End the cocking stroke on a hard stop** (a fixed band notch, a spring
  compressed to a fixed length): no one's strength sets `E`, so `E` is an
  assertable parameter.
- **Let the projectile carry the interface**: a rocket over its launch tube,
  a dart's hollow base on a spigot, a ball in a ring sized to it. A pencil or
  pebble finds nothing to push it; a barrel or flat cup launches anything.
- **Bound the worst case**: `KE ≤ E · m / (m + m_eff)` tends to `E` for heavy
  objects, so keep that at or under 0.08 J, or `E ≤ 0.08 J` outright.

## Triggers and sears

A sear holds the full load while cocked and must let go under a finger:

```text
F_trigger = F_hold · tan(α + φ) · a / b        φ = atan μ
```

`α` is the sear-face angle that resists release (positive pulls the sear
deeper under load), `a` the contact's lever arm about the sear pivot, `b` the
finger's.

- **Hold at μ = 0**: make `α` a few degrees positive; a face angled the other
  way self-releases once `tan|α| > μ` ([[snap-fit-design#mating-and-separating-force]]).
  At the top of the μ range the trigger force stays at the low end of the
  single-finger range in [[handheld-ergonomics#push-buttons]]; use `a/b < 1`.
- **Engagement** `e ≥ 2 × positional tolerance + edge round + deflection`:
  with ±0.25 mm or more per part ([[fdm-design-rule-tables]]) and a 0.2 mm
  edge, 1 mm or more. A shallower sear slips off a layer step.
- **Reset** onto a hard stop by a spring, no beam left bent while engaged
  ([[latches-detents-and-ratchets#latches]]); a safety catch blocks the
  trigger, and cocking keeps the hand out of the arm's path.

## Arm stops absorb what the projectile did not take

- The stop takes roughly `E_stop = (1 − η_max) · E`, most of a catapult's
  store, at a peak force ≈ `2 E_stop / δ` for a stop that gives `δ`: 0.2 J is
  2000 N on a hard stop giving 0.2 mm, 133 N on a TPU bumper giving 3 mm.
- Put the stop at the arm's **centre of percussion**, `r_cp = I_pivot /
  (M r_cm)` (2L/3 for a uniform arm): an impact there sends no shock into the
  pivot. Meet it with a flat face across the arm's width, never an edge.

## Bands, springs and flexures

- **Buy the spring** for anything fired often; a printed PLA spring creeps
  ([[flexure-materials-and-snap-strain#flexures-and-printed-springs]]).
  **Rest uncocked**: a flexure or sear held bent creeps and a held band loses
  force ([[creep-and-stress-relaxation#design-rules]]).
- **Band anchors** are moulded in with a filleted root ([[energy-drive#sources]]).
  Round every edge the band crosses: latex tears from a nick, and a sharp
  edge or layer step makes one. A post standing on the bed is smooth where
  the band wraps but bends across its layers: keep it short and thick, with
  a lip that stops the band walking off.

## Cocking force a child can give

Best one-off lever efforts (NBSIR 73-156), age 4: averages 117–145 N push,
160–180 N pull; 5th percentiles 56–71 N push, 85–107 N pull; age 3 push
averages 74–81 N. Whole-body ceilings, not play forces. A linear spring peaks
at `F = 2E / s`: 0.08 J over 40 mm is 4 N, so energy binds before strength.

## Printed strength: arm, pivot, catch

- **Print the arm lying in its swing plane**, pivot bore vertical: bending
  runs along the strands, shear stays out of the layer welds, the bore prints
  round ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]).
- **Bending** `σ = 6 M / (b h²)` at the hub (`M ≈ F_spring · r_spring`) and at
  the stop. For N shots of PLA allow `0.1 · UTS · (2e6 / N)^(1/5.5)`, about
  14 MPa at 10⁴, over the bore's stress concentration
  ([[beam-and-plate-stiffness#safety-factors-for-printed-plastic]]).
- **Pivot**: a printed pin lying flat for a short span, steel where the stop
  shock loads it ([[shafts-and-bearings#printed-shaft-or-bought-rod]]). Put
  the catch near the spring attachment so the cocked arm carries little bending.

## Checks

```python
import math
E = 0.5 * K_SPRING * (X_COCK**2 - X_END**2)                      # J
M_EFF = I_ARM / R_P**2 + M_CUP + M_PISTON + M_SPRING / 3          # kg
KE = ETA_FRIC * M_P / (M_P + M_EFF) * E
KE_WORST = E * M_HEAVY / (M_HEAVY + M_EFF)   # heaviest object the launcher holds
assert KE_WORST <= 0.08 or IMPROVISED_BLOCKED, "improvised projectile over 0.08 J"
assert KE <= 0.08 or (TIP_RESILIENT and KE / A_TIP <= 2500), "KE / KED over the limit"
assert PROJ_MIN_DIM > 31.7, "stored-energy projectile fits the small-parts cylinder"
f_trig = F_HOLD * math.tan(math.radians(SEAR_ALPHA_DEG) + math.atan(MU_MAX)) * SEAR_A / SEAR_B
assert SEAR_ALPHA_DEG > 0 and f_trig <= F_FINGER_MAX, "sear slips or trigger too stiff"
assert SEAR_ENGAGE >= 2 * POS_TOL + EDGE_ROUND + SEAR_DEFL, "sear engagement too shallow"
sigma = 6 * M_ARM_ROOT / (ARM_B * ARM_H**2)                       # N·mm, mm → MPa
assert sigma * SCF <= 0.1 * UTS_XY * (2e6 / N_SHOTS) ** (1 / 5.5), "arm fails in fatigue"
assert abs(R_STOP - I_PIVOT / (M_ARM * R_CM)) <= 0.15 * R_STOP and HAS_BUMPER
```

Open items no geometry gate closes: the band's real curve and ageing,
friction, the KED contact area as the standard measures it, abuse survival.
Measure speed on a print; spec: [[toy-safety-constraints#what-to-write-in-the-spec]].
