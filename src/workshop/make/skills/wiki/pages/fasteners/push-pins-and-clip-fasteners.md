---
title: Push pins, rivets and clip fasteners
tags: [push-pin, rivet, clip, fastener, friction-pin, cross-axle, hook-and-loop, cable-tie, press-stud, reusable]
aliases: [christmas tree clip, christmas tree fastener, fir tree clip, fir-tree clip, pine tree clip, xmas tree clip, push-in fastener, push rivet, push-in rivet, snap rivet, plastic rivet, panel rivet, trim clip, panel clip, push-pull rivet, ratchet rivet, press stud, snap fastener, popper, ring spring snap, s-spring snap, snap pin, pin connector, printable pin, friction pin, construction toy pin, technic pin, toy connector pin, cross axle, plus axle, x axle, cross hole, axle hole, hook and loop, dual lock, mushroom fastener, reclosable fastener, cable tie anchor, zip tie mount, lego pin, lego-compatible pin, construction set pin, connector peg]
sources:
  - https://www.itweba.com/en/product/christmas-tree-clips-pine-tree-clip.html (holes 0.118-0.394 in, panels 0.028-2.290 in; ribs deflect and spring back; blind holes in softer panels; removable design)
  - https://www.assemblymag.com/articles/85900-fastening-christmas-trees-ain-t-just-for-december (push-out about 31 lb from a 0.197 in hole in HDPE, about 175 lb from a 0.281 in hole in particle board; via search excerpt)
  - https://andymark.com/products/0-156-in-diameter-0-062-to-0-145-in-grip-plastic-push-rivet (hole 0.151-0.161 in, grip 0.062-0.145 in, reusable)
  - https://www.essentracomponents.com/en-us/s/plastic-rivets (pin-expanded legs; push-pull rivets pull to remove; via search excerpt)
  - https://en.wikipedia.org/wiki/Snap_fastener (lip under one disc into a groove on the other; cap, socket, stud, eyelet)
  - https://leprevo.co.uk/press%20choose.htm (ring-spring sockets strongest; S-spring smaller, for light fabrics)
  - https://www.atabuttons.com/snap-button-size-chart (ligne sizes; 20L 12.5 mm most common, 24L 15 mm; all four parts one series)
  - https://github.com/cfinke/Technic.scad (open library: hole 4.85, pin 4.85/3.1, collar 5.6 x 0.7, lip 5.0 x 0.75, slit 0.75 x 3.2, ridges 0.15 x 0.8, 7.8 mm module with 0.70 mm shoulders, axle arms 1.8)
  - https://github.com/jgrizou/lego-scad (pitch 8, hole 4.8, recess 6.2, axle 4.75 against 4.85 studs; tapered axle coupon; arm 1.8 by micrometer; functional features against trademarks)
  - https://www.cailliau.org/Alphabetical/L/Lego/Dimensions/More%20Dimensions/BBEditPreviewTemp.html (bearing hole close to 4.90 mm, axle 4.8 mm, 8 mm spacing)
  - https://www.newelementary.com/2017/04/nexogon-technic-connection.html (pin 4.8 mm, flange 6.2 mm)
  - https://github.com/tbuser/pin_connectors (printable snap pin: radius 4, lip 0.5 per side, centre slot 0.5 r, flats to print on its side, 0.3 tolerance, entry chamfer)
  - https://multimedia.3m.com/mws/media/2366370O/3M-Dual-Lock-Reclosable-Fastener-SJ3550.pdf (shear, tensile, peel, 1000 cycles, 4 in2 per lb, 93 C)
  - https://cdn.shopify.com/s/files/1/1302/1495/files/Velcro_Brand_Hook_88Loop_1000_with_72_Adhesive_System.pdf (hook 88 / loop 1000: shear 8.3 N/cm2, tensile 5.2 N/cm2, T-peel 1.2 lb/in, 5000 cycles)
  - https://www.industrialwebbing.com/template/images/VELCRO_Brand_Sew-on.pdf (woven nylon -56 to 93 C; mushroom hook shear 80 psi)
  - https://gtse.co.uk/cable-ties/cable-ties-buyers-guides/what-are-the-strongest-cable-ties-size-chart (tie width against loop tensile; 20 % margin)
