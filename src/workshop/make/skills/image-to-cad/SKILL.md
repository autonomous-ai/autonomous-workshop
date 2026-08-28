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

The spec has seven sections, in this order, and an eighth when the object has a
functional electrical load or moves under power:

1. **Overall read** — what the object is, its archetype, its construction family.
2. **Top view** (plan, looking down −Z).
3. **Front view** (elevation, looking along +Y).
4. **Side view** (elevation, looking along +X) — then **4b, component
   descriptions**: every visible component written out in words, before any
   decision about parts.
5. **Size** — real-world dimensions in mm, with the scale anchor that produced them.
6. **Decomposition and design selection** — printed parts, feature trees,
   research logs, then one evidence-backed selected design for every applicable
   exterior, mechanical, electrical, lighting and bought-device domain.
7. **Per-feature detail + build123d operation** — one row per feature: geometry,
   numbers, the exact API call, the plane/selector it runs on, boolean order.
8. **Powered system / mechanism** — the power boundary and electrical loads;
   when a part is driven, also the archetype, kinematic parameters, feasibility
   assertion and motion conditions.

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
triage → measure → scale → build 3 views → decompose → write research contracts
   ↑                                                         ↓
   └── revise ← self-critique ← map operations ← select design ← research + compare
```

You close this loop before the user sees anything. The check step is Step 7.

## Before the first run

Resolve the exact materialized skill trees instead of assuming an upstream
repository checkout:

```bash
IMAGE_TO_CAD_SKILL_ROOT="$(workshop skills path)/image-to-cad"
STEP_PARTS_SKILL_ROOT="$(workshop skills path)/step-parts"
CAD_SKILL_ROOT="$(workshop skills path)/cad"
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

Four of the five carry fixtures. Run them after any change to the mask, the
cross-check, or the scoring — a mask that drops a region and a gate that
mis-scores a silhouette both fail silently and in the plausible direction,
which is why each fixture also runs the naive alternative and prints what the
rule is worth:

