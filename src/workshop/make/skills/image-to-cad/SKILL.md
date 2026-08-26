---
name: image-to-cad
description: Turn a reference image (photo, render, screenshot, sketch, or orthographic drawing) into a structured, buildable CAD spec — overall read, top/front/side views, real-world size, part and feature decomposition, per-feature detail, and the exact build123d operation each feature is built with. Use when the user attaches an image and wants a 3D model, a printable part, "make this", "recreate this in CAD", or asks how an object would be modelled. Produces the spec that the `cad` skill implements; it writes no geometry itself.
---

# image-to-cad — read a reference image into a buildable CAD spec

## Purpose

A reference image is the densest brief a user can give and the easiest to
misread. This skill converts one (or several) images into a **build spec**: a
document precise enough that the `cad` skill can write `<name>.step.py` and
its `gen_step()` straight from it, with no second look at the photo.

**You produce a document, not geometry.** No `.py`, no STEP, no STL. The
deliverable is the spec in `templates/build_spec.md`, which hands off to
`cad`.

The spec has seven sections, in this order, and an eighth when the object
moves under power:

1. **Overall read** — what the object is, its archetype, its construction family.
2. **Top view** (plan, looking down −Z).
3. **Front view** (elevation, looking along +Y).
4. **Side view** (elevation, looking along +X).
5. **Size** — real-world dimensions in mm, with the scale anchor that produced them.
6. **Decomposition** — printed parts, the standard elements sourced from a
   catalog, then the feature tree inside each.
7. **Per-feature detail + build123d operation** — one row per feature: geometry,
   numbers, the exact API call, the plane/selector it runs on, boolean order.
8. **Mechanism** — *only when a part is driven*: the archetype, the drive, the
   kinematic parameters, the feasibility assertion, and the motion conditions.

## The one rule that makes this skill work

A single photo shows you **one** viewpoint. The other two views are not in the
image — you reconstruct them. Say so, every time, per fact:

| Tag | Meaning | Allowed to become a hard dimension? |
|---|---|---|
| `[observed]` | Directly visible and measurable in the image | Yes |
| `[inferred]` | Not visible, but forced by symmetry, function, or another observed fact — state the reasoning | Yes, with the reasoning shown |
| `[assumed]` | Neither visible nor forced; a default you chose | Yes, but flagged in the Assumptions list as user-correctable |

Every number in the spec carries one of these three tags. An untagged number is
a defect. **A confident guess presented as a measurement is the single failure
mode this skill exists to prevent** — it is invisible until the user holds a
printed part that is 30% too small.

Never write "roughly", "about", "approximately". If you do not know a value,
derive it (Step 3), or tag it `[assumed]` and give the user the one line they
would edit to fix it.

## The loop

```
triage image(s) → measure pixels → anchor the scale → build 3 views
       ↑                                                    ↓
       └──── revise ←── check ledger + self-critique ←── decompose → map to build123d
```

You close this loop before the user sees anything. The check step is Step 7.

## Before the first run

Resolve the exact materialized skill trees instead of assuming an upstream
repository checkout:

```bash
IMAGE_TO_CAD_SKILL_ROOT="$(workshop skills path)/image-to-cad"
DESIGN_REFERENCE_SKILL_ROOT="$(workshop skills path)/design-reference"
```

The measuring scripts need `pillow`, `numpy` and `scipy` — `requirements.txt`
beside this file. They write no geometry, so build123d, OCP and `cadgen` are
*not* needed to measure an image. `render_views.py` is the one exception: it
builds the model in order to photograph it, so it needs the kernel, and that
import is 5.4 s of the ~7 s a render costs.

```
measure_image.py    pixels to ratios, and the cross-check gate  (step 2)
grid_overlay.py     read an organic outline off a labelled grid (step 2)
render_views.py     build the model and draw its silhouette     (step 8)
check_likeness.py   score that silhouette against the reference (step 8)
ref_silhouette.py   flatten a reference the mask cannot hold     (step 8)
```


```bash
python -m pip install -r "$IMAGE_TO_CAD_SKILL_ROOT/requirements.txt"
```

Install it even when the `cad` skill is already set up. That environment brings
numpy and scipy along with build123d, but **Pillow only ever arrives by
accident** — dragged in by vtk or matplotlib — so `measure_image.py` fails on
`import PIL` in a CAD venv that happens not to have one.

---

## Step 1 — Triage the image

`Read` every attached image first, and **copy each one into
`<project-dir>/ref/`** before measuring it. Every path in this skill — the
`measure_image.py` calls, the `check_likeness.py` pairs — assumes the reference
lives there. A spec that cites a temporary external location cannot be
re-verified once that location is cleaned out, which retires the only evidence
behind every `[observed]` number in it.

Then classify the image, because the classification changes everything
downstream:

**A. What kind of image is it?**

| Kind | Tell | Consequence |
|---|---|---|
| **Orthographic drawing / blueprint** | Flat, no perspective, often dimensioned, multiple aligned views | Best case. Dimensions may be `[observed]` directly. Read the title block for units and scale. |
| **Studio / product render** | Clean background, even lighting, near-orthographic long lens | Proportions are trustworthy; run `scripts/measure_image.py`. |
| **Photo in the wild** | Cluttered background, visible perspective, uneven light | Proportions are distorted by perspective — apply the corrections in `references/view-inference.md` before trusting any ratio. |
| **Sketch / concept art** | Hand-drawn, stylised, non-uniform line weight | Intent only. Almost every dimension becomes `[assumed]`. Ask the user for one governing size. |
| **Screenshot of existing CAD** | UI chrome, gizmos, wireframe or shaded viewport | Read the viewport orientation cube if present; treat as orthographic. |

**B. How many views do you actually have?**

Count distinct viewpoints across all attached images. One 3/4 hero shot is
**one** view, not three — a 3/4 shot foreshortens both horizontal axes at once
and shows you the top face at an angle you cannot measure directly.

