---
title: Linear guides and slides
tags: [slide, rail, drawer, guide, bushing, linear-bearing, binding, stick-slip, preload, end-stop, prismatic]
aliases: [linear guide, sliding pair, drawer slide, dovetail slide, t-slot rail, rod and bushing, linear bushing, linear ball bearing, LM8UU, MGN rail, MGN12, profile rail, carriage, 2:1 rule, binding ratio, sticky drawer, racking, jamming, stiction, fixed and floating bearing]
sources:
  - https://www.linearmotiontips.com/can-plain-bearings-be-used-for-cantilevered-loads/ (2:1 rule at μ = 0.25; 5:1 at 0.10, 1:1 at 0.50; recirculating ~0.001; fixed rail nearer the load)
  - https://www.igus.com/company/plain-bearings-avoid-slip-stick (2:1 rule measured to the rail nearest the drive; fixed/floating pairs; over-defined systems bind, chatter and wear)
  - https://www.linearmotiontips.com/how-to-reduce-the-effects-of-stiction-stick-slip-in-linear-guides/ (stick-slip from μs > μk; finish, lubrication, the 2:1 ratio)
  - https://www.ovisonline.com/blog/resources-3/when-is-a-drawer-too-wide-or-too-big-26 (drawer width ≤ 1.5 × slide length; one slide always drags more; via search excerpt)
  - https://www.kalsi.com/handbook/D21_Sticky_drawer_effect.pdf (lock-up depends on L/W, load position and μ; threshold μ = engagement length / width; via search excerpt)
  - https://iskbearing.com/product-details/lm8uu (LM8UU 8 × 15 × 24 mm)
  - https://www.hiwin.de/en/Products/Linear-guideways/Blocks/Miniature-guides/MGN-HIRES-series/MGN05CZFHM/p/5-002502 (MGN preload classes ZF slight play, Z0 very light, Z1 light)
  - skills/cad/scripts/cadfits.py (slot_for, peg_for, print_in_place_gap)
related: [joints, friction-wear-and-lubricants, shafts-and-bearings, lead-screws, linkages, fit-derivation, mechanism-verification, latches-detents-and-ratchets, layer-anisotropy, thermal-expansion-and-hybrid-parts, exact-constraint-and-kinematic-mounts]
updated: 2026-09-23
---

# Linear guides and slides

