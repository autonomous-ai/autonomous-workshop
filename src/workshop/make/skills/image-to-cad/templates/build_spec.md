<!--
  image-to-cad build spec — template.

  Fill every bracket. Delete every HTML comment before handing this to the user.
  Every number carries [observed] | [inferred] | [assumed]. An untagged number
  is a defect. Units are millimetres throughout.
-->

# Build spec — <object name>

**Source images:** <filenames> · **Distinct viewpoints:** <n> · **Image kind:** <orthographic drawing | studio render | photo | sketch | CAD screenshot>

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
| <base> | 0 → <z1> | <w> | <> |
| <body> | <z1> → <z2> | <w> | <> |
| <head> | <z2> → <H> | <w> | <> |

- **Lean / draft angle:** <deg> `[tag]`
- **Ground contact:** <length> mm, = <%> of total length `[tag]`
- **Features visible only in front:** <>

---

## 4. Side view — elevation, looking along +X

`[observed | inferred | assumed]`

- **Silhouette:** <description>
- **Overall:** <D> × <H> mm `[tag]`
- **Depth at each height band:** <band → depth, for each band above>
- **Lean angle:** <deg> `[tag]`
- **Overhangs steeper than 45° from vertical:** <list, or "none">
- **Features visible only in side:** <>

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

- Bed fit: <fits 200×200 | needs 256 mm bed | must be split — how>
- Minimum wall at this scale: <> mm <ok | thickened from <> mm, which changes <what>>
- Minimum feature: <> mm <ok | <feature> dropped/deepened>
- Overhangs: <handled by orientation <name> | needs support at <where>>
- Print orientation: <named orientation and why>

---

## 6. Decomposition

### 6a. Printed parts

<Default is ONE. If one part, say so and give the reason the split test failed.>

| # | Part | Purpose | Envelope (mm) | Joins to | Joint type | Shared mating dimension | Clearance/side |
|---|---|---|---|---|---|---|---|
| 1 | <> | <> | <> | <> | <> | <one value both halves derive from> | <> |

**Assembly order:** <ordered steps, and the clearance each needs>

**Seams seen in the image that are NOT splits:** <each, with the call: cosmetic groove / deleted / recess>

### 6c. Off-the-shelf components — catalog search log

<One row per standard mechanical element found in Step 1E — gear, bearing,
fastener, spring, bearing, pulley, magnet, insert. Write this section even when
every row is a MISS; a recorded miss stops the next turn re-running the search.
Delete the section only if Step 1E found no standard element at all, and say so
in one line.>

| Feature | Measured parameter | Catalog id, or MISS | How it is modelled | Why |
|---|---|---|---|---|
| <> | <the numbers you searched on> | <`id`, or `MISS — <query>`> | catalog STEP / pocket only / authored stand-in | <> |

**Rule:** a *hit* is used unless there is a stated reason not to — write the
reason. A *miss* is only valid if the search actually ran and returned nothing;
an unreachable API is inconclusive, not a miss.

### 6d. Analogous design references

<Use this for construction patterns, not bought parts. Run the design-reference
search only when a mechanical/product feature has a real construction question.
Write `N/A — no applicable construction analogy` for a unique organic subject.
Never copy dimensions, scale, placement, or silhouette from this table.>

| Query | Catalog id, MISS, or N/A | Relevant feature | Construction lesson used | Local provenance | License/use |
|---|---|---|---|---|---|
| <> | <> | <> | <> | `<project>/ref/external/.../provenance.json` | <> |

### 6b. Feature tree — part <name>

| # | Tier | Feature | Rooted in / cut from |
|---|---|---|---|
| 1 | base | <> | — |
| 2 | additive | <> | <> |
| 3 | subtractive | <> | <> |
| 4 | finishing | <> | <> |

---

## 7. Feature detail + build123d operation

Part: **<name>** — executed in this order inside `gen_step()`.

| # | Feature | Geometry + numbers | build123d call | Plane / selector | Risk |
|---|---|---|---|---|---|
| 1 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |
| 2 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |

**Named parameters that own a shared number:** <parameter → what it owns>

---

## 8. Mechanism

<Write this section only when a part moves under a **driving force** — a band, a
spring, a motor, gravity, a hand crank. A lid that merely opens is a joint and
belongs in 6a. Delete the section if nothing is driven, and say so in one line.>

**Archetype:** <crank-rocker four-bar | slider-crank | pull-back flywheel |
cam-follower | Klann linkage | torsion-return hinge> — <why this one, and what
was rejected. "Runs on a rubber band" is not an archetype.>

### 8a. Drive