| Views | Consequence |
|---|---|
| **1** | two of your three views are `[inferred]`/`[assumed]`. Say this in the Overall read, in one line, before anything else. |
| **2** | the third is `[inferred]` from the two. |
| **3 aligned orthographic** (top + front + side) | the outline is solved. Nearly every proportion is `[observed]`. |
| **4–6** | the outline gains nothing more. What you buy is **hidden surfaces** and **redundancy**. |

**The 6-view set is top, bottom, front, back, left, right.** Once you hold the
first three, rank the remaining three by what they actually buy — they are not
equal, and asking the user for all three when one would do wastes their time:

| Extra view | Buys | Worth asking for |
|---|---|---|
| **bottom** | the underside — the only surface no other view touches at all. Without it the base, sill, chassis, fastener bosses and any hatch are **invented**, and you will discover that only when someone turns the print over. Also gives tyre/foot width directly. | **almost always** |
| **back** | the rear face, rear lights, rear track vs front track, and a clean head-on silhouette of anything the side view showed only in profile. | when the object's rear differs from its front, i.e. usually |
| **other side** | for a bilaterally symmetric object, **nothing** — and `symmetry.left_right` already told you it is symmetric. Its value is the *null result*: detecting a badge, a filler cap, a port, an offset seat. | only when you suspect asymmetry |

**No number of views gives you absolute scale.** Six orthographic views of an
unlabelled object still leave every dimension a ratio. Scale comes only from
Step 3's anchor list — a dimensioned drawing, a known object in frame, a
standard the part must meet, or the user. Do not let a rich view set talk you
out of asking the one question that matters.

State the count and the ranking in the Overall read, so the user can see what
one more photo would be worth before you commit to `[assumed]` values.

**C. Is the object symmetric?** Symmetry is the cheapest inference you have.
Mirror symmetry about a plane turns half an unobserved view into `[inferred]`.
Rotational symmetry turns the whole top view into `[inferred]`. Establish the
symmetry group in Step 1 and reuse it everywhere.

**D. Is it a known object?** If the image shows a named product, standard, or
part family, that standard's real dimensions outrank anything measured from
pixels. Web-search the spec, cite it, tag `[observed]` from the source, and say
which source. If a `step-parts` skill is installed, search its catalog for the
component before modelling a stand-in.

**E. Is any feature a standard mechanical element?** This is a **separate**
question from D and it catches what D cannot. D fires on a *name*. E fires on a
*form* — and a form needs no name to be standard.

If any feature is a **gear, bearing, bolt, screw, nut, washer, rivet, pin,
spring, bushing, o-ring, circlip, chain, belt, pulley, coupling, hinge, caster,
magnet, or threaded insert**, it is standard whether or not the image labels it.
Measure its governing parameter off the pixels — a gear's tooth count and
module, a bearing's bore and OD, a fastener's thread and length — then search
`$step-parts` on those numbers before you decide how to model it.

**The failure this prevents is silent.** Procedurally authoring a standard
element can look like modelling while actually substituting an inaccurate
stand-in for an available catalog part.

Record the outcome — a hit **or a miss** — in section 6c of the spec. A miss is
a finding: it tells the next turn not to re-run the same search.

**F. Would an analogous design resolve a construction question?** A design
reference is useful when the object is a mechanical/product form or when one
feature's build123d construction family is uncertain. It is not useful as a
substitute silhouette for a unique organic subject. Record the one or two
form-and-feature queries worth running after decomposition; never search by
product name alone and then copy the nearest-looking object.

---

## Step 2 — Measure the pixels

Do not eyeball ratios. Run the bundled measurement tool:

```bash
python <skill-dir>/scripts/measure_image.py <project-dir>/ref/<image>.jpg
```

It is deliberately dumb and deterministic — no segmentation network, no model
call. It estimates the background from the image's border ring, thresholds the
object silhouette, denoises it with an erode-then-dilate pass, and reports:

- `bbox` — the object's pixel bounding box and its `aspect` (w/h);
- `fill_ratio` — silhouette area ÷ bbox area, which separates a solid blocky
  mass (→ ~1.0) from an open frame, a stand, or a legged object (→ low);
- `row_profile` / `col_profile` — the silhouette's width at each height and
  height at each column, decimated to 24 buckets. **This is the taper signal**:
  a flat profile means prismatic, a monotonic ramp means a taper, a bulge with a
  waist means a lofted or revolved form;
- `row_bands` / `col_bands` — contiguous runs where the profile is roughly
  constant, which is where your loft stations and your part splits usually belong;
- `symmetry` — left/right and top/bottom silhouette mirror scores in [0,1].

Flags: `--views a,b,c` to label the images, `--palette K` to also split the
silhouette into K colour clusters, `--invert` for a light object on a dark
ground, `--threshold N` to override, `--no-reject-shadow` to disable shadow
rejection, `--json-only` for the raw record. For the interior — `--rows`,
`--cols`, `--region`, `--isolate` — see "Interrogate the mask" below.

**A multi-colour subject needs the two-sided mask, which is the default.** A
one-sided luminance test silently drops subject regions whose brightness is
close to the background even when their colour is distinct.

The mask admits any region that is *chromatically* distinct from the
background and *attached* to the silhouette, whatever its luminance. Both
conditions are load-bearing: hue alone lets in a warm-lit tabletop, and the
touch test is what keeps the box on the object. When it fires, the record
carries `mask.offhue_region_share` and a note — read it, because it tells you a
part of the subject would have been missing.

**Cast shadows are rejected by default.** A contact shadow can pass a pure
luminance threshold and inflate every ratio derived from the bounding box. The
tool therefore also checks chromaticity. Pass `--no-reject-shadow` only for a
subject whose colour genuinely matches its ground.