```bash
python <skill-dir>/scripts/measure_image.py   --self-check
python <skill-dir>/scripts/check_likeness.py  --self-check
python <skill-dir>/scripts/ref_silhouette.py  --self-check
python <skill-dir>/scripts/render_views.py    --self-check
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
form-and-feature queries worth running after decomposition; research Internet
sources for specifications and construction evidence, never search by product
name alone and then copy the nearest-looking object.

**G. Is any light functional?** A glowing region, coloured lens, beacon,
headlamp, tail lamp, light strip, illuminated button or backlight is a powered
landmark unless the brief explicitly makes it inert decoration. Inventory its
function, position, colour, behavior and luminous surface, but do not identify
an exact LED/module from appearance. Trigger `$electromechanical-integration`
now: it automatically searches GitHub for a licensed integration analogy,
`step.parts` for exact bought geometry, and then manufacturer/public CAD
services on a confirmed catalog miss. If the lamp is removable, discovery must
select the exact mating socket and contacts at the same time; a lamp MPN without
its receiver is not a completed component choice. Every search outcome becomes
provenance; a login wall is unavailable, not a miss.

**H. Which design domains must this analysis select?** Inventory five domains:
exterior construction, mechanical mechanism, electrical topology, lighting,
and other bought devices. Mark inactive domains `N/A`; every active domain must
end this `image-to-cad` turn with one selected design in spec section **6g**.

Selection does not mean guessing early. A construction family directly forced
by the visible form — for example a revolved body or a changing-section loft —
may be selected from the image evidence. A mechanism, electrical topology,
actuator, lamp/emitter, socket/contact system or other bought device follows a
strict research-first order:

1. write the functional, dimensional, packaging and evidence contract;
2. research Internet and networked-catalog sources using that contract;
3. extract applicable specifications, constraints, revisions and licenses;
4. compare viable candidates and name meaningful rejections;
5. select the design and exact component/interface only from the resulting
   evidence.

Do not select an exact MPN from appearance and then search for evidence that
confirms it. The only exact part that may enter the analysis preselected is one
the user explicitly requires; research still verifies its ratings, geometry
and mating interfaces. Steps 2–4b produce the measured constraints needed by
the contracts; Steps 5c–5e run the research, and Step 5f records the selection.

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

## Step 4b — Describe every component, before deciding any part

Spec section **4b**. One prose entry per **visible component** — what a person
pointing at the object would name — written before the first thought about how
it prints. Body, stripe, fins, tail cavity, socket, lamp, post, base: seven
things a viewer sees, which may still be three printed parts. Which is which is
Step 5's question, and answering it early is how a component vanishes before
anyone has described it.

**The two neighbouring sections cannot hold this.** Steps 2–4 describe the whole
object's silhouette, one view at a time; Step 7 describes build123d calls, by
which point the shape is settled and the only open question is which API makes
it. Nothing in between asks what each component *looks like*. So a component
that is never written down is not caught by a failing gate — it is simply
absent, and the model validates, prints and assembles without it.

Prose, not a table. The detail that carries a likeness is never in the same
place twice: on one component it is that the nose stops in a small spherical
cap instead of a point, on another that only the **inner** face of each fin is
painted, across a strip 5–8 mm wide, so the flame appears only when the lamp is
lit and the object goes quiet when it is off. A column called "Visual
requirement" reduces both to a clause, and a construction family — "loft through
changing sections" — states how to build a shape while saying nothing about
which shape.

Each entry carries form, size with ranges rather than false precision, how the
component meets its neighbours, the detail that only shows on a second look,
and **what breaks if it is wrong**. That last one is where a real tolerance can
be written: *the post enters the belly at 15–20° from horizontal, nose up and
canted slightly left; a few degrees off and the lamp stops looking like it is
climbing* tells a later reader that ±5 mm on the base diameter is nothing and
±3° on the post is everything. No dimension table can say that, because the
table's columns are the same for every row.

Two boundaries the description has to settle, because a single view cannot:

- **A seam or a colour change?** A stripe running through the whole cross
  section and a stripe painted on the surface are identical in the photograph
  and different solids in CAD.
- **A component or a bought part?** A lamp that is visibly part of the
  silhouette is a component to be described here *and* a bought part to be
  selected in 6c — describing it does not excuse skipping the catalog, and
  buying it does not excuse leaving it out of the form.

An entry that says no more than its bounding box is not a description. Look
again, or write plainly that the component is not resolvable from the available
views and carry that into Assumptions. An honest gap is recoverable; a box
nobody questioned is not.

Every entry then gets a row in 4b's component ledger, and every row has to
survive to delivery — through Step 5's split, through `check_landmarks.py`, and
into the likeness renders.

---

## Step 5 — Decompose, research, and select the design

The order inside this step is load-bearing: 5a–5b expose the parts, features and
interfaces; 5c–5e research the active domains; 5f selects the design. Do not
fill an exact mechanism, electrical topology, lamp, actuator or bought-device
choice into the selected-design row before its research log exists.

Two decomposition levels, and **do not confuse them**:

### 5a. Printed parts — default to ONE

Do not open this step until 4b describes every component. Splitting first
answers "what is this object made of" with "what is convenient to print", and
each printed part here must account for whole components from 4b — if one is in
no part, say where it went.

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

### 5c. Source standard and bought elements — write the search log

Every element Step 1E and every bought electrical item Step 1G flagged gets a
row in spec section **6c**, whether the search hit or missed. Search
`$step-parts` on the measured numbers or exact MPN, then decide one of three,
and **state which**:

| Decision | When | What the spec records |
|---|---|---|
| **catalog STEP** | a hit at or near your measured parameter | the `id`, the delta from your measurement, and that `cad` imports it via `cadgen.step_scene.import_step` |
| **pocket only** | the component is bought, not printed — bearing, magnet, PCB | the local STEP path and its `sha256`, and that the cavity is derived from that file rather than typed |
| **authored stand-in** | a hit exists but you are deliberately not using it, or the search missed | **the reason**, in one line |

The third row is the one people skip. Rejecting a catalog hit can be legitimate,
but it must carry a reason; an unstated choice is indistinguishable from an
oversight.

A **miss is a result**, not a blank. Record the query that missed so the next
turn does not pay for the same search twice.

**A hit is a file, not a number.** Download it into `<project-dir>/ref/`, for
the reason the reference images live there — a seat derived from a STEP in a
temporary directory cannot be re-verified once that directory is cleaned out:

```bash
python "$STEP_PARTS_SKILL_ROOT/scripts/download_step_part.py" --id <part-id> \
    --download --out-dir <project-dir>/ref
