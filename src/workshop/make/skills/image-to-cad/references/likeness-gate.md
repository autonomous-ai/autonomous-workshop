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

```bash
python <skill-dir>/scripts/render_views.py <project-dir>/<name>.step.py \
    --match ref/03-side.png  --label side \
    --match ref/02-front.png --label front \
    --match ref/04-rear.png  --label rear \
    --search-fov 0,25,40 -o snap
```

**Use `--match`, not `--view`, against a photograph.** A photo has an unknown
azimuth, elevation and focal length; an orthographic render compared against
one taken 15 degrees off will miss 0.90 however right the model is, and what
you would then be measuring is how well you guessed the camera. `--match`
searches the pose space and scores with this gate's own `normalise`/`compare`,
so it keeps the pose that maximises the number the gate will print. Measured on
a perspective reference: the same model scored **0.865 with a fixed
orthographic camera and 0.974 with the camera searched**. Reserve `--view` for
the orthogonal set a human reviews, and for a reference that is itself an
orthographic drawing.

It prints the recovered angles, and they are worth reading. A pose far from the
one the photograph plainly shows is a finding, not a pass: the search has found
the best available fit to a shape that is wrong somewhere else.

**And when the search recovers nearly the *same* pose for viewpoints that are
plainly different, the finding is in the reference, not the model.** That is the
tell for a mask failure: the search is fitting the reference's holes rather than
its outline, and no amount of shape work will move it.

`render_views.py` now **fails on that tell** rather than leaving it to be read.
Any two references handed cameras within 20 deg of each other whose own
silhouettes score below IoU 0.85 are a contradiction — the same camera cannot
produce two different outlines — and the run stops with `MASK SUSPECT`. On the
reference set that prompted this, the raw images fail with

    front and hero: cameras agree to 15.0 deg, yet their own silhouettes score IoU 0.6699
    hero and iso:   cameras agree to 18.75 deg, yet their own silhouettes score IoU 0.6413

reporting IoU 0.787 / 0.777 / 0.788, while the flattened ones pass silently at
0.950 / 0.859 / 0.860 with cameras 52 deg apart. The warning is what a whole
round of shape sweeps used to cost.

### Flatten a reference the mask cannot hold — `ref_silhouette.py`

Both the gate and `measure_image.py` pull the reference silhouette out with one
luminance threshold around an estimated background, plus a *chromatic* shadow
test. A studio render of a **multi-colour object on a neutral ground** defeats
that from both sides at once, and neither side announces itself:

- at the default threshold the mask punches **holes** in the object — every
  region whose luma sits inside the threshold band goes: a white shaft end, a
  signature, the specular highlight on a bore wall or a barb. The reference
  then measures 10–26 % holey and the model is scored against a perforated
  target;
- lower the threshold and the holes close, but the soft **cast shadow** comes
  in — shadow rejection is chromatic, so on a grey object over a grey ground it
  has nothing to work with, and the shadow adds material under the subject that
  reads as *the model is too small*.

Measured on one such reference set, on geometry that did not change between the
three columns:

| reference | mask @28 | mask @14 | flattened |
|---|---|---|---|
| front | 0.784 | 0.849 | **0.945** |
| hero | 0.787 | 0.787 | **0.916** |
| iso | 0.787 | 0.809 | **0.890** |

That is the difference between "this model is 20 % wrong" and "this model is
right", reported by the same gate about the same solid — and the pose search
had been landing 17° from the true camera the whole time.

The remedy is the one this skill already prescribes for line art: **make the
reference measurable, then measure it with the unchanged instrument.**

```bash
python <skill-dir>/scripts/ref_silhouette.py <project-dir>/ref/*.png
python <skill-dir>/scripts/ref_silhouette.py --self-check
```

It writes `<stem>-sil.png` beside each original and leaves the originals alone.
The rule knows nothing about the model — *ground-like* pixels (low saturation,
mid luminance) **connected to the frame border** are background, everything
else is object, holes filled. A cast shadow is ground-like and reaches the
border, so it goes; a specular highlight is ground-like but enclosed, so it
stays. Nothing is drawn, moved or smoothed.

Then point `--match` and the gate at the flattened files, and say in the README
that you did. The script reports how far the new outline sits from the tool's
own mask over the rows a contact shadow cannot reach, and exits non-zero if the
outline moved — that report is what makes this a measurement rather than a
retouch, so quote it.

