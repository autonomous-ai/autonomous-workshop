---
name: image-to-cad
description: Turn a reference image (photo, render, screenshot, sketch, or orthographic drawing) into a structured, buildable CAD spec — overall read, top/front/side views, real-world size, part and feature decomposition, per-feature detail, and the exact build123d operation each feature is built with. Use when the user attaches an image and wants a 3D model, a printable part, "make this", "recreate this in CAD", or asks how an object would be modelled. Produces the spec that the `cad` skill implements; it writes no geometry itself.
---

# image-to-cad — read a reference image into a buildable CAD spec

## Purpose

Convert one or more reference images into a **build spec** precise enough that
`cad` writes `<name>.step.py` and its `gen_step()` from it with no second look
at the photo.

**You produce a document, not geometry.** No `.py`, no STEP, no STL. Fill
`templates/build_spec.md` — plus `templates/build_spec_powered.md` when a load
is functional or a part is driven — and hand off to `cad`.

Seven sections in this order, plus an eighth when the object has a functional
electrical load or moves under power:

1. **Overall read** — what it is, archetype, construction family.
2. **Top view** (plan, down −Z).
3. **Front view** (elevation, along +Y).
4. **Side view** (elevation, along +X) — then **4b**, every visible component
   in words, before any decision about parts.
5. **Size** — mm, with the scale anchor that produced them.
6. **Decomposition and design selection** — printed parts, feature trees,
   research logs, one evidence-backed selected design per active domain.
7. **Per-feature detail + build123d operation** — geometry, numbers, API call,
   plane/selector, boolean order.
8. **Powered system / mechanism** — power boundary and loads; when driven, also
   archetype, kinematic parameters, feasibility assertion, motion conditions.

## The one rule that makes this skill work

A single photo shows **one** viewpoint. The other two views are reconstructed.
Tag every number:

| Tag | Meaning | Hard dimension? |
|---|---|---|
| `[observed]` | Directly visible and measurable | Yes |
| `[inferred]` | Forced by symmetry, function, or another observed fact — show the reasoning | Yes, with reasoning |
| `[assumed]` | A default you chose | Yes, flagged user-correctable |

An untagged number is a defect. **A confident guess presented as a measurement
is the failure mode this skill exists to prevent** — invisible until the user
holds a part 30 % too small. Never write "roughly", "about", "approximately":
derive it (Step 3), or tag `[assumed]` and give the one line the user edits.

## The loop

```
triage → measure → scale → build 3 views → decompose → write research contracts
   ↑                                                         ↓
   └── revise ← self-critique ← map operations ← select design ← research + compare
```

Close it before the user sees anything; the check step is Step 7.

**Read this file once at the start of the spec turn.** Load a progressive
reference only when its trigger fires. Do not reread this skill mid-loop.

## Before the first run

Resolve the exact materialized skill trees instead of assuming an upstream
repository checkout:

```bash
IMAGE_TO_CAD_SKILL_ROOT="$(workshop skills path)/image-to-cad"
STEP_PARTS_SKILL_ROOT="$(workshop skills path)/step-parts"
CAD_SKILL_ROOT="$(workshop skills path)/cad"
```

Measuring needs `pillow`, `numpy`, `scipy` (`requirements.txt` beside this
file) — not build123d or OCP. `render_views.py` is the exception: it builds the
model, so it needs the kernel.

```
measure_image.py    pixels to ratios, and the cross-check gate  (step 2)
grid_overlay.py     read an organic outline off a labelled grid (step 2)
render_views.py     silhouette, and --shaded review render      (step 8)
check_likeness.py   score that silhouette against the reference (step 8)
ref_silhouette.py   flatten a reference the mask cannot hold    (step 8)
```

```bash
python -m pip install -r "$IMAGE_TO_CAD_SKILL_ROOT/requirements.txt"
```

Install even when `cad` is set up: that venv brings numpy and scipy, but
**Pillow only ever arrives by accident**, so `measure_image.py` fails on
`import PIL`. All five carry fixtures — run `--self-check` after any change to
the mask, the cross-check, or the scoring, since a mask that drops a region and
a gate that mis-scores both fail silently and in the plausible direction.

---

## Step 1 — Triage the image

`Read` every attached image, and **copy each into `<project-dir>/ref/`** before
measuring. Every path in this skill assumes the reference lives there; a spec
citing a temporary location cannot be re-verified, which retires the evidence
behind every `[observed]` number.

**A. What kind of image?**

| Kind | Consequence |
|---|---|
| **Orthographic / blueprint** | Best case. Dimensions may be `[observed]`. Read the title block for units and scale. |
| **Studio render** | Proportions trustworthy; run `measure_image.py`. |
| **Photo in the wild** | Perspective distorts every ratio — correct per `references/view-inference.md` first. |
| **Sketch / concept art** | Intent only. Almost every dimension `[assumed]`. Ask for one governing size. |
| **Screenshot of CAD** | Read the orientation cube if present; treat as orthographic. |

**B. How many views?** Count distinct viewpoints. One 3/4 hero shot is **one**
view — it foreshortens both horizontal axes at once.

- **1** → two views are `[inferred]`/`[assumed]`. Say so in the Overall read,
  first line.
- **2** → the third is `[inferred]`.
- **3 aligned orthographic** → the outline is solved; nearly every proportion
  `[observed]`.
- **4–6** → no more outline; you buy **hidden surfaces** and **redundancy**.

