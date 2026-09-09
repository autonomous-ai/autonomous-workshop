<!--
  image-to-cad build spec — powered / mechanism addendum.

  Load this file only when Step 1G finds a functional electrical load, or a
  part moves under a driving force (band, spring, motor, gravity, hand crank).
  Paste these sections into the spec at their numbered positions: 6f after 6e,
  section 8 after section 7, and the checklist block into the Verification
  checklist. An inert decorative lens, or a lid that merely opens, needs none
  of it — say so in the one line the core template leaves there.

  Same rules as the core template: fill every bracket, delete every HTML
  comment, every number carries [observed] | [inferred] | [assumed], mm
  throughout.
-->

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

## Verification checklist — powered additions

Paste this block into the core template's Verification checklist. When a light
is removable, also add these rows to that checklist's motion table:

| id | check | expect | moving → obstacles | input |
|---|---|---|---|---|
| <light-insert> | `linear_motion_collision` | clear | <lamp> → <socket/product> | insertion axis to lock datum |
| <light-lock> | `rotation_motion_collision` | clear | <lamp> → <socket/product> | unlocked → locked angle |
| <light-retained> | `linear_motion_collision` | **blocked** | <locked lamp> → <socket/product> | axial removal direction |
| <light-unlock> | `rotation_motion_collision` | clear | <lamp> → <socket/product> | locked → unlocked angle |
| <light-remove> | `linear_motion_collision` | clear | <unlocked lamp> → <socket/product> | extraction along insertion axis |

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