It cannot separate a subject from a *cluttered* background: the whole rule rests
on the ground being one flat colour, which is what a render gives you and a
photo in the wild does not.

Then run the gate on the pairs it wrote — `render_views.py` prints the command:

```bash
python <skill-dir>/scripts/check_likeness.py \
    --pair snap/side.png  ref/03-side.png  --label side \
    --pair snap/front.png ref/02-front.png --label front \
    --pair snap/rear.png  ref/04-rear.png  --label rear \
    --min 0.90 --report measure/likeness.md
```

It normalises both silhouettes to a common height — height only, so the aspect
ratio stays in the comparison — and reports IoU per view plus twelve horizontal
bands giving the model's width as a fraction of the reference's. **The bands
are the point.** An IoU says the model is wrong; a band ratio of 0.39 at 0.83
from the top says the model is 60 % too narrow near its base, which is one
edit, not an afternoon.

**`--report` keeps its own history, and that is what makes the edit loop
converge.** The report file is rewritten in full on every run, so each round
used to erase the previous number and the only question that matters between
rounds — *did that edit help?* — had no answer on disk. Every run now also
appends one row per view to `<report stem>-history.jsonl` and renders the last
twenty into the report, with a delta and a trend of `improving`, `regressing`,
`stalled` or `first`. Read the delta before editing again: a round that moved
the number down is a round to revert, and a run of `stalled` means the edits
are not reaching the shape the gate measures. Without `--report` there is no
history, the delta prints as `—`, and the run says so.

**The floor does not come down quietly.** Setting `--min` below 0.90 requires
`--accept-mismatch "<reason>"`, a `--report` for the reason to be written into,
and two earlier rounds already recorded **for each view being scored**, against
the same reference each was scored on; short of any of those the gate exits 2
rather than scoring. The count is per view because rounds spent on one
viewpoint say nothing about a viewpoint being scored for the first time, and a
history counted in bulk would let the second ride in on the first's rounds. The reason this is a hard stop and not
advice: below the floor every round exits 1 and prints the same verdict, so the
cheapest way to change the output is to lower the floor — which measures
nothing and reads, in the record, exactly like a pass. A recorded acceptance is
a decision; `--min 0.00` is a missing one. And an acceptance recorded on run 1
is not even that: nothing had tried to fix the mismatch yet.

That is iteration only, and it is not how a mismatch reaches delivery.
**Final delivery never lowers the floor.** `verify_project --image-derived`
holds it at 0.90 and runs this gate raw, so `measure/likeness.md` keeps
recording the failure as a failure. What `--likeness-accept-mismatch` changes
there is the *runner's* verdict rather than the score: it is accepted only for
a view whose history already shows it stalled out, the pipeline record marks
that gate `accepted-fail` and carries the reason in full, and the run is then
allowed to finish. So the two files say different things on purpose — the
likeness report is the measurement, the pipeline record is the decision. A
delivery below 0.90 stays what `CLAUDE.md` calls it: an explicit human
acceptance of a measured failing result.

**A failing loop ends after three rounds that move nothing.** `stalled` or
`regressing` three times in a row for one view — an `improving` round resets
the count — and the verdict becomes `stalled out`. The exit stays non-zero,
because the shape has not changed and neither should the answer; what the gate
swaps is the instruction. It prints how many rounds the view has had, which run
holds its best, and what the last three rounds bought in total — then points at
the **delivery** decision, `verify_project --likeness-accept-mismatch`, and
deliberately not at a lowered `--min`. A stalled loop being told to lower its
own floor is how the number stops meaning anything, so the stalled path never
suggests it. That decision is the user's: below 0.90 only an explicit human
acceptance of a measured failing result can ship, so an agent's job at this
point is to stop rendering and ask.
Without a stopping condition the alternative is what this gate was built after
— rounds of rendering that left one number on disk.

**The delivered round has to be the best round.** A run scoring below the best
that view has ever recorded fails as `regressed-from-best`, however far above
the floor it lands, and the report names the run to revert to. Against the
floor alone this is invisible: every round between the floor and 1.0 prints
`ok`, so a loop can wander downhill and deliver a worse shape with a passing
gate.
Overriding it costs `--accept-regression "<reason>"`, and `verify_project`
mirrors that one as `--likeness-accept-regression`. That waiver needs a
`--report` too: the best it would override lives in that report's history, so
without one it would read like a recorded decision and do nothing. In the
history table the round to beat is marked `*`, and a run that clears the floor
but falls under it is reported as `regressed from best` rather than as below
target — the verdict names the mark that was actually missed.

