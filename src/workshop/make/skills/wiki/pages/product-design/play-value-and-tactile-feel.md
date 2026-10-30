---
title: Play value and tactile feel
tags: [play-value, tactile, fidget, click, detent, haptic, weight, texture, toy]
aliases: [fidget toy, fidget cube, clicker, clicky, satisfying click, snap ratio, click ratio, tactile ratio, force travel curve, force-stroke curve, haptic feedback, tactile feedback, play pattern, play type, replay value, toy feel, perceived quality, heft, desk toy, worry stone, squish, squishy, magnetic slider, warm to the touch, thermal effusivity]
sources:
  - "https://cdn.sparkfun.com/assets/6/b/7/9/b/MX2A_BROWN-Datasheet-EN_US.pdf (Cherry MX2A Brown: 45 cN actuation, 2 mm pre-travel, 4 mm travel, 30 cN initial, 55 cN pressure point, 80 cN final)"
  - "https://cdn.sparkfun.com/assets/f/4/4/1/4/MX2A_BLUE-Datasheet-EN_US.pdf (Cherry MX2A Blue, tactile and clicky: 50 cN actuation, 60 cN pressure point, 2.2 mm pre-travel, 4 mm travel)"
  - "https://atta.szlcsc.com/upload/public/pdf/source/20210810/E9D668B3CD873EF2E1D697CD6499F0D8.pdf (ALPS tact switch specification: click ratio = click force / operating force, 53 +/- 10 %; 3.8 N, 0.72 mm, return force 1 N min; force within +/-30 % after 200,000 cycles)"
  - "https://nmbtc.com/wp-content/uploads/parts/documents/STV%20data%20sheet.pdf (NMB STV tactile switch: 2.5 N, 0.21 mm, click ratio at least 40 %, 1,000,000 operations)"
  - "https://www.lcsc.com/blog/tactile-vs-nontactile-membrane-switch/ (metal dome snap ratio window 40-65 %, vague below 35 %, unreliable recovery above 65 %; 180-400 gf; 0.1-0.5 mm travel; 10^6 cycles)"
  - "https://deskthority.net/wiki/Tactile_force (tactile force overcomes the peak; actuation placed just after the peak)"
  - "https://engineering.purdue.edu/~hongtan/pubs/PDFfiles/J38_Tan_etal_ToH2008.pdf (torque-ripple detection 14.34 N mm at 0.006 cycle/deg down to 0.05 N mm at 0.357 cycle/deg on a 30 N mm offset; switch feel colours the perceived quality of the whole car; a sudden force drop made virtual buttons crisper)"
  - "https://www.cs.ubc.ca/labs/spin/sites/default/files/local_pdfs/Designing_for_Feel_Contrasts_between_Human_and_Automated_Parametric_Capture_of_Knob_Physics.pdf (subtle detents confused with uneven friction; reference knobs had 12 or more detents per turn)"
  - "https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf (12, 18 or 24 detents; detent torque 30-90 gf cm; 30,000 cycles)"
  - "https://www.playscotland.org/play-types/ (Hughes' 16 play types, 1996; object, exploratory, mastery, creative play)"
  - "https://www.museumofplay.org/app/uploads/2022/01/6-2-article-elements-of-play.pdf (Eberle 2014: anticipation, surprise, pleasure, understanding, strength, poise; surprise must first be prepared for; open-ended play lasts)"
  - "https://joanganzcooneycenter.org/2011/10/12/inventing-playful-invention-four-steps-to-designing-toys-for-creative-play/ (play patterns modelling, collecting, storytelling, invention, battling, nurture; one- or two-pattern toys are limited)"
  - "https://legohouse.com/de-de/schools/learning-through-play (joy, meaning, active engagement, iteration, social interaction)"
  - "https://toolsandtoys.net/fidget-cube-kickstarter/ (Fidget Cube faces: click with 3 clicky and 2 silent buttons, glide, flip, breathe, roll, spin)"
  - "https://ktvz.com/health/cnn-health/2021/12/29/kids-can-benefit-from-fidget-toys-to-fulfill-their-primal-need-to-move-and-feel/ (children squeeze when angry, click or tap when bored; classrooms accept quiet fidgets)"
  - "https://www.insidehook.com/design/why-dont-we-take-lightweight-products-seriously (container 15 % lighter valued the same, 30 % lighter valued less; value tracks expected weight; added dead weight in products)"
  - "https://ora.ox.ac.uk/objects/uuid:b4d28cb9-e7e2-45b2-b90f-06c7b22dcbae (same yoghurt from a heavier bowl rated denser, pricier, better liked)"
  - "https://brucecharlesdesigns.com/products/robertson-stainless-slider (steel magnetic slider 31 x 49 x 11 mm, 2.1 oz; six 6 x 3.5 mm N52 magnets 0.8-1.2 mm under the face)"
  - "https://en.wikipedia.org/wiki/Quarter_(United_States_coin) (5.67 g, 24.26 mm, 1.75 mm)"
  - "https://en.wikipedia.org/wiki/Thermal_effusivity (e = sqrt(k rho c); contact temperature weighted by effusivity; skin 1.0, pine 0.36-0.66, PVC 0.6, stainless 7.23, aluminium 23.7 kJ/m2 K s^0.5)"
  - "https://research.tudelft.nl/en/publications/surface-roughness-of-3d-printed-materials-comparing-physical-meas (Ra and Rq do not predict how rough an FDM surface feels)"
  - "https://pmc.ncbi.nlm.nih.gov/articles/PMC6926983/ (roughness measured along the layers is near zero; across them it peaks at shallow build angles)"
  - "https://roymech.org/Useful_Tables/Tribology/Bearing-Friction.html (ball bearing f = 0.0015, M = F f d/2; start-up up to twice; seal friction extra)"
