# Running the likeness gate

Read this file when writing the spec's verification checklist, so the handoff
to `cad` carries exact commands rather than a description of them.

**These are CAD-phase tools.** This skill produces a document; it renders and
scores nothing. What follows is documented here so the spec can name the
commands the build turn will run, and so the thresholds it sets are the ones
the gate actually measures.

The integrated final run — `verify_project --image-derived` — is the completion
gate and is in `SKILL.md`, Step 8. Everything below is the iteration loop that
leads up to it.

Why each rule below exists — what IoU and bands measure, why the camera is
searched, mirror-image models, masks that cannot hold a subject, filled
openings, clipped references — is in
`skills/wiki/pages/image-reading/silhouette-likeness.md` (`wiki show
silhouette-likeness`). Loop discipline, replay, sweep costs and reading a
parameter sweep: `skills/wiki/pages/image-reading/likeness-iteration.md`
(`wiki show likeness-iteration`).

```bash
python <skill-dir>/scripts/render_views.py <project-dir>/<name>.step.py \
    --match ref/03-side.png  --label side  --camera=0,0 \
    --match ref/02-front.png --label front --camera=-90,0 \
    --match ref/04-rear.png  --label rear  --camera=90,0 \
    --search-fov 0,25,40 -o snap
```

`--camera AZ,EL[,TOL]`, one per `--match` in order, is where each reference was
plainly taken from, in the renderer's frame: azimuth from +X toward +Y,
elevation from the XY plane, `front` looking from -Y at (-90, 0), `right` at
(0, 0), `iso` at (-45, 35). TOL defaults to 30 degrees. Use the `=` form, since
argparse reads a leading `-` as an option.

**Use `--match`, not `--view`, against a photograph.** `--match` searches the
pose space and scores with this gate's own `normalise`/`compare`, so it keeps
the pose that maximises the number the gate will print. Reserve `--view` for
the orthogonal set a human reviews, and for a reference that is itself an
orthographic drawing. Read the recovered angles it prints: a pose far from the
one the photograph shows is a finding, not a pass.

**`MASK SUSPECT`.** Any two references handed cameras within 20 deg of each
other whose own silhouettes score below IoU 0.85 stop the run — the same camera
cannot produce two different outlines, so a reference mask has failed.

**A reference of one part scores that part.** When the references are of the
separate pieces of a set rather than of the assembled whole, name the piece each
one shows in the handoff table; the CAD phase passes it to `verify_project` as
`--likeness-entry LABEL=part_<role>.step.py`, and the piece, not the combined
lineup, is rendered and scored.

### Declare the camera, or the gate cannot see handedness

`--camera` confines the search to the declared window, where the mirror pose
is out of reach, and then searches the model's two reflections inside that
window too. When a reflection beats the model by more than 0.02 the run fails
`HANDEDNESS SUSPECT` and names the axis:

    HANDEDNESS SUSPECT -- inside the declared camera window a reflection of the model fits the reference better than the model does:
      hero: model IoU 0.6443, mirrored in X 0.9918

That is a source fix (mirror across that axis), never a shape sweep. A
replayed pose (`--poses-from`) outside its declared window fails as well. A
`--match` without `--camera` still searches every azimuth and prints
`(no --camera: mirror-blind)`; `verify_project --image-derived` refuses a
`--likeness-ref` without one. Give the ledger one row that states a side.

### Flatten a reference the mask cannot hold — `ref_silhouette.py`

For a multi-colour object on a neutral ground (a studio render), flatten the
reference, then measure it with the unchanged instrument:

```bash
python <skill-dir>/scripts/ref_silhouette.py <project-dir>/ref/*.png
python <skill-dir>/scripts/ref_silhouette.py --self-check
```