Rank the extra three rather than asking for all of them: **bottom** almost
always (the only sight of the underside — without it the base, sill, chassis
and fastener bosses are invented), **back** when the rear differs from the
front (usually), **other side** only when you suspect asymmetry, since
`symmetry.left_right` already settled bilateral symmetry. Detail:
`references/view-inference.md`.

**No number of views gives absolute scale.** Six views of an unlabelled object
still leave every dimension a ratio; scale comes only from Step 3. State the
count and the ranking in the Overall read.

**C. Symmetric?** The cheapest inference you have. Mirror symmetry turns half
an unobserved view into `[inferred]`; rotational symmetry turns the whole top
view into `[inferred]`. Establish the group once and reuse it.

**D. A known object?** A named product or standard outranks anything measured
from pixels. Web-search the spec, cite it, tag `[observed]` from the source.

**E. Any feature a standard mechanical element?** Separate from D: D fires on a
*name*, E on a *form*, and a form needs no name to be standard. A **gear,
bearing, bolt, screw, nut, washer, rivet, pin, spring, bushing, o-ring,
circlip, chain, belt, pulley, coupling, hinge, caster, magnet, or threaded
insert** is standard whether or not the image labels it. Measure its governing
parameter — tooth count and module, bore and OD, thread and length — then
search `$step-parts` on those numbers before deciding how to model it.
Procedurally authoring one looks like modelling while substituting an
inaccurate stand-in for an available catalog part. Record the outcome — hit
**or miss** — in spec 6c; a miss tells the next turn not to repeat the search.

**F. Would an analogous design resolve a construction question?** Useful for a
mechanical/product form or an uncertain construction family; not a substitute
silhouette for a unique organic subject. Record the one or two
form-and-feature queries worth running after decomposition. Research sourced
specifications and construction evidence — never search by product name and
copy the nearest-looking object.

**G. Any functional light?** A glowing region, coloured lens, beacon, headlamp,
tail lamp, light strip, illuminated button or backlight is a powered landmark
unless the brief makes it inert decoration. Inventory function, position,
colour, behavior and luminous surface, but do not identify an LED from
appearance. Trigger `$electromechanical-integration` now. If the lamp is
removable, discovery must select the mating socket and contacts at the same
time — a lamp MPN without its receiver is not a completed choice. A login wall
is unavailable, not a miss.

**H. Which design domains must this analysis select?** Inventory five: exterior
construction, mechanical mechanism, electrical topology, lighting, other bought
devices. Mark inactive ones `N/A`; every active one ends this turn with a
selected design in spec **6g**.

A construction family forced by the visible form may be selected from image
evidence. A mechanism, topology, actuator, lamp, socket/contact system or
bought device follows a research-first order: write the functional,
dimensional, packaging and evidence contract → research Internet and catalog
sources → extract specifications, constraints, revisions, licenses → compare
candidates and name rejections → select only from that evidence. Do not select
an MPN from appearance and then search for confirmation. The only preselected
exact part is one the user requires, and research still verifies its ratings,
geometry and mating interfaces.

---

## Step 2 — Measure the pixels

Do not eyeball ratios.

```bash
python <skill-dir>/scripts/measure_image.py <project-dir>/ref/<image>.jpg
```

Deterministic — no segmentation network. It estimates the background from the
border ring, thresholds the silhouette, denoises, and reports `bbox`/`aspect`,
`fill_ratio`, `row_profile`/`col_profile` (the taper signal),
`row_bands`/`col_bands` (where loft stations and part splits belong), and
`symmetry`. Stdout is compact JSON; the human summary is on stderr. Field-by-
field interpretation, the shape→family table, and the four ways the silhouette
lies: `references/view-inference.md`.

The **two-sided mask is the default** and admits any region chromatically
distinct from the background *and* attached to the silhouette; when it fires,
`mask.offhue_region_share` tells you a subject region would have been missing.
**Cast shadows are rejected by default** — pass `--no-reject-shadow` only when
the subject's colour genuinely matches its ground.

**Line art defeats the mask, and not obviously.** The denoise deletes 1–2 px
strokes, so a white-interior sheet reports `no object found` on some panels and
a plausible bbox on the ones it half-holds. Flood-fill the white background so
each outline becomes a solid silhouette, then measure the filled images with
this same tool. Anything about 2 px wide still needs a direct ink read.

**`--palette K` is how you measure anything inside the outline** — a stripe, a
cockpit opening, a tyre against its fender, a lens, a panel line. Each cluster
reports hex, share, bbox as a fraction of the object's box, and a per-column
vertical span. Gloss splits one paint into lit and shaded clusters; raise K
until the feature appears. Clusters are colour, not parts.

### Interrogate the mask — do not write a probe script

The numbers an assembly turns on are **interior**. Reach for these first; write
a probe only when none can answer the question, and then say in the spec what
you measured by hand and why, so the next reader knows the instrument changed.
A hand-written probe re-derives the silhouette with an ad-hoc threshold and may
omit shadow rejection, making ratios across views incomparable.

```bash
... --rows 640,720,800   # or a slice: --rows 230:480:10
... --cols 300,512
... --region 169,685,798,960
... --isolate '#6E4A30' --isolate '#C69E4A'
```

- **`--rows` / `--cols`** report the object's runs at each line in original
  pixel coordinates. *Two runs on a row is the fact that the object is two
  parts there*, and the gap is the clearance. `--run-gap N` sets how wide a
  hole must be to count (default 2, so antialiasing is not a gap).