related: [snap-fit-design, joints, dowel-pins-and-press-fits, fdm-hole-accuracy, layer-anisotropy, magnets-and-strap-slots, straps-buckles-and-textile-attachment, rod-ends-and-clevises, shaft-hub-connections, interlocking-joinery-for-prints, fdm-joining-split-prints, toy-safety-constraints, creep-and-stress-relaxation, bayonet-and-twist-locks, telescoping-tubes-and-locks]
updated: 2026-10-01
---

# Push pins, rivets and clip fasteners

Push-in fasteners join parts with one push and no tool: a flexing fin, leg
or spring snaps behind a hole. Each family differs in what sets its hole,
how its hold compares with its removal force, and whether it survives
removal. The calculation behind every flexing feature is
[[snap-fit-design]]; printed pegs and dowels are
[[dowel-pins-and-press-fits]] and [[fdm-joining-split-prints#connectors]].

## Choosing a push-in fastener

| fastener | hole rule | holds by | removal | reuse | printed? |
|---|---|---|---|---|---|
| **fir-tree clip** | the vendor's hole and panel range | ribs spring back behind the panel or bite its wall | pull-out far above push-in | mostly single use; removable designs exist | buy; print a flat arrow clip instead |
| **push rivet** | tight band, about ±0.13 mm | pin spreads split legs | pull the pin (push-pull type), or push it through | yes, with care | two flat pieces |
| **press stud** | set through fabric by size series | socket spring grips the stud head | pull apart | thousands of cycles | buy metal; printed = annular snap |
| **friction pin** (construction toy) | system hole, counterbore each face | split end lip snaps into the far counterbore | pull with a tool | high | yes, on its side |
| **cross axle** | cross hole, same envelope as the round hole | arms bear on the flanks | slides out | yes | yes, lying down |
| **hook and loop**, mushroom | adhesive or sewing | hooks in loops, heads interlocked | peel | 1000–5000 cycles | buy |
| **cable tie** | slot over the tie width | pawl in the head | cut | single use | buy; print the anchor |
| **R-clip, hairpin** | cross hole in a pin | sprung belly | pull | yes | [[rod-ends-and-clevises#clevis-pins-and-what-holds-them]] |

## Fir-tree (Christmas-tree) clips

- **How.** Flexible ribs deflect through the hole and spring back behind it.
  In a blind hole they hold only if the panel is softer than the clip.
- **Hole and grip.** The vendor gives both. One maker's range spans holes of
  3.0–10.0 mm and panels of 0.7–58 mm. A clip holds only within its panel
  range, because the ribs catch at discrete steps.
- **Hold.** Push-out forces quoted: about 140 N from a 5.0 mm hole in HDPE,
  780 N from a 7.1 mm hole in particle board. They depend on temperature,
  hole, panel thickness, fin design and materials, so the hold in your part
  is a test result.
- **In a printed part** the hole is the vendor's number, not a fit class.
  Printed holes come out small and faceted: check the hole on a coupon
  ([[fdm-hole-accuracy]]). Give a through hole a flat back face for the ribs
  to catch on.
- **Printing one.** Round ribs printed upright have their roots across the
  layers ([[layer-anisotropy]]). Laid down, half of each rib overhangs.
  Print a flat clip instead: an arrowhead on two prongs, extruded in the bed
  plane, sized as a pair of cantilevers ([[snap-fit-design#cantilever]]).

## Push rivets

- **How.** A body with split legs goes through the stack, and a pin pushed
  into it spreads the legs behind the far panel. Until the pin is pulled,
  the legs cannot close.
- **Hole and grip.** One 4 mm rivet takes a 3.84–4.09 mm hole and a
  1.6–3.7 mm stack. Grip is the total stack thickness. Too thin and it
  rattles; too thick and the legs never clear the far side.
- **Removal.** Push-pull rivets release when the pin is pulled. Others are
  reused by pushing the pin through.
- **Printing one.** Print body and pin flat. The legs flex in the bed plane;
  the pin is a wedge whose own hold is a small snap or friction
  ([[snap-fit-design]]). Spread undercut
  `y = (D_spread − D_hole) / 2` must clear the hole edge with the pin in.

## Press studs and snap fasteners

- **How.** A male stud's head passes a sprung lip in the female socket. The
  cap and socket sit on one side, the stud and its post on the other.
- **Socket springs.** Ring-spring sockets hold strongest. S-spring sockets
  are smaller and neater, for light fabrics and wristbands.
- **Sizes** go by ligne: 20L (12.5 mm) is the most common, 24L (15 mm) suits
  jackets. All four parts must come from one size series.
- **Printed** studs are annular snaps: a split socket ring, or a stud with a
  slotted head ([[snap-fit-design#annular-snap]]). For repeated use, design
  to about 60 % of the single-snap strain. For a textile attachment, buy
  metal ([[straps-buckles-and-textile-attachment]]).

## Construction-toy friction pins

The common construction-toy system is an 8 mm grid of round holes. Its
geometry is published by open, measured libraries:

| feature | value |
|---|---|
| hole pitch | 8.0 mm |
| round hole | 4.8–4.9 mm (4.85 in one library) |
| counterbore at each face | Ø 6.2 mm, about 0.7 mm deep |
| module (beam) thickness | 7.8 mm |
| pin body | Ø 4.85, bore Ø 3.1 |
| pin collar (seats in the near counterbore) | Ø 5.6 × 0.7 mm |
| pin end lip (snaps into the far counterbore) | Ø 5.0 × 0.75 mm |
| end slit | 0.75 mm wide, 3.2 mm deep |
| friction ridges, along the pin | 0.15 mm high, 0.8 mm wide |
| cross axle | 4.75–4.8 mm across, arms 1.8 mm thick |

**How it works.** The slit lets the pin end close by the lip's undercut,
`(5.0 − 4.85)/2 ≈ 0.08 mm` per side, as it passes the bore. The lip springs
out into the far counterbore while the collar sits in the near one, so the
pin is located between them. A frictionless pin has no ridges and spins; a
friction pin's ridges drag in the bore. Compatibility is a functional fit:
copy the dimensions, never the names or brand marks.

**Rules for a printed pin and hole system:**

- **Do not copy a moulded undercut.** 0.08 mm is below what a 0.4 mm nozzle
  resolves. Size the lip from strain. Each half of the slotted end is roughly
  a cantilever of length `L_s` (slit depth) and thickness
  `h = (D_pin − d_bore)/2`, so `ε ≈ 1.5 h y / L_s²`. A half-tube is stiffer
  than this flat-beam figure, so treat it as a lower bound. Worked:
  `h = 0.875`, `L_s = 3.2` gives 1.0 % at the moulded `y`. A printable
  `y = 0.25` gives 3.2 %, over PLA's 2 %. Lengthen the slit to 5 mm and it
  falls to 1.3 %.
- **Slit width ≥ 2y + gap:** both halves close by `y`.
- **Lip spacing.** Seated, the collar's inner face and the lip's return face
  are `T − 2c` apart (plate thickness `T`, counterbore depth `c`), plus a
  small axial play so it latches.
- **Fits.** For a frictionless pin, `PIN_D = cadfits.peg_for(HOLE_D, "slip")`.
  A friction pin keeps that body and adds ridge crests at or above
  `peg_for(HOLE_D, "press")`, proved on a coupon.
- **Calibrate holes with a taper.** A tapered axle or pin, marked along its
  length, shows where the printed hole really closes.

## Cross axles in cross holes

- A cross (plus) section passes torque by bearing on its arm flanks. Its
  envelope equals the round hole's, so it turns freely in a round hole and
  is keyed in a cross hole. One hole family gives both a bearing and a key.
- It fits four ways, 90° apart. A phased part on a cross axle can sit a
  quarter turn wrong ([[joints#keyed-joints]]).
- Cross hole arm width: `cadfits.slot_for(ARM_T, SEAT)` for a hub fixed on
  the axle, `RUN` for one that slides along it.
- **Printing the axle:** lay it down so the layers run along it. Turn the
  arms to ±45° so every flank is a 45° overhang, or stand it on one arm.
- **Printing the hole:** with the hole vertical, the nozzle rounds the inner
  corners at the arm ends. Round the axle's arm tips to match (one library
  uses 0.4 mm).
- Torque-carrying hubs and other shaft keys:
  [[shaft-hub-connections]].

## A generic printed snap pin

A well-used printable design shows the recipe:

- 8 mm shaft, lip 0.5 mm proud per side over a 3 mm zone. The lead-in cone
  is about 34° to the axis, then a land, then a sloped return. A sloped
  return makes it removable by force; a square one makes it permanent
  ([[snap-fit-design#mating-and-separating-force]]).
- A centre slot half the shaft radius wide, from a quarter of its length to
  the tip: wider than twice the lip, so the halves close freely.
- Flats on two sides leave 7 mm across. It prints lying on a flat, the halves
  flex in the bed plane, and bending runs along the layers.
- The hole is opened by 0.3 mm and given an entry chamfer.

## Hook-and-loop and mushroom fasteners

| system | shear | tensile | T-peel | cycles |
|---|---|---|---|---|
| woven nylon hook and loop | 8.3 N/cm² | 5.2 N/cm² | 1.2 lb/in (2.1 N/cm) | 5000 |
| mushroom 250 / 250 | 15 N/cm² | 30 N/cm² to part, 15 to engage | 3.3 N/cm | 1000 to half peel |
| mushroom 250 / 400 | 41 N/cm² | 41 N/cm² to part, 21 to engage | 2.6 N/cm | 1000 to half peel |

- **Load it in shear or tension, never peel.** Peel per width is tiny. A lip
  or hood on the printed part stops an edge from lifting.
- **Area.** The mushroom maker suggests starting at 4 in² (26 cm²) per pound
  (4.45 N) of static load. Make one side larger than its mate.
- **Engage force.** Mushroom heads snap in at 15–21 N/cm². A 4 cm² patch then
  needs 60–84 N: give the part a face to press on.
- **Pocket depth** is the engaged thickness: about 3.3 mm for woven hook and
  loop, about 5.7 mm for mushroom tape, which varies with the press.
- **Heat.** Both are rated to about 93 °C; the printed part usually softens
  first. Adhesive surface preparation and cure:
  [[straps-buckles-and-textile-attachment#hook-and-loop-with-adhesive-backing]].

## Cable ties

Widths and strengths: [[magnets-and-strap-slots#cable-ties-and-straps]].
One chart gives loop tensile of 8 kg at 2.5 mm, 18 kg at 3.6 mm, 22 kg at
4.8 mm and 55 kg at 7.6 mm, and asks at least 20 % margin over the load. A
printed anchor is a bar the tie wraps, loaded as a beam. Print it in the bed
plane ([[straps-buckles-and-textile-attachment#bars-that-carry-webbing-are-beams]])
and size its slot `cadfits.slot_for(TIE_W, "free")`. It is usually weaker
than the tie.

## Failure classes

| symptom | cause | rule |
|---|---|---|
| fir-tree clip spins or falls out | panel outside the clip's grip range; printed hole oversize | panel inside the range; hole checked on a coupon |
| push rivet rattles | stack thinner than the grip range | grip range brackets the stack |
| printed pin end snaps off | lip copied from a moulded part; slit too short | strain from `1.5 h y / L_s²`; lengthen the slit |
| pin will not seat | slit narrower than 2y; lip spacing ≠ `T − 2c` | slit ≥ 2y + gap; derive the lip from the plate |
| pin shears at a layer line | printed standing up | print on its side on a flat |
| cross-axle part a quarter turn out | four-way key on a phased part | a D-flat or an extra key |
| patch peels off | load in peel; no lip | load in shear; hood the edge |
| small part released in a toy | a removable pin or clip comes out | [[toy-safety-constraints#small-parts-the-choke-test]] |

## Checks

```python
eps = 1.5 * (PIN_D - PIN_BORE) / 2 * LIP_Y / SLIT_DEPTH**2
assert eps <= EPS_REPEAT, f"pin end strain {eps:.3f} over the repeated-use limit"
assert SLIT_W >= 2 * LIP_Y + GAP, "slit closes before the lip passes the hole"
assert abs((LIP_RETURN_Z - COLLAR_FACE_Z) - (PLATE_T - 2 * CB_DEPTH) - AXIAL_PLAY) < 0.05, "lip misses the far counterbore"
assert PIN_D >= 4 * LINE_W, "below four lines the slicer drops or blobs the pin"
assert GRIP_MIN <= STACK_T <= GRIP_MAX, "rivet or clip outside its grip range"
assert PANEL_HOLE_MIN <= HOLE_MEASURED <= PANEL_HOLE_MAX, "printed hole outside the vendor's range"
assert LOAD_MODE in ("shear", "tension"), "hook-and-loop loaded in peel"
assert PATCH_CM2 >= 26.0 * W_STATIC_N / 4.45 or TESTED, "mushroom patch below the maker's starting area"
assert not PHASED or KEY != "cross", "a cross axle keys four ways"
```

Open items: retention, removal force and cycle life of printed pins and clips
are forces and life; no rigid gate measures them. Give each snap its declared
overlap allowance ([[snap-fit-design#what-a-snap-fit-leaves-open]]) and test a
coupon.
