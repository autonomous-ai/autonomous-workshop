# view-inference

Reconstructing the two views the photo does not show.

**Trigger:** You have fewer than three aligned orthographic views — i.e. almost
every real request. Load this before writing Step 4 of the spec.

## Why this exists

A 3/4 hero shot is **one** viewpoint. It shows you the front, the side, and the
top all at once, and it lies about all three: each is foreshortened by an
unknown amount and rotated by an unknown angle. The failure this document
prevents is reading a depth straight off a hero shot, writing it into the spec
as a dimension, and delivering a part that is visibly too shallow.

You cannot recover the missing views by looking harder. You recover them by
**reasoning from symmetry, function, and the one axis the image measures
honestly** — then labelling the result `[inferred]` or `[assumed]`.

## Reading `measure_image.py` output

```bash
python <skill-dir>/scripts/measure_image.py hero.jpg
```

| Field | What it tells you | What to do with it |
|---|---|---|
| `aspect_w_over_h` | Silhouette bbox ratio | Your primary proportion. In a 3/4 shot the width is inflated by the rotated depth — see the correction below. |
| `fill_ratio` | Silhouette area ÷ bbox area | ≈1.0 → solid blocky mass. 0.6–0.85 → tapered or shaped body. <0.5 → open frame, legs, handle, or a hollow silhouette. A low fill ratio on an object you assumed was a solid box means you misread the object. |
| `row_profile` | Silhouette **width** at each height, top→bottom, normalised to its max | The elevation taper signal. Drives the front/side construction family. |
| `col_profile` | Silhouette **height** at each column, left→right | Cross-checks the row reading and exposes asymmetric massing. |
| `row_shape` / `col_shape` | `flat` / `wide_start` / `wide_end` / `waisted` / `bulged` / `irregular` | Direct construction-family hint — see the table below. Names are relative to the profile index (rows run top→bottom, cols run left→right), never to a compass direction. |
| `row_bands` / `col_bands` | Contiguous runs of roughly constant width, as `{from, to, width}` fractions | **Where your loft stations and height bands go.** A band boundary is the image telling you the section changed character. |
| `widest_at_height_frac` | 0.0 = widest at the top, 1.0 = widest at the bottom | Goes straight into the proportion ledger. |
| `symmetry.left_right` | Mirror IoU in [0,1] | >0.95 → treat bilateral symmetry as `[observed]` and mirror the unobserved half. 0.8–0.95 → symmetric object shot slightly off-axis. <0.8 → genuinely asymmetric, **or** a strong 3/4 rotation. Check which before concluding. |
| `symmetry.top_bottom` | Same, vertically | Rarely 1.0 for a real object; high values suggest a revolve about a horizontal axis, or that you cropped a symmetric detail. |

### shape → construction family

| `row_shape` | Elevation reads as | Author the body as |
|---|---|---|
| `flat` | Constant width up the height | Extrude |
| `wide_start` / `wide_end` | Linear taper | Tapered extrude (`taper=`) if the section stays similar; loft if the section *shape* also changes |
| `waisted` | Narrow in the middle | Revolve (if `symmetry.left_right` > 0.95 and the plan is round) or loft |
| `bulged` | Fat in the middle | Revolve or loft |
| `irregular` | Character changes more than once | **Loft over the stations `row_bands` just handed you** |

Two independent readings agreeing is your confirmation: if `row_shape` says
`waisted` and the object also looks rotationally symmetric, a revolve is almost
certainly right. If they disagree, the silhouette is being confused by the
background — say so and fall back to your eyes.

### When the silhouette lies

`measure_image.py` sees an outline, not an object. It will mislead you when:

- **The background is busy.** A cluttered photo yields a mask full of
  background. Symptom: `fill_ratio` near 1.0 with a bbox covering most of the
  frame. Crop to the object and re-run.
- **A hole reads as solid.** A through-hole is inside the silhouette, so the
  tool cannot see it. Holes always come from your eyes.
- **A shadow joins the object.** Handled since v0.2: the tool requires an
  object pixel to differ from the background in *chromaticity*, or to be far
  too dark or too bright for a shadow to explain, because dimming a surface
  scales all three channels together and leaves its chromaticity untouched.
  It still fails on a subject whose colour genuinely matches its ground, and on
  a coloured bounce-light spill. Symptom of a miss: the bottom band is wider
  than the object visibly is, `symmetry.left_right` well below what the object
  looks like, and `widest_at_height_frac` dragged toward 1.0. Crop above the
  shadow. `--no-reject-shadow` restores the old behaviour.
- **A dark object on a dark ground, or light on light.** Symptom: an error, or a
  nonsense bbox. Try `--invert`, then `--threshold` between 12 and 45.

## Correcting for perspective

**Diagnose the shot first.**

| Symptom | Shot type | Correction |
|---|---|---|
| Vertical edges stay parallel; the top face is a thin sliver | Near-orthographic, long lens | None needed. Proportions are trustworthy. |
| Vertical edges converge slightly toward the top | Mild perspective | Measure ratios at the object's **mid-height** where distortion is least. Accept ±10%. |
| Vertical edges converge strongly; near corner much larger than far | Wide-angle, close | Ratios off the image are unusable for depth. Use function and symmetry instead; tag depth `[assumed]`. |
| Two vanishing directions visible on the top face | 3/4 view | Apply the width/depth split below. |