**Line art defeats the mask, and not obviously.** The erode-then-dilate denoise
deletes 1-2 px strokes, so on a white-interior line-art sheet the tool reports
`no object found` on the panels it cannot hold and — worse — a plausible
bounding box on the ones it half-holds. Do not reach for a probe script: flood-fill
the white background so each outline becomes a solid silhouette, then measure the
filled images with this same tool. The fill threshold has to swallow the
antialiasing without leaking through the outline. Even filled, the denoise still
erases anything about 2 px wide, so a genuinely thin feature is the one case that
does need a direct ink read.

**`--palette K` is how you measure anything inside the outline.** The
silhouette cannot see a painted stripe, a cockpit opening, a tyre against its
fender, a lens, or a panel line — every one of them is interior. Each cluster
reports its hex, its share, its bbox as a fraction of the object's box, and a
per-column vertical span, which is exactly what the three view sections need.
Two cautions: a glossy surface can split into lit and shaded clusters of the
same paint, so raise K until the target feature appears and merge shading twins
by eye; and clusters represent colour, not parts.

### Read the image directly when the subject is organic

`--rows`, `--cols`, `--region` and `--isolate` all read the mask. For a
freeform subject the numbers the spec actually needs are a **station table** —
one (x, z, half-height) row per station along a curve — and no mask summary
produces one. Stamp coordinates on the image and read them:

```bash
python <skill-dir>/scripts/grid_overlay.py ref/side.png -o tmp/side-grid.png
python <skill-dir>/scripts/grid_overlay.py ref/side.png -o tmp/head.png \
    --crop 300,120,700,520 --zoom 3
```

Labels stay in original image pixels even inside a zoomed crop, so a station
read off the grid and a `--rows` scan are two reads of one instrument and can
be cross-checked against each other. That is the whole reason this is a tool
and not a throwaway script.

### Interrogate the mask — do not write a probe script

Everything above summarises the whole outline. The numbers an assembly's spec
actually turns on are **interior**, and there are three flags for them. Reach
for these **first**. Write a probe script only when none of them can answer the
question — and when you do, say in the spec what you measured by hand and why
the tool could not, so the next reader knows which numbers came from a
different instrument.

```bash
# where does this row break into separate blocks?   (part splits, gaps, windows)
... --rows 640,720,800          # or a slice: --rows 230:480:10
... --cols 300,512              # the same scan down columns
# what is inside just this box?                     (a gear window, an inset tray)
... --region 169,685,798,960
# where is the part I can name off the reference?   (the walnut base, the brass crank)
... --isolate '#6E4A30' --isolate '#C69E4A'
```

- **`--rows` / `--cols`** report the object's runs at each line, in original
  pixel coordinates. *Two runs on a row is the fact that the object is two
  parts there*, and the gap between them is the clearance. `--run-gap N`
  controls how wide a hole has to be before it counts as a split (default 2, so
  an antialiasing seam does not read as a gap).
- **`--region x0,y0,x1,y1`** re-reports every measurement for that window only —
  so `fill_ratio 0.995` and `row_shape flat` on a base box is *derived*
  evidence that it is a prismatic extrude. The silhouette is still taken from
  the whole frame, so background estimation stays valid. The record is stamped
  `scope: REGION ONLY` and the `cross_check` is suppressed, because a window's
  aspect says nothing about L:W:H.
- **`--isolate '#RRGGBB'`** locates a colour you can *name*, where `--palette K`
  returns whichever clusters happen to dominate. Matching is per-channel within
  `--isolate-tolerance` (default 46). It reports `blobs` and up to four `parts`,
  largest first — **read `parts`, not `all`** because a colour appearing in
  separate regions gives `all` a box that spans empty space.

Why this matters more than convenience: a hand-written probe re-derives the
silhouette with an ad-hoc threshold and may omit the shadow rejection above,
making ratios across views incomparable. Cross-check independent reads of the
same edge when possible.

Read the JSON, then reconcile it against what you see. The tool measures the
**silhouette**, so it cannot tell a hole from a notch, and a busy background
will wreck it — if `fill_ratio` or `symmetry` contradicts the image, trust your
eyes and say the tool disagreed. Full interpretation guide:
`references/view-inference.md`.

### The cross-check gate — run it before you write a single ratio

Give the tool two or more canonically named views (`top`/`bottom`,
`front`/`back`, `left`/`right`/`side`) and it adds a `cross_check` block. Each
view constrains the ratio of two of the three dimensions, so two views spanning
all three close the loop and any further view over-determines it. The tool
solves L : W : H across all of them at once and reports how far each view
disagrees.

```bash
python <skill-dir>/scripts/measure_image.py top.png front.png side.png \
    --views top,front,side
```

**This is the highest-value number the tool produces.** Under ~5 % the images
share one camera scale and you may treat every proportion as `[observed]`. Above
it, at least one view is foreshortened or shot at a different distance — find
the bad view and drop it. **Do not average.** Averaging a foreshortened view
into a good one produces a spec that is confidently, uniformly wrong, which is
the exact failure this skill exists to prevent.

Quote the solved ratio and the worst disagreement in the Overall read.

With exactly three views the system has a single redundant equation, so the
residual spreads evenly and **every view reports the same disagreement** — the
gate tells you the set is bad without telling you which member is bad. That is
the concrete thing a fourth, fifth or sixth view buys: with duplicated pairs
(top+bottom, front+back, left+right) the outlier becomes identifiable instead of
merely detectable.

One thing the gate does **not** catch is shadow inflation. A contact shadow can
enlarge every view in roughly the same proportion, so the views agree while all
remain wrong. Shadow rejection handles segmentation; cross-checking handles
cross-view geometry.

**The gate assumes a plan view is drawn nose-left.** It reads a `top`/`bottom`
view's *width* as the object's length. Hand it a nose-up plan and it silently
compares span against length and reports a disagreement that is not there.
Rotate top/bottom images nose-left before running the gate.

---

## Step 3 — Anchor the scale