- **`--region x0,y0,x1,y1`** re-reports every measurement for that window, so
  `fill_ratio 0.995` and `row_shape flat` on a base box is *derived* evidence
  of a prismatic extrude. Stamped `scope: REGION ONLY`, `cross_check`
  suppressed — a window's aspect says nothing about L:W:H.
- **`--isolate '#RRGGBB'`** locates a colour you can *name*. Per-channel within
  `--isolate-tolerance` (default 46). **Read `parts`, not `all`**: a colour in
  separate regions gives `all` a box spanning empty space.

Read the JSON, then reconcile it against what you see. The tool measures the
**silhouette**, so it cannot tell a hole from a notch — if `fill_ratio` or
`symmetry` contradicts the image, trust your eyes and say the tool disagreed.

### Read the image directly when the subject is organic

The mask summaries produce no **station table** — one (x, z, half-height) row
per station along a curve — which is what a freeform subject needs. Stamp
coordinates on the image and read them:

```bash
python <skill-dir>/scripts/grid_overlay.py ref/side.png -o tmp/side-grid.png
python <skill-dir>/scripts/grid_overlay.py ref/side.png -o tmp/head.png \
    --crop 300,120,700,520 --zoom 3
```

Labels stay in original image pixels even inside a zoomed crop, so a station
read off the grid and a `--rows` scan are two reads of one instrument and can
be cross-checked.

### The cross-check gate — run it before you write a single ratio

Give the tool two or more canonically named views (`top`/`bottom`,
`front`/`back`, `left`/`right`/`side`) and it adds a `cross_check` block,
solving L : W : H across all of them at once and reporting each view's
disagreement.

```bash
python <skill-dir>/scripts/measure_image.py top.png front.png side.png \
    --views top,front,side
```

**This is the highest-value number the tool produces.** Under ~5 % the images
share one camera scale and every proportion may be `[observed]`. Above it, at
least one view is foreshortened — find the bad view and drop it. **Do not
average**: averaging a foreshortened view into a good one produces a spec that
is confidently, uniformly wrong. Quote the solved ratio and the worst
disagreement in the Overall read.

With exactly three views the residual spreads evenly and **every view reports
the same disagreement** — the gate says the set is bad without saying which
member is. That is what a fourth to sixth view buys: duplicated pairs make the
outlier identifiable.

The gate does **not** catch shadow inflation: a contact shadow enlarges every
view in the same proportion, so the views agree while all remain wrong.

**The gate assumes a plan view is drawn nose-left** — it reads a `top`/`bottom`
view's *width* as the object's length. Rotate top/bottom images nose-left
first, or it reports a disagreement that is not there.

---

## Step 3 — Anchor the scale

Pixels give **ratios**. One real dimension turns every ratio into mm. Take the
first anchor that applies and **state which**:

1. **User supplied a governing dimension** — `[observed]`.
2. **A dimensioned drawing** — read the dimension lines, `[observed]`.
3. **A known object in frame** — measure its pixels, look up its real size,
   divide. `[inferred]`, cite the object and dimension.
4. **A standard the object must meet** — web-search it, cite it, `[inferred]`.
5. **Function forces it** — derive the minimum, `[inferred]`, show the reasoning.
6. **Nothing at all** — pick one governing dimension, `[assumed]`, derive every
   other as a ratio, and put it **first** in Assumptions: *"Everything scales
   with this — change it and the rest follows."*

Then the sanity gate: does it fit a 200×200 mm FDM bed (if not, name the split
or the scale-down)? Is any wall under 0.8 mm (2 × 0.4 mm nozzle) at this scale
— walls do not scale below the nozzle, so a scaled-down model needs them
re-thickened, which changes the look? Is any feature under ~1.5 mm? Flag each.

Anchor lookup table: `references/scale-anchors.md`.

---

## Step 4 — Write the three views

Each view: **outline → internal features → what is hidden → confidence**. mm
throughout, a tag on every number.

**Top view (plan, down −Z)** — the footprint. Outline shape, bounding
rectangle, corner radii, symmetry axes, where the widest point sits along the
length, and every feature appearing *only* in plan (bosses, holes, ribs, the
opening of a cavity). This decides `rect().extrude()` versus a `Sketch`
profile, and it is the view most often missing from a hero shot.

**Front view (elevation, along +Y)** — silhouette, the height breakdown as a
stack of bands (base / body / neck / head, each with a height, summing to the
total), draft or lean angle, ground-contact footprint.

**Side view (elevation, along +X)** — the profile, where taper, lean,
cantilever and overhang live. Depth at each height band, lean angle, and —
critically for FDM — **every surface steeper than 45° from vertical**.

For an unobserved view, write the reconstruction reasoning explicitly.
Perspective correction and recovering a plan from a 3/4 shot:
`references/view-inference.md`.

---

## Step 4b — Describe every component, before deciding any part

Spec section **4b**. One prose entry per **visible component** — what a person
pointing at the object would name — written before the first thought about how
it prints. Body, stripe, fins, tail cavity, socket, lamp, post, base: seven
things a viewer sees, which may still be three printed parts. Which is which is
Step 5's question, and answering it early is how a component vanishes before
anyone describes it.

