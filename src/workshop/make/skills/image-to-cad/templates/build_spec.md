<!--
  image-to-cad build spec — template.

  Fill every bracket. Delete every HTML comment before handing this to the user.
  Every number carries [observed] | [inferred] | [assumed]. An untagged number
  is a defect. Units are millimetres throughout.
-->

# Build spec — <object name>

**Source images:** <filenames> · **Distinct viewpoints:** <n> `[observed]` · **Image kind:** <orthographic drawing | studio render | photo | sketch | CAD screenshot>

**Project directory:** `output/<object_name>/` — the object's own name in
snake_case, never a placeholder. Every path below (`ref/`, `measure/`,
`part_<role>.step.py`) is relative to it, and CAD has no other source for the
name.

---

## 1. Overall read

<One paragraph: what the object is, what it is for, its archetype.>

- **Construction family (base solid):** <extrude | tapered extrude | revolve | loft | sweep | sketch-driven> — <why, from the image's evidence>
- **Symmetry:** <bilateral about X | rotational about Z | none> `[observed|inferred]`
- **View coverage:** <count observed views and name every reconstructed view>
- **Finish / material read:** <what it appears to be made of; what will be dropped as texture rather than geometry>

> **Reconstruction note:** <If fewer than 3 orthographic views: state plainly which views are reconstructed and from what. Delete this line only if you had 3+ true views.>

---

## 2. Top view — plan, looking down −Z

`[observed | inferred | assumed]` — <one line of reasoning if not observed>

- **Outline:** <shape class: rounded rectangle | circle | racetrack | freeform>
- **Bounding footprint:** <W> × <D> mm `[tag]`
- **Corner radius:** <r> mm `[tag]`
- **Symmetry axes:** <which>
- **Widest point:** at <x>% along the length `[tag]`
- **Features visible only in plan:** <bosses, holes, cavity opening, ribs — each with position and size>
- **Hidden in this view:** <what the plan cannot show>

---

## 3. Front view — elevation, looking along +Y

`[observed | inferred | assumed]`

- **Silhouette:** <description>
- **Overall:** <W> × <H> mm `[tag]`
- **Height bands** (must sum to the total height):

| Band | From → to (mm) | Width (mm) | Note |
|---|---|---|---|
| <base> | 0 → <z1> `[tag]` | <w> `[tag]` | <> |
| <body> | <z1> → <z2> `[tag]` | <w> `[tag]` | <> |
| <head> | <z2> → <H> `[tag]` | <w> `[tag]` | <> |

- **Lean / draft angle:** <deg> `[tag]`
- **Ground contact:** <length> mm, = <%> of total length `[tag]`
- **Features visible only in front:** <>

---

## 4a. Side view — elevation, looking along +X

`[observed | inferred | assumed]`

- **Silhouette:** <description>
- **Overall:** <D> × <H> mm `[tag]`
- **Depth at each height band:** <band → depth, for each band above>
- **Lean angle:** <deg> `[tag]`
- **Overhangs steeper than 45° from vertical:** <list, or "none">
- **Features visible only in side:** <>

---

## 4b. Component descriptions — in words, before any part decision

<Prose, one entry per **visible component** — not per printed part, and not a
table. Skill Step 4b owns why.>

For each component:

- **Form** — what someone would have to know to draw it without seeing the
  photograph: how it is generated (revolve / loft / swept profile), where it is
  widest and at what fraction of its length, whether an edge is straight,
  chamfered, concave or flicked into a point, how each end terminates.
- **Size** — the dimensions that decide the form, each `[tag]`ed. Ranges are
  allowed and are better than a false precision; a range is a constraint, a
  spuriously exact number is a guess wearing a decimal.
- **How it meets its neighbours** — seated in a slot, passing through the full
  cross-section, glued to a face, cantilevered. State whether a boundary is a
  real seam or only a colour change: a stripe running through the whole section
  and a stripe painted on the surface look identical in one view and are
  different solids.
- **Detail that only appears on a second look** — a flare at a mouth, a strip
  of colour on one face, a small radius where a point was expected. This is the
  line most often missing, and it is the one the likeness gate scores.
- **What it is for, visually** — and **what breaks if it is wrong**. "The post
  enters the belly at 15–20° from horizontal, nose up and canted slightly left;
  a few degrees off and the lamp stops looking like it is climbing" is a
  tolerance, written where a tolerance is actually decidable. Say which
  dimensions are loose and which are not: this is the section that tells a
  later reader that ±5 mm on the base diameter is nothing and ±3° on the post
  is everything.
- **Evidence** — `[observed]` / `[inferred]` / `[assumed]`, per claim, not per
  component.

