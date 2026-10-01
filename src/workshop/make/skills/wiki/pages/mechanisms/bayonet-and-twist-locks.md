---
title: Bayonet mounts and twist locks
tags: [bayonet, twist-lock, quarter-turn, lug, slot, ramp, preload, detent, keying, breech-lock]
aliases: [bayonet mount, bayonet fitting, bayonet joint, bayonet lock, bayonet cap, bayonet socket, BC lamp cap, B22, BA15, BAY15d, lamp pin offset, lens mount, lens bayonet, BNC, BNC coupling, quarter turn, quarter-turn fastener, quarter turn latch, Dzus, turnlock, cowl fastener, twist lock, twist-lock lid, twist and lock, push and twist, lug cap, lug closure, twist-off cap, push and turn cap, child resistant closure, breech lock, breech-lock ring, interrupted thread, interrupted screw, L-slot, J-slot, serif slot, helical ramp, cam and groove, camlock coupling, bayonet lamp base, quarter-turn jar lid, lug lid]
sources:
  - https://en.wikipedia.org/wiki/Bayonet_mount (L-slot with a serif; the spring pushes the peg into the serif; lamp cap codes)
  - https://www.classicbulbs.co.uk/faq/data-books-free-bayonet-caps-what-do-the-pin-offset-codes-mean-ba-bau-bax-bay-baz-baw (BA 180 deg, BAU 150 deg, BAY 3.2 mm axial offset, BAX pins 0.8 and 2 mm)
  - https://en.wikipedia.org/wiki/Lens_mount (three or four tabs, one tab a different size, spring-loaded locking pin)
  - https://en.wikipedia.org/wiki/Canon_FD_lens_mount (breech-lock ring turns, the mating faces do not)
  - https://en.wikipedia.org/wiki/Interrupted_screw (2 x 90 deg sectors 1/4 turn, 3 x 60 deg 1/6, 4 x 45 deg 1/8; half the circumference; Welin stepped screw three quarters)
  - https://en.wikipedia.org/wiki/BNC_connector (two lugs, quarter turn of the coupling nut)
  - https://patents.google.com/patent/US6921283B2/en (BNC J-slot with a detent between initial and terminal portions; wave washer bias)
  - https://en.wikipedia.org/wiki/Dzus_fastener (spiral cam slots on the stud, spring receptacle, projections resist reverse rotation)
  - https://en.wikipedia.org/wiki/Cam_and_groove (levers pull the grooved male onto a gasket, over-centre arms, no rotational alignment)
  - https://patents.google.com/patent/US7988003 (push-and-turn closure; skirt length difference lets the outer cap slip unless pushed)
  - https://www.burchbottle.com/blog/difference-between-ct-and-lug-c69851/ (lug finish: interrupted threads, about a quarter turn, over-tightening strips it)
  - https://www.nicksherlock.com/2024/01/reverse-engineering-lens-mounts-for-3d-printing/ (0.3 mm chamfer under printed lugs, 1 mm root fillets, raise the lug's lower edge 0.2 mm when the turn is stiff)
  - https://www.rotorclip.com/formulas-wave-springs/ (single-turn wave spring deflection 30-70 %, multi-turn 20-80 %)
  - Shigley's Mechanical Engineering Design, ch. 3 (cantilever bending and transverse shear in a rectangular section)
related: [joints, latches-detents-and-ratchets, removable-lamp-interfaces, snap-fit-design, printed-threads, lead-screws, springs, exact-constraint-and-kinematic-mounts, overhangs-and-print-orientation, layer-anisotropy, creep-and-stress-relaxation, sealing-and-ingress-protection, mechanism-verification, shaft-hub-connections, telescoping-tubes-and-locks, push-pins-and-clip-fasteners, swivels-and-turntables]
updated: 2026-10-01
---

# Bayonet mounts and twist locks