**No neighbouring section can hold this.** Steps 2–4 describe the whole
silhouette one view at a time; Step 7 describes build123d calls, by which point
the only open question is which API makes the shape. A component never written
down is not caught by a failing gate — it is simply absent, and the model
validates, prints and assembles without it.

Prose, not a table: the detail carrying a likeness is never in the same place
twice. On one component it is that the nose stops in a small spherical cap
instead of a point; on another that only the **inner** face of each fin is
painted, across a strip 5–8 mm wide, so the flame appears only when the lamp is
lit. A "Visual requirement" column reduces both to a clause, and a construction
family states how to build a shape while saying nothing about which shape.

Each entry carries form, size with ranges rather than false precision, how it
meets its neighbours, the detail that only shows on a second look, and **what
breaks if it is wrong** — which is where a real tolerance gets written: *the
post enters the belly at 15–20° from horizontal, nose up and canted slightly
left; a few degrees off and the lamp stops looking like it is climbing* tells a
later reader that ±5 mm on the base diameter is nothing and ±3° on the post is
everything.

Two boundaries a single view cannot settle:

- **A seam or a colour change?** A stripe through the whole cross section and a
  stripe painted on the surface are identical in the photograph and different
  solids in CAD.
- **A component or a bought part?** A lamp in the silhouette is described here
  *and* selected in 6c. Describing it does not excuse skipping the catalog;
  buying it does not excuse leaving it out of the form.

An entry that says no more than its bounding box is not a description. Look
again, or write plainly that it is not resolvable from the available views and
carry that into Assumptions — an honest gap is recoverable, a box nobody
questioned is not. Every entry gets a row in 4b's component ledger, and every
row must survive Step 5's split, `check_landmarks.py`, and the likeness renders.

---

## Step 5 — Decompose, research, and select the design

The order is load-bearing: 5a–5b expose parts, features and interfaces; 5c–5e
research the active domains; 5f selects. Do not fill an exact mechanism,
topology, lamp, actuator or bought device into the selected-design row before
its research log exists.

### 5a. Printed parts — default to ONE

Do not open this step until 4b describes every component; splitting first
answers "what is this object made of" with "what is convenient to print". Each
printed part must account for whole components from 4b — if one is in no part,
say where it went.

Most consumer objects are **one sculpted body**. Split only when the object
physically must come apart: a lid or removable cover; a moving joint; a form
that cannot print in any single orientation; anything larger than the bed; a
part that must be a different material or colour. A visual seam is **not** a
reason to split — model it as a cosmetic groove on one body and say so. Getting
this wrong is the most common way a spec balloons from one clean part into six
that never fit together.

Per printed part: name, purpose, outer envelope, and — with more than one — the
joint type, the **single shared mating dimension**, and the clearance per side.
`cad` derives both halves from that one dimension.

Split test, cosmetic-seam table, print-in-place, base-solid hunting:
`references/decomposition.md`.

### 5b. Feature tree inside each part

Decompose each printed part into an ordered feature list:

1. **Base solid** — the one primitive or profile carrying the mass.
2. **Additive** — bosses, ribs, lugs, handles, flanges, fenders.
3. **Subtractive** — cavities, holes, slots, channels, ports, reliefs.
4. **Finishing** — fillets, chamfers, edge breaks, texture, engraving.

Order is part of the spec: **most stable anchor first**, fillets last (a fillet
before a boolean usually gets consumed or fails). Cut after union unless the
cut is what makes the shape possible.

### 5c. Source standard and bought elements — write the search log

Every element from 1E and every bought electrical item from 1G gets a row in
spec **6c**, hit or miss. Search `$step-parts` on the measured numbers or exact
MPN and read the compact `items`/`total` JSON; the API's `facets` counts cover
the whole catalog rather than the query, so `--facets` is only for learning
which `--family`/`--category` to retry with.

| Decision | When | The spec records |
|---|---|---|
| **catalog STEP** | a hit at or near your measured parameter | the `id`, the delta from your measurement, and that `cad` imports it via `cadgen.step_scene.import_step` |
| **pocket only** | bought, not printed — bearing, magnet, PCB | the local STEP path and its `sha256`, and that the cavity is derived from that file rather than typed |
| **authored stand-in** | a hit exists but you are not using it, or the search missed | **the reason**, in one line |

The third row is the one people skip. Rejecting a hit can be legitimate, but an
unstated choice is indistinguishable from an oversight. A **miss is a result**:
record the query so the next turn does not pay for it twice.

**A hit is a file, not a number.** Download it into `<project-dir>/ref/`:

```bash
python "$STEP_PARTS_SKILL_ROOT/scripts/download_step_part.py" --id <part-id> \
    --download --out-dir <project-dir>/ref
```

Then **do not write the component's dimensions into the spec**. A servo, LED
module, bearing or board owns its dimensions in a datasheet, so a pocket sized
by hand cannot be audited by anything: every gate passes a bracket whose seat is
2 mm too shallow for the motor it was drawn for. The spec records the file and
the pose; `cad` derives the cavity and screw pattern from that file with
`scripts/cadmount.py`.

Every component the model must physically hold gets a row in spec **6e**, which
becomes `measure/mounts.json` for `check_mount`. Without it the seat has no gate
at all — `validate`, `interfere`, `check_fit`, `check_motion` and `check_mesh`
all pass a bracket whose screw holes were never drilled. Rest:
`$cad`'s `references/bought-parts.md`.

### 5d. Research mechanical, electrical and lighting systems before selecting

