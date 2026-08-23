---
name: cadcode
description: Use when the user wants to create, edit, or print a parametric 3D model from a natural-language description — "phone stand", "wall mount", "honeycomb tray", "GoPro adapter", "vase" — or to tweak, re-render, or fix an existing CadQuery `.py` part for hobbyist 3D printing.
---

# CADCode — hobbyist 3D CAD via CadQuery

## Purpose

Turn natural-language descriptions of 3D parts into printable, inspectable
3D models. The source of truth is **CadQuery Python** (B-rep on OpenCASCADE
— same kernel as SolidWorks / FreeCAD). Every generated `.py` file is a
small, editable parametric program. The user owns the file; tweak
parameters, re-render, re-print.

Optimised for **hobbyist 3D printing**, not commercial CAD. The deliverable
is an archival STEP plus a watertight STL that the user's slicer can ingest
and that the viewer renders as the preview.

## Treat the design as a project

**A design is a small software project, not a single script.** Trivial parts
(a cube with a hole, a plate, a single hex tray) fit in one `.py` file.
Anything bigger — multi-part assemblies, designs with many features, any
part with more than ~120 lines of code — gets a project directory.

A project looks like:

```
my_design/
├── spec.md             design intent (English, human-readable)
├── params.py           ALL dimensions + manufacturing constants
├── validation.py       runtime constraints (printability, fit, sanity)
├── main.py             entrypoint — defines `gen_step()` (preferred) or
│                       assigns `result` (legacy single-file form)
├── parts/              one file per physical part
│   ├── __init__.py
│   ├── base.py
│   └── cover.py
├── features/           reusable feature functions (cutouts, vents, …)
│   └── __init__.py
└── assemblies/         positioning + union of parts
    ├── __init__.py
    └── product.py
```

`scripts/cad <project_dir>/` calls cadpy's artifact pipeline, which reads
``main.py`` with the project directory on ``sys.path`` (so ``from params
import Params`` and ``from parts.base import …`` work), then calls
``gen_step()``. **Use `Skill(skill='cadcode')` and `Read`
`templates/project_skeleton/` when you need the canonical layout** — copy
it to the user's workspace, edit, run.

Rules of the project format:

- **All dimensions live in `params.py`.** Geometry code never hardcodes
  numbers. The user (or you next turn) edits a value once; nothing else
  changes. Bad: `.box(120, 80, 35).shell(-3)`. Good: `.box(p.width, p.depth, p.height).shell(-p.wall)`.
