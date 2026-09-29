---
title: Straps, buckles and textile attachment
tags: [strap, webbing, buckle, slot, textile, sewing, hook-and-loop, cord-lock, d-ring]
aliases: [side release buckle, quick release buckle, ladder lock, ladderloc, cam buckle, cam strap, tri-glide, triglide, slide adjuster, d-ring, webbing slot, strap loop, sew-on flange, sewing holes, velcro, hook and loop, cord lock, cord stopper, toggle, zipper pull, paracord, shock cord, backpack hardware]
sources:
  - https://www.acesupplies.co.uk/ace-hub/ace-knowledge-base/plastic-buckle-sizes/ (nominal vs slot width; 25 mm buckles take 23–25 mm webbing; slot "just over 25 mm")
  - https://www.amazon.com/Release-Buckles-Backpack-Adjustable-Replacement/dp/B08MQ5VYYW (1 in buckle, inside width 26 mm; via search excerpt)
  - https://elesawebbing.com/how-to-choose-the-right-width-thickness-for-nylon-webbing/ (webbing thickness classes 0.8–1.5, 1.6–2.5, ≥3 mm; common widths; via search excerpt)
  - https://countrybrookdesign.com/blog/webbing-strength-and-safety-ratings-explained (1 in nylon/polyester 1500–2000 lb, polypropylene to about 600 lb; via search excerpt)
  - https://austinzuehlke.me/3DPrintedHardware.html (PETG pack hardware printed flat, filleted slot edges, 3/16 in shock cord)
  - https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament (hook test: PLA 73/40 kg, PETG 55/25 kg, ASA 57/17 kg flat/upright)
  - https://www.trivantage.com/blog/products/fastener-physics-101-cam-buckles-ladderloc-webbing (cam clamps, ladderloc holds by friction)
  - https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/sewing-3d-parts/ (print holes and lace rather than pierce; TPU for sewn parts; recessed stitch line)
  - https://doi.org/10.1145/3772318.3791574 (SewFab, CHI 2026; seam strength vs hole size; via search excerpt)
  - https://www.velcro.com/news-and-blog/2023/07/how-to-apply-adhesive-backed-velcrobrand-fasteners-for-a-secure-bond/ (surface prep, 15–25 °C application, 24–72 h cure, round corners)
  - https://www.itapestore.com/velcro-brand-adhesives-guide/ (Adhesive 19 for polyethylene/polypropylene; via search excerpt)
  - https://www.paracordplanet.com/paracord-sizes/ (550 paracord about 4 mm; via search excerpt)
  - https://www.paracord.eu/paracord-accessory/cord-end-stopper/cord-locks (cord-lock holes 4–4.9 mm; via search excerpt)
  - https://makerworld.com/en/models/1055730-side-release-buckle (do not print a buckle upright; PETG preferred; via search excerpt)
related: [snap-fit-design, magnets-and-strap-slots, layer-anisotropy, fdm-print-orientation-for-strength, creep-and-stress-relaxation, fdm-hole-accuracy, filament-properties, beam-and-plate-stiffness, springs, adhesives-and-solvent-welding, latches-detents-and-ratchets]
updated: 2026-09-23
---

# Straps, buckles and textile attachment

