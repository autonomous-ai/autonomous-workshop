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

<Write one entry per **visible component** of the object, not per printed part.
A component here is what a person pointing at the object would name: body,
stripe, fins, tail cavity, socket, lamp, post, base. Which of these become
printed parts is section 6's question and must not be answered yet; several
components routinely end up in one printed part, and deciding the split first
is what makes a component disappear before anyone has described it.

Prose, not a table. A table forces every component into the same cells, and the
detail that carries the likeness is never the same twice: on one part it is that
the nose stops in a small spherical cap rather than a point, on another that
only the *inner* face of each fin is painted, over a strip 5–8 mm wide, so the
flame appears only when the lamp is lit. Neither survives a cell called
"Purpose".

This section exists because the two places that look like they hold it do not.
Sections 2–4a describe the whole object's silhouette per view; section 7
describes build123d calls, by which point the shape is already settled. A
component never written down between those two is a component the generator
will not have.>

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

<A component whose entry cannot say more than its bounding box has not been
described. Either look at the reference again, or write plainly that this
component is not resolvable from the available views and carry that into
Assumptions — an honest gap is recoverable, a box that was never questioned is
not.>

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

### 6a. Printed parts

<Default is ONE. If one part, say so and give the reason the split test failed.

Do not start this table until section 4b describes every component. Splitting
first silently answers "what is this object made of" with "what is convenient
to print", and the components that never make it into a row are the ones nobody
wrote down — they do not fail a gate, they are simply absent. Each row's parts
must account for whole components from 4b; if a component is not in any row,
say where it went.>

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

<One row per standard mechanical element found in Step 1E and bought powered
component found in Step 1G — gear, bearing, fastener, spring, pulley, magnet,
insert, actuator, LED/lamp/module, controller, connector or board. Write this
section even when every row is a MISS; a recorded miss stops the next turn
re-running the search. Delete the section only if Steps 1E and 1G found none,
and say so in one line.>

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

<Use this for construction patterns, not bought parts. Run the design-reference
search only when a mechanical/product feature has a real construction question.
Write `N/A — no applicable construction analogy` for a unique organic subject.
Never copy dimensions, scale, placement, or silhouette from this table.>

| Query | Catalog id, MISS, or N/A | Relevant feature | Construction lesson used | Local provenance | License/use |
|---|---|---|---|---|---|
| <> | <> | <> | <> | `<project>/ref/external/.../provenance.json` | <> |

### 6e. Mount declarations — becomes `measure/mounts.json`

<One row per component the model must physically hold. Delete the section if no
6c row is modelled as a seat or a pocket, and say so in one line. The seat and
the screw pattern are derived from the component's own STEP; this table declares
where it sits, not how big it is.>

| id | component (`ref/…`) | `sha256` from 6c | pose in assembly coords | parts measured against | min clearance | bolt axis | bolts |
|---|---|---|---|---|---|---|---|
| <> | <`ref/<file>.step`> | <64 hex> | <`[x,y,z]`, or `{position, rotation}` in deg> `[tag]` | <labelled parts; omit for the whole assembly> | <mm, default 0.10> `[tag]` | <`[0,0,1]`; omit to search any> `[tag]` | <`true`, or `false` for a strapped, glued or captive-screwed part> |

**A derived seat is not proof the model has one.** The generator may never have
subtracted it, may have cut it in the wrong place, or may have added a feature
later that ate half of it — `validate`, `interfere`, `check_fit`,
`check_motion` and `check_mesh` pass all three. `check_mount` is the only gate
that reads the component's own STEP back into the assembly.

Insertion is a joint, so a seated component also gets **both** directions in the
motion table below: `clear` along the way the component travels in, `blocked`
along the way it must not back out. Set `allow_seated_contact` on anything that
starts installed.

### 6f. Removable-light mating interfaces — becomes `power.json` + `motion.json`

<Write one row per lamp/light module that can be removed from a socket. Delete
this section only when every functional light is soldered, fixed or integrated,
and state that explicitly. The exact lamp, socket and separate contacts each
need their own 6c row; every carried socket/contact seat needs a 6e row. Prefer
a purchased socket documented for the exact lamp family. A printed receiver is
allowed only with authoritative mating geometry, bought rated contacts and a
written reason a purchased socket was not used.>