For every **mechanism** — driven, hand-operated, gravity-loaded or purely
retaining — first write a selection contract: required input and output motion,
travel or angle, direction, load/torque/force, speed/duty, available envelope,
fixed datums, assembly and service path, print constraints, and the evidence
needed to accept a candidate. Search for applicable mechanism families and
cited implementations; use `$design-reference` when a construction analogy
would help. Compare the viable archetypes, select one, record why the nearest
alternative was rejected. A hidden mechanism may be `[inferred]` or
`[assumed]`, but it may not be unresearched.

For every **electrical load, actuator or lighting system**, invoke
`$electromechanical-integration` Phase A — it owns the contract, the automatic
GitHub/`step.parts`/manufacturer search sequence, the candidate comparison, the
complete power boundary, and removable-socket selection. Do not restate its
workflow here; this spec records what it returns:

| It returns | Lands in spec |
|---|---|
| exact devices, ratings, package geometry, `sha256` | **6c** (with a 6e mount for anything seated) |
| selected topology, rejected alternatives | **6g** |
| socket/contact system and mating geometry for a removable lamp | **6f**, plus five motion IDs — insert clear, lock clear, locked pull blocked, unlock clear, remove clear |
| source, protection, switch/control, connectors, wire route, return path, service access | **8a** |

Trigger it without waiting for another request. The image owns the light's
visible position and optic; the MPN, ratings and package geometry come from
component evidence, never appearance. Visible lenses, bezels and diffusers
remain product geometry. When the brief asks for a self-contained or portable
product that runs, spins, moves or emits light, do not silently put the
battery, switch or wiring outside CAD scope; if the image and brief do not
settle onboard versus tethered, ask that one question before Step 6, because
the answer changes the body, service access and mass distribution. Until a
removable lamp's three-clearance fit coupon — final material, process and
orientation, exact hardware — is `passed`, report real-world fit as unverified.

A part moving under a **driving force** — band, spring, motor, gravity, hand
crank — needs spec **8** as well as its 5a row. The split test says the part is
separate; it says nothing about what the part *does*, and Step 6 cannot invent
a link length from a silhouette. A photograph almost never shows the mechanism
— it shows the shell over it — which is exactly why this is written here rather
than improvised at build time. Three things, in order:

1. **Name the archetype.** "Runs on a rubber band" is a power source, not a
   mechanism. A crank-rocker four-bar, a slider-crank, a pull-back flywheel and
   a cam-follower are — each with a different parameter set, part count and
   visible form. Choose one, record what you rejected. When the choice changes
   the outline and the image cannot settle it, that is the question worth asking.
2. **Write the parameters as numbers** — fixed pivots in assembly coordinates,
   link lengths, joint limits, phase offsets — and make Step 6's features derive
   from them rather than restate them. A pivot appearing in both section 7 and
   section 8 is two numbers that will drift apart.
3. **Write the feasibility condition as an `assert`** for `<name>_lib.py`. A
   four-bar violating Grashof, a slider overrunning its slot, a cam whose
   follower leaves its track: each validates, exports, prints, then jams.
   `validate`, `interfere`, `check_fit` and `check_mesh` all pass them. That
   assert is the only thing that does not.

Then write the motion conditions into the verification checklist — **both**
directions of every joint, with `blocked` pointing the way the drive pulls — so
the build turn emits `measure/motion.json` rather than deciding for itself.
What a rigid-body sweep cannot reach — band force, gait, friction retention,
elastic recovery, snap-fit compliance — goes in 8d and then Open questions.
Those need a print, not a gate.

### 5e. Search analogous designs — patterns, never dimensions

When 1F found a real construction question, use `$design-reference` after the
feature tree is known and before Step 6. Prefer manufacturer/standard sources
for numbers and licensed CAD repositories for construction patterns. Record
used, rejected, missed and unavailable results with stable URL,
revision/commit, license, the exact specification taken, and the construction
lesson. Do not prefer a result because it appeared first. The user's image
still owns every dimension, placement and silhouette no authoritative source
fixes. Each outcome-defining result goes in spec **6d**; for an organic form
where analogy cannot help, record `N/A — no applicable construction analogy`.

### 5f. Select and freeze the analysis design

After the research logs are complete, fill spec **6g** — one row per domain:
exterior construction, mechanical mechanism, electrical topology, lighting,
other bought devices. `N/A` only for an inactive domain. Each active row:

- the selection contract written before search;
- the research, specifications, constraints and evidence used;
- the viable candidates compared;
- the selected design, with exact MPN/interface when the domain buys one;
- the nearest rejected alternative and the reason;
- any assumption remaining after research.

This is the design decision, not a suggestion list. By handoff, CAD must be
able to implement the selected construction, mechanism, topology and devices
without choosing among alternatives. If research cannot support a selection,
leave the spec incomplete and put the decision in Open questions; do not hide
it behind a generic motor, lamp, box or mechanism.

---

## Step 6 — Map every feature to a build123d operation

Implement the design selected in 6g. Do not silently replace its mechanism,
topology, lamp/interface or bought device while mapping features; if an
operation exposes a contradiction, return to the research contract, revise the
selection, and update 6g first.

One row per feature, six columns, so `cad` never has to invent an approach:

`feature | geometry + numbers | build123d call | plane / selector | order | risk`

Pick the construction family from the **form**, not from habit. This is the
highest-consequence decision in the spec — a form authored in the wrong family
cannot be rescued by parameter edits, only by re-authoring.

