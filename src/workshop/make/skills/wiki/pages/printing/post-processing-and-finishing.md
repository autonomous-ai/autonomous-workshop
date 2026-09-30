---
title: Post-processing and finishing printed parts
tags: [post-processing, sanding, primer, paint, vapor-smoothing, epoxy-coating, dye, finish, masking]
aliases: [sanding 3d prints, filler primer, painting prints, acetone smoothing, vapour smoothing, vapor polishing, xtc-3d, epoxy coat, dyeing nylon, rit dyemore, polysmooth, surface finishing, grit sequence, masking]
sources:
  - https://www.hubs.com/knowledge-base/post-processing-fdm-printed-parts/ (grit ladder, wet sanding, primer and paint coats, vapour smoothing and dipping tolerances, epoxy coating, polishing and paint adhesion)
  - https://blog.prusa3d.com/postprocessing-of-3d-prints-step-by-step_29270/ (P100 then P400, body filler, filler spray primer)
  - Smooth-On XTC-3D technical bulletin, https://www.smooth-on.com/tb/files/XTC3D_TB.pdf (layer < 1/64 in, 60 °C cure, exotherm, compatible prints)
  - U-Pol HIGH#5 high-build primer TDS, https://u-pol.com/wp-content/uploads/HIGHW-TDS.pdf (about 45 µm build, 1–2 coats, sand P400–P600 dry / P600–P800 wet)
  - https://nonpaints.com/en/spraymax-1k-filler-primer-in-aerosol (aerosol filler primer 30–50 µm per coat, 2–3 coats; via search excerpt)
  - https://wiki.polymaker.com/printing-tips/post-processing/smoothing (acetone for ABS/ASA, IPA for PVB, cracking from over-exposure)
  - https://layercraftlog.com/filaments/can-i-use-acetone-vapor-to-post-process-abs-3d-prints-safely (0.1–0.3 mm redistribution, CMM shrinkage on cubes; via search excerpt)
  - https://www.sciencedirect.com/science/article/pii/S2588840426000120 (pure acetone gives pronounced corner rounding and dimension loss; via search excerpt)
  - https://facfox.com/docs/kb/the-best-paint-for-pla-petg-abs-nylon (paint per material, nylon dyed not painted)
  - https://www.matterhackers.com/articles/how-to-dye-nylon-3d-prints (synthetic dye, about 60 °C bath; via search excerpt)
  - https://www.xometry.com/resources/3d-printing/xtc-3d/ (epoxy coat adds about 0.2–0.5 mm; via search excerpt)
related: [fdm-surface-finish, adhesives-and-solvent-welding, colour-matching, form-and-finish-heuristics, fit-derivation, fdm-multi-material-design, sealing-and-ingress-protection, heat-resistance-of-printed-parts]
updated: 2026-09-23
---

# Post-processing and finishing printed parts

A finish either removes material (sanding, vapour smoothing) or adds it
(filler, primer, paint, epoxy). Both move every surface they touch. A fit
that `cadfits` derived for a bare print is wrong after finishing unless the
face was masked or the finish was put into the derivation. Decide the finish
per face before the fits are derived. This page covers what each step does to
geometry. What the slicer can do before any post-processing is in
[[fdm-surface-finish]].

## What each step does to a surface

Per-face change, positive = material added. These are ranges from vendor data
and hobby guides, not a measured process. Treat them as a budget, not a
prediction.