<Separate what the object *is* from how the original happened to be made. "The
fins seat in four slots 15–20 mm deep, and cutting slots in a round body is the
hardest operation in the piece" is true of the wooden original and irrelevant to
a printed one, where the fins and body are one solid and the slot is invisible.
Keep the observation — it explains a proportion, and it matters if the object is
ever reproduced the same way — but mark it as the original's process, not as a
feature the reconstruction owes. The reverse error is worse: dropping a
*visible* consequence of that process, such as the seam line a slot leaves.>

**Component ledger** — every entry above must appear here, and every row must
still exist at delivery:

| Component | Described in 4b | Becomes part(s) | Landmark check |
|---|---|---|---|
| <> | yes | <6a part name(s), filled in later> | <the local check that proves it exists> |

---

## 5. Size

**Scale anchor:** <what fixed the scale, and its source> — `[observed|inferred|assumed]`

| Dimension | Value (mm) | Confidence | Source |
|---|---|---|---|
| Overall L × W × H | <> | `[tag]` | <> |
| <governing dimension> | <> | `[tag]` | <> |
| Wall thickness | <> | `[tag]` | <FDM default: N × 0.4 mm nozzle> |
| <…> | <> | `[tag]` | <> |

**Print sanity:**

- Bed fit: <fits <W>×<D> mm `[tag]` | needs <W>×<D> mm bed `[tag]` | must be split — how>
- Minimum wall at this scale: <> mm `[tag]` <ok | thickened from <> mm `[tag]`, which changes <what>>
- Minimum feature: <> mm `[tag]` <ok | <feature> dropped/deepened>
- Overhangs: <handled by orientation <name> | needs support at <where>>
- Print orientation: <named orientation and why>

---

## 6. Decomposition

<Decompose first, run the research logs in 6c–6f, then select in 6g — never an
exact mechanism, topology, lamp, actuator, socket or bought device before its
search evidence exists.>

### 6a. Printed parts

<Default is ONE; if one part, give the reason the split test failed. Do not
start this table until 4b describes every component, and account for every 4b
component here — if one is in no row, say where it went.>

| # | Part | Purpose | Envelope (mm) | Joins to | Joint type | Shared mating dimension | Clearance/side |
|---|---|---|---|---|---|---|---|
| 1 | <> | <> | <> `[tag]` | <> | <> | <one value both halves derive from> `[tag]` | <> `[tag]` |

**Assembly order:** <ordered steps, and the clearance each needs>

**Seams seen in the image that are NOT splits:** <each, with the call: cosmetic groove / deleted / recess>

### 6b. Feature tree — part <name>

| # | Tier | Feature | Rooted in / cut from |
|---|---|---|---|
| 1 | base | <> | — |
| 2 | additive | <> | <> |
| 3 | subtractive | <> | <> |
| 4 | finishing | <> | <> |

### 6c. Off-the-shelf components — catalog search log

<One row per Step 1E standard element and Step 1G bought powered component,
MISS rows included — a recorded miss stops the next turn re-running the search.
Delete the section only if 1E and 1G found none, and say so in one line.>

| Feature | Measured parameter | Catalog id, or MISS | Local STEP + `sha256` | How it is modelled | Why |
|---|---|---|---|---|---|
| <> | <the numbers you searched on> `[tag]` | <`id`, or `MISS — <query>`> | <`ref/<file>.step`, or — for a miss> | catalog STEP / pocket only / authored stand-in | <> |

**Rule:** a *hit* is used unless there is a stated reason not to — write the
reason. A *miss* is only valid if the search actually ran and returned nothing;
an unreachable API is inconclusive, not a miss.

**Never write a bought component's own dimensions into this spec.** They live in
a datasheet, not in this repository, and once typed nothing downstream can check
them. Cite the downloaded file instead and let `cadmount` derive the cavity from
it; a stand-in envelope is the one case that carries a number, and it carries
the reason beside it.

### 6d. Analogous design references

<Construction patterns only, not bought parts, and only when a feature has a
real construction question. `N/A — no applicable construction analogy` for a
unique organic subject. Numbers come from a manufacturer, standard or official
source; an analogy never supplies the user's scale, placement or silhouette.>

| Query | Status | Source authority/type | Stable URL + revision/commit | Relevant feature | Specification/constraint taken | Construction lesson used | License/use |
|---|---|---|---|---|---|---|---|
| <> | <used / rejected / MISS / unavailable / N/A> | <manufacturer / standard / official docs / licensed source CAD> | <> | <> | <exact claim, value + units + applicability, or N/A> | <> | <> |

### 6e. Mount declarations — becomes `measure/mounts.json`

<One row per component the model must physically hold. Delete the section if no
6c row is modelled as a seat or a pocket, and say so in one line. The seat and
the screw pattern are derived from the component's own STEP; this table declares
where it sits, not how big it is.>