| The image shows… | Author as | build123d idiom |
|---|---|---|
| Constant cross-section (box, tray, bracket, plate) | Extrude | `Box(w, d, h)`, or `extrude(amount=h)` over a `BuildSketch` |
| Constant section + uniform draft | Tapered extrude | `extrude(amount=h, taper=3)` |
| Rotationally symmetric (vase, knob, bottle, dome) | Revolve | `Polyline(...)` → `make_face()` → `revolve(axis=Axis.Z)` |
| Section changes along the length — fuselage, hull, swoosh, grip | **Loft over ≥3 stations** | one wire per station from a shared `section_at(t)` helper → `Solid.make_loft(wires, ruled=True)` |
| Constant-ish section following a curved path (tube, rail, strap) | Sweep | `sweep(is_frenet=True)` |
| Planar arch — roll hoop, handle, bail | Extruded ellipse band | two concentric `Ellipse`s, clipped, `extrude(amount=d)` |
| Hollow shell of uniform wall | Shell | `offset(body, -wall, openings=body.faces().sort_by(Axis.Z)[-1])` |
| Non-trivial 2D outline | Sketch | `Rectangle()` → `fillet(sk.vertices(), r)` → `Circle(mode=Mode.SUBTRACT)` → `extrude()` |
| Repeated feature on a line/grid | Array | `with GridLocations(dx, dy, nx, ny): Hole(r)` |
| Repeated feature around an axis | Polar array | `with PolarLocations(r, n): ...` |
| Painted stripe, inlay, or lens on a sculpted skin | Conformal skin patch | `(inflated_loft - raw_loft) & tool` |
| Blended organic mass | Loft stack, bevels baked into the section | `Solid.make_loft()`; keep 3D `fillet()` off tangent chains |

**Do not downgrade organic silhouette features to boxes.** On animals,
figurines, toys, characters, vehicles and product shells, a crest, casque,
horn, fin, brow, cheek, muzzle, fairing, canopy or raised colour lobe that is
visibly rounded or tapered is part of the reference silhouette — author it as a
loft, sweep, revolved cap or conformal skin patch. Use `Box()` only where the
reference shows hard planar faces and square edges. If you simplify an organic
feature, preserve its silhouette envelope and mark the row's risk a deliberate
simplification.

Then name the **selector** per feature — this is where image-derived specs most
often fail to build. Never use `Plane.rotated()` on a non-global plane: it
composes in world axes and silently yaws what you meant to pitch. Re-select
after every boolean, since a face list captured earlier refers to faces that no
longer exist. Selector cookbook, worked snippets and boolean-order rules:
`references/build123d-operations.md`.

Mixed objects decompose naturally: a lofted outer skin carrying the image, with
extruded/booleaned interior carrying the engineering. Say which is which.

**A high-likeness organic subject carries more rules than a family choice** —
separating silhouette mass from surface decoration, the contact and clearance
rows every seated module owes, the section vocabulary a station table needs
beyond a radius, and why a required cue may not be solved by moving it along
the hidden axis: `references/high-likeness-organic.md`.

## Step 6b — Depth comes from the elevations, not from what occludes what

Occlusion order is weak evidence and may conflict across views. Take lateral
placement from near-orthographic elevations where offsets are measurable, and
record unresolved conflicts in Assumptions.

## Step 7 — Prove the read, then self-critique

**Proportion ledger.** Extract 4–6 ratios and put them in the spec as
assertions to check after generation with `scripts/inspect`, ±10 %:

- overall length : height : depth;
- ground-contact length ÷ total length (a "floating" stance is a *measurable*
  short contact patch, not a vibe);
- where the widest/tallest point sits along the length;
- wall thickness ÷ overall width, if a wall is visible at an opening;
- the height of any undercut ÷ body height.

A ledger makes the next edit cheap: the numbers name which aspect of the form
drifted.

**`check_spec_format` now owns the mechanical half of this review** — untagged
dimensions, leftover template placeholders, a scaffold project directory, a
functional load with no section 8, a section 8 with no feasibility `assert`, a
joint declared in only one direction, and a likeness floor pre-discounted below
0.90. Run it on the spec you just wrote; it is static and costs milliseconds:

```bash
python "$CAD_SKILL_ROOT/scripts/check_spec_format" <project-dir>
```

**Then critique what no gate can see**, and fix what fails:

- Does the top view contain a feature the front view contradicts?
- Do the front view's height bands sum to the stated total height?
- Does the side view's depth agree with the top view's depth?
- Is any feature in the tree missing a build123d operation?
- Does any feature float — added to nothing, connected to nothing?
- Does a pivot or link length appear in both section 7 and section 8?
- Does the `blocked` direction of every joint point along the drive direction?
- Would every construction family survive the actual form? (A tapering body
  specified as `.extrude()` is wrong **by construction**, not "close enough".)
- Print check: bed size, minimum wall, minimum feature, overhangs > 45°, and
  one named print orientation.

**Soft cap: 2 revision passes.** Past that the gap is user intent, not
analysis — ask one question.

**A scene of many repeated pieces needs a landmark gate of its own**, since a
layout can match its archetype while missing most of what defines it:
`references/repeated-scene.md`.

---

## Step 8 — Specify the likeness gate; CAD measures it