| step | per-face change | notes |
|---|---|---|
| sanding out layer lines | − about the layer-line depth, a fraction of one layer height | removes peaks; aggressive sanding costs accuracy (Hubs) |
| filler primer, aerosol | + 30–50 µm per coat, 2–3 coats (search excerpt); a high-build aerosol ≈ 45 µm build (U-Pol) | partly sanded back |
| colour paint | 2–4 coats until opaque (Hubs) | "Paint and primer add bulk … which will alter tolerances" (Hubs) |
| clear coat | one or more further coats | same budget as paint |
| two-part epoxy coat (XTC-3D type) | < 1/64 in (0.4 mm) per layer (Smooth-On); ≈ 0.2–0.5 mm total (search excerpt) | self-levels: thick in concave corners, thin on edges |
| acetone vapour (ABS/ASA) | 0.1–0.3 mm of surface redistribution (search excerpt) | outer dims shrink, holes close; corners round |
| solvent dip | uncontrolled | "tolerances will not be maintained" (Hubs) |
| dye (nylon) | none | but the part soaks up water and swells ([[moisture-and-drying#nylon-is-a-different-material-wet]]) |
| polishing compound | negligible | paint may not adhere afterwards (Hubs) |

A full primer + paint + clear system therefore adds on the order of
0.1–0.3 mm per face. A hole loses twice that on its diameter.

## Fits, threads and mating faces

- **Mask or re-derive.** Every face in the fit audit is either masked during
  finishing (tape, plug, a sacrificial pin in the hole) or its finish
  thickness goes into the fit. Diametral effect of a per-face change `t`:
  bore `d_eff = d − 2 t`, shaft `d_eff = d + 2 t`.
- **Threads cannot be finished.** Primer and paint fill the flanks of a
  printed thread ([[printed-threads]]); vapour smoothing rounds the crests.
  Mask them, or use a heat-set insert installed *after* finishing
  ([[heat-set-inserts]]).
- **Snap-fit undercuts and detents** change engagement by the coating
  thickness on both faces. Mask the hook face and the catch.
- **Sealing faces** must not be smoothed after a gland was sized
  ([[sealing-and-ingress-protection#making-the-printed-wall-itself-watertight]]).
- **Bond faces** are masked or sanded back to bare plastic: glue on paint is
  as strong as the paint's adhesion ([[adhesives-and-solvent-welding]]).
- **Sliding faces** keep their clearance only if both sides are masked or both
  are coated in the derivation; a coated and an uncoated face do not wear
  alike.

Design a masking edge: a step, groove or chamfer where finished and
functional surfaces meet, so tape has a line to follow.

## Detail loss and edge rounding

- Vapour smoothing and heavy epoxy coats round sharp edges and fill fine
  detail. Pure acetone gave "pronounced corner rounding and dimension loss" in
  one study (search excerpt). A layer-line texture is not fully masked either:
  vapour smoothing "will not heal gaps" (Hubs).
- Keep embossed or engraved detail deeper than the total finish build, with a
  margin. As a rule of thumb derived from the table: keep features on a
  smoothed or coated face at least ~3× the per-face change deep and wide.
- An epoxy coat pools in concave corners and pulls away from convex edges; a
  crisp inside corner becomes a fillet. Brush the coat on "a section at a
  time" for intricate prints (Smooth-On).
- If the design depends on a sharp edge, do not vapour-smooth it; sand and
  prime instead.

## Sanding

- Grit ladder: start at P100 (Prusa) to P150 (Hubs, for ≤ 0.2 mm layers),
  then 220 → 400 → 600, and 1000–2000 for a polished finish (Hubs). Prime,
  then sand the primer at P400 (Prusa); the high-build primer TDS gives
  P400–P600 dry or P600–P800 wet (U-Pol).
- Wet sand from start to finish to prevent friction heat (Hubs). PLA softens
  near 55–60 °C ([[heat-resistance-of-printed-parts#temperatures-per-material]]),
  so dry power-sanding smears it.
- Sand in small circles, clean between grits (Hubs).
- **Design for the sanding block:** finished faces flat or convex and
  reachable. A narrow recess or deep inside corner on a finished face cannot
  be sanded, so either keep it off the cosmetic surface or accept primer-only
  there.
- Use filler (body filler for large voids, epoxy for small, ABS slurry for
  ABS) before primer (Hubs, Prusa). Body filler dries opaque, so it must be
  painted over.

## Support scars and seams

Support-contact faces have the worst surface ([[fdm-surface-finish#which-faces-look-best]]).
A scar costs a sand + fill + prime cycle. Put supports on faces that are
hidden or will be painted anyway, never on a face that must stay bare
(a transparent or colour-matched face that will not be painted). A glued split
line is filled like a scar; plan it on an edge
([[form-and-finish-heuristics#seams-and-parting-lines]]).

## Smoothing per material

| material | smooths with | design consequence |
|---|---|---|
| ABS, ASA | acetone vapour (Polymaker: heated 65–75 °C for 1–3 min sessions, or cold vapour) | holes close, corners round; over-exposure can cause long-term cracking (Polymaker) and reduces strength (Hubs) |
| PVB (PolySmooth type) | isopropyl alcohol mist | for display parts; IPA-smoothed PVB loses strength and heat resistance (Polymaker) |
| PLA | THF or MEK per Hubs, "more difficult"; acetone does not smooth it ([[adhesives-and-solvent-welding#what-bonds-what]]) | treat PLA as sand/fill/prime or epoxy-coat only |
| PETG | no practical hobby solvent | sand, epoxy-coat or print it smooth |
| nylon | not smoothed; dyed | dye instead of paint |

If a smooth, glossy part is the requirement, choose ABS/ASA at the material
decision, not after printing.

## Epoxy coating

- XTC-3D type coats work on PLA, ABS, PETG, SLA and SLS prints (Smooth-On).
  Working time 10–20 min; tack-free about 2 h; one layer < 0.4 mm; recoat when
  "tacky hard" (Smooth-On).
- Smooth-On offers a 60 °C (150 °F) mild-heat cure. That is at or above PLA's
  HDT: cure PLA parts at room temperature.
- The coat carries no solvent, so it "does not melt plastic"; but mixed
  epoxy is strongly exothermic in mass, so spread it thin (Smooth-On).
- The coat hides layer lines under a shell; it does not remove them (Hubs).
- A thin epoxy coat changes tolerances little unless the part was sanded
  first (Hubs); still budget it on every coated fit.

## Paint adhesion and dye per material

| material | paint | notes |
|---|---|---|
| PLA | straightforward; spray primer then acrylic or spray paint (FacFox) | filler primer common |
| ABS, ASA | straightforward (FacFox) | scuff a smoothed or glossy face before priming |
| PETG | harder to get durable paint (FacFox); scuff and use a plastic primer or adhesion promoter (search excerpts) | consider printing in the final colour |
| nylon | paint adheres poorly; dye it with a synthetic-fibre dye (Rit DyeMore type) at about 60 °C, below the filament's HDT (FacFox, MatterHackers) | white or natural nylon dyes best |
| PLA, PETG, ABS | dye | negligible uptake; not a colouring route |
| any polished face | may reject paint (Hubs) | scuff before priming |

Clean with isopropyl alcohol and handle with gloves before priming (FacFox).
Colour naming and matching belongs to [[colour-matching]].

## Splitting for separate colours

- A hard colour boundary on one part needs a masking edge (step, groove or
  reveal). Masking tape along a smooth continuous surface bleeds.
- Cleaner: print each colour as its own part and paint it before assembly,
  splitting on an edge or reveal ([[form-and-finish-heuristics#seams-and-parting-lines]],
  [[fdm-joining-split-prints#where-to-cut]]).
- The joint between two painted parts carries paint on both faces: either
  mask the mating faces, or add `2 · t_finish` per mating pair into the slip
  clearance of the connector.
- Pegs and sockets that locate the split stay bare; paint in the socket makes
  a press fit out of a slip fit.
- Printing the colours instead avoids painting altogether:
  [[fdm-multi-material-design]].

## Safety

Solvent vapour (acetone, MEK, THF), epoxy and sanding dust need ventilation,
gloves and a respirator per the product's data sheet; acetone is highly
flammable (Polymaker, Smooth-On). This page does not give a process; read the
SDS. Finished parts for food or children: [[food-and-toy-safety]].

## Checks

```python
# per-face finish budget, mm (positive = added); illustrative values
t_primer, t_paint, t_clear, t_sanded = 0.10, 0.08, 0.04, 0.05
t_finish = t_primer + t_paint + t_clear - t_sanded
assert 0 <= t_finish <= 0.3, "finish build outside the researched range: re-check the process"

# a bore that is finished instead of masked must be derived with the finish in it
d_bore_model, d_pin, min_clear = 5.50, 5.00, 0.15   # 5.15 bare + 2 * t_finish
assert d_bore_model - 2 * t_finish - d_pin >= min_clear, "paint closes the running fit: mask the bore"

# embossed detail on a smoothed/coated face survives the finish
emboss_depth = 0.6
assert emboss_depth >= 3 * t_finish, "detail will fill in under the finish"

# every face in the fit audit has a declared finish treatment
fit_faces = {"bore_a": "masked", "thread_m3": "masked", "shell_outer": "painted"}
assert all(v in ("masked", "bare", "in-derivation") for k, v in fit_faces.items() if k != "shell_outer")
```