| Interface id | Type | Lamp component + exact MPN | Receiver strategy | Receiver component + exact MPN | Contact component + exact MPN | Sources + revisions |
|---|---|---|---|---|---|---|
| <> | <twist_lock / bayonet / push_fit / threaded / plug_in / other> | <6c id + MPN> | <purchased_socket / printed_receiver + justification> | <6c id + MPN, or printed part> | <6c connector id> | <lamp URL/rev; receiver URL/rev> `[tag]` |

| Interface id | Source datum | Lugs | Insert depth | Lock rotation | Direction | Clearance | Derivation | Retention stop | Connector access | Tool/finger access |
|---|---|---|---|---|---|---|---|---|---|---|
| <> | <> | <count> `[tag]` | <mm> `[tag]` | <deg> `[tag]` | <CW / CCW / none> | <mm> `[tag]` | <`cadfits` derivation or purchased-socket seat from STEP> | <> | <> | <> |

| Interface id | insert `clear` id | lock `clear` id | retained pull `blocked` id | unlock `clear` id | remove `clear` id |
|---|---|---|---|---|---|
| <> | <> | <> | <> | <> | <> |

**Physical fit coupon** — one complete receiver interface, not a plain gauge:

| Interface id | Status | Material | Process | Orientation | Exact hardware samples | Candidate clearances | Selected clearance | Method | Result |
|---|---|---|---|---|---|---|---|---|---|
| <> | <planned / passed / failed> | <> | <printer/process + nozzle/layer> `[tag]` | <> | <lamp + socket/contact lot/sample ids> | <at least 3 values, mm> `[tag]` | <tested value; only for passed> `[tag]` | <print and dry-fit procedure> | <> |

`planned` means the CAD interface and its test are specified but physical fit
is unverified. `failed` blocks the design. `passed` is valid only when the
selected clearance was one of the candidates tested with the exact production
hardware, final material/process and final print orientation; update the CAD
parameter and this spec to that tested value. The current CAD clearance must
always be one of the coupon candidates.

The Section 7 feature table must include the purchased-socket seat or printed
receiver, insertion mouth/channel, swept locking path or thread, end stop and
capture shoulder, connector/terminal access, wire channel and removal access.
Do not reduce the interface to a nominal drilled hole.

---

## 7. Feature detail + build123d operation

Part: **<name>** — executed in this order inside `gen_step()`.

| # | Feature | Geometry + numbers | build123d call | Plane / selector | Risk |
|---|---|---|---|---|---|
| 1 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |
| 2 | <> | <> `[tag]` | `<call>` | `<selector>` | <> |

**Named parameters that own a shared number:** <parameter → what it owns>

---

## 8. Powered system / mechanism

<Write this section when any electrical load is functional or a part moves
under a **driving force** — a band, spring, motor, gravity or hand crank. A lid
that merely opens is a joint and belongs in 6a. For functional lighting with no
moving mechanism, complete 8a and delete 8b–8d with an explicit N/A line.>

**Mechanism archetype:** <crank-rocker four-bar | slider-crank | pull-back
flywheel | cam-follower | Klann linkage | torsion-return hinge | N/A — no
driven mechanism> — <why this one, and what was rejected. "Runs on a rubber
band" is not an archetype.>

### 8a. Drive

**Electrical completeness rule:** a motor, servo, solenoid, LED, lamp, beacon,
strip or illuminated control is a load, never an energy source. For every
functional electrical load, complete the electrical rows below and one schema 3
power path per independently rated branch; use `N/A — non-electrical drive`
only for a genuinely mechanical drive. A self-contained or portable product
that runs, spins, moves or emits light requires an onboard source and control
unless the user explicitly chooses a tethered supply. Do not write
"battery/switch outside CAD scope" merely because the photograph does not show
the underside.

| Property | Value | Note |
|---|---|---|
| Electrical loads / driven output | <DC motor \| servo \| solenoid \| LED/lamp/module \| linkage \| other> `[tag]` | every bought electrical load also gets a 6c row |
| Energy source | <battery chemistry + cell count \| external supply \| supercapacitor \| rubber band #<size> \| printed spring \| catalog spring \| gravity \| hand> `[tag]` | a purchasable source also gets a 6c row |
| Power boundary | <onboard \| external/tethered \| N/A mechanical> `[tag]` | external still needs an inlet/lead, connector and strain relief |
| Switching / control | <SPST switch \| PWM + MOSFET \| H-bridge \| ESC \| servo controller \| mechanical release> `[tag]` | name the device that actually interrupts or controls power |
| Electrical compatibility | <source min/nominal/max V; each load's rated V; actuator running/stall A or other load continuous/peak A; controller/switch ratings> `[tag]` | cite manufacturer/standard evidence; geometry gates cannot verify this |
| Complete power path(s) | <source + → protection if required → switch/controller → one actuator/load → source −> `[tag]` | one path per independently rated branch; no functional load may end at an unspecified wire |
| Interconnect / routing | <connector types, wire route, clearance envelope, strain relief> `[tag]` | every carried connector/board gets 6c and every seat gets 6e |
| Service access | <battery hatch \| charging port \| removable plug \| external lead> `[tag]` | state how power is replaced, charged and made safe for assembly |
| Stored by | <winding <n> turns on <part> \| compressing <n> mm \| deflecting <deg>> `[tag]` | |
| Anchored at | <the part + feature holding each end> | must resist the pull, not just touch it |
| **Drive direction** | <e.g. "band pulls −Y along the axle groove"> | this is the direction every `blocked` condition tests |