The proportion ledger is checked against the *model*. Nothing else in the
toolchain checks the model against the *photograph* — the only question an
image-derived model exists to answer. `validate`, `interfere`, `check_fit` and
`check_motion` all pass a figure that is 60 % of the way there.

This skill has no generator, so it cannot honestly render or score. In the
spec, list every usable reference as a stable `LABEL=ref/<file>` pair, set the
per-view threshold (default 0.90), and give every landmark a local verification
target. **Do not claim a likeness result during this phase.**

Set a threshold defensible for the viewpoint, not one already discounted for a
model nobody has built yet. Treat 0.90 as the target, not the pass mark for an
unreviewed first attempt, and read the score as a **floor on the disagreement,
never a ceiling on quality** — it is blind to colour, and on a multi-material
reference colour is much of what a human compares.

The CAD phase renders from those viewpoints and scores. `render_views.py`
builds from the **generator** rather than the `.step`, so the picture is
answerable to the code. In this repository the CAD runner owns the final
integrated form:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> \
    --fresh --exports --image-derived --unpowered \
    --likeness-ref side=ref/03-side.png \
    --likeness-ref front=ref/02-front.png \
    --likeness-ref rear=ref/04-rear.png
```

Use `--powered` whenever section 8a declares a functional electrical load.
Image-derived final mode requires one of the two explicitly, so a missing
`measure/power.json` cannot become a quiet skip.

**A silhouette is for the gate; look at the model with `--shaded`.** A
machine's identity is interior — slots, pockets, bores, a pin on an arm, one
part seated in another — and a filled outline shows none of it: an assembly
renders as a single blob whose parts cannot be told apart at any resolution.
`--shaded` writes `<label>-shaded.png` **beside** each mask, never instead of
it, with frame and camera matching exactly. Use it for every appearance review,
the mask for every score; neither replaces the other, and neither sees colour
or material the way a person does.

Three rules the gate enforces rather than advises: **the delivered round has to
be the best round** (a run below the best that view ever recorded fails as
`regressed-from-best`, since against the floor alone the loop can wander
downhill and still deliver); **the floor cannot be lowered on run 1**
(`--accept-mismatch` needs a `--report` and two earlier rounds *for that view*
against that same reference); and **the loop stops after three rounds that move
nothing**, printing the command that records the user's acceptance.

The CAD phase's iteration loop — searching the camera with `--match` instead of
guessing it, flattening an untrustworthy reference, replaying a stored pose so
an IoU delta belongs to the shape, sweeping a dimension through the gate, and
what each costs — is in `references/likeness-gate.md`. Read it while writing
the verification checklist so the handoff carries exact commands; this phase
runs none of them.

## Ask only about preferences

The user verifies **taste**, never **geometry**.

- **Ask** (only when it changes geometry): intended real size when no anchor
  exists; which device it must fit; whether a visible seam is functional or
  cosmetic; whether an unobservable back face matters.
- **Never ask** (decide silently): wall thickness, fillet radius, clearance,
  joint type, fastener size, print orientation, construction family, feature
  order.

Ask the fewest, highest-leverage questions — ideally one, never a quiz.

---

## Output

Fill `templates/build_spec.md`, write it to
`<project-dir>/<object_name>_spec.md` (absolute path) so the `cad` turn can
read it, and render it inline in your reply. Sections 6f and 8 and the powered
checklist live in `templates/build_spec_powered.md`; read that file only when
Step 1G found a functional load or Step 5d found a driven part, and paste its
sections in at their numbered positions.

**Name the project directory in the spec.** Every downstream path is relative
to a directory nothing else in the pipeline names. Use `output/<object_name>/`
in snake_case, never a placeholder (`project_name`, `object_name`,
`my_project`, anything in angle brackets) — `check_layout` fails a scaffold
name before anything is built.

The spec belongs inside that directory: final verification reads the project's
own `README.md` and `*_spec.md` to find an assembly path that prose documents
and no `measure/motion.json` proves. A spec parked in the workspace root is
invisible to it, and the check silently finds nothing to check.

If the user gives an output root, run/version pattern, or "new folder every
run" rule, the spec path and every downstream CAD path must use that exact
fresh directory. Do not silently reuse a previous project directory under a
different name.

## Handoff to cad

> Spec written to `<abs path>`. To build it: use the `cad` skill with this spec —
> it becomes one `<name>.step.py` whose named parameters are the Size table and
> whose `gen_step()` body is the feature table, in order.

| Spec section | Becomes |
|---|---|
| Size + proportion ledger | the named parameters at the top of `<name>.step.py` |
| Ledger assertions, print checks | checks after generation — `inspect refs --facts` for bounds, targeted `measure`/`align` for the rest |
| Printed parts (5a) | labelled children of the `cadgen.assembly.AssemblyHelper` compound |
| Catalog search log (6c) | `cad` skips its own `$step-parts` pass for every row decided here, and imports each hit with `cadgen.step_scene.import_step` |
| Mount declarations (6e) | `measure/mounts.json` for `check_mount`, with the component path and `sha256` from 6c; `cad` derives the seat and bolt pattern from the component's own STEP with `cadmount.py` rather than typing them |
| Removable-light interfaces (6f) | schema 3 `measure/power.json`, the purchased socket seat or `cadfits`-derived receiver, five linked conditions in `measure/motion.json`, and the coupon status |
| Design-reference log (6d) | URL-cited construction evidence only; `cad` may reuse the named idiom but does not import or execute external reference code or geometry |
| Design selection (6g) | the construction family, mechanism, topology, lighting strategy and bought-device choices `cad` implements; CAD does not reopen selection |
| Feature table (Step 6), in order | the body of `gen_step()` |
| Mechanism (spec 8) | the kinematic parameters and feasibility `assert` in `<name>_lib.py`, and `measure/motion.json` for `check_motion` |
| Approved spec vs repaired source | `measure/check_spec.py`; every repair changing a parameter, landmark, part count or construction family is reconciled back into the spec |
| Landmark ledger | `measure/check_landmarks.py`; every defining item gets a count, bbox, station, axis, label or measured relationship |
| Assumptions | the assumptions bullets in `cad`'s final response |

`cad` then runs `verify_project --image-derived` with every usable reference as
`--likeness-ref LABEL=PATH`, and `--powered`/`--unpowered` per section 8a.
Geometry and manufacturing claims stay deterministic; the renderer supplies
separate visual evidence and cannot substitute for validate, interference, fit,
mesh, motion, mount or thickness checks. A source repair leaving this spec
stale is a failed handoff, even when the geometry improved.

Do **not** invoke `cad` yourself unless the user asks to build.

---

## Progressive references

Load only when the trigger fires.

| Reference | Load when |
|---|---|
| `references/view-inference.md` | fewer than 3 orthographic views — i.e. almost always. Before Step 4. |
| `references/scale-anchors.md` | no dimension was given. |
| `references/decomposition.md` | visible seams, moving parts, or more than ~6 features. |
| `references/build123d-operations.md` | before writing Step 6. |
| `references/high-likeness-organic.md` | any animal, figurine or character; always for an explicit 90–95 % likeness target. |
| `references/repeated-scene.md` | the reference shows repeated, individually visible pieces. |
| `references/likeness-gate.md` | writing the verification checklist. |
| `templates/build_spec_powered.md` | spec sections 6f, 8 and the powered checklist — a functional electrical load (1G) or a part driven under force (5d). |
| `$cad`'s `references/organic-lofts.md` | the subject is an animal, figure, hull, or any body whose section changes along a curved spine. |
| `$cad`'s `references/bought-parts.md` | the model must hold a motor, servo, LED module, bearing, board or any purchased part — every 1E/1G row modelled as a seat. |
| `$design-reference` | Step 1F identifies a construction question. Not for bought-component geometry, and never as a source of scale. |
| `$electromechanical-integration` + its `references/lighting-discovery.md` | Step 1G finds functional lighting or any functional electrical load. |

## Non-negotiables

- **Every number carries a confidence tag.**
- **Run the cross-check gate whenever you have 2+ views** and quote its verdict.
- **Never invent a dimension for a named real-world product.** Cite or ask.
- **Never author a standard mechanical element without searching the catalog.**
  A gear you drew and a catalog hit you rejected look identical in the finished
  model; section 6c is what tells them apart.
- **Never let an analogous design override the user's evidence.** 6d supplies a
  construction idiom, never dimensions, scale, placement or a substitute
  silhouette.
- **Analysis owns the design selection.** 6g selects every active domain before
  handoff, only after its contract, searches and comparison are recorded.
- **A driven mechanism is specified, never implied.** Section 8 names the
  archetype, fixes the link lengths, and carries a feasibility `assert`. Every
  deterministic gate passes a linkage that cannot complete its cycle.
- **Every functional electrical load has a complete power chain** — source,
  protection, switch/controller, connectors, wire route, return path, service
  access, voltage/current compatibility. A removable lamp also names its exact
  socket/contact system, mating geometry, five-phase motion contract and
  real-hardware coupon; CAD alone is never proof of physical fit. A portable
  powered product may not lose its battery and switch to an unapproved
  "outside CAD scope".
- **No geometry.** This skill writes markdown.
- **Never present a single 3/4 photo as three observed views.**
- **Millimetres throughout.**
- **Every feature has an operation and a selector.**
- **Match the form's construction family.** A double-curved body specified as a
  constant-depth extrusion is a defect, not an approximation.
- **Score the likeness; never assert it.** Quote the mean IoU and the worst
  band, and say which edit the band names. "Looks close" is the claim this
  skill exists to replace with a number.
- **Score every round, not just the last one.** A rebuild loop that renders
  many times and scores once cannot say whether any of them helped. Run the
  gate with `--report` after each edit and let the delta column decide whether
  to keep the change.
- **Search the camera before blaming the shape.** A fixed orthographic render
  against a photograph measures your guess at the viewpoint, not the model.

## Required final response

1. **One sentence** — what the object is and what you spec'd.
2. **The spec** — inline, all seven sections, plus 8 when any load is
   functional or a part is driven.
3. **Spec file path** — absolute.
4. **Confidence summary** — views observed vs reconstructed, and the single
   assumption that most affects the result.
5. **Assumptions** — `[assumed]` values as bullets, scale anchor first, each
   correctable in one edit.
6. **Sourcing** — one line per standard element or bought powered component:
   hit used, hit rejected with reason, search missed, or service unavailable.
   Say "no standard or powered elements" only if 1E and 1G found none. Silence
   reads as "never looked".
7. **Design references** — URLs/revisions with the exact sourced specification
   or construction lesson, recorded misses, or `N/A` with the reason.
8. **Selected design** — one line per active 6g domain, with the choice and the
   nearest rejected alternative.
9. **Next step** — the `cad` handoff line.