related: [handheld-ergonomics, buttons-knobs-and-front-panels, latches-detents-and-ratchets, snap-fit-design, flexure-materials-and-snap-strain, printed-fatigue, flexures-and-living-hinges, counterweights-and-gravity-balance, magnets-and-strap-slots, fdm-surface-finish, form-and-finish-heuristics, product-aesthetics, toy-safety-constraints, noise-and-vibration, linear-guides-and-slides, shafts-and-bearings, swivels-and-turntables, spinning-toys-and-flywheels]
updated: 2026-10-10
---

# Play value and tactile feel

A toy or fidget is judged in the hand first: does the action land with a clear
click, stop where it should, weigh what it looks like, and invite the next go?
Finger sizes: [[handheld-ergonomics]]; switches and knobs: [[buttons-knobs-and-front-panels]].

## Play patterns decide what the object must do

Name the pattern before the form. Hughes' 16 play types include object,
exploratory, mastery and creative play; toy designers name modelling, collecting,
storytelling, invention, battling and nurture. A one- or two-pattern toy is limited.

| pattern | the object must give | printed means |
|---|---|---|
| manipulative | actions with distinct feel and sound | detents, clicks, spin, slide |
| mastery | a goal, a visible success state, graded difficulty | balance, catch, a puzzle that locks when solved |
| construction | joints made and unmade many times | snaps and pegs in repeated-use strain ([[snap-fit-design]]) |
| pretend | a character or tool that reads at a glance | silhouette, colour ([[product-aesthetics]]) |
| collect | a series on one shared system | one interface, many covers |
| compete | two sides and a fair rule | symmetric parts, a stop that decides |
| nurture | something to care for and adjust | poseable joints, accessories |
| surprise / reveal | a hidden state an action changes | a door, a flip ([[volvelle-two-state-display]]) |

## What makes play repeatable

Eberle's play runs anticipation, surprise, pleasure, understanding, strength,
poise; the LEGO Foundation lists joy, meaning, engagement, iteration, social play.