Pixels give you **ratios**. One real dimension turns every ratio into mm. Find
your anchor in this priority order and **state which one you used**:

1. **The user supplied a governing dimension.** Use it directly as `[observed]`.
2. **A dimensioned drawing.** Read the dimension lines — `[observed]`.
3. **A known object in frame.** Measure its pixels, look up its real size, and
   divide. Tag `[inferred]` and cite the reference object and dimension.
4. **A standard the object itself must meet.** Web-search the governing
   dimension, cite it, and tag it `[inferred]`.
5. **Function forces it.** Derive the minimum functional dimension, tag it
   `[inferred]`, and show the reasoning.
6. **Nothing at all.** Pick one governing dimension, tag it `[assumed]`, derive
   every other dimension from it as a ratio, and put it **first** in the
   Assumptions list with the one-liner: *"Everything scales with this — change
   it and the rest follows."*

Then run the sanity gate before going further:

- Does it fit a 200×200 mm FDM bed? If not, say so and name the split or the
  scale-down.
- Is any wall thinner than 0.8 mm (2 × 0.4 mm nozzle) at your chosen scale?
  Walls do not scale below the nozzle — a scaled-down model needs its walls
  re-thickened, which changes the look. Flag it.
- Is any feature smaller than ~1.5 mm? It will not survive FDM. Flag it.

Details and a lookup table of common scale anchors: `references/scale-anchors.md`.

---

## Step 4 — Write the three views

Each view gets the same treatment: **outline → internal features → what is
hidden → confidence**. Use mm throughout, `[observed]`/`[inferred]`/`[assumed]`
on every number.

**Top view (plan, looking down −Z)** — the footprint. State the outline shape,
its bounding rectangle, the corner radii, the symmetry axes, where the widest
point sits along the length, and every feature that appears *only* in plan
(bosses, holes, ribs, the opening of a cavity). This is the view most often
missing from a hero shot, and the one that decides whether the part is a
`rect().extrude()` or a `Sketch` profile.

**Front view (elevation, looking along +Y)** — the face the user thinks of as
"the front". State the silhouette, the height breakdown as a stack of bands
(base / body / neck / head with a height each, summing to the total), the draft
or lean angle, and the ground-contact footprint.

**Side view (elevation, looking along +X)** — the profile. This is where taper,
lean, cantilever, and overhang live. State the depth at each height band, the
lean angle, and — critically for FDM — **every surface steeper than 45° from
vertical**, because those need support or a redesign.

For a view you did not observe, write the reconstruction reasoning explicitly
and tag every inferred or assumed dimension.

Perspective correction, foreshortening, and how to recover a plan from a 3/4
shot: `references/view-inference.md`.

---

## Step 5 — Decompose

Two levels, and **do not confuse them**:

### 5a. Printed parts — default to ONE

Follow the `cad` skill's rule: most consumer objects are **one sculpted body**.
Split into separate printed parts **only** when the object physically must come
apart:

- a lid or removable cover;
- a moving joint (hinge, linkage, bearing);
- a form that cannot print in any single orientation;
- anything larger than the bed;
- a part that must be a different material or colour.

A visual seam in the photo is **not** a reason to split. Mass-produced objects
are split for injection-moulding and assembly-line reasons that do not apply to
FDM. If the image shows a seam that serves no function for a printed part,
model it as a **cosmetic groove on one body** and say so. Getting this wrong is
the most common way an image-derived spec balloons from one clean part into six
that never fit together.

For each printed part state: name, purpose, outer envelope, and — if there is
more than one — the joint type, the **single shared mating dimension**, and the
clearance per side. `cad` will derive both halves from that one dimension.

### 5b. Feature tree inside each part

This is what "chia từng phần" usually means in practice. Decompose each printed
part into an ordered feature list:

1. **Base solid** — the one primitive or profile that carries the mass. Everything
   else is added to or cut from it.
2. **Additive features** — bosses, ribs, lugs, handles, flanges, fenders.
3. **Subtractive features** — cavities, holes, slots, channels, ports, reliefs.
4. **Finishing** — fillets, chamfers, edge breaks, texture, engraving.

Order matters and is part of the spec: **most stable anchor first**, fillets
last (a fillet applied before a boolean usually gets consumed or fails). Cut
after union unless the cut is what makes the shape possible.

Decomposition heuristics, and how to spot base-solid candidates in a photo:
`references/decomposition.md`.

### 5c. Source the standard elements — write the search log

Every element Step 1E flagged gets a row in spec section **6c**, whether the
search hit or missed. Search `$step-parts` on the measured numbers, then decide
one of three, and **state which**:

| Decision | When | What the spec records |
|---|---|---|
| **catalog STEP** | a hit at or near your measured parameter | the `id`, the delta from your measurement, and that `cad` imports it via `cadgen.step_scene.import_step` |
| **pocket only** | the component is bought, not printed — bearing, magnet, PCB | the pocket size, derived from the catalog record's real dimensions |
| **authored stand-in** | a hit exists but you are deliberately not using it, or the search missed | **the reason**, in one line |

The third row is the one people skip. Rejecting a catalog hit can be legitimate,
but it must carry a reason; an unstated choice is indistinguishable from an
oversight.

A **miss is a result**, not a blank. Record the query that missed so the next
turn does not pay for the same search twice.

### 5d. If anything is driven, solve the mechanism before Step 6

A part that moves under a **driving force** — a band, a spring, a motor,
gravity, a hand crank — needs spec section **8** as well as its row in 5a. The
split test tells you the part is separate; it says nothing about what the part
*does*, and Step 6 cannot invent a link length from a silhouette.

A photograph almost never shows the mechanism — it shows the shell over it. So
this section is `[inferred]` and `[assumed]` most of the way down, which is
exactly why it must be written out here instead of left to the build turn to
improvise.

Three things, in order:

1. **Name the archetype.** "Runs on a rubber band" is a power source, not a
   mechanism. A crank-rocker four-bar, a slider-crank, a pull-back flywheel and
   a cam-follower are — and each carries a different parameter set, a different
   part count, and a different visible form. Choose one and record what you
   rejected. When the choice changes the outline and the image cannot settle it,
   that is the one question worth asking under "Ask only about preferences".
2. **Write the parameters as numbers** — fixed pivots in assembly coordinates,
   link lengths, joint limits, phase offsets — and make Step 6's features derive
   from them rather than restate them. A pivot that appears in both section 7
   and section 8 is two numbers that will drift apart.
3. **Write the feasibility condition as an `assert`** for `<name>_lib.py`. A
   four-bar that violates Grashof, a slider that overruns its slot, a cam whose
   follower leaves its track: every one of them validates, exports, prints, and
   then jams. `validate`, `interfere`, `check_fit` and `check_mesh` all pass
   them. That assert is the only thing that does not.

Then write the motion conditions into the verification checklist — **both**
directions of every joint, with the `blocked` direction pointing the way the
drive pulls — so the build turn emits `measure/motion.json` rather than deciding
for itself whether the thing moves.

What a rigid-body sweep still cannot reach — band force, gait, friction
retention, elastic recovery, snap-fit compliance — goes in 8d and then in Open
questions. Those need a print, not a gate.

### 5e. Search analogous designs — patterns, never dimensions

When Step 1F found a real construction question, use `$design-reference` after
the feature tree is known and before writing Step 6:

```bash
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" search \
    "<construction family> <defining feature> <operation cue>" --limit 5
```

Select a result only when a named feature demonstrates a relevant construction
pattern. Fetch it into the current project and add it to spec section **6d**.
The user's image/spec still owns every dimension, placement and silhouette;
catalog volume and area are validation facts for the upstream model, not a
scale anchor. If nothing is relevant, record the query as `MISS`. If the
subject is an organic form for which this sketch-and-extrude corpus cannot help,
record `N/A — no applicable construction analogy` instead of forcing one.

The current indexed source is licensed for **non-commercial research only**.
Do not search or fetch its source for a commercial task. A reference that is
used must retain its local `LICENSE.md` and `provenance.json`; run
`design_refs.py verify <project-dir>` before handoff.

---

## Step 6 — Map every feature to a build123d operation

For each feature in the tree, give a row with **six** columns. The whole point
of this section is that `cad` never has to invent an approach:

`feature | geometry + numbers | build123d call | plane / selector | order | risk`

Pick the construction family from the **form**, not from habit. This is the
highest-consequence decision in the whole spec — a form authored in the wrong
family cannot be rescued by parameter edits, only by re-authoring.

| The image shows… | Author as | build123d idiom |
|---|---|---|
| Constant cross-section (box, tray, bracket, plate) | Extrude | `Box(w, d, h)`, or `extrude(amount=h)` over a `BuildSketch` |
| Constant section + uniform draft | Tapered extrude | `extrude(amount=h, taper=3)` |
| Rotationally symmetric (vase, knob, bottle, dome) | Revolve | `Polyline(...)` → `make_face()` → `revolve(axis=Axis.Z)` |
| Section changes along the length — fuselage, hull, swoosh, grip | **Loft over ≥3 stations** | one wire per station from a shared `section_at(t)` helper → `Solid.make_loft(wires, ruled=True)` |
| Constant-ish section following a curved path (tube, rail, strap) | Sweep | `sweep(is_frenet=True)` |
| Planar arch — roll hoop, handle, bail | Extruded ellipse band | two concentric `Ellipse`s, clipped, `extrude(amount=d)` |
| Hollow shell of uniform wall | Shell | `offset(body, -wall, openings=body.faces().sort_by(Axis.Z)[-1])` |
| Non-trivial 2D outline (any profile you would draw with a pencil) | Sketch | `Rectangle()` → `fillet(sk.vertices(), r)` → `Circle(mode=Mode.SUBTRACT)` → `extrude()` |
| Repeated feature on a line/grid | Array | `with GridLocations(dx, dy, nx, ny): Hole(r)` |
| Repeated feature around an axis | Polar array | `with PolarLocations(r, n): ...` |
| Painted stripe, inlay, or lens on a sculpted skin | Conformal skin patch | `(inflated_loft - raw_loft) & tool` |
| Blended organic mass | Loft stack, bevels baked into the section | `Solid.make_loft()`; keep 3D `fillet()` off tangent chains |

**Do not downgrade organic silhouette features to boxes.** On animals,
figurines, toys, characters, vehicles, and product shells, a crest, casque,
horn, fin, brow, cheek, muzzle, fairing, canopy, or raised colour lobe that is
visibly rounded or tapered is part of the reference silhouette. Author it as a
loft, sweep, revolved cap, or conformal skin patch. Use `Box()` only when the
reference actually shows hard planar faces and square edges. If you simplify an
organic feature, preserve its silhouette envelope and mark the row's risk as a
deliberate simplification; do not let a rectangular primitive become the default
stand-in.

For high-likeness figurines, separate **silhouette mass** from **surface
decoration** in the spec. Build and validate the large organic core solids first:
torso, head, tail, limbs, perch/base. Then add colour bands, wrinkles, ridges,
scales, spikes, beads, and texture as shallow surface details with bounded
penetration, or as separate labelled visual skins. Do not specify a full-depth
band or spike field that cuts through a lofted body unless the table also names
the boolean/overlap limit that keeps the resulting solid non-self-intersecting.

For any explicit 90-95% likeness target, the **spec itself has a completeness
gate before CAD starts**. A short intent document, prompt-style visual target,
or placement-only table is not a build spec; it is a flow failure because the
CAD step will invent primitive stand-ins. The spec must include, at minimum:
view coverage and reconstruction notes, a measurement audit including tool
limitations, observed side/front station tables for the main organic silhouette,
a scale anchor with ratios, printable-part decomposition, connector/shared
dimension tables when modular, one build123d operation row per feature with
numbers and risks, named parameters that own shared dimensions, a proportion
ledger, and a verification checklist. If those sections cannot be populated
from the images, stop and measure/probe the images again before writing CAD.