Webbing is far stronger than printed hardware: 1 in (25 mm) nylon or polyester
webbing is sold at roughly 1500–2000 lb breaking strength, polypropylene at up
to about 600 lb. Every printed buckle, slide or ring is the weak link, so size
it for the load and print it so the load runs along the layers. Cable-tie and
simple strap slots are in [[magnets-and-strap-slots#cable-ties-and-straps]].

## Webbing sizes and the slot that takes them

Nominal widths: 20 mm (3/4 in ≈ 19 mm), 25 mm (1 in), 38 mm (1.5 in),
50 mm (2 in); 10–15 mm for light trim. Thickness classes: thin 0.8–1.5 mm,
medium 1.6–2.5 mm, heavy ≥ 3 mm. Narrow fabrics have loose tolerances: a
"25 mm" buckle is expected to take 23–25 mm webbing, and a "19/20 mm" one
either. **Measure the webbing that will be used**; do not trust the label.

```text
slot width   w_slot = w_webbing + (1 … 2) mm       commercial 25 mm buckle: 26 mm inside
slot height  h_slot = n_layers · t_webbing + (0.5 … 1) mm
             n_layers = 1 for a fixed end, 2 where the webbing doubles back
```

The width allowance is observed practice (commercial 26 mm for 25 mm webbing;
printed designs 1–2 mm), not a standard. A vertical slot prints undersize
([[fdm-hole-accuracy#why-a-vertical-hole-comes-out-small]]); derive the slot as
a clearance feature ([[fit-derivation]]) and prove the first one on a print.
Too wide and the webbing folds and rides up one edge; too tight and it will
not thread. Round every edge the webbing wraps (a starting point, not a
sourced figure: radius ≥ half the webbing thickness): a sharp printed edge
saws the webbing.

## Bars that carry webbing are beams

Wherever webbing wraps a bar (tri-glide, ladder lock, D-ring straight, slot
bridge), the bar carries both legs: load `2T` spread over the slot width.
Simply supported with a uniform load:

```text
M = 2T · w_slot / 8          Z = b · d² / 6   (d = depth in the load direction)
σ = M / Z  ≤  σ_allow        (printed PETG X-Y UTS ≈ 50 MPa; allow ≤ half)
```

Worked: T = 200 N (20 kg), w_slot = 26 mm → M = 1300 N·mm.
A 4 × 4 mm bar gives σ = 122 MPa and breaks. A bar 5 mm wide and 8 mm deep
in the load direction gives 24 MPa. Depth in the pull direction is what
counts ([[beam-and-plate-stiffness#depth-beats-width-and-material-belongs-at-the-surface]]).
Bars that are clamped into side frames are stiffer than this; the simply
supported case is the safe one.

## Print flat: the strap plane on the bed

Print buckles, slides, loops and rings with the webbing plane parallel to the
build plate. Then every bar's bending and every ring's hoop tension run along
the extrusion lines. CNC Kitchen's hooks show the penalty for getting it
wrong: PLA 73 kg flat against 40 kg upright, PETG 55 kg against 25 kg, ASA
57 kg against 17 kg ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]],
[[fdm-print-orientation-for-strength#orient-by-load]]).

PETG failed by stretching, PLA and ASA snapped. A strap part that is dropped,
yanked or worn is better ductile than strong: prefer PETG, nylon or ASA over
PLA, and PLA not at all in sun or a hot car
([[heat-resistance-of-printed-parts]]).

## Side-release buckle

The male half has two cantilever prongs with barbs, and usually a central
tongue that guides insertion and stops the prongs bending sideways. The
female housing has side windows; the barbs snap into them, and the buckle is
released by squeezing the barbs inward through the windows.

- Each prong is a cantilever snap: size it with
  [[snap-fit-design#cantilever]]. Worked, PETG (yield strain about
  50.8 / 2117 ≈ 2.4 %, amorphous → about 70 % → 1.7 %): h = 2 mm, undercut
  y = 1.5 mm needs L ≥ sqrt(1.5 · 2 · 1.5 / 0.017) ≈ 16 mm for one snap,
  and at the repeated-use 60 % (≈ 1.0 %) L ≥ 21 mm. A tapered prong
  shortens it ([[snap-fit-design#cantilever]]).
- Under strap load the barbs bear on the window shoulders in shear. Give the
  load face a 90° return so tension cannot cam the prongs out; release is by
  squeeze only ([[snap-fit-design#mating-and-separating-force]]).
- The prongs bend in the plane of the buckle, so a flat print puts their
  bending along the layers. Never print the buckle standing up.
- Repeated use relaxes the prongs ([[creep-and-stress-relaxation]]); design for
  the 60 % repeated-use strain, not the single-snap value.

## Tri-glides, ladder locks and cam buckles

- **Tri-glide (slide adjuster):** webbing threads over the centre bar and is
  held by friction and the wraps pinching each other. The centre bar is the
  beam above with load `2T`.
- **Ladder lock:** webbing enters from below, wraps a bar and exits; tension
  levers the bar and pinches the webbing against the frame. It holds by
  friction alone, so webbing thickness and stiffness decide whether it slips:
  prove it with the actual webbing, wet if it will get wet.
- **Cam buckle:** an eccentric cam on a pin pinches the webbing against the
  body; pulling the standing part rotates the cam further in, so load tightens
  the grip. Teeth or serrations bite; smooth faces spare soft webbing. Use a
  metal pivot pin ([[hinges-and-pin-joints]]); the closed cam-to-body gap must
  be less than the webbing thickness, and the lever needs a detent or spring
  to stay closed when unloaded ([[latches-detents-and-ratchets]]).

Friction holders slip gradually rather than break: good for adjusters, not
for anything that must hold a set length under shock.

## D-rings and loops: printed or bought

A welded steel D-ring costs little and is far stronger than a printed one;
heavy-wire 1 in rings are about 5 mm (0.20 in) wire. Printed rings are fine
for light, non-critical loads — bag trim, cable management, a keychain.
**Never print** hardware for climbing, fall arrest, lifting, vehicle
tie-down, child restraint or a leash for a strong dog: buy rated metal
hardware. For a printed ring, size the straight side as the bar above, give
the corners generous inside radii (they are curved beams), print it flat, and
record a test load with a safety factor ([[beam-and-plate-stiffness#safety-factors-for-printed-plastic]]).

## Sewing printed parts to fabric

- **Print the holes; do not pierce.** A needle forced through a rigid print
  starts cracks. Lace or stitch through designed holes, or print the sewn part
  in TPU, which takes a needle.
- Put the holes in a thin flange with a **recessed stitch groove** so the
  thread sits below the surface and does not abrade.
- Hole diameter: needle plus doubled thread; 1–2 mm (unsourced start) for hand-sewing
  thread, larger for waxed cord; printed holes come out small
  ([[fdm-hole-accuracy]]). Hole pitch 3–6 mm (about 4–8 stitches per inch).
  No printed-part source for edge distance was found: keep at least one hole
  diameter plus two perimeters of material to the flange edge and prove it
  by pulling a sample.
- Flange thickness about 1.2–2 mm (a starting point, unsourced) keeps
  stitching feasible; a rigid flange should
  be no stiffer than the fabric needs, or it tears the fabric at its edge.
- Alternative: print TPU directly onto fabric so the first layer melts into
  the weave, then sew the fabric normally.

## Hook-and-loop with adhesive backing

- Bond to a flat, smooth face: the plate side of the print, or an ironed top
  surface. Ridged FDM top surfaces cut contact area.
- Clean and dry the surface, round the tape corners, press firmly, apply at
  about 15–25 °C, and wait 24 h (up to 72 h for some acrylic adhesives) before
  loading.
- Low-surface-energy plastics (PP, PE) need an adhesive made for them. Sources
  disagree on which family (one names a rubber-based "Adhesive 19", another
  acrylic); check the vendor datasheet for the actual substrate.
- Where the part will be washed or wet, sew the hook-and-loop to a strap and
  pass the strap through a slot instead.
- For bonding generally: [[adhesives-and-solvent-welding]].

## Cord locks, toggles and zipper pulls

- 550 paracord is about 4 mm; common shock cord 3/16 in (≈ 4.8 mm). Bought cord
  locks use 4–5 mm holes for 4 mm cord. Size the printed hole from the cord
  measured, plus clearance.
- A cord lock is a plunger with a cross hole, pushed out of line with the body
  hole by a spring so the cord is pinched. A printed plastic spring creeps and
  loses its preload; buy the steel spring ([[springs]],
  [[creep-and-stress-relaxation]]).
- A zipper pull hangs from the slider tab through a loop of cord or a split
  ring; a printed pull that clips directly on the tab is a thin ring in
  bending — keep the ring section ≥ 2 mm and print flat.

## Checks

```python
assert w_webbing_measured + 1.0 <= w_slot <= w_webbing_measured + 2.0, "webbing slot width"
assert h_slot >= n_layers * t_webbing + 0.5, "webbing slot too thin for the layers it carries"
M = 2 * T * w_slot / 8
sigma = M / (bar_b * bar_d**2 / 6)
assert sigma <= 0.5 * uts_xy, f"strap bar at {sigma:.0f} MPa"
eps = 1.5 * prong_h * undercut / prong_L**2
assert eps <= 0.6 * eps_perm, "buckle prong over the repeated-use strain"
assert print_orientation == "flat", "strap hardware must be printed with the webbing plane on the bed"
assert not life_safety_load, "rated metal hardware only for life-safety loads"
```
