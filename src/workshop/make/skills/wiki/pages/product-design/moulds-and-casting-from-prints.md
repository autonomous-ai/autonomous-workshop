---
title: Moulds and casting from prints
tags: [mould, casting, silicone, master, sprue, vent, registration-key, draft, undercut, cure-inhibition, shrinkage, urethane]
aliases: [mold, mold making, silicone mold, silicone mould, rtv mould, block mould, two-part mould, split mould, printed master, master pattern, mould box, mold box, pour spout, air vent, registration keys, mould keys, platinum silicone, tin cure silicone, cure inhibition, casting resin, urethane casting, smooth-cast, mold star, printed mold, direct printed mould, overmolding]
sources:
  - https://www.smooth-on.com/tutorials/making-piece-cut-block-mold/ (≥ 1/2 in between model and box, ≥ 1/2 in over the top, zig-zag cut, pour thin stream into the lowest spot)
  - https://www.smooth-on.com/tutorials/mold-max-25-create-2-silicone-mold/ (1 in clearance box, acorn-nut keys, Ease Release 200 between silicone halves, clay funnel as pour spout)
  - https://www.smooth-on.com/tutorials/venting-silicone-mold-eliminate-bubbles-finished-casting/ (vents over the highest points of the top half, punched with sharpened brass tube)
  - https://polytek.com/blog/how-to-make-a-one-piece-silicone-rubber-block-mold/ (≥ 1/2 in on all sides and above, fix the model to the base, pour rubber into rubber)
  - https://www.smooth-on.com/support/faq/210/ (SLA print must be fully UV cured, ≥ 6 h turned, IPA 91 % + soap wash, XTC-3D or acrylic seal, Inhibit X, tin cure less inhibited)
  - https://www.smooth-on.com/support/faq/184/ (platinum critically sensitive to sulfur; tin cure shrinks more over time, shorter library life)
  - https://www.liqcreate.com/supportarticles/platinum-cured-silicone-3dprint-resin/ (photoinitiators, uncured resin, sulfur, cleaning residue; 60 min at 60 °C heated UV; 2 h at 80 °C or 3 days to dry)
  - https://formlabs.com/support/Silicone-mold-making-and-silicone-part-production/ (wash, full cure, 24–48 h rest, epoxy barrier, compatible resins list, 10–20 uses)
  - https://formlabs.com/white-papers/silicone-part-production-with-3d-printed-tools/ (≥ 2° draft, vents ~0.5–2 mm, gate at the lowest point, mould stock ≥ 1 cm beyond the part, 2 mm minimum silicone overmould shell)
  - https://formlabs.com/blog/how-to-make-silicone-molds/ (≥ 1 cm silicone over the master, 0.1 mm alignment clearance, silicone picks up layer lines, 25–50 µm layers)
  - https://blog.prusa3d.com/the-beginners-guide-to-mold-making-and-casting_31561/ (pour channel ≥ 3–5 cm long, 1 cm wide or 3 cm for thick materials, vent above the gate, 30–50 casts)
  - https://www.smooth-on.com/tb/files/Smooth-Cast_300q,_300,_305___310.pdf (shrinkage 0.01 and 0.0065 in/in, RH < 50 %, pour at the lowest point, 60 psi pressure casting, release for silicone-into-silicone)
  - https://www.smooth-on.com/tb/files/MOLD_STAR_15_16_30_TB.pdf (platinum silicone shrinkage < 0.001 in/in; via search excerpt)
  - https://arxiv.org/pdf/2608.13233 (cast silicone actuator walls needed ~5 mm to fill without voids; bonded cast interfaces failed above ~200 kPa)
related: [resin-printing-design, fdm-surface-finish, form-and-finish-heuristics, food-and-toy-safety, sealing-and-ingress-protection, wall-thickness-and-hollowing, overhangs-and-print-orientation, adhesives-and-solvent-welding, fit-derivation]
updated: 2026-09-23
---

# Moulds and casting from prints

A print can be the **master** a silicone mould is poured around, or the
**mould** itself. Either way the cast part inherits every surface flaw of the
print, and the chemistry of the print can stop the mould from curing. Read
this before modelling a master, a mould box, or a printed mould cavity. It
decides the mould type, the clearances, where material enters and air leaves,
and which prints poison which silicones. For the parting-line look of a
product that was moulded in industry, see
[[form-and-finish-heuristics]].

## Pick the mould type from the part

| part | mould | why |
|---|---|---|
| one flat face, no deep undercut | one-part open block mould | the flat face is the open pour face; no parting line |
| no flat face, modest undercuts | one-part **cut** block mould | cast whole, then cut open with a zig-zag cut that re-registers like a jigsaw |
| all-round detail, through holes | two-part silicone mould | a parting line on the widest silhouette, keys, sprue and vents |
| rigid part, many copies, no undercut | printed rigid mould (resin or FDM) | skips the silicone step; needs draft |
| soft (silicone) part, internal cavities | printed rigid mould with cores | the soft casting deforms out of undercuts itself |