A slide is two parts that must move along one axis and nowhere else. Whether
it runs or jams is decided less by its clearance than by **where the force
is applied relative to how long the guide is**. This page gives that rule,
then the guide forms from printed rails to bought profile rails. The short
catalogue rows are in [[joints#prismatic-joints]]; materials for sliding
contact are in [[friction-wear-and-lubricants]].

## The binding ratio

A slider of guided length `L` is pushed by a force `F` along the axis but
offset sideways by `D` from the guide line (a drawer pulled at one corner, a
carriage driven from one side). The moment `F · D` is taken by a couple of
normal forces `N` at the two ends of the guide, and each end rubs:

```text
couple        N · L = F · D
friction      F_f  = 2 μ N = 2 μ F D / L
binds when    F_f ≥ F   ⇔   D / L ≥ 1 / (2 μ)
```

Pushing harder does not help: both sides scale with F. The cure is a longer
guide, a force nearer the guide line, or less friction.

| μ (plain sliding) | largest D / L | name |
|---|---|---|
| 0.10 | 5 | |
| 0.25 | 2 | the "2:1 rule" for plain bearings |
| 0.50 | 1 | |
| ~0.001 (recirculating balls) | ~500 | why ball guides tolerate overhung loads |

Printed plastic on printed plastic sits at the high end of plain-bearing
friction ([[snap-fit-design#mating-and-separating-force]] lists μ by
material), so design printed slides to D / L ≤ 1 and treat 2 as a limit for
low-friction pairs only.

**Drawer form.** A drawer of width `W` pulled at one side has `D = W/2`, so
it locks up when `μ > L / W`: the threshold friction equals the engagement
length over the engagement width. A shallow, wide drawer (small L/W) sticks;
a deep, narrow one does not. Cabinet practice keeps drawer width at or below
about 1.5 × the slide length, and the catalogue's printed-rail row asks for
guided length ≥ 2 × the slide width ([[joints#prismatic-joints]]) — the
formula tells you how much margin either rule leaves at your μ.

Clearance makes it worse: a slider with total clearance `c` in a guide of
length `L` can tilt by about `c / L` rad before both ends bear, and the
tilted slider wedges at the same ratio. Longer engagement shrinks both.

## Measure to the right rail

With two parallel rails and four bearings, the 2:1 distance is measured from
the force to the **nearest** rail only if that rail is the *fixed* (guiding)
one and the far rail is *floating* (extra clearance across the axis, or a
single roller that only supports). With both rails tight the system is
over-defined: measure to the far rail, expect more drive force, binding,
chatter and wear. Put the fixed side next to the drive and spread the
bearings on it as far apart as the part allows.

The same over-constraint argument says: one precise guide plus one loose
support, never two precise guides fighting print error
([[shafts-and-bearings#supports-and-spans]]).

Why two guiding rails over-constrain a slide:
[[exact-constraint-and-kinematic-mounts]].

## Stick-slip

Stick-slip is a slide that jerks instead of gliding: static friction `μs`
exceeds kinetic `μk`, so the drive winds up, breaks free, overshoots and
sticks again. It is worst in plain bearings, with a compliant drive, and at
low speed.

- Reduce `μs − μk`: PTFE, POM or wear-optimised filaments, a suitable grease
  ([[friction-wear-and-lubricants#lubricants-check-the-base-oil-against-the-plastic]]).
- Smooth the running surface; orient printed slides so they run **along**
  the layer lines, not across them ([[layer-anisotropy]]).
- Stiffen the drive (short belts, rigid links) and respect the binding ratio,
  which is the first remedy the bearing makers list.

## Guide forms

| form | build | use | notes |
|---|---|---|---|
| **printed rail / T-slot** | rail printed flat; slot `slot_for(rail, "free")` above ~40 mm length | drawers, trays, covers | run along the layers; chamfer entries; guided length from the binding ratio |
| **dovetail** | 60° flanks; male derived with `peg_for` from the female | slides captured in two directions | self-centres under load; wedges if the clearance is tight and the part tilts |
| **print-in-place slider** | gaps from `print_in_place_gap("sliding")` | captive sliders, toy mechanisms | horizontal gaps `xy`, ceilings `z`; only a print proves it frees |
| **rod and printed bushing** | steel rod, bore `slot_for(rod, RUN)`; two bushings spaced apart | low-duty guides | steel against printed plastic runs far better than plastic on plastic |
| **linear ball bushing** (e.g. LM8UU, 8 × 15 × 24 mm) | ground rod; bushing pressed or clamped in a printed housing | printer-style axes | a thin shell: an over-tight press or clamp can distort it, so prefer a strap or split housing; search `$step-parts`, seat with `cadmount` |
| **profile rail** (MGN miniature rails) | bought rail and carriage, screwed to a flat, straight datum | precise, stiff, overhung loads | preload class ZF (slight play), Z0 (very light), Z1 (light); higher preload is stiffer and needs a flatter, straighter mount |

Dimensions of bought guides come from the catalog file, never typed here or
in the model.

## Clearance and preload in printed slides

- Take clearances from `cadfits`: `slip` for short guides, `free` for long
  ones and tall Z spans; `print_in_place_gap` for slides printed assembled.
- Clearance that must be removed without making the slide tight is taken up
  by **preload**: a printed leaf spring or flexure pad on one side presses the
  slider against the fixed side. The spring force times μ is added drag, so
  keep it just above the rattle force.
- Long printed guides warp; the clearance must exceed the warp over the
  engaged length, or add a preload pad that follows it.

A long printed slide on a metal rail moves with temperature:
[[thermal-expansion-and-hybrid-parts]].

## End stops and retention

- Every slide has a **closed stop** and an **open stop**, each a `blocked`
  motion condition at the stroke end; the travel between is `clear`
  ([[joints#the-two-conditions-every-joint-owes]]).
- A drawer that must not fall out needs an open stop that can be passed only
  on purpose: a flexing tab, a detent, or a removable stop part in the
  retention chain ([[latches-detents-and-ratchets#detent-holding-force]]).
- A detent or magnet at the closed position keeps a drawer shut against
  vibration.
- A drive screw or motor must not be the stop: put the hard stop in the frame
  ([[lead-screws]]).

## Checks

```python
import cadfits
assert DRIVE_OFFSET / GUIDE_LEN < 1 / (2 * MU), "slide binds: force too far off the guide for its length"
assert DRAWER_DEPTH / DRAWER_WIDTH > MU, "drawer pulled at one side will lock up"
slot = cadfits.slot_for(RAIL_W, "free" if GUIDE_LEN > 40 else "slip")   # derived, never typed
assert N_FIXED_RAILS == 1, "two fixed rails: the guide is over-defined"
assert HAS_OPEN_STOP and HAS_CLOSED_STOP, "slide has no designed end stops"
```

Open items: friction coefficient, wear and stick-slip belong to the material
pair, the finish and the speed. Record the pair and the lubricant; no rigid
gate measures them.