**Lighting ledger** — delete only when no functional lighting exists:

| id | function | part + pose | colour | behavior | optical direction / luminous surface | emitter/module + driver | installation | interface id + receiver | lens/light pipe/diffuser | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| <> | <position/head/status/beacon/etc.> | <> | <> | <steady/blink/strobe/dim/animation> | <> | <exact MPN or unresolved> | <removable_socket / soldered / fixed_module / integrated> | <6f id + socket/contact, or N/A> | <visible product geometry> | `[tag]` + manufacturer/standard URL |

Every lighting item triggers `$electromechanical-integration`'s automatic
GitHub → `step.parts` → manufacturer/public-CAD discovery. Record those queries
in schema 3 `github_search` and `component_search`; do not infer an MPN or
mating socket from the image.

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

- **Fixed pivots** (assembly coords): <name → (x, y, z)> `[tag]`
- **Moving pivots:** <name → the link that carries it>
- **Joint limits:** <link → range, or "continuous"> `[tag]`
- **One cycle does:** <in the object's own terms, with every numeric output
  tagged>

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

**Per functional electrical load**

- [ ] every motor/light/etc. is explicitly functional, externally powered, or a non-functional stand-in
- [ ] source, protection where required, switch/controller, one actuator/load
      and return form one complete path per independently rated branch
- [ ] source voltage/current and switch/controller ratings are compatible with
      actuator running/stall or other load continuous/peak requirements, with
      cited manufacturer/standard evidence
- [ ] every carried battery holder, switch, controller, connector and board has
      its 6c decision and every physical seat has a 6e mount declaration
- [ ] wire routing, connector access, strain relief and battery replacement or
      charging access have geometry targets
- [ ] every functional light has function, colour, behavior, emitter/module,
      visible optic and a recorded GitHub/public-service search outcome
- [ ] every removable light has a complete 6f record naming exact lamp,
      receiver/contact evidence, mating geometry, service access and all five
      motion-condition IDs
- [ ] purchased socket/contact components have independent 6c search records,
      assembly CAD, 6e mount declarations and appear in the electrical path
- [ ] `insert` and `lock` are clear, locked axial pull is blocked in the actual
      removal direction, and `unlock` and `remove` are clear in `check_motion`
- [ ] the fit coupon records exact material/process/orientation and hardware;
      `planned` is reported as physically unverified, `failed` blocks delivery,
      and `passed` selects one clearance that was actually tested
- [ ] schema 3 `measure/power.json` passes `check_power <project-dir>`
- [ ] a self-contained or portable powered product does not depend on an
      external supply unless the user explicitly selected one

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
| <crank-full-turn> | `rotation_motion_collision` | clear | <> → <> | <start> → <end>° `[tag]`, <steps> steps `[tag]` |
| <axle-retained> | `linear_motion_collision` | **blocked** | <> → <> | <the direction 8a says the drive pulls> |
| <band-stays-on-post> | `linear_motion_collision` | **blocked** | <> → <> | <> |
| <assemble> | `assembly_sequence` | clear | <> | steps in 6a order |
| <light-insert> | `linear_motion_collision` | clear | <lamp> → <socket/product> | insertion axis to lock datum |
| <light-lock> | `rotation_motion_collision` | clear | <lamp> → <socket/product> | unlocked → locked angle |
| <light-retained> | `linear_motion_collision` | **blocked** | <locked lamp> → <socket/product> | axial removal direction |
| <light-unlock> | `rotation_motion_collision` | clear | <lamp> → <socket/product> | locked → unlocked angle |
| <light-remove> | `linear_motion_collision` | clear | <unlocked lamp> → <socket/product> | extraction along insertion axis |

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