- Silicone moulds forgive undercuts because the mould stretches off the part.
  Formlabs notes deep undercuts still make both master and castings hard to
  remove, so a deep undercut gets its own mould piece or a relief cut.
- A **rigid** mould (printed resin, PETG, PLA) has no give: every face along
  the pull direction needs draft and no undercut, or the part is trapped. When
  the casting is itself silicone, Formlabs asks for **≥ 2°** draft; a rigid
  casting from a rigid mould needs more, as in injection moulding.

## Mould box: the rubber wall around the master

The silicone wall must be thick enough that the mould keeps its shape when it
is filled.

```text
gap from the master to every box wall      >= 12.7 mm  (1/2 in)
rubber over the highest point              >= 12.7 mm  (Formlabs: >= 10 mm)
typical on medium masters                  25 mm (1 in)
```

- Smooth-On and Polytek give 1/2 in (≈ 13 mm) minimum on all sides and on
  top; Smooth-On's worked two-part example uses 1 in. Treat 10–13 mm as the
  floor and go up with size: a big, soft mould sags.
- Print the mould box as its own part (walls ≥ the floor from
  [[wall-thickness-and-hollowing]]), fix the master to the base
  (screw, glue, or a printed boss) so it cannot float, and seal box seams.
  Leaking silicone under the master is the usual failure.
- Rubber volume = box interior minus master volume. Compute it in CAD from
  the two solids rather than guessing; one mixed batch should fill it.

## Two-part moulds: parting line and keys

- Put the parting line on the master's **widest silhouette** in the pull
  direction, the same place an injection-moulded part would have it.
- The first half is poured against a clay (non-sulfur) or printed parting
  board. A **printed parting board** is better than clay here: model it as a
  plate with the master's silhouette cut out, and put the keys on it.
- **Keys**: hemispherical bumps and dimples (Smooth-On press acorn nuts into
  the clay) around the perimeter, outside the cavity, so the halves only close
  one way. Use at least three, not on a symmetric pattern.
- Before pouring the second half, coat all cured silicone with release
  (Smooth-On: Ease Release 200). **Silicone bonds to silicone.**
- For a printed rigid two-piece mould, alignment pins need clearance; Formlabs
  starts at 0.1 mm and tunes it. Derive the pin and socket from one parameter
  ([[fit-derivation]]).

## Sprue, gate and vents

Material enters at one point and air must leave from every high point.

- **Pour at the lowest point.** Smooth-On's casting-resin bulletin: pour in a
  single spot at the lowest point and let the liquid find its level. Formlabs
  places the inlet high on the mould block with a U-shaped channel (a generous
  bend radius) that joins the cavity at its **lowest** point.
- **Sprue size**: Prusa gives a pour channel ≥ 3–5 cm long and about 1 cm
  wide, 3 cm for thick materials. The sprue also acts as the reservoir that
  feeds shrinkage, so it stays above the cavity.
- **Vents** go over every local high point of the cavity in the pouring
  orientation, and at sharp turns and where two flow fronts meet (Formlabs,
  0.5–2 mm diameter). A vent is working when the cast material fills it.
- Model sprue and vents as solids on the **master** (or as cores in a printed
  mould), not as holes punched afterwards: then their positions are asserted,
  not improvised.
- Find the high points in CAD: in the pouring orientation, any face whose
  outward normal points up and is not already connected to the sprue or a vent
  traps a bubble.

## Surface finish transfers exactly

Silicone reproduces fine detail, including every layer line, seam and support
mark ([[fdm-surface-finish]]). Decide finish on the master, not the casting:

- Resin masters at 25–50 µm layers (Formlabs) need little finishing; see
  [[resin-printing-design]].
- FDM masters: orient so the visible faces are top or vertical faces, place
  seams on the parting line, then fill (sanding primer or brushed epoxy
  coating) and sand. A coating adds thickness and rounds edges; do not coat a
  dimension that matters.
- Texture you **want** (fuzzy skin, knurl) also copies, so it can be
  designed on the master.

## Cure inhibition: platinum silicone on printed masters

Platinum (addition-cure) silicone stops curing where it touches certain
chemicals, leaving a sticky layer against the master. Tin (condensation-cure)
silicone rarely inhibits but shrinks more over time and has a shorter shelf
life (Smooth-On).

Inhibitors that matter for prints:

- **Uncured resin and photoinitiator residue** on SLA/MSLA prints: the most
  common cause (Liqcreate, Smooth-On). Deep recesses and through-holes that
  the UV lamp never saw stay under-cured.
- **Sulfur** (sulfur-bearing clays, some resins and rubbers): platinum
  silicone "will not cure under any circumstances" (Smooth-On).
- Cleaning residues: leftover IPA or resin cleaner.

Prevention, in the order worth trying:

1. Wash thoroughly (IPA, then soap and water), dry, then **over-cure** with
   the part turned so every face is lit: Smooth-On ≥ 6 h UV; Formlabs 60–120
   min extra; Liqcreate 60 min at 60 °C, then 2 h at 80 °C or 3 days to let
   residues escape. Formlabs waits 24–48 h before casting.
