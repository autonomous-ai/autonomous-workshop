# ADR 0095: Powered toys state their circuit, and Make proves it with check_power

- Status: Proposed on 2026-10-29 for the Macintosh fidget (`toys-spec/
  macintosh-fidget`). Implemented on branch `powered-toys` with
  deterministic tests: Design Contract schema 10's `electrical` section,
  the catalogue categories and seeds, Wired Parts, the leads `method`, the
  Manual's cells and soldering lines, `make_round --full`'s power class and
  the host's power-report check. Nothing is validated by a live run yet,
  and every new catalogue seed is unconfirmed.
- Date: 2026-10-29
- Amends: ADR 0092 (Check Steps, leads steps and the Manual's front page),
  ADR 0094 (schema 10 is schema 9 plus an optional section)
- Amended on 2026-10-30 by "Amendment: an external source" below (the
  buyer's own USB charger; Macintosh fidget gaps E1-E3)
- Relates to: ADR 0061 (Spark keeps Make's own verification), ADR 0062/0063
  (STEP only, print gates on source), the vendored
  `electromechanical-integration` skill and `verify_project --powered`

## Context

The first powered toy is the Macintosh fidget. It is lit by an amber LED
through a 75 ohm resistor and a lever microswitch on the + lead, from 2 x AAA
cells in a printed bay with spring, plate and bridge contacts. A rear door
holds the cells with a captive M2 x 6 screw. The floppy fully in presses the
switch, and the screen lights. The circuit draws about 12.7 mA at 3.0 V, about
60 hours on alkaline cells.

Its readiness review (`toys-spec/macintosh-fidget/WORKSHOP-READINESS.md`,
G1-G10) found that Workshop could not state or prove any of that:

- The catalogue had no cell, contact or switch category, and none of the
  fidget's parts (G1).
- Bought Parts existed only inside a kit's Assembly Tree (G2).
- Only a lamp could have leads (G3).
- A Check Step could hold only lamps and power (G5).
- The Manual printed one battery line per `power` part and had no soldering
  step (G6, G7).
- No contract field stated the circuit, and nothing required the powered
  gate (G4).
- design-a-toy never asked about the circuit (G9).

`autonomous-product-to-cad` already builds powered products:

- The `electromechanical-integration` skill selects real parts with cited
  evidence.
- It writes `measure/power.json` (schema 3) with each component's role
  (source, protection, switch, controller, connector, wire, actuator, load,
  inlet), its voltage and current, its mount, and each source-to-load path
  with the current it must carry.
- Its `check_power` gate checks the report's internal consistency, the
  mounts and the wire envelopes.
- `verify_project --powered` refuses without the report, runs `check_power`
  whenever the report exists, and refuses an image-derived final run that
  names neither `--powered` nor `--unpowered`.

The resync to upstream `23089af` brought that skill and its wiki pages into
Workshop unchanged.

## Decision

1. **Design Contract schema 10 adds an optional `electrical` section.**
   The owner approves the circuit in it, and design-a-toy's Electrical grill
   fills it:
   - `parts`: each part is a catalogue Bought Part playing one of
     `check_power`'s roles, and the role must fit the part's category.
   - `paths`: each path starts at its source, runs through exactly one load
     (with no other source or load inline), returns to the source, and
     states its `current_ma`. Wires stay out of the sequence.
   - `supply_v`.
   - `standby_ma`.
   - `runtime_h`.
   - `switch_logic` (one sentence).
   - `assembled_by`: `maker` or `buyer`.
   - `joins`: `solder` or `solderless`.
   - `batteries_included`.

   Every non-wire part lies on a path. Schema 10 is schema 9 plus this
   section, and a schema 10 contract without it is unpowered. Schema 1 to 9
   contracts and frozen runs refuse the section and keep what they sealed.
2. **No kit needed (G2).** The section's parts are sealed with their
   catalogue snapshot in the WISH context, the same place a kit's tree
   snapshot goes, so a toy sold assembled still carries its Bought Parts.
   The host and the receipt therefore know what was bought. A kit that
   also states a circuit must name the same entries in both: every wired
   tree part is an electrical part, and every electrical part is a tree
   Bought Part.

   We recommend the tree-less list for the Mac fidget. It is sold assembled
   by the maker, so a buyer-facing Manual would be a cost with no reader.
   We rejected a separate tree-less `bought[]` list: the electrical parts
   are the bought parts that matter, and a second list would have to agree
   with them.
3. **The catalogue gains `cell`, `contact` and `switch` (G1).** Twelve
   fidget seeds are added with `lead diameter` sizes where a part has
   leads. Each seed's pack and source are null, and each stays unconfirmed
   until the owner confirms it.
4. **Wired Parts (G3, G5).** A leads step and its routes may name any
   Wired Part: a lamp, or a Bought Part with a lead diameter (a switch, a
   resistor, a wire). The run-local tree sweep already reads the lead
   diameter. A Check Step may name lamps, power, cells, contacts, switches,
   wires and `other` parts, as long as it has at least one lamp and one
   power or cell part.
5. **The Manual (G6, G7).** Loose cells give one `Batteries: N x <name>`
   line. A battery contact prints no line.

   A leads step may name its `method`: `twist`, `solder` or `connector`.
   The method titles the step. A soldered step adds a soldering iron and
   solder to the self-prepared tools and adds the company's
   `warnings.soldering` to the front page. A company configuration without
   that warning writes no Manual.
6. **Make proves the circuit with the upstream gate (G4); no parallel
   gate.**
   - Make writes `measure/power.json` with `electromechanical-integration`.
     Each non-wire electrical part becomes a report component with the same
     id and role, and each contract path becomes a report path with the
     same id, source and load. That path's sequence, wires left out, is the
     contract's, and it is rated for at least `current_ma`.
   - `make_round --full` passes `--powered` for a schema 10 circuit. For
     any other image-derived run it passes `--powered` when a power report
     exists and `--unpowered` otherwise. This also fixes the refusal that
     every Contract Mode `--full` met on main, which passed
     `--image-derived` without a class.
   - Before Make is accepted, the host reads the manifest-bound report and
     the final pipeline record, sha-checked:
     - the record's newest run must pass `check_power` (a skipped or failed
       row refuses, and a NOTE row is no run);
     - the report must be the sealed circuit;
     - each path must be rated for the contract's current;
     - the source's declared voltage must cover `supply_v`.

     The host does not rerun the gate (ADR 0061). The receipt's `power`
     entry lists the paths, supply, standby, runtime, `assembled_by` and
     `joins`.

   `check_power` and `check_mount` still judge the evidence, the mounts and
   the wire envelopes.
7. **design-a-toy (G9, G8).** The grill gains one Electrical bullet. It
   covers the circuit, switch logic, standby drain, LED current and
   runtime, and who solders.

   Stage 3d states a switch's actuation as two `check_motion` conditions on
   the lever's operating zone, which is modelled as a validation envelope:
   blocked at *in* and clear at *out*. This is a documented method with no
   new code, and no run has tested it yet.

## Considered options

- **Contract the fidget as a kit.** This works today, but it forces a
  buyer Manual, Check Steps and bags onto a toy sold assembled, and still
  states no circuit.
- **Seal a draft `power.json` in the contract.** A power report needs
  mounts, evidence and searches that only Make can produce. The contract
  states what the owner decides: the parts, paths, numbers and who
  assembles. Make's report must then agree with it.
- **A Workshop electrical gate.** This would duplicate `check_power` and
  drift from upstream on the next resync. The host check adds only that
  the report is the sealed circuit.

## Consequences

- A powered Make costs a power report. Every carried component needs a
  mount, evidence and a `component_search` record. That is upstream's
  evidence bar, and it may be heavy for a toy. The owner should judge it
  on the first live run.
- `batteries_included` is sealed but not yet read. The company's batteries
  warning still says batteries are not included. Choosing the warning by
  the flag is a follow-up.
- Battery-door rules (G10: a tool to open, a captive fastener, an abuse
  test) stay in the wiki and in contract rows the Component Reviewer
  judges. Nothing gates them.
- The receipt's power entry reports the circuit Make proved. It does not
  claim that a physical toy lights.

## Amendment: an external source (2026-10-30, readiness gaps E1-E3)

Status: Accepted; implemented and deterministically tested; not yet
validated by a live run.

### Context

The Macintosh fidget became a USB-C night light: the buyer's own USB
charger powers it, with no cells and no battery door. A floppy half in
closes one microswitch (screen glow and dim warm light) and fully in closes
a second (bright). Its readiness notes
(`toys-spec/macintosh-fidget/WORKSHOP-READINESS.md`, E1-E5) found three
gaps in decision 1:

- **E1.** A path had to start at a `source`, and a source had to be a
  `power` or `cell` Bought Part. The draft therefore sealed the buyer's
  charger as a Bought Part the toy never ships. `check_power` already
  models this case as its `external` boundary: a non-carried source and a
  carried `inlet`.
- **E2.** `runtime_h` had to be above 0, so the draft stated a placeholder
  `1`.
- **E3.** Decision 1 said "one path per load", while the draft has a dim and
  a bright path to each warm LED. Whether `check_power` accepted that was
  untested.

### Decision

1. **An external source.** A source part may be exactly
   `{"id", "role": "source", "external": true}`. It names no Bought Part, so
   it has no `bought` and no `count`; only a source may be external. It is
   not in the sealed catalogue snapshot, the Manual or the receipt's part
   count. A circuit with an external source carries an `inlet` part (the
   receptacle, an `other` Bought Part), and every path from the external
   source passes an inlet before it returns. A path is otherwise checked as
   before: it begins and ends at its source, holds its load once, and
   carries no other source or load. A circuit's sources are all external or
   all carried, because `check_power` has one boundary per report.
2. **No runtime without cells.** When every source is external, `runtime_h`
   is null or absent, and `batteries_included` is false. A circuit with a
   carried source still needs `runtime_h` above 0.
3. **Make's report and the host check.** For an external source, Make's
   `measure/power.json` declares `boundary: external` and the source as a
   component with the same id, `role: source` and `carried: false`.
   `check_power` already requires the carried inlet. Before Make is
   accepted, the host additionally refuses a report whose boundary or the
   source's `carried` disagrees with the contract. It also refuses an
   external boundary for a contract that carries its source. The source's
   declared voltage must still cover `supply_v`. The receipt's `power`
   entry gains `boundary` (`external` or `onboard`), counts only the parts
   the toy carries, and reports a null `runtime_h`.
4. **Several paths to one load.** Decision 1's "one path per load" means at
   least one. A load may have several paths, such as a dim and a bright
   branch through different resistors and switches. `check_power` rates
   each path independently and refuses only an inline second load, and a
   test runs the vendored gate on the USB fidget's seven paths to four
   loads. No folding rule is needed.
5. **No new schema.** This is an additive amendment to schema 10, the way
   ADR 0082's #80 amendment widened schema 2 Interfaces. Every schema 10
   section that sealed before stays valid with the same meaning, because
   no earlier section could carry `external` or a null `runtime_h`. Schema 1
   to 9 contracts and frozen runs are unchanged.

### Not decided here

- **E4.** The PCBA (USB-C, LEDs and resistors on one board) has no catalogue
  form. The contract lists the parts individually, and Make models the board
  as a mount or validation envelope. Buying it as one line is the owner's
  decision.
- **E5.** Filaments carry a colour, not a material, and there is no
  translucent natural filament. The owner adds catalogue entries. Contract
  rows state PETG where it matters, and no gate reads material.
- The draft's new catalogue seeds (`usb-c-receptacle-power`,
  `led-2835-warm-2200k` and the 150, 470 and 110 ohm resistors) wait for
  the owner. The tests use them only in a test catalogue.