| id | component (`ref/…`) | `sha256` from 6c | pose in assembly coords | parts measured against | min clearance | bolt axis | bolts |
|---|---|---|---|---|---|---|---|
| <> | <`ref/<file>.step`> | <64 hex> | <`[x,y,z]`, or `{position, rotation}` in deg> `[tag]` | <labelled parts; omit for the whole assembly> | <mm, default 0.10> `[tag]` | <`[0,0,1]`; omit to search any> `[tag]` | <`true`, or `false` for a strapped, glued or captive-screwed part> |

**A derived seat is not proof the model has one**, and `validate`, `interfere`,
`check_fit`, `check_motion` and `check_mesh` all pass a seat that was never
cut. `check_mount` is the only gate that reads the component's own STEP back
into the assembly.

Insertion is a joint, so a seated component also gets **both** directions in the
motion table below: `clear` along the way the component travels in, `blocked`
along the way it must not back out. Set `allow_seated_contact` on anything that
starts installed.

### 6f. Removable-light mating interfaces

<Only when a functional light can be removed from a socket: fill 6f from
`templates/build_spec_powered.md`. Otherwise state in one line that every
functional light is soldered, fixed or integrated, or that the object has
none.>

### 6g. Research-backed analysis design selection

<One selected design per active domain; CAD implements these rows and chooses
nothing. `N/A — inactive` only when the domain truly does not apply. Exterior
construction may be selected from image evidence when the form forces it; every
other domain is research-first, per Skill 5f.>

| Domain | Selection contract written before search | Internet research performed | Viable candidates compared | Selected design | Nearest rejected alternative + reason | Evidence / provenance | Remaining assumption |
|---|---|---|---|---|---|---|---|
| Exterior construction | <silhouette, section change, landmarks, manufacturing constraints> | <image evidence; design-reference query when useful> | <1–3 construction families, or one forced by evidence> | <exact construction family and part strategy> | <> | <reference measurements / 6d provenance> | <> |
| Mechanical mechanism | <input/output motion, travel, load, speed/duty, envelope, datums, assembly/service path> | <Internet mechanism research + 6d when useful> | <> | <exact archetype, parameters owned by §8, and driven parts> | <> | <cited URLs / provenance> | <> |
| Electrical topology | <power boundary, source range, load demand, protection/control, connectors, service access> | <electromechanical Phase A evidence> | <> | <source → protection → control → load → return topology> | <> | <manufacturer/standard URLs + power evidence> | <> |
| Lighting | <function, colour, behavior, luminous surface, optical direction, envelope, installation/removability> | <GitHub → step.parts → manufacturer/public-CAD research> | <> | <exact emitter/module, driver, optic and socket/contact interface> | <> | <6c/6f rows + authoritative URLs> | <> |
| Other bought devices | <function, governing dimensions/ratings, mount and service constraints> | <step.parts + manufacturer/public-CAD research> | <> | <exact MPN/STEP or documented envelope after a confirmed miss> | <> | <6c local STEP + sha256> | <> |

**Selection status:** <complete — CAD can implement without choosing among
alternatives | incomplete — name the unresolved domain and repeat it in Open
question>

---

## 7. Feature detail + build123d operation

<Implement 6g. A contradiction here sends you back to the research contract to
update 6g — never a silently different mechanism, topology, lamp or device.>

Part: **<name>** — executed in this order inside `gen_step()`.

| # | Feature | Geometry + numbers | build123d call | Plane / selector | Risk |
|---|---|---|---|---|---|
| 1 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |
| 2 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |

**Named parameters that own a shared number:** <parameter → what it owns>

---

## 8. Powered system / mechanism

<Fill this section, and the powered checklist block, from
`templates/build_spec_powered.md` whenever an electrical load is functional or
a part moves under a stored or applied driving force. A lid that merely opens
is a joint and belongs in 6a. Otherwise replace this line with one stating that
nothing is powered or driven; `check_spec_format` demands the section back the
moment the spec names such a load.>

---

## Proportion ledger

Assertions to check after generation with `scripts/inspect`, ±10% unless stated:

| Ratio | Value | Source |
|---|---|---|
| L : W : H | <> | `[tag]` |
| ground contact ÷ total length | <> | `[tag]` |
| widest point position along length | <> | `[tag]` |
| wall ÷ overall width | <> | `[tag]` |

**Hard asserts** (exact, not ±10%): <any dimension the user stated explicitly>

---

## Verification checklist

Each item pairs a SANITY check with a VISUAL check, per `cad`'s build loop.

**Likeness handoff**