2. Seal the master: brushed epoxy coating (XTC-3D) or a gloss acrylic spray.
3. Test first: pour a small patch of the silicone on a scrap print from the
   same resin and post-cure; a cured, non-tacky interface means the master is
   safe.
4. If it still inhibits: an inhibition-blocking primer for platinum silicone
   (Smooth-On Inhibit X), or switch to tin-cure silicone.

Smooth-On demonstrate platinum silicone over plain FDM PLA; FDM filaments are
rarely the problem. Tin and platinum silicones do not mix.

## Release agents

| mould | cast material | release |
|---|---|---|
| silicone | urethane / epoxy resin | usually none; release extends mould life (Smooth-On) |
| silicone | silicone | **always** (Ease Release 200, or petroleum jelly per Formlabs) |
| printed rigid | anything | always; FDM layer lines key the casting mechanically |
| silicone half | second silicone half | always |

Brush release into the texture, then mist, and let it dry (Smooth-On: 30 min
for resin casting; Formlabs about 10 min). Release is a thin film; it does
not fill layer lines.

## Shrinkage and cast-part walls

Scale the master (or the printed cavity) by the shrinkage of each material
in turn. Platinum silicone is about 0.1 % or less and is usually neglected;
casting resins are not:

| material | linear shrinkage (in/in) |
|---|---|
| platinum silicone (Mold Star class) | < 0.001 |
| urethane resin, fast (Smooth-Cast 300/300Q) | 0.01 |
| urethane resin, slow (Smooth-Cast 305/310) | 0.0065 |

- A 100 mm casting in a fast urethane comes out about 1 mm short. Scale the
  master by `1 / (1 - s)` and keep fit-critical holes as post-machined or
  as inserted parts.
- Urethanes react with moisture: cast below 50 % RH. Pressure casting at 60
  psi (≈ 4 bar) shrinks bubbles; vacuum degassing is for the silicone.
- Cure time "depends on mass": a thick section runs hotter and faster than a
  thin one. Keep casting walls uniform, as for resin prints
  ([[resin-printing-design#shrinkage-and-post-cure-distortion]]).
- **Thin cast walls do not fill.** Formlabs' minimum overmoulded silicone
  shell is 2 mm; a study of cast silicone pneumatic actuators needed about 5
  mm walls to fill enclosed geometry without voids. Keep walls of a casting
  ≥ 2 mm and plan vents at each thin region.
- Parts cast in several pieces and bonded are weakest at the bond: the same
  study saw bonded silicone interfaces fail above about 200 kPa. Cast
  pressurised bodies in one piece around a core where possible
  ([[fluid-fittings-and-pneumatics]]).

## Printing the mould directly

- **Resin moulds** (SLA/MSLA) give the best cavity finish. Cure and wash as
  above if casting platinum silicone. Formlabs reports 10–20 uses before wear
  for silicone part production; Prusa reports 30–50 casts from a silicone
  mould.
- **FDM moulds** (PETG, ABS/ASA, PLA): layer lines lock the casting in;
  release, a coat of epoxy, and draft all help. PLA softens at the lowest
  temperature of the three, so a hot-curing or strongly exothermic resin can warp it — use PETG or ABS
  there ([[heat-resistance-of-printed-parts]]).
- **Flexible TPU moulds** peel off small undercuts like silicone, but their
  surface is FDM-rough and layer seams leak thin resins; seal the mould seam
  with a clamp and a lip.
- Formlabs extends mould stock ≥ 1 cm beyond the part and adds an overflow
  trough; a printed rigid mould also needs screws or clamps to hold the halves
  shut against the head of liquid.
- Food or skin contact of the cast part is a property of the casting
  material, not the mould ([[food-and-toy-safety]]).

## Checks

```python
import math
# mould box around a master bounding box (mm)
assert GAP_SIDES >= 12.7 and GAP_TOP >= 10.0, "silicone wall below 1/2 in / 1 cm"
box_inner = (MX + 2 * GAP_SIDES, MY + 2 * GAP_SIDES, MZ + GAP_TOP)
rubber_ml = (box_inner[0] * box_inner[1] * box_inner[2] - MASTER_VOL) / 1000.0
assert rubber_ml <= BATCH_ML, "one mixed batch must fill the box"
# keys: asymmetric and outside the cavity
assert N_KEYS >= 3 and not KEYS_SYMMETRIC
# shrinkage compensation of the master
scale = 1.0 / (1.0 - S_CAST)                 # S_CAST = 0.01 for Smooth-Cast 300
assert abs(MASTER_L - PART_L * scale) < 0.05
# rigid printed mould: draft on every pulled face
assert MIN_DRAFT_DEG >= 2.0
# every upward-facing local high point is vented
assert set(HIGH_POINTS) <= set(VENTED_POINTS), "a high point traps air"
assert CAST_WALL_MIN >= 2.0, "cast wall under 2 mm will not fill"
```