```

Then **do not write the component's own dimensions into the spec**. A servo,
LED module, bearing or board owns its dimensions in a datasheet rather than in
this repository, so a pocket sized by hand cannot be audited by anything: every gate
in the toolchain passes a bracket whose seat is 2 mm too shallow for the motor
it was drawn for. The spec records the file and the pose; `cad` derives the
cavity and the screw pattern from that file with `scripts/cadmount.py`.

Every component the model must physically hold then gets a row in spec section
**6e**, which becomes `measure/mounts.json` for `scripts/check_mount`. Without
that row the seat has no gate at all — `validate`, `interfere`, `check_fit`,
`check_motion` and `check_mesh` all pass a bracket whose screw holes were never
drilled. `$cad`'s `references/bought-parts.md` carries the rest.

### 5d. Research mechanical, electrical and lighting systems before selecting them

For every mechanical mechanism — driven, hand-operated, gravity-loaded or
purely retaining — first write a selection contract: required input and output
motion, travel or angle, direction, load/torque/force when known, speed/duty
when relevant, available envelope, fixed datums, assembly and service path,
print/process constraints, and the evidence needed to accept a candidate.
Search the Internet for applicable mechanism families and cited
implementations, and use `$design-reference` when a build123d construction
analogy would help. Compare the viable archetypes the evidence returns; then
select one and record why the nearest alternative was rejected. A hidden
mechanism may be `[inferred]` or `[assumed]`, but it may not be unresearched.

For every electrical load, actuator or lighting system, write its functional,
electrical, optical and packaging contract before choosing a topology or MPN,
then invoke `$electromechanical-integration` Phase A. That phase performs the
Internet/catalog research and comparison; this spec records its selected
topology, exact devices and rejected alternatives. User-mandated exact hardware
is still researched for ratings, geometry, receiver/contact compatibility and
service requirements before it is accepted into the design.

A functional light needs spec section **8** even when nothing moves. Inventory
the emitter/module, driver/control, visible lens/light-pipe/diffuser, source,
complete power path and physical wire route. Read
`$electromechanical-integration`'s `references/lighting-discovery.md` and let it
run the GitHub → `step.parts` → manufacturer/public-CAD search sequence without
waiting for another user request. The image owns the light's visible position
and optic; the exact MPN, ratings and package geometry come from the selected
component evidence.

A removable lamp also needs spec section **6f** before geometry begins. Select
the exact socket and contacts, prefer the purchased receiver documented for the
lamp family, and give each bought part its own 6c row and 6e mount. Record the
interface datum, lugs, insertion depth, lock rotation/direction, derived
clearance, retention stop, electrical/tool access, and IDs for all five motions:
insert clear, lock clear, locked pull blocked, unlock clear, remove clear. A
custom printed receiver is not permission to invent the mate: it requires
authoritative geometry, bought contacts, `cadfits` derivation and a stated
reason a purchased socket was not used. Specify a three-clearance physical fit
coupon made in the final material/process/orientation with the exact hardware;
until its status is `passed`, report real-world fit as unverified.

A part that moves under a **driving force** — a band, a spring, a motor,
gravity, a hand crank — needs spec section **8** as well as its row in 5a. The
split test tells you the part is separate; it says nothing about what the part
*does*, and Step 6 cannot invent a link length from a silhouette.

A photograph almost never shows the mechanism — it shows the shell over it. So
this section is `[inferred]` and `[assumed]` most of the way down, which is
exactly why it must be written out here instead of left to the build turn to
improvise.

**Every functional electrical load owes a complete power boundary.** A motor,
servo, solenoid or light is a load, never an energy source. The spec states
whether its source is onboard or external, the source voltage/current and
compatibility evidence, the switch or controller, one complete path per
independently rated branch, the connectors and wire route, and how the source
is replaced, charged or disconnected. Every battery holder, switch, controller,
connector, emitter/module or board that the product physically carries gets a
6c catalog row and, when seated, a 6e mount declaration; wires at least get a
routed clearance envelope and strain relief. Visible lenses, bezels and
diffusers remain product geometry. An external source still needs an inlet or
lead, connector and strain relief at the product boundary.

When the brief asks for a self-contained or portable product that runs, spins,
moves or emits light, do not silently put the battery, switch or wiring outside
CAD scope. If
the image and brief do not settle onboard power versus a tethered supply, ask
that one question before Step 6 because the answer changes the body, service
access and mass distribution.

For a driven mechanism, three more things, in order:

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
the feature tree is known and before writing Step 6. Research current Internet
sources with the form/feature/operation query. Prefer manufacturer/standard or
official technical sources for numerical specifications, and licensed source
CAD repositories for construction patterns. Record used, rejected, missed and
unavailable results with stable URL, revision/commit, license, exact
specification or constraint taken, relevant feature and construction lesson.

Compare candidates against the research contract; do not prefer a result merely
because it appeared first. The user's image/spec still owns every dimension,
placement and silhouette that no authoritative product source fixes. Add each
outcome-defining result to spec section **6d**. If the subject is an organic form
for which analogous research cannot help, record
`N/A — no applicable construction analogy` instead of forcing one.

### 5f. Select and freeze the analysis design

After the research logs are complete, fill spec section **6g**. Write one row
for each of these domains: exterior construction, mechanical mechanism,
electrical topology, lighting, and other bought devices. Use `N/A` only for an
inactive domain. Each active row contains:

- the selection contract written before search;
- the Internet research, specifications, constraints and evidence used;
- the viable candidates compared;
- the selected design, including exact MPN/interface when the domain buys one;
- the nearest rejected alternative and the rejection reason;
- any assumption that remains after research.

This is the design decision, not a suggestion list for the CAD turn. By handoff,
CAD must be able to implement the selected construction, mechanism, topology
and devices without choosing among alternatives. If research cannot support a
selection, leave the spec incomplete and put the unresolved decision in Open
questions; do not hide it behind a generic motor, lamp, box or mechanism.

---

## Step 6 — Map every feature to a build123d operation

Implement the selected design from section 6g. Do not silently replace its
mechanism, electrical topology, lamp/interface or bought device while mapping
features. If a Step 6 operation exposes a contradiction, return to the relevant
research contract, revise the selection and update 6g before continuing.

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

**A high-likeness organic subject carries more rules than a family choice.**
Separating silhouette mass from surface decoration, the contact and clearance
rows every seated module owes before the assembly is posed, the section
vocabulary a station table needs beyond a radius, and why a required cue may
not be solved by moving it along the hidden axis are in
`references/high-likeness-organic.md`. **Load it for any animal, figurine or
character, and always for an explicit 90-95 % likeness target.**

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

**A scene of many repeated pieces needs a landmark gate of its own.** A layout
can match its archetype while missing most of what defines it, and a procedural
distribution silently replaces a photographed composition with a new one. The
categories to inventory, the point at which observed centroids stop being
evidence and become assembly coordinates, and the local placement audit that
has to prove count, uniqueness and exclusion-zone clearance are in
`references/repeated-scene.md`. **Load it whenever the reference shows
repeated, individually visible pieces.**

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

## Step 8 — Specify the likeness gate; CAD measures it

The spec's proportion ledger is checked against the *model*. Nothing in the
toolchain checks the model against the *photograph* — which is the only
question an image-derived model exists to answer, and the one every other gate
leaves open. `validate`, `interfere`, `check_fit` and `check_motion` can all
pass a figure that is 60 % of the way there.

This skill has no generator yet, so it cannot honestly render or score a model.
In the spec, list every usable reference as a stable `LABEL=ref/<file>` pair,
set the per-view threshold (default 0.90), and give every landmark a local
verification target. Do not claim a likeness result during this spec phase.

The later CAD phase renders the model from those reference viewpoints and
scores it. The renderer is `render_views.py`, beside the gate; it builds the
shape from the **generator** rather than from the `.step`, so the picture is
answerable to the code and not to an artifact that may predate it.

In this repository the CAD runner owns the final integrated form. It also
requires the spec/source and landmark audits, writes the four orthogonal review
views, checks the fresh STEP against the source, and persists the run record:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> \
    --fresh --exports --image-derived --unpowered \
    --likeness-ref side=ref/03-side.png \
    --likeness-ref front=ref/02-front.png \
    --likeness-ref rear=ref/04-rear.png
```