**The 3/4 width/depth split.** In a 3/4 shot the silhouette width is *not* the
object's width — it is the sum of the projected width and the projected depth:

```
silhouette_width ≈ W·cos(θ) + D·sin(θ)
```

where θ is the rotation away from face-on. You do not know θ, W, or D — three
unknowns, one equation. So do not solve it. Instead:

1. **Take height as your honest axis.** Height is unaffected by rotation about
   the vertical axis, so `bbox_px.h` is your most reliable measurement and the
   best thing to anchor scale to.
2. **Read W and D from the visible face edges, not the silhouette.** Find the
   front face's own left and right edges in the image and measure between them;
   do the same for the side face's near and far edges. These are still
   foreshortened, but each is now a single face rather than a sum.
3. **If you can see the top face's corner angle**, the near corner of a
   rectangular top reads as ~90° only face-on. A visibly obtuse near corner
   means significant rotation — trust the height, tag the depth `[assumed]`.
4. **Round to a plausible proportion.** Most product depths land on a simple
   ratio of the width: 1.0 (square plan), 0.75, 0.6, or 0.5. Pick the nearest
   one that the image does not contradict, state the ratio in the ledger, and
   tag it `[assumed]`. A stated ratio the user can correct in one edit beats a
   false precision like "62.4 mm".

## Recovering the top view

The plan is the view a hero shot hides most thoroughly, and the one that decides
whether the body is a plain `extrude()` or a sketched profile. In priority
order:

1. **Rotational symmetry.** If the front and side silhouettes have the same
   outline, and any horizontal feature reads as an ellipse, the plan is a
   **circle** — `[inferred]`, high confidence. Author as a revolve.
2. **Bilateral symmetry.** `symmetry.left_right` > 0.95 gives you one mirror
   plane. It fixes the plan's symmetry axis but not the depth.
3. **The visible top face.** If any part of the top is visible, its outline —
   however foreshortened — tells you the plan's *shape class*: rounded
   rectangle vs circle vs racetrack vs freeform. Shape class is `[inferred]`
   with confidence; the depth number is not.
4. **Function.** A base must support the mass above it: the plan must be at
   least large enough that the centre of mass sits inside the footprint.
   A shelf's depth is set by what it holds. A grip's plan is set by a hand.
5. **Archetype default.** Failing all of the above, use the archetype's usual
   plan proportion, tag it `[assumed]`, and put it in the Assumptions list.

Write the reasoning into the spec, not just the conclusion:

> Top view `[inferred]` — front and side silhouettes match to within 4% and the
> shade's lower rim reads as an ellipse, so the plan is circular. Ø `[inferred]`
> 180 mm from the front view's max width. The base plate's plan is `[assumed]`
> circular and coaxial; nothing in the image contradicts it.

## Multiple images

When the user attaches several images, **reconcile before you spec**:

1. Label each with a canonical view name and run
   `measure_image.py a.png b.png c.png --views top,front,side`. The names matter:
   `top`/`bottom`/`plan` measure L×W, `side`/`left`/`right`/`profile` measure
   L×H, `front`/`back`/`rear` measure W×H. Any other label is skipped by the
   cross-check.
2. **Read `cross_check` first.** It solves L : W : H over every named view at
   once and gives `per_view_disagreement_pct`. Under ~5 % the images share one
   camera scale. Above it, the offending view is named for you — drop it rather
   than normalising around it.
3. Where two images disagree on a feature, the more orthographic one wins. Say
   which you used.
4. A detail shot or close-up is worth more than a hero shot for one specific
   feature and worth nothing for overall proportion. Use each for what it
   measures well and say so.

### What views four to six actually buy

The outline is solved at three orthographic views. Beyond that:

- **Redundancy.** With six views each dimension is constrained four times
  instead of twice, so `cross_check` stops being a single closure test and
  becomes a real outlier detector — one bad photo is *identifiable*, not just
  detectable.
- **Hidden surfaces.** The bottom view is the only sight of the underside; a
  spec written without it has an invented base, sill and fastener pattern. The
  back view is the only clean read of the rear face and of anything the side
  view showed edge-on.
- **A null result on symmetry.** The opposite side view usually adds nothing to
  a bilaterally symmetric object — `symmetry.left_right` already said so. Ask
  for it only to rule out an asymmetric feature you suspect.

What they do **not** buy is scale. Six views of an unlabelled object still give
only ratios. See Step 3's anchor list.

## Pitfalls

- Reading depth off a 3/4 shot and writing it as a hard dimension.
- Passing `--no-reject-shadow` out of habit and letting a contact shadow back
  into the silhouette.
- Trusting `cross_check` to catch shadow inflation. It cannot — a shadow grows
  every view by roughly the same proportion, so the views agree with each other
  while all of them are wrong together.
- Asking the user for three more photos when the bottom view alone would have
  answered the question.
- Reading a `--palette` cluster as a part. It is a colour: gloss splits one
  paint into a lit and a shaded cluster, and two unrelated black components
  land in the same one.
- Concluding "asymmetric" from a low `symmetry.left_right` that is actually just
  camera rotation.
- Presenting an `[inferred]` top view without the reasoning that produced it.
- Using `fill_ratio` from an uncropped photo.
- Averaging two disagreeing images instead of picking the better one and saying
  why.