- **More than one state.** A part that only moves is examined once; one with
  positions, a lock and a release is played with.
- **A reveal you can anticipate still works.** Peekaboo repeats because surprise
  is a reward "we must first be prepared to appreciate": build the timing, make
  the release crisp. **Feedback on success**: a click when a part seats, a stop
  when a puzzle locks. **Open-ended outlasts scripted.**
- **A quiet mode.** Children click when bored and squeeze when angry; classrooms
  accept quiet fidgets. The Fidget Cube has 3 clicky and 2 silent buttons.

## Fidget actions and the mechanism behind each

| action | mechanism | note |
|---|---|---|
| click | snap dome, tact switch, or a cantilever over a crest | snap ratio 40-65 % |
| flip | over-centre toggle ([[straight-line-and-toggle-linkages#toggle-mechanisms]]) | slow is quiet, fast is loud |
| spin / roll | rotor on a bearing; captive ball; detented wheels like a combination lock | bearing, not bushing |
| glide | joystick: ball joint and centring spring | hard stop at the rim |
| slide | carriage on a rail, or magnets on two plates | detent at each end |
| breathe / rub | worry-stone thumb dish | no layer step under the thumb |
| squeeze | lattice, hollow TPU bulb, bought foam | geometry, not solid TPU |
| pop | bistable dome ([[flexures-and-living-hinges#bistable-mechanisms]]) | peak force reachable |

## The force-travel curve of a good click

A crisp click rises to a peak and drops suddenly. Its snap (click) ratio is
`SR = (F_peak - F_min) / F_peak`, F_min the lowest force after the peak.

| element | force | travel | snap ratio |
|---|---|---|---|
| Cherry MX2A Brown / Blue (clicky) | 45 / 50 cN actuation, 55 / 60 cN peak | 2 / 2.2 mm of 4 mm | — |
| ALPS 6 mm tact switch | 3.8 N | 0.72 mm | 53 ± 10 % |
| NMB STV tact switch | 2.5 N | 0.21 mm | ≥ 40 % |
| metal domes | 180-400 gf | 0.1-0.5 mm | 40-65 % window |

- **Crispness is the ratio, not the force.** The dome window is 40-65 %: below
  35 % reads as a vague bump, above 65 % may not spring back.
- **The event sits just after the peak.** Keyswitches actuate as the force falls;
  a printed click must coincide with the state change it reports.
- **Force band.** Keys pressed thousands of times take 0.45-0.8 N, tact switches
  1-5 N ([[buttons-knobs-and-front-panels#what-a-tactile-switch-gives-you]]),
  panel push buttons 2.8-11 N ([[handheld-ergonomics#push-buttons]]). A fidget
  clicker at 0.5-3 N is a design choice; return briskly (ALPS: ≥ 1 N).
- **Stop right after the click,** on a rigid housing face; spongy over-travel
  reads as cheap. A sudden force drop made virtual buttons crisper, and switch
  feel colours the perceived quality of the whole product.

## Rotary detents: count, depth and friction

- **Count and torque.** Small encoders have 12, 18 or 24 detents per turn at
  30-90 gf·cm. Use 12-24 for a dial turned for its own sake, one notch per state
  for a selector ([[latches-detents-and-ratchets#indexing-detents]]).
- **Fine spacing is felt at tiny amplitude.** Torque-ripple thresholds fell from
  14 N·mm at about 170° per cycle to 0.05 N·mm at 2.8°, on a 30 N·mm base. Layer
  ridges, a lobed bushing or gear teeth are felt as grit even when small; a
  coarse detent (45° and up) must be deep to be felt.
- **A weak detent reads as dirt.** People confuse subtle detents with uneven
  friction: keep the detent well above the friction ripple; end with a hard stop.

## A printed click: flanks, crest and sound

Release force is in [[latches-detents-and-ratchets#detent-holding-force]]; the
flank angle decides whether a printed bump clicks at all:

```text
phi = atan(mu); beta = flank angle from the travel direction
beta <= phi           follower stays where left: no centring, no click
phi < beta < 90-phi   two-way detent: snaps in, pushes out at F_s * tan(beta + phi)
beta >= 90 - phi      locks: a latch, not a detent
s_rev = (r_nose + r_crest) * (sin(alpha) + sin(beta))    travel over which the push reverses
```

Plastic pairs run μ ≈ 0.3-0.8 ([[snap-fit-design#mating-and-separating-force]]).
At μ = 0.5, φ = 27°: a flank centres above 27° and locks at 63°; 45° sits between.
A one-way click takes a 30-45° lead and a steep return the follower falls off.

**The crest sets the crispness.** A 3 mm ball over 45° flanks reverses over
2.1 mm, a notchy roll; a 0.3 mm nose reverses over 0.4 mm, a click. Draw the
crest in the layer plane, as sharp as the nozzle corner; one stacked up Z rounds.

**The sound is the landing.** The stored ½ k y² throws the part onto the next
face: hard on hard (PLA, PETG, steel) ticks, a TPU or felt landing thuds. A thin
hollow shell radiates the tick like a sounding box; a solid block mutes it. A pawl
ticks off each tooth tip ([[latches-detents-and-ratchets#ratchet-and-pawl]]).

## Cycle life: a fidget is a fatigue part

Clicked 300 times a day, a fidget passes 10⁵ cycles in a year. Size the flexure
from the fatigue curve ([[printed-fatigue#a-design-curve-for-printed-pla]]), not
the single-snap strain ([[snap-fit-design#permissible-strain]]):

```text
sigma_max(N) = 0.1 * UTS * (2e6 / N)**(1/5.5);  eps_allow = sigma_max / E
eps_root = 1.5 * h * y / L**2      y = crest height
```

| cycles | 10⁴ | 10⁵ | 10⁶ |
|---|---|---|---|
| PLA σ_max (UTS 52 MPa) / ε_allow (E 3.4 GPa) | 13.6 MPa / 0.40 % | 9.0 MPa / 0.26 % | 5.9 MPa / 0.17 % |

Worked: a PLA beam L 20, h 1.2, b 6 mm at 10⁶ cycles takes y ≤ 0.38 mm; at
E b h³ / 4L³ = 1.1 N/mm that is 0.42 N, a 1.3 N push over 45° flanks at μ 0.5.

- Fillet the root, keep the beam in the layer plane, never leave it deflected at
  rest ([[creep-and-stress-relaxation]]); nylon takes cyclic strain far better.
- When the click must be crisp and last, buy it: a tact switch or metal dome has
  a specified ratio and 10⁵-10⁶ cycles, and the print is only the cap
  ([[buttons-knobs-and-front-panels#printed-flexure-buttons]]).

## Weight in the hand

Yoghurt from a heavier bowl was rated denser, pricier, better liked; a container
15 % lighter was valued the same, 30 % lighter less. Value tracks expected weight.

- **Match the weight to the look.** Apparent density `m / V_envelope`: solid PLA
  about 1.2 g/cm³; a 31 × 49 × 11 mm, 60 g steel magnetic slider 3.6 g/cm³. A
  print that looks like metal or stone and weighs like PLA reads as fake.
- **Ballast.** A US quarter (5.67 g, Ø24.26 × 1.75 mm) is 7.0 g/cm³ in a disc
  pocket; nuts fill nearly all their pocket, loose steel balls 0.6
  ([[counterweights-and-gravity-balance#ballast-pockets-and-dense-fills]]). A
  40 × 25 × 8 mm token is 9.6 g solid; two quarters in a Ø24.5 × 3.6 mm pocket
  make it 18.9 g (2.4 g/cm³), far past the 15-30 % people notice.
- **Where and how.** On the rim of what spins, low in what stands, central in
  what is held. Seal it in at a print pause ([[magnets-and-strap-slots#pause-and-embed]]);
  a rattle reads as broken ([[noise-and-vibration#rattles-and-panel-buzz]]). A
  loose coin or ball is a small part; never lead
  ([[toy-safety-constraints#small-parts-the-choke-test]]).

## Surface: temperature, texture and edges

- **Plastic feels warm, metal cold.** `T_c = (e_s T_s + e_o T_o) / (e_s + e_o)`,
  `e = sqrt(k rho c)`. Skin 1.0, PVC 0.6, stainless 7.23, aluminium 23.7
  kJ/m²·K·s^½, skin at an assumed 34 °C, object 20 °C: plastic touches at 28.8 °C,
  stainless 21.7, aluminium 20.6. Prints feel like wood (0.36-0.66); a flush steel
  coin, washer or ball is the only cold cue a print can give, and reads as metal.
- **Stroke along the layers.** Roughness along the layers is near zero, across
  them large; or use an ironed top ([[fdm-surface-finish#ironing]]). Ra and Rq do
  not predict how rough a print feels: judge a coupon by hand.
- **No edge under a finger.** Fillet every edge the hand rolls over
  ([[form-and-finish-heuristics#edges-fillet-or-chamfer]]); keep the seam away.
- **Squish is geometry.** TPU 95A has E ≈ 26 MPa
  ([[flexures-and-living-hinges#tpu-flexure-joints-in-figures-and-grippers]]):
  10 N on a Ø10 mm pad strains solid TPU 0.5 %, 0.05 mm in 10 mm. Squish comes
  from thin walls, an open lattice or a hollow bulb that buckles.

## Spin and slide

- **Bearing to spin free, bushing to stay put.** A ball bearing runs at f ≈ 0.0015
  (M = F f d / 2), up to twice at start, plus seals; a printed bushing's friction
  is two orders higher and stops in seconds ([[shafts-and-bearings#bushing-or-ball-bearing]];
  spin time: [[spinning-toys-and-flywheels#spin-time-inertia-over-drag]]).
- **A slide is steady force and a defined end** ([[linear-guides-and-slides#stick-slip]]).
  A steel slider's six 6 × 3.5 mm N52 magnets, 0.8-1.2 mm under the face, pull the
  plates into each position with nothing to wear ([[magnets-and-strap-slots#magnet-pockets]]).

## Review: hand it over for 30 seconds

Give it to someone without a word. Is the action found unshown, and is it picked up
again within a minute? Does every action end in a click, stop or detent? Is the click
a drop, with a quiet mode? Does it weigh what it looks like, warm and edge-free where
stroked? Two states, something to master or reveal? Cycles asserted; small parts,
magnets, finger entrapment checked ([[toy-safety-constraints]])?

## Checks

No geometry gate measures snap ratio, sound or felt weight: judge them on a coupon.

```python
import math
phi = math.atan(MU)
assert phi < math.radians(FLANK_DEG) < math.pi / 2 - phi, "flank neither centres nor releases"
sr = (F_PEAK - F_MIN) / F_PEAK
assert not IS_PUSH_CLICK or 0.40 <= sr <= 0.65, f"snap ratio {sr:.0%} outside the crisp band"
sigma = 0.1 * UTS * (2e6 / N_CYCLES) ** (1 / 5.5)
eps = 1.5 * BEAM_H * CREST_H / BEAM_L**2
assert eps <= sigma / E_MOD, f"click beam strain {eps:.2%} over the {N_CYCLES:.0e}-cycle limit"
s_rev = (NOSE_R + CREST_R) * (math.sin(math.radians(LEAD_DEG)) + math.sin(math.radians(FLANK_DEG)))
assert not WANTS_CLICK or s_rev <= S_REV_MAX, f"push reverses over {s_rev:.2f} mm: a roll, not a click"
assert MASS_G / ENVELOPE_CM3 >= RHO_TARGET, "feels lighter than it looks"
```