| Property | Value | Note |
|---|---|---|
| Energy source | <rubber band #<size> \| printed spring \| catalog spring \| motor \| hand> `[tag]` | a purchasable one also gets a 6c row |
| Stored by | <winding <n> turns on <part> \| compressing <n> mm \| deflecting <deg>> `[tag]` | |
| Anchored at | <the part + feature holding each end> | must resist the pull, not just touch it |
| **Drive direction** | <e.g. "band pulls −Y along the axle groove"> | this is the direction every `blocked` condition tests |

> **Printed spring:** pitch must exceed the wire OD. A helix whose pitch equals
> its wire diameter touches itself once per turn — a **non-manifold edge** that
> `validate`, `interfere` and `check_fit` all pass, and that the slicer fuses
> into a solid tube. State pitch, wire section, coil count, OD, and the
> coil gap. Also state the material: PLA recovers poorly, so a printed torsion
> spring is usually the wrong answer to a band.

### 8b. Kinematic parameters

These **own** the numbers Section 7 builds from. A pivot position that appears
in both sections is two numbers that can drift apart — name it here, derive it
there.

| Symbol | Meaning | Value (mm / deg) | Tag |
|---|---|---|---|
| <GROUND> | fixed pivot A → fixed pivot B | <> | `[tag]` |
| <CRANK> | driven link | <> | `[tag]` |
| <COUPLER> | <> | <> | `[tag]` |
| <ROCKER> | output link | <> | `[tag]` |
| <PHASE_LR> | left/right phase offset | <180> | `[tag]` |

- **Fixed pivots** (assembly coords): <name → (x, y, z)>
- **Moving pivots:** <name → the link that carries it>
- **Joint limits:** <link → range, or "continuous">
- **One cycle does:** <in the object's own terms — "one turn advances the
  diagonal pair through a 34 mm stride">

### 8c. Feasibility condition

Copy this into `<name>_lib.py`. **No gate checks it.** A four-bar with the wrong
proportions, a slider that overruns its slot, a cam whose follower leaves the
track — each one validates, exports, prints, and then jams.

```python
assert <s> + <l> <= <p> + <q>, "not Grashof: crank cannot complete a revolution"
```

### 8d. Not answerable by any gate here

<Carry every line to Open questions. Do not let a passing check imply one of
them: band force and torque; whether the gait actually walks; friction
retention; elastic recovery; snap-fit compliance. `check_motion` is a
rigid-body sweep and reaches none of them — only a print does.>

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

**Per component**

- [ ] <feature> sits on solid material — assert <>; visually confirm in <view>
- [ ] <feature> depth reaches — assert <>; cross-section <axis>

**Per sourced component**

- [ ] every Step 1E element appears in 6c as a hit or a recorded miss
- [ ] every hit that was NOT used carries a stated reason

**Per design reference**

- [ ] every used analogy names the construction lesson and supplies no dimensions
- [ ] every fetched reference passes `design_refs.py verify <project-dir>`
- [ ] every fetched reference retains its local license and provenance

**Per interface**

- [ ] <mating pair> meets with <> clearance — assert <>; cross-section <axis>
- [ ] assembly path is reachable — `check_motion` `assembly_sequence`, one step
      per row of 6a's assembly order. **Not a render:** a render cannot see the
      collision behind the part.

**Per motion** <delete together with Section 8 if nothing is driven>

Every joint gets **both** directions. `expect: "clear"` is a motion that must be
possible; `expect: "blocked"` is a capture — and its direction is the one 8a's
drive pulls. A catch placed anywhere else reads as a clean pass.

| id | check | expect | moving → obstacles | input |
|---|---|---|---|---|
| <crank-full-turn> | `rotation_motion_collision` | clear | <> → <> | 0 → 360°, 36 steps |
| <axle-retained> | `linear_motion_collision` | **blocked** | <> → <> | <the direction 8a says the drive pulls> |
| <band-stays-on-post> | `linear_motion_collision` | **blocked** | <> → <> | <> |
| <assemble> | `assembly_sequence` | clear | <> | steps in 6a order |

Set `allow_seated_contact` on anything that starts installed. Written to
`<project-dir>/measure/motion.json`, run as:

```bash
python skills/cad/scripts/check_motion <project-dir> --manifest measure/motion.json
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

Spec written to `<abs path>`. To build it: use the `cad` skill with this spec —
Size + ledger become the named parameters of `<name>.step.py`, the Step 7 table
in order becomes its `gen_step()` body, and the ledger assertions become
post-generation `scripts/inspect` checks. Section 8, when present, becomes the
kinematic parameters and the feasibility `assert` in `<name>_lib.py`, plus
`measure/motion.json` for `scripts/check_motion`.