**A whole-object reference must contain the whole object.** If its extracted
silhouette touches any image edge, `render_views.py --match` and
`check_likeness.py` refuse it: height normalisation would otherwise turn a
clipped top or base into a false shape defect, and camera search would optimise
against the crop. Keep that frame as qualitative evidence and select a complete
view for the numeric gate. `--allow-clipped-reference` exists only for an
explicit partial-feature comparison; it is not a way to make a cropped
whole-object view count as a completion gate.

`render_views.py` draws nothing but the object, so there is no burnt-in view
label — a chip like "ISO" is object to any threshold and stretches the bounding
box to the frame edge, which scored one early front view at IoU 0.10 with the
model blameless. The gate keeps only the largest connected blob as a second
line of defence.

Every pose is recorded in `snap/poses.json`, and **`--poses-from` composes with
`--match`**: give it both and each reference is scored against its *stored*
camera instead of a fresh search. That is what makes the iteration loop honest —
the IoU delta between two runs belongs to the shape, because the camera did not
move — and it is also almost the whole cost of the command. Measured on a
six-part model, three references, `--search-fov 0,25,40`:

| the same command line | time | IoU |
|---|---|---|
| searching | **59.2 s** | 0.954 / 0.914 / 0.891 |
| `--poses-from snap/poses.json` | **7.8 s** | 0.954 / 0.914 / 0.891 |

Identical numbers, 7.6× faster, and the output says `(replayed camera -- not
searched)` on every line so a replay is never mistaken for a search. So the
sweep loop is: **search once, replay while you edit, search again at the end** —
the last search matters because a big shape change moves the best pose with it.

Two more costs worth knowing before a sweep, from the same model:

- **The build123d import is 5.2 s of every invocation** and a whole render is
  6.3 s. Twenty-five separate calls during one sweep spend 2 minutes on nothing
  but imports; put every `--view` and every `--match` in one call.
- **`--search-fov 0,25,40` costs 2.6×** what a single FOV does (23.1 s vs
  13.1 s for one reference). It is for the final measurement against a
  perspective reference, not for the loop. `--compare-step` adds 5.6 s and
  belongs only in the final run.

### A dimension no view measures can still be measured — through the gate

Three-quarter views constrain depth only weakly and a single front view not at
all, so the axial chain of a reconstruction is usually the one number left as
`[assumed]`. It does not have to be. `--match` searches the camera and
`check_likeness` scores the silhouette, so **sweeping one parameter and reading
the IoU is a measurement against the references**, not a guess — and it is cheap,
because after the first tessellation each searched pose costs ~20 ms.

Sweep one parameter at a time with everything else fixed, and write the table
into the spec beside the value you took:

| `CHAMBER_L` | front | hero | iso |
|---|---|---|---|
| 17.5 | 0.948 | 0.908 | 0.876 |
| 22.5 | 0.951 | 0.913 | 0.882 |
| **26.0** | 0.945 | **0.916** | **0.890** |
| 34.0 | 0.951 | 0.914 | 0.892 |

Read the *shape* of the curve, not just its maximum. Two outcomes matter as much
as a peak:

- **A plateau** means the references stop constraining the parameter there. Take
  the low end of the plateau and say the constraint is weak — a value picked
  from the far end of a flat region is `[assumed]` wearing a measurement's
  clothes.
- **A flat line** means the feature is invisible from every reference angle, and
  then **do not claim it**. On the pump above, a conical rear from Ø80.5 down to
  Ø50 moved the 3/4 silhouettes by 0.4 % of their area and the IoU by less than
  0.001 — the cover lugs and the barbs set the envelope and the rear sits inside
  it. A shape the references cannot see is not evidence for a feature, and
  modelling one anyway is invention with a number attached.

Read the score as a **floor on the disagreement, never a ceiling on quality**:
it is blind to colour, and on a multi-material reference colour is much of what
a human compares.

Treat 0.90 as the target, not the pass mark for an unreviewed first attempt.
