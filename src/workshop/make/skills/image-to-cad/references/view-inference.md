# view-inference

Reconstructing the two views the photo does not show.

**Trigger:** You have fewer than three aligned orthographic views — i.e. almost
every real request. Load this before writing Step 4 of the spec.

A 3/4 hero shot is **one** viewpoint and lies about all three views. Recover
the missing views by reasoning from symmetry, function and height (the one axis
a photograph measures honestly), label the result `[inferred]` or `[assumed]`,
and write the reasoning into the spec, not just the conclusion.

The knowledge behind this file lives in the wiki:

- Diagnosing the shot, the 3/4 width/depth split, recovering the top view,
  occlusion as weak evidence: `skills/wiki/pages/image-reading/perspective-and-hidden-views.md`
  (`wiki show perspective-and-hidden-views`).
- The four ways a silhouette lies, per-view rulers, cross-check blind spots,
  mirror symmetry versus rotation: `skills/wiki/pages/image-reading/measuring-reference-photos.md`
  (`wiki show measuring-reference-photos`).
- Image kinds, what views four to six buy, ranking extra views, using several
  images together: `skills/wiki/pages/image-reading/image-types-and-views.md`
  (`wiki show image-types-and-views`).
- Profile shape → construction family: `skills/wiki/pages/image-reading/form-to-construction-family.md`
  (`wiki show form-to-construction-family`).

## Reading `measure_image.py` output

```bash
python <skill-dir>/scripts/measure_image.py hero.jpg
```

| Field | What it tells you | What to do with it |
|---|---|---|
| `aspect_w_over_h` | Silhouette bbox ratio | Your primary proportion. In a 3/4 shot the width is inflated by the rotated depth — see the width/depth split in the wiki. |
| `fill_ratio` | Silhouette area ÷ bbox area | ≈1.0 → solid blocky mass. 0.6–0.85 → tapered or shaped body. <0.5 → open frame, legs, handle, or a hollow silhouette. |
| `row_profile` | Silhouette **width** at each height, top→bottom, normalised to its max | The elevation taper signal. Drives the front/side construction family. |
| `col_profile` | Silhouette **height** at each column, left→right | Cross-checks the row reading and exposes asymmetric massing. |
| `row_shape` / `col_shape` | `flat` / `wide_start` / `wide_end` / `waisted` / `bulged` / `irregular` | Construction-family hint (wiki table). Names are relative to the profile index (rows run top→bottom, cols run left→right), never to a compass direction. |
| `row_bands` / `col_bands` | Contiguous runs of roughly constant width, as `{from, to, width}` fractions | **Where your loft stations and height bands go.** |
| `widest_at_height_frac` | 0.0 = widest at the top, 1.0 = widest at the bottom | Goes straight into the proportion ledger. |
| `symmetry.left_right` | Mirror IoU in [0,1] | >0.95 → bilateral symmetry `[observed]`. 0.8–0.95 → symmetric object shot slightly off-axis. <0.8 → asymmetric **or** strong 3/4 rotation; check which. |
| `symmetry.top_bottom` | Same, vertically | High values suggest a revolve about a horizontal axis, or a cropped symmetric detail. |

`row_shape` maps to a family as: `flat` → extrude; `wide_start`/`wide_end` →
tapered extrude or loft; `waisted`/`bulged` → revolve or loft; `irregular` →
loft over the stations `row_bands` just handed you.

### Tool switches when the silhouette lies

- **Busy background** (`fill_ratio` near 1.0, bbox covering most of the frame):
  crop to the object and re-run.
- **Shadow joined to the object:** shadow rejection is on by default (since
  v0.2); crop above the shadow on a miss. `--no-reject-shadow` restores the old
  behaviour and belongs only to a subject whose colour genuinely matches its
  ground.
- **Dark on dark, light on light** (error or nonsense bbox): try `--invert`,
  then `--threshold` between 12 and 45.
- Holes always come from your eyes.

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
   which you used; use detail shots for their feature only.

## Pitfalls

- Reading depth off a 3/4 shot and writing it as a hard dimension.
- Passing `--no-reject-shadow` out of habit.
- Trusting `cross_check` to catch shadow inflation.
- Asking for three more photos when the bottom view alone would answer.
- Reading a `--palette` cluster as a part.
- Concluding "asymmetric" from a low `symmetry.left_right` that is camera rotation.
- Presenting an `[inferred]` top view without its reasoning.
- Using `fill_ratio` from an uncropped photo.
- Averaging two disagreeing images instead of picking the better one and saying why.