If the details are separate labelled solids, place them as true surface skins:
tangent or with a tiny visible clearance from the core, and non-overlapping with
each other. Do not assume "same visual module" hides collisions. The CAD
interference gate walks leaf solids inside compounds; a compound of overlapping
colour patches, tail joints, eye discs, mouth beads, or bark rings still fails
`inspect interfere`. If a decoration must overlap to be manufactured as one
body, boolean-fuse that local group into one validated solid before review;
otherwise keep it outside the core with clearance.

For tight decorative curls, do not start with a swept Archimedean spiral. A tube
following a small-radius spiral can self-intersect while still looking like the
right construction. Use a collision-safe approximation first — a torus/partial
ring, a few non-touching arcs, or an obviously separated raised spiral line —
and only refine to a real spiral after validation and interference pass. The
same applies to crest and dorsal markers: when the surface height is uncertain,
place the first version clearly outside the core, not "almost embedded".

For bead rows, pupils, nostrils, separate jaw skins, torus tails, and other small
visual cues, specify a clearance at least equal to the small detail's radius
unless the pieces are locally fused and revalidated. Tiny decorative overlaps
still fail `inspect interfere`; do not spend a run on a connector stem, bead row,
or stripe that is optional for silhouette until the primary body, head, perch,
and tail curl clear the gate.

Do not solve interference by making the object explode visually. For a
high-likeness target, a gap between a cue and its core is a defect whether or
not anything renders it. If a required cue reads as floating — eye discs,
mouth beads, jaw patches, dorsal spikes, crest, stripes, or tail curl — the next
spec must group that cue with its local core and prove the local group before
assembling the whole model.

Do not solve interference by moving a required feature out of the reference
pose. A side-view part can be shifted along the hidden depth axis and still pass
the side silhouette while becoming wrong in 3D: a tail no longer rooted in the
body, toe pads no longer gripping the branch, or colour bands standing off the
skin as rods. For 90-95% likeness, the spec must name maximum visible gap or
contact constraints for every defining feature, and CAD must satisfy those
constraints in the actual assembly pose.

A complete station table still needs the right section vocabulary. For a
90-95% organic target, radius-only elliptical stations are insufficient when
the reference shows a flattened flank, keel, cheek, brow, or asymmetric belly;
record the cross-section shape and landmark rails at each station. Sparse ruled
ellipse lofts tend to produce a faceted barrel even when their side envelope is
correct. Likewise, a defining blade such as a casque, crest, ear, or fin is not
allowed to become a constant-depth extruded side polygon: give it at least three
depth stations and loft the rounded volume. Capsule chains are acceptable only
as pose/contact probes for limbs; a reviewable high-likeness limb needs tapered
segment lofts and explicit joint transition masses. Conformal colour shells
also need measured boundary curves in side/profile space; intersecting a shell
with repeated full-height slabs produces technically conformal but visually
uniform bands.

Local groups are not enough; the assembly placement also needs a preflight. For
any high-likeness figurine with head/body, tail/body, limb/body, or feet/perch
contacts, the spec must include a placement table with the intended relation and
a minimum/maximum contact allowance for each pair. Run `inspect interfere` on
the full assembly and, if it fails, treat the run as a failed output.

Do not replace a defining silhouette with a generic safe primitive when the
target is 90-95% likeness. Safe approximations are acceptable only as temporary
gate probes; in the delivered spec, defining cues must use a form family that
matches the image.

Do not trust a risky swept organic feature because a standalone helper or
approximation once looked plausible. Tail spirals, curled tubes, horns, and
crest chains must be validated as the actual emitted part entry before the
combined assembly can be considered reviewable. A passing interference check
does not rescue a `validate` failure on the same run; record it as failed,
update the spec/skill lesson, and start the next version fresh.

Likewise, a visual assembly pose is not allowed to rely on large overlaps.
For every seated module in a multi-part figurine — head into body, tail into
body, limb into body, foot on perch — write one row that names whether it is
`clearance`, `intentional seated contact`, or `cosmetic near-contact`. If it is
not a real connector, leave a visible air/contact relation rather than sinking
the parts into each other. The downstream CAD run must be able to pass
`inspect interfere` before any likeness score is claimed.

Then, per feature, name the **selector** — this is where image-derived specs
most often fail to build:

- `.faces().sort_by(Axis.Z)[-1]` top face, `[0]` bottom,
  `.faces().group_by(Axis.Z)[-2]` the second band down (the inside floor of a
  shelled box);
- `.edges().filter_by(Axis.Z)` all vertical edges — the corner-radius selector;
- `.edges().group_by(Axis.Z)[-1]` the top rim only;
- `Plane.XY.offset(h)` to work at a height without a face to land on;
- an explicit `Plane(origin=…, x_dir=…, z_dir=…)` for an angled frame — **never
  `Plane.rotated()` on a non-global plane, which composes in world axes and
  silently yaws what you meant to pitch**;
- re-select after every boolean: a face list captured earlier refers to faces
  that no longer exist.

Mixed objects decompose naturally: a lofted outer skin carrying the image, with
extruded/booleaned functional interior carrying the engineering. Say which is
which.

Full mapping with worked snippets, selector recipes, and the failure each one
prevents: `references/build123d-operations.md`.

---

## Step 6b — Depth comes from the elevations, not from what occludes what

With oblique views it is tempting to infer lateral placement from occlusion.
Do not: occlusion order is weak evidence and may conflict across views. Take
lateral placement from near-orthographic elevations where offsets are
measurable, and record unresolved conflicts in the Assumptions list.

## Step 7 — Prove the read, then self-critique

**Proportion ledger.** Extract 4–6 ratios from the image and put them in the
spec as assertions to check after generation with `scripts/inspect`, ±10%:

- overall length : height : depth;
- ground-contact length ÷ total length (a "floating" stance is a *measurable*
  short contact patch, not a vibe);
- where the widest/tallest point sits along the length (front third? middle?);
- wall thickness ÷ overall width, if a wall is visible at an opening;
- the height of any undercut ÷ body height.

A ledger makes the next edit turn cheap: the numbers name exactly which aspect
of the form drifted.

**Multi-component scene landmark gate.** A scene with many repeated pieces can
match its broad archetype while missing most defining landmarks.
Before CAD starts, inventory the visible landmarks by category and give each a
count, placement rule, or ratio where the image supports one:

- outer silhouette and frame tiers;
- region boundaries and their layers;
- repeated-site density and exclusion zones, measured as rows/columns or
  occupied area rather than described as "many";
- repeated-piece count and distribution, including whether the layout is
  regular, sparse, clustered, or deliberately irregular;
- one silhouette checklist per defining module;
- rule- or prose-required accessories that are absent from the hero image.

The operation table must have a row for every landmark, and the verification
checklist must score the categories separately. Do not
assign a single 90-95% likeness number until every defining category has its own
finding.

When a reference shows a manageable number of repeated, individually visible
pieces (up to roughly 50), record their observed normalized centroids or a
traceable placement table. Do not replace an irregular photographed layout with
a grid sampler, farthest-point distribution, or random seed merely because the
count is correct. Those algorithms create a conspicuous new composition. Use a
procedural distribution only when the reference itself is procedural or when
the user asked for a new playable setup rather than a reproduction; record that
choice as `[assumed]`.

If those pieces must occupy legal sites, observed centroids are evidence, not
final assembly coordinates. Map
each centroid to one **unique** valid site, enforce every exclusion zone, and
record the displacement or a maximum allowed snap distance. Run a local audit
that proves count, uniqueness, site membership, and exclusion-zone clearance.
A visually plausible centroid can still occupy an excluded region;
full-assembly interference catches the collision late, while the placement
audit prevents it before geometry.

Any defining landmark whose bbox is under roughly 15% of the whole scene needs
a local verification target in the spec. A full-scene render cannot prove a
small feature even when it technically exists.

**Then critique your own spec** against these, and fix what fails:

- Does every number carry `[observed]` / `[inferred]` / `[assumed]`?
- Does the top view contain a feature that the front view contradicts?
- Does the sum of the front view's height bands equal the stated total height?
- Does the side view's depth agree with the top view's depth?
- Is there a feature in the tree with no build123d operation assigned?
- Does any feature float — added to nothing, connected to nothing?
- Does anything move under a driving force with no section 8 — or a section 8
  with no feasibility `assert`?
- Does a pivot position or link length appear in both section 7 and section 8?
- Does every joint in section 8 carry **both** a `clear` and a `blocked`
  condition, with the `blocked` one pointing along the drive direction?