A bayonet joins two coaxial parts with a push and a part turn: lugs pass
axial entry slots, turn under a ledge, and a spring holds them there. Use it
for a lid, cap, nozzle, lens or module that comes off by hand often and must
lock in under one turn. A thread takes many turns ([[printed-threads]]); a
snap fit has no unlock motion ([[snap-fit-design]]). Catalogue rows:
[[joints#latching-and-holding]], [[latches-detents-and-ratchets#latches]].
A bought lamp or part that bayonets into a printed body follows
[[removable-lamp-interfaces]]: never invent its receiver.

## Lug, ledge, spring, stop

- The **lug** (pin, peg or flat tab) is the male feature. The **entry slot**
  lets it in axially. The **ledge** is the material between the turning leg
  and the female's mouth. Retention is the lug's face bearing on the ledge.
- The **spring** holds the lug on its seat; without it the joint rattles and
  turns back. The **stop** ends the turn; a detent or a dip keeps it there.
- Every bayonet owes the five phases insert, lock, retained, unlock and
  remove ([[removable-lamp-interfaces#motion-is-a-five-phase-contract]]).
  `retained` is an axial pull with the lug under the ledge, `blocked`.

**Locate on a face, clamp with the lugs.** A lamp cap or a BNC plug is
pushed out by its spring and sits on the lugs: the ledge is the datum. A
lens is pulled in by spring leaves on its lugs and seats on its flange: the
flange face is the datum. Where position matters, do the second. A large
flat face prints flatter than a lug, and the lugs then carry only the
preload. A breech lock goes further: a separate ring turns and the located
faces never rub, so they do not wear.

## Slot forms

| form | path of the lug | holds by | to unlock | use |
|---|---|---|---|---|
| **L-slot** | axial entry, then a flat circumferential leg | spring friction on the ledge | turn back | light lids where turning back is harmless |
| **J-slot** (L with a serif) | the leg ends in a short axial notch toward the mouth | the spring pushes the lug into the notch; its walls block rotation | push in by the notch depth, then turn | lamp caps, BNC, anything that must not unwind |
| **ramped leg** | the ledge rises as a short helix | the ramp draws the parts together and builds the preload | turn back against friction | gasketed lids: the turn compresses the seal |
| **ramp then dip** | helix, then a flat or a notch | the ramp builds the preload, the dip holds it | push, or overcome the detent | default for a printed sealing bayonet |
| **interrupted thread** (breech lock) | n thread sectors on each part | thread flanks | turn back | high axial load on a short engagement |

The **serif** must be deeper than the axial play plus the print's Z error,
or the lug rides over it. The spring then needs travel for that depth on
top of its locked compression, or the user cannot push in far enough to
unlock.

## Lug count, spacing and keying

| lugs | seats as | fits | notes |
|---|---|---|---|
| 1 | tips; one lug cannot hold a ring flat | one way | only with a separate locating flange |
| 2 at 180° | rocks about the line through both lugs unless a face seats it | two ways | lamp caps (BA), BNC |
| 3 at 120° | three points seat a rigid ring exactly | three ways | lens mounts |
| 4 at 90° | over-constrained: three bear until something bends | four ways | 45° interrupted-screw sectors, large lids |
| unequal | as its count | one way | key by angle, width, axial height or length (below) |

A fourth rigid lug bears only after the part bends
([[exact-constraint-and-kinematic-mounts#over-constraint-in-printed-assemblies]]).

**Keying one way.** Lamp caps show four ways. BA pins sit at 180° and fit two
ways; BAU pins sit at 150°; BAY pins are offset 3.2 mm along the axis; BAX
pins differ in length (0.8 and 2 mm). Lens mounts make one tab a different
size. In a print, make one lug and its entry slot wider than the rest. A
phased part (a spout, an arrow, a contact) needs this, as a phased gear needs
a D-flat ([[joints#keyed-joints]]).

## Rotation, and how much of the circle can bear

`n` lugs of angular width `w` pass entry gaps of width `g ≥ w`. After a turn
`θ` each lug must lie wholly under its ledge and short of the next gap:

```text
(g + w) / 2  ≤  θ  ≤  360/n − (g + w) / 2          degrees
with g ≈ w:   w ≤ θ ≤ 360/n − w   ⇒   n · w ≤ 180°
```

The lugs can bear on at most half the circle, and the turn equals one lug
width. Interrupted screws follow the same rule: two 90° sectors lock in a
quarter turn, three 60° sectors in a sixth, four 45° sectors in an eighth.
Welin's stepped screw put the sectors on stepped radii: three quarters of
the circumference bore and a quarter turn still locked it. In a print, put
alternate lugs on two radii when half the circle is not enough. The rule is
a ceiling: a BNC's two small lugs turn a quarter turn and bear on far less.

## Ramp angle and self-locking

A ramp of rise `Δz` over a turn `θ` at mean lug radius `r_m` is a short
screw thread. With friction angle `φ = atan μ` and total axial preload
`F_p`:

```text
lead angle    λ = atan( Δz / (r_m · θ_rad) )
close torque  T_close = F_p · r_m · tan(λ + φ)      (+ the end detent)
open torque   T_open  = F_p · r_m · tan(φ − λ)      negative: the preload unwinds it
```

It holds by friction alone only when `λ < φ`, and vibration walks a marginal
one ([[lead-screws#self-locking]]). Take μ's low end from
[[snap-fit-design#mating-and-separating-force]].
Worked numbers: `r_m = 20 mm`, `Δz = 1 mm` over 60° gives `λ = 2.7°`. Below
any plastic's friction angle, it closes with `T ≈ 0.15 N·m` at `F_p = 30 N`,
`μ = 0.2`. Drawing 3 mm in 30° gives `λ = 16°`. That unwinds unless a dip or
detent holds it.

## Preload: what holds the lug on its seat

| source | how | design rule | watch |
|---|---|---|---|
| **wave spring** (bought) | wavy washer under the flange or behind the lugs; BNC uses one | keep single-turn deflection within 30–70 %, multi-turn 20–80 % | needs flat seats on both faces |
| **O-ring or gasket** | the seal is the spring | squeeze from [[sealing-and-ingress-protection#o-rings-what-the-toolchain-derives-and-what-it-does-not]]; ring from `stdpart sizes ORing` | force rises steeply; ramp rise = squeeze travel + play |
| **TPU or elastomer pad** | a printed TPU ring compressed by the ramp | large travel, low force | takes a set; [[creep-and-stress-relaxation]] |
| **printed leaf** | a cantilever in the female presses each lug, like a lens mount's spring leaves | repeated-use strain limit ([[snap-fit-design#permissible-strain]]); print in the bed plane | a leaf held bent creeps and loses force ([[creep-and-stress-relaxation#design-rules]]) |
| **coil spring** | behind a plunger or a contact | [[springs#helical-compression-spring]] | lamp holder contacts |

At the locked position the spring's force must exceed what separates the
parts (weight, gasket reaction, a pull in use), and its spare travel the
serif depth.

## The end of the turn

- **Hard stop.** End the leg in a wall. A detent is not a stop
  ([[latches-detents-and-ratchets#indexing-detents]]). Without one, a lug
  turned past `360/n − w` reaches the next entry slot and falls out.
- **Dip (serif).** Positive. Unlocking needs an axial push first, as on a
  push-and-turn child-resistant cap. Add a click and an index mark: a
  half-turned bayonet looks locked.
- **Bump detent.** The lug rides over a bump near the end of the leg. Release
  torque is the detent side force × lug radius
  ([[latches-detents-and-ratchets#detent-holding-force]]).
- **Over-centre.** A Dzus stud's cam slots have projections that resist
  reverse rotation. A small disturbance pushes it back toward closed.

## Sizing the lugs and the ledge

A lug of radial height `h`, arc width `b` and axial thickness `t` carries
its share of the axial load at about mid-height:

```text
load per lug   F_lug = F_axial / n_eff      n_eff = min(n, 3); 2 if the load can be off-centre
bending        σ = 3 · F_lug · h / (b · t²)
shear          τ = 1.5 · F_lug / (b · t)
bearing        p = F_lug / (b · e)           e = radial engagement = h − radial gap
```

Check the ledge the same way with its axial thickness `s` for `t`. Worked:
50 N on two lugs, `h = 1.5`, `b = 6`, `t = 2 mm` gives σ = 4.7 MPa and
τ = 3.1 MPa, far inside PLA. Lugs break by impact, a layer line through the
root, or a ledge too thin to print solid. Keep bearing faces normal to the
axis: a cone there turns axial load into hoop tension and splits the female.

## Families and their geometry

| family | lugs and slots | lock | preload | lesson for a print |
|---|---|---|---|---|
| bayonet lamp cap (B22, BA15) | 2 side pins | J-slot with serif | sprung contacts in the holder | key with pin angle, height or length |
| camera lens mount | 3–4 flat tabs, one a different size | small turn; sprung pin drops into a notch | spring leaves in the body | locate on the flange; one-way keying |
| BNC connector | 2 lugs on the jack, J-slots in the coupling nut | quarter turn, detent between entry and seat | wave washer | detent plus spring, not friction |
| quarter-turn panel fastener (Dzus) | stud with spiral cam slots, spring receptacle | quarter turn, projections resist reverse | the receptacle spring | the slot is a cam: it draws and locks |
| interrupted screw, breech lock | 2–4 thread sectors | 1/4 to 1/8 turn | flank wedging | stepped sectors beat the half-circle limit |
| lug cap on a jar | lugs in the cap, interrupted thread segments on the neck | about a quarter turn | liner compression | over-tightening strips it: add a stop |
| push-and-turn closure | ratchet teeth between an outer and an inner cap | the outer slips unless pushed down | a skirt length difference gives the free play | lock by needing two motions |
| cam-and-groove coupling | two cam levers on the coupler, a groove on the adapter | levers over centre, optional safety pins | gasket | not a bayonet, but no rotational alignment needed |

## Printing a bayonet

- **Axis vertical, both halves.** Lugs and slots are then round, in-plane
  features. Laid on its side, a bayonet has lugs at every angle to the layers
  and the weakest one decides ([[layer-anisotropy]]).
- **Mating end on the bed.** Print the inner part tip-down. The lug's bearing
  face (toward the body) is then a top face, and its leading face is the
  overhang: chamfer it 45°, which also makes the lead-in. Print the outer
  part mouth-down. The ledge's bearing face is then a top face, and the
  leg's roof is the only overhang.
- **Lugs outward on the inner part, grooves in the outer part's bore.** A
  blind groove's roof reaches only the groove depth. Keep it under 1 mm or
  slope it ([[overhangs-and-print-orientation#a-slots-roof-reaches-to-its-far-wall]]).
  A window cut through the wall makes the roof a bridge the leg's full arc
  long, and weakens the hoop that resists splitting.
- **Elephant's foot.** Both mating ends sit on the bed. Chamfer their first
  layers by `cadfits.print_in_place_gap()["bottom_chamfer"]`.
- **Fits from one dimension.** Entry slot width =
  `cadfits.slot_for(LUG_B, RUN)`. Groove radius = lug tip radius +
  `mating_clearance(RUN)`. Leg height = lug thickness + spring travel at insertion +
  `mating_clearance("free")` (a Z span). A lens-mount builder printed a
  0.3 mm chamfer under each lug over three layers and 1 mm root fillets. When
  the turn was stiff, raising the lug's lower edge 0.2 mm freed it.
- **Material.** For a bayonet worked daily prefer PETG or nylon, which flex
  where brittle PLA cracks ([[printed-threads#material]]).
- **Coupon.** Print one lug-and-slot sector before the whole part, as
  [[removable-lamp-interfaces#physical-fit-needs-a-real-hardware-coupon]]
  requires for a bought mate.

## Failure classes

| symptom | cause | rule |
|---|---|---|
| unwinds in use | ramp steeper than the friction angle; no dip or detent | `λ < φ` at the low μ, or a dip |
| falls out after overturning | no hard stop; turn reaches the next entry slot | wall at the end of every leg |
| rattles, rocks | no preload; two lugs and no seating face | spring force at lock > separating load; three lugs or a flange |
| will not turn | elephant's foot, drooped leg roof, a lead chamfer on the bearing face, too much preload | mating end chamfer; roof ≤ 1 mm or sloped; raise the lug edge on a coupon |
| lug snaps at a layer line | bayonet printed on its side; no root fillet | axis vertical, root fillet |
| female splits | conical bearing faces; thin wall pierced by windows | flat bearing faces; blind grooves |
| hold fades over weeks | printed leaf or TPU pad creeps | bought spring, or a dip that holds by geometry |

## Checks

```python
import math
n_eff = min(N_LUGS, 3) if LOAD_CENTRED else 2
assert N_LUGS * LUG_ARC_DEG <= 180.0 or STEPPED_LUGS, "lugs cover more than half the circle"
assert ENTRY_ARC_DEG >= LUG_ARC_DEG, "entry gap narrower than the lug"
lo = (ENTRY_ARC_DEG + LUG_ARC_DEG) / 2
hi = 360.0 / N_LUGS - (ENTRY_ARC_DEG + LUG_ARC_DEG) / 2
assert lo + TURN_MARGIN_DEG <= TURN_DEG <= hi - TURN_MARGIN_DEG, "lug not under the ledge, or reaches the next gap"
assert HAS_END_STOP, "a detent is not a stop"
lam = math.atan(RAMP_RISE / (R_MEAN * math.radians(RAMP_DEG)))
assert lam < math.atan(MU_LOW) or HAS_DIP_OR_DETENT, "the preload unwinds the bayonet"
assert SERIF_DEPTH >= AXIAL_PLAY + Z_ERROR, "the lug rides over the serif"
assert SPRING_SPARE_TRAVEL >= SERIF_DEPTH, "cannot push in far enough to unlock"
assert F_SPRING_LOCKED >= F_SEPARATING, "the lug lifts off its seat"
f_lug = F_AXIAL / n_eff
assert 3 * f_lug * LUG_H / (LUG_B * LUG_T**2) <= UTS_XY / SF, "lug bending"
assert 1.5 * f_lug / (LUG_B * LUG_T) <= Z_FACTOR * UTS_XY / SF, "lug shear across layers"
assert ONE_WAY_KEYED or not PHASED, "a phased part on a symmetric bayonet fits wrong"
```

Open items: closing torque, spring force after creep and the click are
forces; no rigid gate measures them. Print the sector coupon.