It writes `<stem>-sil.png` beside each original and leaves the originals alone.
Point `--match` and the gate at the flattened files, and say in the README that
you did. It marks the file it writes, and `check_likeness.py` and
`render_views.py --match` fill the render's holes too when they see that mark,
so both sides are scored by one rule; every row then records `holes: filled`.
**Each enclosed opening then needs its own landmark-ledger row** (a count, a
clear width, a station). A reference without the mark keeps its holes compared
as they are. The script reports how far the new outline sits from the tool's
own mask over the rows a contact shadow cannot reach, and exits non-zero if the
outline moved — quote that report. It cannot handle a cluttered background.

A white subject on a pale sweep is the other way the mask fails: the ground is
brighter than the default band, so the band rule finds no ground and returns
the whole frame. `--ground auto` (the default) notices that the frame border is
not ground by the band rule and switches to the border rule, which separates
the two by the sign of their tint (a warm white against a cool grey). The
record names the rule that ran. When the tool's own mask sees under half the
flattened outline, the comparison is reported `not comparable` instead of
failing — look at the `-sil.png` yourself before scoring against it — and an
outline that reaches the frame edge always fails.

A coloured subject under a key light is the third: its contact shadow is darker
than any ground the band or border rule accepts, so both keep it, and so does
the default mask — every edge facing away from the light grows a crescent and
the model reads too thin. `auto` never picks the rule for this; pass
`--ground tint`, which calls a pixel ground by its low relative saturation
`(max - min) / max` at any brightness. Lay the `-sil.png` outline over the
photo before scoring: the shadow should sit outside it on every lower edge.
A grey, white or black subject has no tint, and the rule drops it.

### Score the pairs

`render_views.py` prints the command:

```bash
python <skill-dir>/scripts/check_likeness.py \
    --pair snap/side.png  ref/03-side.png  --label side \
    --pair snap/front.png ref/02-front.png --label front \
    --pair snap/rear.png  ref/04-rear.png  --label rear \
    --min 0.90 --report measure/likeness.md
```

It reports IoU per view plus twelve horizontal bands giving the model's width
as a fraction of the reference's. Quote the worst band and the edit it names.

**`--report` keeps its own history.** Every run appends one row per view to
`<report stem>-history.jsonl` and renders the last twenty into the report, with
a delta and a trend of `improving`, `regressing`, `stalled` or `first`. Read the
delta before editing again. Without `--report` there is no history, the delta
prints as `—`, and the run says so.

**The floor does not come down quietly.** Setting `--min` below 0.90 requires
`--accept-mismatch "<reason>"`, a `--report` for the reason to be written into,
and two earlier rounds already recorded **for each view being scored**, against
the same reference each was scored on; short of any of those the gate exits 2
rather than scoring.

**Final delivery never lowers the floor.** `verify_project --image-derived`
holds it at 0.90 and runs this gate raw, so `measure/likeness.md` keeps
recording the failure as a failure. `--likeness-accept-mismatch` changes the
*runner's* verdict rather than the score: it is accepted only for a view whose
history already shows it stalled out, the pipeline record marks that gate
`accepted-fail` and carries the reason in full. A delivery below 0.90 stays an
explicit acceptance of a measured failing result, never a lowered floor. Inside
a Workshop run the Workshop Manager makes it, with a written reason, and the
run reports every such acceptance to the person when it ends (ADR 0074); the
record never calls it a user's decision.

**A failing loop ends after three rounds that move nothing.** `stalled` or
`regressing` three times in a row for one view — an `improving` round resets
the count — makes the verdict `stalled out`. The exit stays non-zero; the gate
prints how many rounds the view has had, which run holds its best, what the
last three bought, and points at `verify_project --likeness-accept-mismatch`,
never at a lowered `--min`. Stop rendering and decide: accept with a reason
that names what the reference shows and why the geometry cannot follow it, or
keep the failure. In a Workshop run that acceptance is the Workshop Manager's
and is reported when the run ends (ADR 0074).