- Would every stated construction family survive the actual form? (A tapering
  body specified as `.extrude()` is wrong **by construction**, not "close
  enough".)
- Print check: bed size, minimum wall, minimum feature, overhangs > 45°, and one
  named print orientation.

**Soft cap: 2 revision passes.** Past that, the gap is user intent, not
analysis — ask one question.

---

## Step 8 — Measure the likeness, do not estimate it

The spec's proportion ledger is checked against the *model*. Nothing in the
toolchain checks the model against the *photograph* — which is the only
question an image-derived model exists to answer, and the one every other gate
leaves open. `validate`, `interfere`, `check_fit` and `check_motion` can all
pass a figure that is 60 % of the way there.

So render the model from the reference viewpoints and score it. The renderer
is `render_views.py`, beside the gate; it builds the shape from the
**generator** rather than from the `.step`, so the picture is answerable to the
code and not to an artifact that may predate it.

In this repository the CAD runner owns the final integrated form. It also
requires the spec/source and landmark audits, writes the four orthogonal review
views, checks the fresh STEP against the source, and persists the run record:

```bash
CADGEN_WARM=1 python skills/cad/scripts/verify_project <project-dir> \
    --fresh --exports --image-derived \
    --likeness-ref side=ref/03-side.png \
    --likeness-ref front=ref/02-front.png \
    --likeness-ref rear=ref/04-rear.png
```

The standalone commands below remain the iteration tools; the integrated final
run is the completion gate.

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

## Ask only about preferences

Same split as `cad`. The user verifies **taste**, never **geometry**.

- **Ask (preference, and only when it changes geometry):** intended real size
  when no anchor exists; which device it must fit; whether a visible seam is a
  functional split or cosmetic; whether an unobservable back face matters.
- **Never ask (engineering — decide silently):** wall thickness, fillet radius,
  clearance, joint type, fastener size, print orientation, which construction
  family to use, feature order.

Ask the **fewest, highest-leverage** questions — ideally one, never a quiz. When
an image gives no scale anchor, ask for one governing real-world dimension.

---

## Output

Fill in `templates/build_spec.md`. Write it to the user's workspace as
`<object_name>_spec.md` (absolute path) so the `cad` turn can read it, and
also render the spec inline in your reply — the user reads it before approving.

If the user gives an output root, run/version pattern, or "new folder every
run" rule, the spec path and every downstream CAD path must use that exact
fresh directory. Do not silently reuse a previous project directory with a
different name; that hides iteration history and makes review findings hard to
trace back to the run that produced them.

## Handoff to cad

End by naming the next step explicitly:

> Spec written to `<abs path>`. To build it: use the `cad` skill with this spec —
> it becomes one `<name>.step.py` whose named parameters are the Size table and
> whose `gen_step()` body is the feature table, in order.

The spec maps onto `cad` one-to-one:

| Spec section | Becomes |
|---|---|
| Size + proportion ledger | the named parameters at the top of `<name>.step.py` |
| Ledger assertions, print checks | checks run after generation — `scripts/inspect refs --facts` for bounds, targeted `measure`/`align` for the rest |
| Printed parts (5a) | labelled children of the `cadgen.assembly.AssemblyHelper` compound |
| Catalog search log (5c / spec 6c) | `cad` skips its own `$step-parts` pass for every row already decided here, and imports each catalog hit with `cadgen.step_scene.import_step` |
| Design-reference log (5e / spec 6d) | reference-only construction evidence; `cad` may reuse the named idiom but does not import or execute the fetched excerpt |
| Feature table (Step 6), in order | the body of `gen_step()` |
| Mechanism (spec 8) | the kinematic parameters and the feasibility `assert` in `<name>_lib.py`, and `measure/motion.json` for `scripts/check_motion` |
| Approved spec versus repaired source | `measure/check_spec.py`; every CAD repair that changes a parameter, landmark, part count, or construction family is reconciled back into the spec |
| Landmark ledger | `measure/check_landmarks.py`; every defining item gets a count, bbox, station, axis, label, or measured relationship in the built geometry |
| Assumptions | the assumptions bullets in `cad`'s final response |

`cad` then runs the final project workflow through
`scripts/verify_project --image-derived`, supplying every usable reference as
`--likeness-ref LABEL=PATH`. Geometry and manufacturing claims remain
deterministic; the sibling renderer supplies the separate visual evidence and
cannot substitute for validate, interference, fit, mesh, motion, mount, or
thickness checks. A source repair that leaves this spec stale is a failed
handoff, even when the geometry itself improved.

Do **not** invoke `cad` yourself unless the user asks to build. Producing the
spec is the whole job; the user approves it first.

---

## Progressive references

Load only when the trigger applies:

- `references/view-inference.md` — reading `measure_image.py` output;
  perspective and foreshortening correction; reconstructing a plan from a 3/4
  shot; symmetry inference; when the silhouette lies. **Load whenever you have
  fewer than 3 orthographic views** (i.e. almost always).
- `references/scale-anchors.md` — the anchor priority list with a lookup table
  of common in-frame reference objects and their real dimensions; scale sanity
  gates; what breaks when you scale a model down. **Load when no dimension was
  given.**
- `references/decomposition.md` — one-part-vs-many decision tree; cosmetic seam
  vs functional split; finding the base solid; feature ordering rules; when a
  photographed assembly should collapse into one printed body. **Load for any
  object with visible seams, moving parts, or more than ~6 features.**
- `$cad`'s `references/organic-lofts.md` — station tables, the loft station
  frame, segment junctions, the one-body assertion, section families, and
  per-region colour. **Load when the subject is an animal, figure, hull, or
  any body whose section changes along a curved spine** — that is a large
  fraction of what people photograph.
- `$design-reference` — analogous parametric designs and cited build123d
  excerpts. **Load when Step 1F identifies a mechanical/product construction
  question; do not load it for bought components or as a source of scale.**
- `references/build123d-operations.md` — the full form→operation mapping with
  runnable snippets, the selector cookbook, boolean-order rules, and the
  specific build failure each choice prevents. **Load before writing Step 6.**

## Non-negotiables

- **Every number carries a confidence tag.** No exceptions.
- **Run the cross-check gate whenever you have 2+ views** and quote its verdict.
  A set that fails it is not a set — it is one good view and some noise.
- **Never invent a dimension for a named real-world product.** Web-search it and
  cite the source, or ask.
- **Never author a standard mechanical element without searching the catalog.**
  A gear, bearing, or fastener you drew yourself and a catalog hit you rejected
  look identical in the finished model. Section 6c is what tells them apart.
- **Never let an analogous design override the user's evidence.** Section 6d
  may supply a construction idiom, never dimensions, scale, placement, or a
  substitute silhouette. Every fetched result retains provenance and license.
- **A driven mechanism is specified, never implied.** If a part moves under a
  band, spring, motor or gravity, section 8 names the archetype, fixes the link
  lengths, and carries a feasibility `assert`. Every deterministic gate in the
  toolchain passes a linkage that cannot complete its cycle; nothing downstream
  will catch what this section omits.
- **No geometry.** This skill writes markdown. If the user wants the model,
  hand off to `cad`.
- **Never present a single 3/4 photo as three observed views.** Name the
  reconstruction.
- **Millimetres throughout.** Do not convert; do not annotate inches.
- **Every feature in the tree has a build123d operation and a selector.** A
  feature with no operation is an unfinished spec.
- **Match the form's construction family.** A tapering or double-curved body
  specified as a constant-depth extrusion is a defect, not an approximation.
- **Score the likeness; never assert it.** A reconstruction is not done because
  it looks about right in a render. Run `render_views.py --match` and then
  `check_likeness.py` against the reference views, quote the mean IoU and the
  worst band, and say which edit the band names. "Looks close" is the claim
  this skill exists to replace with a number.
- **Search the camera before blaming the shape.** A fixed orthographic render
  against a photograph measures your guess at the viewpoint, not the model —
  0.865 and 0.974 on the same geometry. Quote the recovered pose alongside the
  IoU, and treat a pose the reference plainly contradicts as a finding.

## Required final response

1. **One sentence** — what the object is and what you spec'd.
2. **The spec** — inline, all seven sections, plus section 8 when a part is
   driven.
3. **Spec file path** — absolute.
4. **Confidence summary** — one line: how many views were observed vs
   reconstructed, and which single assumption most affects the result.
5. **Assumptions** — the `[assumed]` values as bullets, scale anchor first, each
   phrased as something the user can correct in one edit.
6. **Sourcing** — one line per standard element: catalog hit used, hit rejected
   with the reason, or search missed. Say "no standard elements" if Step 1E
   found none. Silence here reads as "never looked".
7. **Design references** — ids used with the named construction lesson, the
   recorded query miss, or `N/A` with the reason.
8. **Next step** — the `cad` handoff line.