Replace `--unpowered` with `--powered` whenever section 8a declares a functional
electrical load. Image-derived final mode requires one of those explicit
classifications, so a missing `measure/power.json` cannot become a quiet skip.

The CAD phase's own iteration tools — searching the camera with `--match`
instead of guessing it, flattening a reference whose mask cannot be trusted,
replaying a stored pose so an IoU delta belongs to the shape rather than to the
camera, and measuring an otherwise unobservable dimension by sweeping it
through the gate — are in `references/likeness-gate.md`, with what each costs.
Read it while writing the verification checklist so the handoff carries exact
commands; the document-only phase still runs none of them.

Treat 0.90 as the target, not the pass mark for an unreviewed first attempt,
and read the score as a **floor on the disagreement, never a ceiling on
quality**: it is blind to colour, and on a multi-material reference colour is
much of what a human compares.

Two rules the gate enforces rather than advises:

- **The delivered round has to be the best round.** A run scoring below the
  best that view has ever recorded fails as `regressed-from-best`, however far
  above the floor it lands — against the floor alone, every round between it
  and 1.0 reads `ok`, so the loop can wander downhill and still deliver.
  Overriding it costs `--accept-regression "<reason>"`.
- **The floor cannot be lowered on run 1.** `--accept-mismatch` needs a
  `--report`, and needs two earlier rounds recorded *for the view being
  scored*, against that same reference — rounds spent on another viewpoint do
  not buy it. A mismatch accepted before anything tried to fix it was never
  measured against an attempt, so it cannot justify changing the comparison
  floor. `--accept-regression` likewise needs a `--report`: with no history
  there is no best for it to override.