**The delivered round has to be the best round.** A run below the best that
view has ever recorded fails as `regressed-from-best` and the report names the
run to revert to. Overriding it costs `--accept-regression "<reason>"`
(`verify_project --likeness-accept-regression`), which needs a `--report` too.
In the history table the round to beat is marked `*`, and a run that clears the
floor but falls under it is reported as `regressed from best`.

**A whole-object reference must contain the whole object.** If its extracted
silhouette touches any image edge, `render_views.py --match` and
`check_likeness.py` refuse it. `--allow-clipped-reference` exists only for an
explicit partial-feature comparison, never to make a cropped whole-object view
count as a completion gate.

`render_views.py` draws nothing but the object, so there is no burnt-in view
label; the gate keeps only the largest connected blob as a second line of
defence.

### Replay the camera while editing

Every pose is recorded in `snap/poses.json`, and **`--poses-from` composes with
`--match`**: give it both and each reference is scored against its *stored*
camera instead of a fresh search, printing `(replayed camera -- not searched)`
on every line. **Search once, replay while you edit, search again at the end.**
Put every `--view` and every `--match` in one call; keep `--search-fov 0,25,40`
and `--compare-step` for the final measurement.

### A dimension no view measures — sweep it through the gate

Sweep one parameter at a time with everything else fixed, run `--match` and
`check_likeness` per value, and write the table into the spec beside the value
you took. How to read a peak, a plateau and a flat line is in the wiki page.

Read the score as a **floor on the disagreement, never a ceiling on quality**.
Treat 0.90 as the target, not the pass mark for an unreviewed first attempt.

## A reference with a transparent background

A cut-out PNG, or a WebP exported with alpha, states its own silhouette:
alpha above 127 is the subject, and the gate reads it exactly so. The
luminance threshold and the shadow test exist for photographs, which carry no
alpha; they are not applied to a cut-out, and neither is `--threshold`. An
image whose alpha channel is opaque everywhere says nothing and is scored as a
photograph. The reason this is spelled out: read through RGB, a cut-out is
whatever colour the encoder left under its transparent pixels, and one such
reference (2026-09-07, a wind-up duck) scored **0.66 against its own outline**,
so no model could have passed. `measure_image.py` reads the same alpha for
its measurements and says so in the mask notes (`"source": "alpha"`).

## A pale subject on a white ground

A cream or beige print photographed on a white sweep sits inside the
luminance band around the background, and its hue is only about 0.02 off
the ground in normalised rgb, below the 0.045 the shadow test needs. Read
that way the mask keeps the dark and saturated parts (beak, feet, shaded
coils) and drops the lit head and torso; one such reference (2026-09-08, a
cream goose) measured at fill 0.30 with its head missing, and every round's
IoU was a wall built from the mask, not the shape. CIELAB separates the two
cases: cream differs from white by about 10 in b*, while a neutral cast
shadow stays near 0 in a*b* however dark it gets. `measure_image.py` and the
gate therefore also admit a pixel as object when its a*b* distance from the
background is above 4, both inside the shadow test and, for regions inside
the luminance band, through the same attachment rule as the off-hue
admission: the region must touch the silhouette already found. A lighter
neutral patch (a lit tabletop) has no a*b* difference and stays ground; a
background-coloured aperture inside the subject matches the ground's a*b*
and stays open. The mask notes report it as `pale_region_share`. A subject
that is truly the ground's colour still has no silhouette to read; give the
gate a cut-out with alpha (previous section) instead.

## Replay, then search when the replay is under the floor

`--poses-from` replays the previous camera without searching, which is what
makes a round's IoU delta the shape's and not the viewpoint's. It also means
a part that moved (a neck that now leans, a head that turned) can only lose
under the old camera. The `make-round` skill therefore re-searches a
+/-30 degree window around the replayed camera whenever the replay scores
under the floor, and keeps the better of the two (goose, 2026-09-08: replay
0.49, window search 0.75 on the same model). The summary marks such a score
`(re-searched)`, and the new pose is what the next round replays.
