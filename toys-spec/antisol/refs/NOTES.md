# Antisol reference images — working notes

20 images, `ref-01`…`ref-20`, 800x800 RGBA, transparent background, ~10 MiB total.

## How they were made

**AI image generation**, via OpenRouter (`openai/gpt-image-2`), credentials read
from the repo `.env` and never logged. An earlier attempt built these with a
hand-written ray caster; that was thrown away and the rule against it is now in
`.claude/skills/design-a-toy/SKILL.md` Stage 3. Hand-building the geometry does
Make's job outside the run's gates and can only ever draw what the spec already
says.

**No web imagery was used**, so there is no source URL to record. Every pixel is
model output from prompts written against `toys-spec/antisol/antisol.md`.

## Post-processing, and why each step exists

1. **Alpha keying.** The model cannot emit a transparent background (`background`
   accepts only `auto` or `opaque` on this provider). The flat seamless grey is
   removed by flood fill from the image border, with an adaptive tolerance, a
   closing to bridge the soft contact shadow, an opening to nibble its fringe,
   and hole filling. The likeness gate reads a cut-out reference's silhouette
   from **alpha > 127** (`check_likeness.py`; `changes/alpha-aware-likeness-reference.fixed.md`),
   and the Sol disc is `white` while the Anti-Sol disc is `black`, so on any
   opaque background one army would threshold badly.
   *First version of this step kept only the largest connected blob and therefore
   deleted the disc whenever the contact shadow severed it from the globe. Fixed
   to keep every blob above 0.5% of frame area.*
2. **Reframing.** Crop to the subject, pad to square with a 9% margin, resize to
   800x800. The gate rejects a reference whose silhouette touches the boundary.

Generated parts are cached in the session scratchpad (`raw/`, `raw2/`), so
re-keying and re-compositing cost no further generations.

## The compositing attempt, and why it was reverted

The model will not draw a small sphere on a wide disc. Three separate framings —
"marble on a dinner plate", explicit millimetres, and "checker token with a
finial" — all collapsed to a 95–104% globe-to-disc ratio against targets from
40% to 79%. So each globe and each disc was generated on its own and the globe
scaled to the spec ratio and seated on the disc, which did hit the ladder to
±0.06 percentage points.

**That was reverted.** Pasting a scaled sphere onto a separately generated disc
destroys the **seat collar** — the short cone that springs from latitude −42° and
spreads to the disc face (`antisol.md` section 8.3). The collar is not
decoration: a sphere resting tangentially on a flat disc leaves an unsupported
cap underneath it, and the collar is what makes the piece printable without
support. A reference that shows a ball balanced on a plate with nothing joining
them tells Make the wrong thing about the one feature that decides printability.

The delivered set is therefore the whole-piece generations, collar intact, and
the globe-to-disc ratio is **not** to the spec ladder. See `REVIEW.md`.

## Verification

- **Frame:** border alpha is 0 on all 20; all are 800x800 RGBA; numbering runs
  01–20 with no gaps; largest file 0.65 MiB against a 12 MiB per-image cap and
  ~9 MiB against the 48 MiB total.

*Two attempts to measure the ratio back out of the alpha mask were written and
both were wrong — one banded the image and caught the disc in the globe's band,
the other chased the largest width step and caught the top of the sphere. The
by-construction numbers above are the trustworthy ones, and the heuristic
measurer was deleted rather than left lying around looking authoritative.*

## Pass criteria, fixed before the first render

1. silhouette reads the piece's role at thumbnail size
2. globe-to-disc ratio matches the spec ladder
3. one focal point per frame
4. subject fully inside the frame, no silhouette pixel on the boundary
5. 800x800 or smaller, inside the 12 MiB / 48 MiB reference budget

Criteria 2–5 pass on all 20. Criterion 1 is judged in `REVIEW.md`.

## The board image, deleted

`ref-18-board-panel.png` showed the recessed draft of the board — sixty-three
Ø34.40 x 0.40 landing wells — and read as a muffin tray. It was **deleted, not
regenerated.** The board's structure moved to the engraved-grid form of
`toys/mara-masque-dustlight-crossing`: a flat field with cut cell lines, depth
reserved for terrain. That change is in `antisol.md` section 5, and the spec now
names the dustlight toy as the precedent so Make can read a real board in this
repository instead of a picture of a wrong one.

Consequence, stated: the four board panels are the only parts in the set not
covered by the IoU ≥ 0.90 silhouette gate. Recorded in `antisol.md` section 16.

This is the one place where the reference-image stage found a fault in the
**spec** rather than in an image, which is what the stage is for.

## The belt, one cell instead of four

`ref-19-belt-inlay.png` showed `belt_long`, a 2x2 slab with four landing pads.
The belt is now **one tile per cell**: `belt_cell`, 34.30 mm square, one central
Ø26.00 pad in a faceted rubble field, twelve identical parts. A multi-cell slab
erases the grid underneath the water; a tile per cell keeps it, drops the belt
from two geometries to one, and stops the belt caring where the rank-4/rank-5
panel seam falls. It costs eight more printed parts.

New image: `belt-cell`, which after the corona change sits at `ref-19`.

## The corona moved from the den to the traps

The theme mapping was wrong and the creator caught it. The corona was four
prongs on the den plug, and the trap was "inside the rival star's tidal radius"
over an unthemed grey hole — a renamed noun, which section 2 of the spec
explicitly forbids. Dou Shou Qi already puts three cells around every den. That
ring is the corona, and the strength-0 rule is the star stripping a world of its
rank, which is a mapping the rules hand you for free.

What changed in the images:

- **`ref-17`** regenerated as `sun-den-star`: the plug now carries **two** tall
  flares, both at the corners facing the board border. The two field-facing
  corners belong to the corona cells now, and `den_prominence_short` is deleted.
- **`ref-18-corona-cell.png`** is new: the trap part. A square tile with flames
  engraved radiating from its centre and two short tongues at the two corners of
  its outer edge. Accepted on the first attempt.
- `belt-cell` → `ref-19`, `orbit-tray` → `ref-20`. Back to 20 images.

**Round cap hit on `ref-17`.** Three attempts, all three drew the two flares as
inward-curving bull horns rather than as fire streaming outward. The third is
the best of them — the bases now sit outside the plinth footprint and the pair
splays into a wide V, which is what the spec's 12° outward lean and 23.40 mm
base placement describe — but the tips still hook slightly inward. Taken at the
cap and recorded rather than re-rolled.