- **The loop stops after three rounds that move nothing.** `stalled` or
  `regressing` three times running — any `improving` round resets the count —
  and the verdict becomes `stalled out`. It still exits non-zero: rendering a
  shape again does not make it resemble anything. What changes is the
  instruction. The edits have stopped reaching what this gate sees, so the
  remaining decision is whether the measured mismatch is acceptable, and that
  one is the user's, and the gate prints the form of the command that records
  it.

So the spec's job here is to set a threshold that is defensible for the
viewpoint, not one already discounted for a model nobody has built yet.

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

Fill in `templates/build_spec.md`. Write it **into the project directory**
as `<project-dir>/<object_name>_spec.md` (absolute path) so the `cad` turn can
read it, and also render the spec inline in your reply — the user reads it
before approving.

**Name the project directory in the spec.** Every downstream path — `ref/`,
`measure/mounts.json`, `part_<role>.step.py`, every `<project-dir>` in every
command this skill prints — is relative to a directory that nothing else in
the pipeline names. Use `output/<object_name>/` with the object's own name in
snake_case, and never a placeholder (`project_name`, `object_name`,
`my_project`, anything in angle brackets); `check_layout` fails a scaffold name
before anything is built.

The spec belongs inside that directory for the same reason. Final verification
reads the project's own `README.md` and `*_spec.md` to find an assembly path
that prose documents and no `measure/motion.json` proves — a spec parked in the
workspace root is invisible to it, and the check silently finds nothing to
check.

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
| Mount declarations (5c / spec 6e) | `measure/mounts.json` for `scripts/check_mount`, including the exact component path and `sha256` copied from 6c; the seat and bolt pattern `cad` derives from each component's own STEP with `scripts/cadmount.py` rather than typing them |
| Removable-light interfaces (5d / spec 6f) | schema 3 `measure/power.json`, the purchased socket seat or `cadfits`-derived printed receiver, five linked conditions in `measure/motion.json`, and the physical fit-coupon status |
| Design-reference log (5e / spec 6d) | URL-cited construction evidence only; `cad` may reuse the named idiom but does not import or execute external reference code or geometry |
| Analysis design selection (5f / spec 6g) | the construction family, mechanism, electrical topology, lighting strategy and exact bought-device choices that `cad` implements; CAD does not reopen candidate selection |
| Feature table (Step 6), in order | the body of `gen_step()` |
| Mechanism (spec 8) | the kinematic parameters and the feasibility `assert` in `<name>_lib.py`, and `measure/motion.json` for `scripts/check_motion` |
| Approved spec versus repaired source | `measure/check_spec.py`; every CAD repair that changes a parameter, landmark, part count, or construction family is reconciled back into the spec |
| Landmark ledger | `measure/check_landmarks.py`; every defining item gets a count, bbox, station, axis, label, or measured relationship in the built geometry |
| Assumptions | the assumptions bullets in `cad`'s final response |

`cad` then runs the final project workflow through
`scripts/verify_project --image-derived`, supplying every usable reference as
`--likeness-ref LABEL=PATH`, with `--powered` whenever section 8a contains a
functional electrical load and `--unpowered` otherwise. Geometry and manufacturing claims remain
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
- `$design-reference` — Internet research for analogous construction patterns
  and authoritative design specifications. **Load when Step 1F identifies a
  mechanical/product construction question; do not load it for bought
  component geometry or treat an analogy as a source of scale.**
- `$electromechanical-integration` and its
  `references/lighting-discovery.md` — automatic GitHub, catalog and public-CAD
  discovery; authoritative electrical/optical evidence; power paths and CAD
  handoff. **Load whenever Step 1G finds functional lighting or any other
  functional electrical load.**