- **`main.py` defines `gen_step()`** at module scope. It returns one of:
  a ``cq.Workplane`` / ``cq.Shape`` (single solid), a ``cq.Assembly``
  (multi-part hierarchy with names + colors + locations), or an
  envelope ``dict`` like ``{"shape": <…>, "stl": True, "mesh_tolerance":
  0.03}`` when you want to tune mesh fidelity or request extra output
  formats (see the [Artifact-control envelope](#artifact-control-envelope)
  section). The legacy ``result = <shape>`` form is still accepted for
  trivial single-file scripts — the runner treats it as if
  ``gen_step()`` returned ``result``.
- **Every mating interface shares one dimension.** Both halves of a mate
  derive from a **single** base value in `params.py`, with the FDM clearance
  applied in exactly **one** place — never size the two halves independently.
  Full rule + the helpers that enforce it: step 6 of "Running the loop".
- **One file per physical part** under `parts/`. Each part knows nothing
  about its siblings; it builds in its own local frame.
- **Each feature is its own function.** `add_left_usb_c_cutout(part, p)`,
  not nested inline. Compose them in a pipeline so each edit has a clear
  target.
- **Assembly = positioning + union, never geometry.** Build parts in
  `parts/`, place them in `assemblies/`.
- **`validation.py` runs at startup** with `assert` checks on Params.
  Bad dimensions fail loudly before paying a render cycle.

### Artifact-control envelope

For most parts, return the shape directly from ``gen_step()`` and let the
defaults handle the export. When you need control:

```python
def gen_step():
    body = build_my_part(p)
    return {
        "shape": body,                       # required: cq.Workplane | cq.Shape
        "mesh_tolerance": 0.03,              # mm, default 0.05
        "mesh_angular_tolerance": 2.0,       # deg, default 3.0
    }
```

The envelope keys (``shape`` | ``instances`` | ``children`` for content;
``mesh_tolerance`` / ``mesh_angular_tolerance`` for output) are all that the
cadpy pipeline accepts — unknown keys raise. The ``.stl`` is always written;
no envelope flag is needed.

See `references/project-structure.md` for the long version.

## The loop

The cadcode skill turns you into a self-correcting CAD designer. **You close
the feedback loop yourself** — do not hand a possibly-broken model to the
user for verification.

```
understand task → inspect repo → make plan → edit .py → run scripts/cad
       ↑                                                       ↓
       └────────── fix ←─── read failure / render ←────────────┘
```

What "fix" means in practice:

- ``ok=false``: read the traceback, change the smallest responsible line, re-run.
- ``is_solid=false`` or volume far off expected: load `references/repair-loop.md`, classify, fix, re-run.
- ``warnings`` non-empty: deterministic geometry defects — any non-`info` warning is **blocking** (full taxonomy: Non-negotiables). For ``disconnected_bodies``, anchor the floating feature to the body (`references/patterns/anchor-to-body.md`) or, for a mechanism, solve the joint so the links actually meet (`references/kinematic-placement.md`). For ``collision``, reposition or resize so mating faces meet at the right clearance. Fix and re-run.
- Preview STL looks wrong (proportions off, hole misplaced, parts misaligned, a member poking through a plate): edit the `.py` and re-run. **Always inspect every part** — geometry can be valid (`is_solid=true`, no warnings) but still wrong.

You have everything you need to close the loop on your own:

- The user's prompt and any attached reference image (inspect).
- The current workspace files including prior `.py` versions (inspect).
- `scripts/cad` for compile + solid check + STEP/STL/metadata export (run).
- `scripts/check` for a quick validation when you only need a sanity check (run).
- This SKILL.md + the references for domain knowledge (plan).

**Iterate until the model is correct.** Soft cap of 4 iterations before you
ask the user a clarifying question — past that, you're probably guessing
about user intent rather than fixing a geometry bug. Closing the loop is
what makes you feel like an engineer instead of an autocomplete.

## Plan-phase design discipline

When Vibe runs you in its **Plan phase** (enforced by the phase system
prompt: no writing `.py`, no running the generator), you write no geometry —
you produce the plan the user approves before the build. That plan
is an **engineering spec**, not a sales pitch. Hold it to five rules:

1. **Exact measurements.** Every dimension, quantity, and metric is a precise
   number with a unit. Never "about", "roughly", or "approximately" — if you
   don't know a value, derive it (below) or ask the user.
2. **Component-level breakdown.** List each distinct part with its outer
   dimensions, material, and purpose, and state exactly how parts connect —
   joint/feature type, mating dimensions, clearance/tolerance, attachment
   points, alignment. A single-part object still lists its one part.
3. **Physical correctness.** Account for gravity, balance, load-bearing, center
   of mass, structural stability, and FDM layer-line orientation. State your
   assumptions and confirm the design behaves under real-world conditions. Show
   only the checks that apply — for a part with no load case (decorative, a
   loose-fit cover), say so in a clause rather than inventing a load.
4. **Show the math.** For each derived or load-bearing number, show the formula
   and the values used so a reader can check it: `name = formula = value unit`.
5. **Verification checklist.** End the plan with the explicit list the build will
   clear one item at a time, each paired with how it is checked — a SANITY check
   (a number / `validate()` assert / `functional` warning) and a VISUAL check
   (which render, or a **cross-section** for an interior interface). Two groups:
   **(A) per component** — every feature sits on solid material (no tooth / peg /
   boss / rib over a void, hole, or notch) and depths actually reach; **(B) per
   interface** — each mating pair (peg/socket, clutch, gear, tab/slot, lip/groove)
   actually meets and can transmit its force (form-fitting, not a smooth pocket
   over round pegs), with the right clearance and a reachable assembly path.

**Scale to the request.** A trivial edit ("make the wall 2 mm thicker", "move
the holes 5 mm apart") needs only the exact before→after values and any physical
consequence — one to three lines. A new part or any multi-part / load-bearing
design gets the full treatment.

**Aesthetic discipline.** A Vibe part should look like a premium consumer
product (Apple-anchored, but a broad high-end range — see
`references/industrial-design.md`), not a blocky CAD default. For any
user-facing part, give each part in the plan a one-line **`Form`** clause naming
its radius language (the unified corner/edge radius and where it's applied) and
its primary surface treatment (e.g. "4 mm unified vertical radius, 1 mm top
chamfer, calm front face, fasteners hidden on the back"). This is **secondary to
function and printability** — never trade away strength, wall thickness,
tolerance, clearance, or print orientation for looks; if an aesthetic choice
would compromise the part, say so and pick function. Trivial edits skip the
`Form` clause.

**Assembly & functional discipline.** A part that is a valid solid but can't be
assembled or used is a failure — whether it can't be *installed* (a MagSafe stand
whose puck *pocket* is perfect but whose **captive cable + connector collar**
can't pass the opening) or can't *function* (a dial that sits clear of its drive
pegs, so turning it does nothing). For any design with a real component or a
moving / mating mechanism, the plan must include:
- **Assembly & setup sequence** — the ordered steps to assemble and set up the
  finished print (install each component, route its cable/connector, place the
  device), and the clearance each step needs. Model the WHOLE component,
  including captive cables, connector collars, and plugs — **web-search the
  component's dimensions** (body, cable Ø, connector-collar Ø×len) and state them
  as assumptions the user can correct.
- **Functional requirements** — what it must do (hold / charge / route / rest /
  remove / drive / mesh), each tied to a dimension and carried into the
  Verification checklist (rule 5).

Read `references/component-integration.md` for the discipline. Encode the
constraints two ways (see the build loop): hard `validate()` asserts for
impossible fits, and `functional` warnings for assembly-feasibility. Trivial
edits skip this.

### Where the numbers come from — source them, don't guess

Every number you put in the model comes from exactly one of three places. Know
which, and never invent one.

1. **Real-world dimensions of a named product** (a phone, a motor, a doorbell, a
   bearing you don't recognize, a mount standard, a connector collar) — **web-search
   the manufacturer/catalog spec**, then **state it as an assumption the user can
   correct** and round for printing. Don't carry these from memory; they drift by
   model/region and a confident guess is the classic failure. If a search can't
   pin a specific device, say so and ask the user for the dimension.
2. **Hardware the cadlib helpers already cover** (screws, nuts, bearings, magnets,
   heat-set inserts, common cable jackets) — the helper owns the dimensions; pass
   it a named size (`bearing="608"`, `screw_size="M3"`) and let
   `cadlib/tables.py` supply the geometry. Don't transcribe those numbers into
   your model. For an open-ended fit the helper takes a raw dimension
   (`cable_diameter=…`) — that's where a web-searched value goes.
3. **Generic FDM best-practice** (tolerances, wall thickness, boss sizing, fits) —
   use the rules below, which are formulas, not lookups:

| Best-practice rule | Load for the why |
|---|---|
| `wall = N × nozzle` (0.4 mm nozzle → 0.8 / 1.2 / 1.6 / 2.0 / 2.8 mm; 2.0 mm enclosure, 2.8 mm + ribs load-bearing) | `references/patterns/wall-thickness-rules.md` |
| Clearance hole `= nominal + 0.3–0.4 mm`; self-tap `= major − 0.3 mm`; cbore `= cap-head Ø + 0.5 mm` | `references/hobbyist-defaults.md` |
| Boss OD `= 2·clearance + 2·wall`; screw engagement `= 2·screw-Ø` | `references/patterns/screw-boss.md` |
| FDM slop: press-fit `+0.2`, hand-assembly `+0.4`, snap/interference `0.3–0.5 mm` | `references/hobbyist-defaults.md` |
| Rib vs wall stiffness (one rib ≈ 5–10× cheaper than doubling walls; `h³`) | `references/patterns/rib-stiffener.md` |

Material properties (e.g. PETG ≈ 0.6× PLA stiffness and creeps under sustained
load) are starting assumptions — keep the engineering formula but label the
constant as one to verify/web-search for the user's actual material.

### Physics checklist — what to show

- **Tip-over / balance:** center of mass vs support footprint. Compute the
  horizontal CoM offset and compare to the base edge:
  `x_CoM < base_overhang` ⇒ stable; report the margin.
- **Load path / bearing stress:** where weight enters, what carries it to the
  ground or mount, and the fastener/wall that takes the reaction.
- **Stiffness / deflection:** wall thickness and ribs for the stated load;
  remember doubling thickness is 8× stiffer (`h³`), a rib is usually cheaper.
- **FDM layer orientation:** a load pulling *across* the layer lines is far
  weaker (e.g. boss pull-out drops ~50%). State the print orientation wherever
  strength matters.
- **Build volume:** confirm the part fits the printer (a Bambu bed is ≈ 256 mm
  cube — verify for the user's printer model; cadpy's sanity bound is 200 × 200 mm).
- **Assumptions to state:** material (and its density/stiffness), applied load,
  orientation in use, support condition (free-standing, wall-mounted, clamped).
  Label every assumed input (a phone's mass, a bag's weight) as an assumption
  the user can correct — never present a guess as a measured fact, and never
  fabricate a load just to fill the section. Skip checks that don't apply and
  say why.

End the Physics check with a one-line verdict: stable / load-safe / printable
under the stated assumptions, or the condition that would make it fail.

### Default to ONE premium part; split only when it must come apart

**Most consumer objects are a single, sculpted premium part** — a phone stand, a
knob, a bracket, a wall mount, a vase, a MagSafe stand. Default to **one
well-proportioned solid body** with any component (charger puck, cable, bearing,
phone) integrated into it as a recess / pocket / channel. A premium object reads
as one continuous form, **not a flat plate bolted to a flat base**.

Reach for multiple printed parts **only** when the object physically must come
apart: a lid or removable cover, a part with a moving joint (hinge, linkage), a
shape that can't print in one orientation, or anything larger than the bed. *A
phone stand is one part; a box with a lid is two.* When unsure, choose one part —
a unified body looks better and has nothing to misfit. The multi-part fit /
collision / shared-dimension discipline below applies **only** to designs that
are genuinely several printed parts; never split a single object to satisfy it.

### Spec format — the shape to fill in

> **What I'll make** — one line.
> **Parts** — usually **one**. Give it outer dims, material, purpose. *Only if
> the design is genuinely multi-part*, add an entry per printed part and state
> exactly how each connects (joint type, the shared mating dimension, the
> clearance per side).
> **Form** — the premium read in one line: the unified corner/edge radius and
> the primary surface treatment (the aesthetic discipline above +
> `references/industrial-design.md`). A solid, resolved body — never a thin slab.
> **Measurements & math** — each derived/load-bearing number as
> `name = formula = value unit` (e.g. `wall = 7 perim · 0.4 mm = 2.8 mm`).
> **Physics check** — only the checks that apply (tip-over CoM vs base, load
> path, stiffness, layer orientation, build volume), then a one-line **Verdict**.

**Worked example — MagSafe phone stand (one premium part).** A solid, gently
tapered wedge body — *not* a flat plate: ~75 × 80 mm base, ~95 mm tall, leaning
~12° back; a Ø56 × 3 mm puck recess sunk into the front face, the cable channeled
out the back (model the puck **and** its captive cable + connector collar —
`references/component-integration.md`); 3 mm walls, 4 mm unified vertical radius,
floor ballast low for stability, an 8 mm front lip the phone rests on. One
printed part, charger integrated — mimic `assets/example_magsafe_stand.py`.
(These numbers are illustrative; the puck/cable/collar dimensions are
web-sourced from Apple's spec and stated as assumptions — see rule 1 above.)

*Only if the design is multi-part*, make each connection explicit and numeric
(e.g. "base + lid, 0.2 mm slip fit on a 2 mm lip; four M3 self-tap bosses, 6 mm
engagement, on an 80 × 60 mm bolt pattern") — a multi-part plan that doesn't
state how the parts join is incomplete.

## Use this skill when

The user asks for any of:

- A specific printable part: phone stand, wall hook, bracket, mount, jig,
  enclosure, knob, organizer, hex tray, gridfinity bin, vase, GoPro/action-
  camera adapter, replacement knob, light cover, cable clip.
- A CadQuery `.py` file, parametric model, or STL/STEP output.
- Editing an existing CadQuery file: "make the wall 2mm thicker", "add
  fillets to the top edges", "move the screw holes 5mm apart".
- A printable replacement part with a stated device + dimensions.

Do **not** use this skill for: render-only concept art, FEA / simulation,
robotics description files (URDF / SDF), or 2D laser-cut DXF. If a sibling
skill is installed for those domains, use it; otherwise tell the user this
skill is not the right tool.

## Default assumptions

Use these defaults unless the user specifies otherwise:

- **Units**: millimeters.
- **Origin**: center of the main body, base plane on `XY`, height along `+Z`.
- **Output**: closed, positive-volume solids. ``scripts/cad`` reports
  ``is_solid`` in its JSON — do not declare done when it's ``false``. Do
  not add an ``assert <shape>.isValid()`` line to the user's ``.py``;
  cadpy already validates as part of the artifact pipeline.
- **Print bed**: 200×200mm typical FDM. Warn if your model exceeds it.
- **Wall thickness for FDM enclosures**: 2.0–3.0 mm.
- **Cosmetic fillet**: 1.0–2.0 mm where geometry allows.
- **Cable channels / slots**: 2–4 mm wider than the cable / connector.
- **Clearance holes**: `hole = nominal + 0.3–0.4 mm` (so M3 → 3.4 mm, M4 → 4.5 mm,
  M5 → 5.5 mm); self-tap into plastic `= major − 0.3 mm`. For screws/nuts/inserts,
  prefer the cadlib helper with a named size rather than transcribing the hole.
- **Tolerances baked into the print** (FDM, 0.4mm nozzle): assume 0.2 mm
  positive slop on holes the user will press a part into; assume 0.4 mm slop
  on parts the user will assemble by hand.

### Ask only about preferences; decide all engineering silently

Split every open decision into two buckets and treat them oppositely. The user
verifies **taste**, never **geometry**.

- **Personal preferences — only the user can know these. Ask, but sparingly.**
  No "correct" answer; depends on the person or their stuff: which device/phone,
  colour/finish, size for their space, left- vs right-handed, wall- vs desk- vs
  handheld, how many of X it holds. Ask only when the answer actually changes
  geometry, and ask the **fewest, highest-leverage** questions — ideally one,
  never a quiz.
- **Engineering choices — there is a best answer. Never ask; pick it.** Wall
  thickness, clearance/tolerance, fillet radius, joint type (tab-slot vs snap vs
  screw), fastener size and thread, boss sizing, print orientation, which parts
  split out. Decide these from best practice and the references — silently.
  Default-and-state: make the call, note it in one line only if it changes fit
  or load, and move on. Never turn an engineering decision into a question.

The test: *could a competent product designer pick this correctly without
knowing the user?* If yes, it's engineering — decide it.

- Warrants a question (preference): device when "phone stand" names no model;
  portrait vs landscape when both are common; wall mount vs desk stand when not
  implied; capacity ("1 pen or 6").
- Never ask (engineering — just pick, optionally note): wall thickness, fillet
  radius, clearance, joint/fastener type and thread, print orientation, finish,
  print-bed edge chamfer (always yes — it lifts off cleaner).

## Root model

- **Skill directory**: this folder. Tools live at `scripts/cad` and
  `scripts/check`.
- **Workspace cwd**: relative target paths resolve from the user's working
  directory. Use absolute paths when you write a `.py` file so subsequent
  tool calls find it.
- **Source = the `.py` file (or project) you wrote**. STEP, STL, and the
  metadata sidecar are *derived*. When the user asks for a change, edit the
  `.py` and re-generate. Do not edit the STL or STEP.
- **Entry function**: ``gen_step()`` at module scope (or the legacy
  ``result =`` form for trivial scripts) — the contract is in the project
  rules above. Without one of these, the runner fails.

## Available tools

The skill lives at ``~/.claude/skills/cadcode/`` (or wherever the user
installed it). From the workspace, the launchers are:

```bash
# Single-file mode: pass any .py file defining gen_step() (or, for
# trivial scripts, ending with a module-level `result = <shape>`).
python ~/.claude/skills/cadcode/scripts/cad   <input.py>      [flags]

# Project mode: pass a directory containing main.py — sibling modules
# (params.py, parts/, features/, assemblies/, validation.py) are
# automatically added to sys.path
python ~/.claude/skills/cadcode/scripts/cad   <project_dir>/  [flags]

python ~/.claude/skills/cadcode/scripts/check <input.py>
```

Common flags on ``scripts/cad``:

- ``--out-dir DIR``       where artifacts land (default: alongside input)
- ``--stem NAME``         output filename stem (default: input/dir name). Use
  ``<project>_assembled`` for a multi-part `cq.Assembly` so the combined-all-parts
  file is self-describing — see step 5.
- ``--mesh-tolerance MM`` linear meshing tolerance for the STL (default 0.05)
- ``--angular-tolerance DEG``  angular meshing tolerance for the STL (default 3°)
- ``--wall-clock-s S``    subprocess timeout (default 30; bump for complex parts)

Use ``--help`` for the full flag set. Always pass an **absolute path** for
``<input.py>`` or ``<project_dir>`` — the agent's cwd may not be the
user's workspace.

**`scripts/cad`** — primary tool. Runs the CadQuery file (or project) in
an isolated subprocess (rlimit + restricted imports + 30s wall-clock kill)
and writes the canonical artifact set next to the source via the cadpy
pipeline:

- `<name>.step` — full B-rep archival, with XCAF labels + colors.
- `<name>.stl` — slicer-ready mesh, always written. It is also the mesh the
  viewer renders as the preview.
- `<name>.step.json` — source hash, generator metadata, validation summary
  (``is_solid``, ``volume_mm3``, mesh tolerances).

Prints a single JSON line on stdout:
``{ok, step_path, stl_path, metadata_path, is_solid, volume_mm3, bbox,
error?}``.

**`scripts/check`** — quick validator. Runs the `.py` and reports
`is_solid`, `volume_mm3`, manifold status, and any min-wall warnings
without keeping artifacts. Use this to sanity-check a model before paying
for the full export.

## Running the loop

Each phase of the loop in concrete terms:

### 1. Understand the task

Read the user's prompt fully. Classify it: **new part**, **edit of an
existing `.py`**, **render-only review**, or **validation-only check**. If
a reference image was attached, `Read` it first — its dimensions and
style are usually authoritative.

### 2. Inspect the workspace

List the workspace files. If a `.py` exists from a prior turn AND this is
an edit request, `Read` it before writing. Don't regenerate from scratch
when an edit will do — minimal diffs respect the user's prior tweaks.

If you're unsure how to approach a feature (hex grid, tapered shell,
multi-part union), `Read` one of the example assets in this skill's
`assets/` directory and mimic the pattern.

### 3. Make a plan

In your reasoning, write down: parameters (name + value + unit), key
features, build order. Catch dimension errors before they cost a render
cycle. For multi-feature parts, decide the union order — most stable
anchor first. (In Vibe's planning phase this becomes the user-facing
spec — see [Plan-phase design discipline](#plan-phase-design-discipline).)

### 4. Edit the `.py`

Write the file with:
- A 1-line docstring at top describing the part.
- Named parameters with units in comments (`PHONE_W = 77  # iPhone 15 PM`).
- A single ``gen_step()`` function at module scope returning the final
  shape (or an envelope ``dict`` to tune mesh tolerance — see
  the [Artifact-control envelope](#artifact-control-envelope) section).

Pick a filename from the part: `phone_stand.py`, `gopro_adapter.py`. Use
absolute paths for the `Write` tool — the workspace cwd is not the skill
directory.

### 5. Run `scripts/cad`

```bash
python ~/.claude/skills/cadcode/scripts/cad <abs/path/to/file.py>
```

This compiles, checks `is_solid`, exports STEP + STL + metadata, and prints
a JSON line.

**Naming the combined-all-parts file (multi-part designs).** When the design is
a `cq.Assembly` — the returned 3D file combines every part into one assembled
scene — name that output so its filename says so. Pass ``--stem
<project>_assembled`` so cadpy writes ``<project>_assembled.step`` /
``.stl`` / ``.step.json`` (and `scripts/review` writes into
``<project>_assembled_review/``):

```bash
python ~/.claude/skills/cadcode/scripts/cad <abs/path/snap_lid_box>/ --stem snap_lid_box_assembled
```

The `_assembled` file is the **final assembled item** (all parts combined); the
individual parts remain the separate named bodies inside that same `.step`. A
**single-part** design combines nothing — keep the plain ``<project>`` stem, no
suffix.

### 6. Read the failure (or the render)

Don't skip this step. Even when `ok=true is_solid=true`, geometry can be
visually wrong. Work the plan's **Verification checklist** here: clear each item
with BOTH its sanity check (a number / assert / `functional` warning) and its
visual check (a render — a **cross-section** for any interior interface):

- **Resolve `warnings` first.** Any non-`info` warning in the JSON's
  ``warnings`` array is blocking (full taxonomy: Non-negotiables) — go to
  step 7.
- **Prove the parts fit and don't collide (multi-part designs).** A clean
  pairwise `collision` check only proves the parts don't *overlap*, not that
  they *join*. **The mating rule (canonical):** for every mating interface — a
  tab and its slot, a lip and its groove, a boss and its hole, a peg and its
  socket — both sides derive from **one** source-of-truth dimension in
  `params.py`, with the FDM clearance applied in exactly **one** place. Never
  size the two halves independently: that is how a tab and slot silently drift
  until they jam or fall out. The atomic helpers (`add_nut_trap`,
  `add_open_cable_channel`, `add_screw_post`) already guarantee this; for a
  hand-built mate, derive the second half with `cadlib.fits` — `slot_for(tab,
  fit)` (female for a male) or `peg_for(hole, fit)` (male for a female) — see
  `assets/example_snap_lid_box.py`. Then walk the assembly sequence: there must
  be a real ordered path to put it together (lid drops past the lip, captive
  cable passes the opening). A model with valid solids but unchecked mating is
  **not done**.
- **Look at every part from all directions, AND the assembly.** Run
  ``python scripts/review <project_dir>`` — it renders the assembled model and
  *each named part* from **all directions** (a 3/4 iso plus all six axis-aligned
  faces) under ``<stem>_review/``, auto-cuts the assembly's x/y/z center
  cross-sections, and re-lists the warnings. You **MUST** `Read` **every** PNG it
  produces and look. A whole-assembly preview hides a floating standoff *inside* a
  tray or a small spike on one part — the per-part, all-direction views do not.
  For an interior interface (a peg in a socket, a tooth on a disc, a lip in a
  groove) the center cuts may miss the plane — render a targeted **cross-section**
  there: ``python scripts/review <project_dir> --section <x|y|z>[@offset_mm]``
  (add ``--part <name>`` to cut one part), then `Read` it.
- **Justify each part.** For every part, state in one line what it is for and
  what it connects to (which mounting interface / mating face). If you cannot
  justify a part, or it does not connect to anything, it is a defect — fix it.
- **Clear the Verification checklist, item by item.** For each item do BOTH a
  sanity check and a visual check. **(A) Per component:** every feature sits on
  SOLID material (nothing perched over a void / hole / notch) and depths
  actually reach. **(B) Per interface:** the mating features MEET in the right
  axis and can TRANSMIT their force (a smooth pocket over round pegs can't
  drive; a captive cable's collar must pass its opening). Walk the plan's
  assembly sequence against the renders, cross-sectioning interior interfaces.
  Encode each item as a hard `validate()` assert (impossible fits) **and** a
  `functional` warning returned from `gen_step()`
  (`return {"shape": shape, "warnings": functional_checks(p)}`) — fix the
  geometry/params and re-run until the `.step.json` lists none. See
  `references/component-integration.md`.
- **Critique the look against the premium bar.** Reading those same PNGs, judge
  each part against `references/industrial-design.md`: does it carry one unified
  radius language, or a scatter of raw 90° arrises? Are transitions blended,
  primary surfaces calm, fasteners minimized? The JSON's `sharp_edges` advisory
  (an info warning, never blocking) counts the un-softened convex arrises — drive
  it toward zero on visible faces with `cadlib.styling` (`soften_edges` /
  `break_edges`), **within printability and strength limits**. Refine and re-run
  any part that reads cheap, blocky, or unresolved; leave functional arrises
  sharp. Do this before hand-off — a part that works but looks like a default box
  is not done.
- Compare against the user's prompt and any reference image.
- Check the bbox in the JSON: does it match the intent (right order of
  magnitude, fits on a 200×200mm bed)?

If anything is off — compile error, non-solid, a warning, a floating or
purposeless part, a member protruding through a plate, wrong proportions,
misplaced holes — go to step 7.

### 7. Fix

Apply the **smallest responsible** source change:
- Compile errors → load `references/repair-loop.md`, fix the line.
- `is_solid=false` → boolean op probably went wrong; reduce / restructure.
- Wrong proportions → re-check parameters against bbox.
- Hole/feature misplaced → recompute against the right reference face
  with the right selector (`.faces(">Z[1]")` etc.).

Then go back to step 5. **Soft cap: 4 iterations** before asking the user
a clarifying question. Past 4, you are probably guessing about user
intent rather than fixing a geometry bug.

### 8. Hand off

Final reply to the user (mandatory, see "Required final response" below):
the STL path, bbox + volume, parameters to tweak, and one or two
assumptions you made.

## Non-negotiables

- The agent **never** edits the generated STEP / STL / metadata sidecar.
  Edit `.py`, re-generate.
- Every generated `.py` (or project ``main.py``) defines exactly one
  ``gen_step()`` at module scope, OR for trivial single-file scripts
  assigns the final shape to a module-level ``result``. cadpy accepts
  both.
- Every CadQuery `.py` starts with `import cadquery as cq` and uses `cq.`
  throughout. CadQuery is the only modeling library available.
- Run `scripts/cad` (or at minimum `scripts/check`) before declaring done.
  Never claim a model is printable from reading code alone.
- Never declare done with a **blocking** warning (`disconnected_bodies`,
  `collision`, `sliver`, `invalid_brep`, `empty`, `check_failed`) **or a
  `functional` warning** in the `warnings` array, a floating/disconnected part,
  two parts that interpenetrate, or a part you cannot justify. A `functional` warning (`severity: "warning"`) means the design
  can't be assembled/used as intended (e.g. a connector that won't fit its
  opening, a coupling that doesn't engage its drive pegs, or a feature perched
  over a void) — fix it. The advisory `sharp_edges` hint (`severity: "info"`) is not
  blocking — soften what you can within printability and leave functional arrises
  sharp. Always run `scripts/review` and `Read` **every** PNG it produces
  before declaring done (the full drill is step 6).
- Ask the user only about *personal preferences* that change geometry, and ask
  the fewest possible. Decide every *engineering* choice silently from the
  references — never ask about wall thickness, clearance, joint/fastener type,
  or print orientation. (See "Ask only about preferences".)
- Use millimeters throughout. Do not convert; do not annotate inches.

## Reference examples

Working ``.py`` files you can study (do NOT load eagerly — read on demand
when you need to mimic a pattern):

| File | Demonstrates |
|---|---|
| ``assets/example_cube_with_hole.py`` | Hello world: primitives, face selectors, ``.hole()`` |
| ``assets/example_hex_tray.py`` | Parametric grid, hex polygon math, ``.pushPoints`` |
| ``assets/example_spur_gear.py`` | Polar arrays of trapezoidal teeth, shaft bore + keyway |
| ``assets/example_twisted_vase.py`` | Multi-level loft of rotated cross-sections, ``.shell()`` for hollow walls |
| ``assets/example_gopro_mount.py`` | Multi-part union (base + stem + 3-finger head), standard GoPro spec, ``.cboreHole`` |
| ``assets/example_knurled_knob.py`` | Polar array of cutting features (knurling), chamfers, M3 set screw |
| ``assets/example_desk_valet.py`` | Premium look: unified radius language via ``cadlib.styling`` (``design_radius_for`` + ``soften_edges`` + ``break_edges``), shelled tray |
| ``assets/example_magsafe_stand.py`` | Functional integration: a captive-cable component done right — `add_open_cable_channel` (connector-clearance), hard `validate()` + soft `functional_checks()` warnings via the envelope dict |
| ``assets/example_snap_lid_box.py`` | **Multi-part fit (study this for any assembly).** A real `cq.Assembly` of base + lid as separate printed parts: the lid lip is derived from the base cavity via `cadlib.fits.peg_for` (one shared dimension), seated collision-clean, with `functional_checks()` proving it assembles |

These are the canonical patterns. Mimic the file shape: docstring at top,
named parameters at the top of the file, a single ``gen_step()`` at module
scope returning the final shape. (Some older assets still use the legacy
``result = ...`` form — copy their geometry, not that shape.)

## Progressive references

Load these only when their trigger applies (saves the host agent's context):

- `references/industrial-design.md` — the premium-product (Apple-anchored)
  aesthetic bar: unified radius language, proportion and restraint, surface
  continuity, ergonomics/texture, and printing the show-face down. **Load when
  designing or polishing the look of any user-facing part** — function and
  printability still win every conflict. Backed by `cadlib.styling` and the
  `unified-radius` / `surface-continuity` patterns.
- `references/component-integration.md` — **load before integrating any real
  component** (charger, phone, connector, motor, bearing). The discipline for
  making a design actually assemble and work: model the whole component incl.
  captive cables / connector collars, write the assembly/setup sequence, and
  enforce it with hard `validate()` asserts + soft `functional` warnings. Backed
  by `cadlib.cutouts.add_open_cable_channel` and the `cable-channel` pattern.
- `references/project-structure.md` — when to use a project directory
  vs a single file, the canonical layout, the seven rules, editing rules.
  **Load before scaffolding any multi-part design.**
- `references/cadquery-modeling.md` — CadQuery idioms: workplanes, faces
  selectors, hole/cboreHole, fillet/chamfer, polygon for hex grids, loft for
  taper, common pitfalls.
- `references/hobbyist-defaults.md` — two parts: (1) how to source dimensions —
  web-search real-world product specs and state them as assumptions; (2) the
  generic FDM best-practice rules/formulas (tolerances, wall = N×nozzle,
  self-tap, cbore, bearing seat, XY-comp, elephant's foot, sanity-scale check).
- `references/repair-loop.md` — diagnosis + repair when `scripts/cad`
  returns `ok=false` or `is_solid=false`: classify the failure, the smallest
  responsible fix, when to re-render vs re-validate.
- `references/assembly.md` — `cq.Assembly` workflow for designs with
  **physically separate parts** (lid + base, hinge, removable cover, robot
  chassis + wheels). **Load before designing anything the user prints as
  multiple pieces and assembles** — using `.union()` for these instead of
  Assembly loses clearances, fits, and per-part STL export.
- `references/kinematic-placement.md` — **mechanism** placement: parts that
  share a *moving* joint or form a closed loop (four-bar / Hoeken walking legs,
  crank + coupler + rocker, scissor lift, pantograph, steering linkage). Solve
  the joint so the shared pin coincides instead of eyeballing each link's angle.
  **Load before placing any linkage** — guessed angles leave joints apart and
  trip `disconnected_bodies`. The four-bar helper lives in `cadlib.kinematics`.

## Helper library (`cadlib`)

The skill ships a Python package at `~/.claude/skills/cadcode/cadlib/`
with composable, tested CadQuery helpers. **Prefer importing these over
re-deriving geometry from the pattern docs.** The runner adds the skill
root to `sys.path`, so `from cadlib.X import Y` resolves inside the
sandbox.

```python
from cadlib.enclosure import hollow_box, add_lid_lip, lid_plate
from cadlib.mounting  import add_screw_post, add_heat_set_pocket, add_nut_trap
from cadlib.cutouts   import (
    add_press_fit_pocket, add_magnet_pocket, add_bearing_seat, add_cable_channel,
    add_open_cable_channel,   # captive cable + connector collar (installable)
)
from cadlib.mechanical import add_snap_fit_cantilever, add_dovetail_slot, add_rib_stiffener
from cadlib.fits      import mating_clearance, slot_for, peg_for, print_in_place_gap  # shared mating dims
from cadlib.styling   import design_radius_for, soften_edges, break_edges
from cadlib.kinematics import solve_fourbar, place_two_point, circle_intersections
from cadlib.layout    import four_corner_points, grid_points, circle_points
from cadlib.tables    import (
    SCREW_TABLE, NUT_TABLE, HEATSET_TABLE, BEARING_TABLE, MAGNET_TABLE, CABLE_TABLE,
)
```

Every helper:

- is **keyword-only** (no positional surprises)
- **returns** a new `cq.Workplane` (does not mutate `part`)
- **raises `ValueError`** on impossible param combinations (so failures
  point at the spec, not at OCCT five frames deep)
- has a one-paragraph docstring with units + one usage example — `Read`
  the helper's source file if you want the full signature

When **no helper fits**, write the geometry inline in a function named
`custom_<feature>()` — that's a signal the library is missing a helper,
worth promoting later. **Do not copy the pattern doc's template
verbatim** when a `cadlib` helper exists — the docs are reference, the
package is the source of truth.

### Recipes — worked examples to mimic

Two complete recipes live at `~/.claude/skills/cadcode/recipes/`. Read
them when designing a similar product:

| Recipe | Demonstrates |
|---|---|
| `electronics_enclosure.py` | hollow_box + add_lid_lip + four_corner_points + add_screw_post + custom side port + lid_plate |
| `magnetic_lid_box.py`      | hollow_box + four_corner_points + add_magnet_pocket × 2 (base + lid) + lid_plate |

Both return the assembled preview shape from ``gen_step()``. For multi-part
products where each piece prints separately, follow the ``cq.Assembly``
pattern in ``references/assembly.md`` — cadpy preserves part names, colors,
and locations in the STEP file.

## Pattern library

Atomic mechanical-engineering patterns, each in its own file under
`references/patterns/`. **Load only the patterns you actually need** — they
are small but adding 16 to every turn blows context. Match the user's
language to the trigger column and `Read` the corresponding file.

| Trigger phrases the user might say | Pattern file |
|---|---|
| snap fit, clip-on lid, clamshell, snap together | `references/patterns/snap-fit-cantilever.md` |
| living hinge, fold-open, flexure, clamshell flap | `references/patterns/living-hinge.md` |
| press fit, interference fit, tight fit, shaft hole | `references/patterns/press-fit-pocket.md` |
| dovetail, slide-on lid, T-slot mount, sliding rail | `references/patterns/dovetail-slide.md` |
| screw boss, mounting post, PCB standoff, M2/M3/M4/M5 hole | `references/patterns/screw-boss.md` |
| heat-set insert, brass insert, Ruthex / Voron insert | `references/patterns/heat-set-insert-pocket.md` |
| nut trap, embedded nut, captive nut, hex pocket | `references/patterns/nut-trap.md` |
| ribs, stiffener, gusset, brace, "make this stronger" | `references/patterns/rib-stiffener.md` |
| crack at corner, fatigue, stress relief, fillets | `references/patterns/fillet-stress-relief.md` |
| blocky / cheap-looking, "make it premium / nicer / rounder / more Apple", unified corner radius, clear `sharp_edges` | `references/patterns/unified-radius.md` |
| hard shoulder, abrupt step, blend a junction, crisp chamfer line, fillet vs chamfer, seamless | `references/patterns/surface-continuity.md` |
| wall thickness, nozzle width, "how thick should X be" | `references/patterns/wall-thickness-rules.md` |
| print orientation, layer lines, "how should I print this" | `references/patterns/print-orientation.md` |
| overhangs, supports, teardrop hole, bridging | `references/patterns/overhang-relief.md` |
| draft angle, taper a wall, stacking/nesting parts, tapered release | `references/patterns/draft-angle.md` |
| magnet, magnetic closure, N42 / N52, neodymium | `references/patterns/magnet-pocket.md` |
| bearing, 608 / 688 / 6800, skate bearing, pulley | `references/patterns/bearing-seat.md` |
| cable channel, wire routing, strain relief, USB cable | `references/patterns/cable-channel.md` |
| floating part, disconnected bodies, standoff on a curved wall, strut into a plate, "part not attached" | `references/patterns/anchor-to-body.md` |
| four-bar / 4-bar linkage, crank + coupler + rocker, Hoeken / Klann / Jansen walking leg, scissor lift, pantograph, "joints must meet", legs hanging disconnected | `references/patterns/four-bar-linkage.md` |
| print-in-place, print-in-one, no-assembly mechanism, captive moving part (slider / drawer / hinge / gear / ball joint), "moving parts in a single print", parts came out fused / "stuck together" | `references/patterns/print-in-place.md` |

Each file has the same shape: **Trigger**, **Why (the mechanics)**, **CadQuery
template**, parameter ranges, and pitfalls. The template is copy-pasteable
and uses real CadQuery APIs — adapt parameters to the user's part rather
than starting from scratch.

When a design needs **multiple patterns** (e.g., enclosure with magnet
closure + screw bosses + cable channel), load all the relevant pattern
files at the start of the design phase, then weave them into one `.py`.

## Required final response

Your final reply to the user MUST contain, in order:

1. **One sentence** stating what you made (e.g., "Made a phone stand for an iPhone 15 Pro Max, 130mm tall, tilted 20°.").
2. **Output path** — the STEP for archival inspection plus the STL absolute
   path the user can drag into a slicer. **For a multi-part / assembled design,
   present the final assembled item separately from its component parts:** give
   the assembled item (the whole-scene ``<project>_assembled.stl`` +
   ``.step``, named via ``--stem`` — see step 5) as its own line first, then
   list each named component part beneath it — name, what it is, and its
   per-part view/STL from the STEP (`scripts/review` renders one PNG per part).
   The final assembled item and its parts are **distinct deliverables** — never
   collapse them into a single entry. A single-part design lists just the one item.
3. **Bounding box + volume** so the user knows it'll fit on a 200×200mm bed.
4. **Tweakable parameters** — the variables at the top of the `.py` and what they do.
5. **Assumptions** — one or two bullets for anything geometry-changing you defaulted (case allowance, screw size, tilt direction).

Skip anything else. The user wants a printable file, not a thesis.