| Label | Project-local reference | Minimum IoU | Why this viewpoint is usable |
|---|---|---:|---|
| <> | `ref/<file>` | 0.90 | <> |

- [ ] the spec phase records the pairs and threshold but does not claim a score
- [ ] the CAD phase passes every pair to `verify_project --image-derived` as
      `--likeness-ref LABEL=PATH`
- [ ] the delivery floor is 0.90 and fixed: `verify_project --image-derived`
      does not take a lowered one. `check_likeness --accept-mismatch` records a
      mismatch **while iterating** — and only once that view has two rounds on
      record — which is a note about the loop, never a delivery decision.
      Shipping below 0.90 remains the user's explicit acceptance of a **failing**
      gate, never a floor the run lowered for itself: recorded at final with
      `--likeness-accept-mismatch "<reason>"`, allowed only for a view whose
      history shows it stalled out, and written into the pipeline record as
      `accepted-fail` while `measure/likeness.md` keeps reporting the failure
- [ ] the delivered round is the best round: `check_likeness` fails a run that
      scores below the best this view has recorded, floor or no floor
- [ ] three rounds in a row that move the number by nothing end the loop:
      the gate reports `stalled out`, still fails, and hands the accept-or-
      reject decision to the user rather than inviting another render
- [ ] the final command declares `--powered` for any functional electrical load,
      otherwise `--unpowered`; never neither

**Per component**

- [ ] <feature> sits on solid material — assert <>; visually confirm in <view>
- [ ] <feature> depth reaches — assert <>; cross-section <axis>

**Per sourced component**

- [ ] every Step 1E/1G element appears in 6c as a hit, recorded rejection/miss,
      or unavailable service
- [ ] every hit that was NOT used carries a stated reason
- [ ] every used hit is downloaded into `<project-dir>/ref/` and cited by path
- [ ] no component dimension is typed into this spec or into a generator
- [ ] every seated component has a 6e row, and `check_mount <project-dir>`
      exits 0 — clash, clearance and screw access are measured, not asserted

**Per functional electrical load** <the block is in `templates/build_spec_powered.md`; delete this line when nothing is powered>

**Per design reference**

- [ ] every used source records a stable URL, revision/commit when available,
      source authority, license/use and the exact claim or lesson taken
- [ ] every numerical specification comes from a manufacturer, standard or
      official technical source and states units plus applicability
- [ ] every analogy names only the construction lesson; it does not supply the
      user's scale, placement or substitute silhouette
- [ ] `measure/check_spec.py` covers every selected 6d evidence row used by 6g

**Per interface**

- [ ] <mating pair> meets with <> clearance — assert <>; cross-section <axis>
- [ ] assembly path is reachable — `check_motion` `assembly_sequence`, one step
      per row of 6a's assembly order. **Not a render:** a render cannot see the
      collision behind the part.

**Per motion** <delete only when nothing is driven **and** nothing is inserted,
seated, slid, rotated, latched or captured>

Every joint gets **both** directions. `expect: "clear"` is a motion that must be
possible; `expect: "blocked"` is a capture — and its direction is the one the
drive pulls, or the way a seated part must not back out. A catch placed
anywhere else reads as a clean pass.

| id | check | expect | moving → obstacles | input |
|---|---|---|---|---|
| <crank-full-turn> | `rotation_motion_collision` | clear | <> → <> | <start> → <end>° `[tag]`, <steps> steps `[tag]` |
| <axle-retained> | `linear_motion_collision` | **blocked** | <> → <> | <the direction 8a says the drive pulls> |
| <band-stays-on-post> | `linear_motion_collision` | **blocked** | <> → <> | <> |
| <assemble> | `assembly_sequence` | clear | <> | steps in 6a order |

Set `allow_seated_contact` on anything that starts installed. Written to
`<project-dir>/measure/motion.json`, run as:

```bash
python "$CAD_SKILL_ROOT/scripts/check_motion" <project-dir> --manifest measure/motion.json
```

---

## Assumptions

<Scale anchor first. Each phrased as a one-edit correction.>

1. **<Scale anchor>** `[assumed]` <value>. Everything scales with this — change it and the rest follows.
2. <>
3. <>

---

## Open question

<At most one, and only if it changes geometry and only the user can answer it.
Delete this section if you have none.>

---

## Next step

Spec written to `<abs path>` inside `output/<object_name>/`, the project
directory named above; build it there. To build it: use the `cad` skill with this spec —
Size + ledger become the named parameters of `<name>.step.py`, the Step 7 table
in order becomes its `gen_step()` body, and the ledger assertions become
post-generation `scripts/inspect` checks. Section 8, when present, becomes the
kinematic parameters and the feasibility `assert` in `<name>_lib.py`, plus
`measure/motion.json` for `scripts/check_motion`.