- `$cad`'s `references/bought-parts.md` — fetching a bought component's STEP,
  deriving the cavity and the screw pattern from that file, why offsetting an
  imported solid silently loses features, and what `check_mount` still cannot
  answer. **Load whenever the model has to hold a motor, servo, LED module,
  bearing, board or any purchased part** — that is every Step 1E/1G row modelled
  as a seat rather than as printed geometry.
- `references/build123d-operations.md` — the full form→operation mapping with
  runnable snippets, the selector cookbook, boolean-order rules, and the
  specific build failure each choice prevents. **Load before writing Step 6.**
- `references/high-likeness-organic.md` — silhouette mass versus surface
  decoration, seated-contact and clearance rows, the section vocabulary a
  station table needs beyond a radius, and why a cue may not be moved along the
  hidden axis to clear interference. **Load for any animal, figurine or
  character, and always for an explicit 90-95 % likeness target.**
- `references/repeated-scene.md` — the per-category landmark inventory, when an
  observed centroid becomes an assembly coordinate, and the placement audit
  that runs before geometry. **Load whenever the reference shows repeated,
  individually visible pieces.**
- `references/likeness-gate.md` — the CAD phase's iteration loop: searching the
  camera with `--match`, flattening an untrustworthy reference, replaying a
  stored pose, sweeping one parameter through the gate, and what each costs.
  **Load when writing the spec's verification checklist**, so the handoff names
  exact commands.

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
  substitute silhouette. Every used result records its Internet URL, revision
  and license; do not download it into a local design-reference store.
- **Analysis owns the design selection.** Section 6g selects every active
  exterior, mechanical, electrical, lighting and bought-device domain before
  CAD handoff. A mechanism, topology, lamp, actuator, socket/contact set or
  other bought device is selected only after its research contract, searches
  and candidate comparison are recorded.
- **A driven mechanism is specified, never implied.** If a part moves under a
  band, spring, motor or gravity, section 8 names the archetype, fixes the link
  lengths, and carries a feasibility `assert`. Every deterministic gate in the
  toolchain passes a linkage that cannot complete its cycle; nothing downstream
  will catch what this section omits.
- **Every functional electrical load has a complete power chain.** A motor,
  servo, solenoid or light is not an energy source. Section 8 names the onboard
  or external source, protection where required, switch/controller, connectors,
  wire route, return path, service access and voltage/current compatibility.
  Lighting also records function, colour and behavior plus every GitHub and
  public component-service search outcome. A removable lamp also names its
  exact socket/contact system, complete mating geometry, five-phase motion
  contract and real-hardware coupon; CAD alone may never be described as proof
  of physical fit. A self-contained or portable powered product may not lose
  its battery and switch as an unapproved "outside CAD scope" assumption.
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
- **Score every round, not just the last one.** Comparing renders by eye between
  edits is the same claim under a different name, and it leaves nothing behind:
  a rebuild loop that renders many times and scores once cannot say whether
  any of the twelve helped. Run the gate with `--report` after each edit and let
  the history's delta column decide whether to keep the change or revert it.
- **Search the camera before blaming the shape.** A fixed orthographic render
  against a photograph measures your guess at the viewpoint, not the model —
  0.865 and 0.974 on the same geometry. Quote the recovered pose alongside the
  IoU, and treat a pose the reference plainly contradicts as a finding.

## Required final response

1. **One sentence** — what the object is and what you spec'd.
2. **The spec** — inline, all seven sections, plus section 8 when any electrical
   load is functional or a part is driven.
3. **Spec file path** — absolute.
4. **Confidence summary** — one line: how many views were observed vs
   reconstructed, and which single assumption most affects the result.
5. **Assumptions** — the `[assumed]` values as bullets, scale anchor first, each
   phrased as something the user can correct in one edit.
6. **Sourcing** — one line per standard element or bought powered component:
   catalog hit used, hit rejected with the reason, search missed, or service
   unavailable. Say "no standard or powered elements" only if Steps 1E and 1G
   found none. Silence here reads as "never looked".
7. **Design references** — Internet URLs/revisions used with the exact sourced
   specification or construction lesson, recorded misses, or `N/A` with the
   reason.
8. **Selected design** — one line per active 6g domain, with the evidence-backed
   choice and nearest rejected alternative.
9. **Next step** — the `cad` handoff line.
