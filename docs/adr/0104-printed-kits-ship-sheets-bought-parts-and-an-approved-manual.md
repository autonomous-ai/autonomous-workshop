# ADR 0104: A printed kit ships its sheets, its Bought Parts and its approved Manual

- **Status:** Accepted (builder, 2026-11-14), for the Amsterdam kit pilot. All
  five decisions are implemented with deterministic tests; the pilot (step 6)
  has not run.
  Each decision below says what is implemented on main and what no live run
  has exercised yet; this header is updated as each step lands.
  - Decision 2 (Bought Parts, tools and packaging billed): implemented,
    deterministic tests only; no kit has been published with it.
  - Decision 1, loose Parts only (`loose_reason`, one loose letter across
    filaments): implemented, deterministic tests only.
  - Decision 1 (Sheets) and decision 3 (the Sheet gate, `small_reason`,
    spares): implemented, deterministic tests only. No Amsterdam Sheet
    has been checked by it yet, and no printed test Sheet confirms its
    constants.
  - Decision 4 (the print layout is the Factory primary, and the
    not-printed `bodies` key fix): implemented, deterministic tests only.
    No kit layout has crossed to Factory yet, and whether Factory prints
    one layout STEP as several plates is still open.
  - The 2026-11-16 amendment (a loose Part's `spares`): implemented,
    deterministic tests only. No kit contract declares it yet.
  - The second 2026-11-16 amendment (every kit Part is one connected
    solid): implemented, deterministic tests only. No kit has re-run its
    gates under it yet.
  - Decision 5 (the owner-approved Manual sealed and shipped byte for
    byte): implemented, deterministic tests only. No Proof has sealed a
    Manual yet. `kit_manual` is an optional APPROVAL field and the schema
    stays 4, as with ADR 0105's `fit_table`.
- **Date:** 2026-11-14
- **Amends:** ADR 0092 (what a kit prints, which Manual ships, a kit's
  Bought Parts block), ADR 0095's 2026-11-07 amendment (the Bought Parts
  block was refused for kits; the printed-only primary was powered non-kits
  only), ADR 0096 (the Approved Proof may seal an owner-approved Manual).
- **Unchanged:** every non-kit, every kit sealed without the new fields, and
  every frozen run. No existing gate is relaxed.
- **Relates to:** `docs/agents/owner-rules.md` "Assembly kits",
  `toys-spec/mini-city-organizer/amsterdam-kit/` (not in git: `cad/sheets.py`,
  `cad/audit_steps.py`, `cad/manual_build.py`, `research/MIN-PART-SIZE.md`).

## Context

The Amsterdam canal tray exists as a user-assembled kit outside Workshop: a
CAD project whose printed Parts sit on FDM sprue sheets (a frame, runners,
break-off gates and debossed part numbers), checked by the project's own
nipper-access, fragile-tip and minimum-size code, with an owner-approved
35-page Manual. The owner wants Workshop to carry such a kit from contract
to publish. A product agent mapped four gaps, each confirmed in the code:

1. **Factory refuses a kit with Bought Parts.** Factory bills every solid of
   the one primary STEP as filament. `_assert_printed_bodies_only`
   (`src/workshop/integrations/factory.py`) refuses a primary with a
   `bought_` body, a magenta body or a `not-printed.json` listing. A kit's
   `assembled.step` must carry its Bought Parts in magenta (ADR 0092
   decision 5), and the printed-only primary that removes them
   (`measure/electrical/printed.step`) is sealed only for powered non-kits:
   `draws_bought_parts` returns False for any Assembly Tree. Separately, the
   adapter reads `not-printed.json`'s `not_printed` key while `kit_tree.py`
   writes `bodies`, so that branch never fired on a real kit.
2. **A kit's Bought Parts are never billed.** `sealed_bought_lines` read the
   electrical section and the `bought-parts` block, and the block was refused
   for any kit (`bought_list.py`). So a kit bills nothing for its pins, and
   the catalogue had no nipper. The Amsterdam kit ships 7 steel pins Ø1.5, a
   glue tube and a mini nipper.
3. **Workshop has no FDM sheet.** ADR 0091's Print Sheet is paper. Each
   printed Part is gated alone in its print stance (ADR 0092 decision 11),
   but nothing lays Parts on a frame, and the owner's sheet rules (gates cut
   by nippers, fragile tips facing open space, a minimum loose-part size,
   spares for small Parts) live only in the project's code.
4. **The approved Manual cannot ship.** Make writes its own Manual from the
   tree (`kit_manual.py`), and the host binds that file's hash. The owner
   approved a different, hand-directed 35-page Manual
   (`manual/AMSTERDAM-KIT-MANUAL-standalone.pdf`). The box also ships it
   printed, with packing, and neither was billed.

## Decision

### 1. A kit may declare FDM Sheets (`assembly_tree.sheets`)

- **Term.** A **Sheet** is one printed plate of one filament: a frame of
  runners carrying printed Parts by break-off gates, each Part's id
  debossed on the runner. It is not a Print Sheet (paper, ADR 0091).
- **Contract.** A kit tree may add `sheets`, each
  `{id, filament, parts: [{id, count}]}`. A Sheet id is the filament's Part
  letter and a number (`A1`, `B2`). Each listed Part is a printed Part of
  that filament. Over all Sheets a Part's `count` is its tree total plus its
  spares, never less. A printed Part on no Sheet is a **loose Part** and
  states `loose_reason` (owner rule: a part that cannot be flat leaves the
  sheet with a written reason). A tree without `sheets` is unchanged.
- **Loose letters** (pilot finding L06, implemented). Loose Parts may share
  one Part letter across filaments, as the Amsterdam kit's T01-T15 do on
  its sheets and in its approved Manual; a letter is either wholly loose
  or wholly one filament. `loose_reason` is accepted on any kit's printed
  Part now; the rule that a Part on no Sheet needs one lands with Sheets.
- **Why not a Sheet Part and a "cut from sheet" step in the tree.** That was
  the first proposal. ADR 0092's tree holds each Part as one leaf and makes
  every step produce one Sub-assembly; a cut step would turn one leaf into
  many, which the counting, reconciliation, insertion and Manual code all
  assume cannot happen, and a Sheet has no body in `assembled.step` to
  reconcile. A Sheet is a print form of Parts, like `print_parts()` (ADR
  0092 decision 11), so it sits beside the tree, as Check Steps do. The
  Manual's "cut from the sheet" instruction is read from it.
- **Geometry.** Each Sheet is a CAD file `sheet_<id>.py` in the project
  (so in an Approved Proof's manifest) defining `sheet()`, which returns
  `{"frame": shape, "parts": [{"id", "shape", "gates": [{"shape", "x", "y",
  "d"}]}]}`: the frame with its runners and tags; every Part copy in its
  print stance at its place on the plate; and each copy's gate bars, each
  with its cut point on the Part outline and `d` = +1 (runner below) or -1
  (runner above). The name is not `*.step.py`, so cadgen never builds a
  Sheet as a project entry. The project's `sheets.py` packs and gates the
  Amsterdam sheets this way already; only its return shape is new.

### 2. A kit's Bought Parts, tools and packaging are sealed and billed (implemented)

- The `bought-parts` block (ADR 0095 amendment) is allowed in a schema 10 or
  later kit. Its parser holds it to the tree: every catalogue entry a tree
  leaf names, unless the electrical section counts it, is listed with at
  least the tree's count (more are spares); any other entry is a tool or
  consumable the tree's `materials` lists, such as the nippers and glue the
  box includes, or **packaging** (below). Self-prepared materials are
  left out of the block.
- **Packaging** (owner and leader, 2026-11-14). A kit's box also carries a
  printed Manual and its packing (small-part bags, a liner between
  sheets), and both are billed as priced extras like the pins. They are a
  new catalogue category, `packaging`, which is never a tree leaf and never
  a Manual material (the tree parser refuses both); the block names them.
- `sealed_bought_lines` bills the block as before. A kit whose tree holds
  Bought Parts but whose Wish sealed no block now bills them unpriced, by
  the tree's count, so `factory_extra_materials` refuses the publication
  instead of leaving their cost out. This is a stricter Release; it relaxes
  nothing.
- The catalogue adds `nipper-mini` (tool, 150 US cents, the owner's own
  estimate on the kit proposal page), `kit-manual-print-a5` (packaging, 120
  cents) and `kit-packing` (packaging, 50 cents), the owner's estimates of
  2026-11-14, and the kit's two pin lengths, `steel-pin-1.5x20.6` and
  `steel-pin-1.5x4.3` (fasteners, 6 cents each like the 29.5 mm pin),
  bought at length so the buyer cuts nothing (leader, 2026-11-14). All are
  unconfirmed estimates, not supplier quotes. The Amsterdam kit's extras
  are therefore 3 pins 1.5 x 20.6 and 5 pins 1.5 x 4.3 (each with one
  spare), a glue tube, a mini nipper, a printed Manual and its packing.
- The block stays out of the Proof's seed hash, so the owner can price a
  sealed kit without re-sealing its Proof.

### 3. Sheet checks are deterministic print gates in `make_round`

A new gate, `kit_sheets.py check` (beside `make_round`), runs on every
Sheet of a kit with Sheets in assembly rounds, `--print-gates-only` and
final verification; never in a component round, since a Sheet spans
Components. It also fails a missing `sheet_<id>.py` and one the contract
does not name. It ports the project's
`sheets.py` checks, which the owner reviewed on the Amsterdam sheets, with
their constants:

- **Same Parts.** The Sheet holds exactly its contract's Part copies, each
  equal in volume and area to that Part's `print_parts()` shape (so a Sheet
  cannot carry a stale Part), on the bed, in the Sheet's filament.
- **Separable.** Each Part copy is at least 2.0 mm from the frame and every
  other Part, except at its own gates, and touches at least one gate.
- **Nipper access** (owner rule "every gate must be cut with nippers"). Each
  gate's jaw keep-out, 6.0 mm to each side of its centre line and 2.0 mm
  back from the cut point, is free of every Part, the frame and the other
  gate bars, and the cut lands on a straight or convex edge across the
  bar's width.
- **Fragile tips** (same rule). A tip narrower than 1.6 mm 0.3 mm behind its
  apex, or narrowing to under 0.6 of its width 1.5 mm behind, has no gate
  within 3 mm, no Part or frame within 3 mm, and no frame or gate within
  8 mm straight ahead.
- **Minimum size** (owner rule, MIN-PART-SIZE R1), on every printed Part
  of a kit with Sheets, loose or not, from its sorted print-stance size:
  thickness at least 1.6 mm, short side at least 4 mm, long side at least
  8 mm, footprint at least 35 mm², volume at least 50 mm³. A Part states
  `small_reason` to pass under it; the gate lists every such Part, the
  receipt carries them, and a Part with one still needs every other limit.
- **Spares.** A Part whose longest side is under 15 mm has at least one
  spare on its Sheets.
- **Sheets are flat plates** (owner rule): no Part copy on a Sheet is over
  3.0 mm tall.
- **One bed** (2026-11-14): the whole Sheet, frame, gate bars and copies,
  fits within 250 x 250 mm in plan. Factory prices and ops print on a
  Bambu A1, whose bed is 256 mm; 3 mm a side stays clear. A larger Sheet is
  measured by Factory on an unbounded bed and flagged `oversize_bed`, and
  no plate prints it. The eight Amsterdam kit Sheets measure 243.9 mm at
  most, and all pass.

The ordinary print gates (`check_mesh`, `check_overhang`,
`check_thickness`) still gate each Part alone; the Sheet gate adds to them.
A failing report fails the round and `verify_project`, so it blocks Spark
Make's finalizer, and the Proof's `--print-gates-only` runs it too. The
round summary records the report as `sheets`.

### 4. A kit's Factory primary is its print layout

- Final verification (`make-round/scripts/kit_print.py layout`, after the
  Sheet gate) seals `measure/kit/print.step` for every kit: every Sheet as
  `sheet()` builds it and one copy of every printed Part on no Sheet for
  each time the toy uses it, laid apart in rows; no Bought Part. Since
  2026-11-14 (record schema 2) each Sheet is one leaf, `<Sheet>`: its
  frame, runners, tags, gate bars and copies fused into one connected
  solid, as the plate leaves the printer. Each loose copy stays its own
  leaf, `loose/<Part>#n`, its own solid. Leaves keep their filament colours.
  A Sheet that does not fuse into one connected solid fails the layout.
  `measure/kit/print.json` records the STEP's hash, the tree it was laid
  out for, each Sheet's copies, the loose copies and the leaf names.
- Why fused: Factory's slicer (panda-social-backend `internal/slicer`,
  read 2026-11-14) splits the STEP into its solids, then auto-orients and
  auto-arranges each one onto 256 mm plates. An unfused Sheet was priced
  and arranged as loose frames, gate bars and Parts, so its plates were
  not the Sheets; a gate bar too thin to slice was counted at full volume.
  Fused, each Sheet is one flat object on one plate (the One bed rule of
  decision 3 keeps it within the bed). The grams change little.
- Before Make acceptance the host (`workshop.make.kit_print`) checks, on
  the sealed bytes, that the record is for the sealed tree and names the
  sealed STEP; that its Sheets and loose copies are exactly what the tree
  gives; and that the STEP's leaves are exactly those names, so no Bought
  Part body is in it. Each Sheet leaf must be one connected solid, meaning
  one solid with one outer shell (a void inside is allowed). Each loose
  leaf must hold a solid, and loose copies of one Part must match in volume
  and area. Only a schema 2 record is accepted. The unfused schema 1
  (`<Sheet>/frame`, `<Sheet>/<Part>#n`) was current for a few hours on
  2026-11-14 and no kit run wrote it; accepting it would let any run ship
  unfused Sheets. A kit with Sheets must have a layout. A kit without
  Sheets is checked when it wrote one (current tools always do); a frozen
  run that wrote none keeps its scene. The Make receipt records it as
  `kit_print`, in the printed-only primary's shape (ADR 0095, 2026-11-07)
  plus `layout_path` and `layout_sha256`.
- The Factory adapter ships that file as the root `assembled.step`, the
  only STEP that crosses, so Factory weighs the filament the maker prints,
  frames included; the scene stays in Made. Release refuses a layout record
  whose `print.json` is not sealed. The not-printed check of
  `_assert_printed_bodies_only` now reads the kit file's real `bodies` key
  (it read `not_printed`, which the file never had) and applies when the
  scene itself would cross; the magenta and `bought_` scans still run on
  whatever crosses.

- Amendment 2026-11-17: a seeded kit's batch (ADR 0098) exports no
  per-occurrence `parts/` in the run and runs no `package-check` at the
  seal. The print layout is the only STEP a kit ships, and the host checks
  it; the scene's assembly package keeps the kit's Part names (`T01-tray`),
  which the Factory path ignores as it ignores any package it cannot read.
  The Amsterdam kit's seal failed package-check on those names.

### 5. An owner-approved Manual is sealed with the Proof and shipped

- `seal_proof.py seal --kit-manual PDF` takes the owner-approved Manual,
  copies it to `approved/kit-manual.pdf` (so it is in the seed manifest)
  and records `kit_manual: {file, sha256}`. This is an optional field and
  APPROVAL stays schema 4. The seal refuses a contract without an Assembly
  Tree, a file that is not a PDF, and a re-seal that would drop a sealed
  Manual. `validate_seed` refuses a `kit_manual` that is not that sealed
  file, or one whose contract is not a kit.
- Make still plans the Manual from the tree (`manual.json`, all of its
  coverage checks). When the seed seals a Manual, `verify_project` passes
  it to `kit_manual.py --approved PDF --approved-sha256 HEX`, which writes
  those exact bytes as `manual/manual.pdf` without drawing anything and
  records `pdf.source: "owner-approved"`; otherwise the source is
  `"generated"`. `verify_made_manual` binds the PDF to the sealed hash. It
  refuses a seeded kit whose PDF is not the approved bytes, and a Manual
  that claims the owner approved it when no seal carries one.
- Release ships `manual/manual.pdf` as today (a Made file to Factory and the
  public archive). The approved Manual pictures the Approved Proof; a seed
  deviation that changes what it shows is reported, not redrawn.

## Amendment 2026-11-16: a loose Part declares its spares

- **Problem.** A Part on a Sheet carries spares in its Sheet counts, but a
  loose Part had no way to declare any. `kit_print.py` laid out exactly
  one copy per use, so the Factory primary shipped fewer Parts than an
  approved Manual promised. The Amsterdam kit's Manual promises five loose
  spares (T09 +1, T10 +1, T11 +2, T12 +1), which is 30 loose copies, but
  the layout held 25. The spare rule of decision 3 also checked only Parts
  on Sheets.
- **Contract.** A loose Part (one with `loose_reason`) may add
  `"spares": <positive integer>`: the copies printed beyond the toy's
  total. The field is optional, and leaving it out means none. A Part
  without `loose_reason` that declares it is refused, as is a value that is
  not a positive integer (`0`, `true`, `1.0`). A Part on a Sheet keeps
  taking its spares in its Sheet counts.
- **Layout and host check.** Decision 4's loose copies of a Part are its
  tree total plus its `spares`. This is so in `kit_print.py layout`
  (`loose`, `copies`, the `loose/<Part>#n` leaves of
  `measure/kit/print.step`, and so Factory's grams and price) and in the
  host's `workshop.make.kit_print`, which refuses a record or STEP without
  the declared spares.
- **Gate.** Decision 3's spare rule now covers loose Parts the same way.
  In a kit with Sheets, a loose Part whose longest print-stance side is
  under 15 mm fails `kit_sheets.py check` unless it declares
  `spares` of at least 1. The 15 mm limit, the one-spare minimum and the
  absence of any `small_reason` exemption are those of the Sheet rule.
  A kit without Sheets is not checked, as before.
- **Unchanged.** A contract without `spares` lays out, prices and passes
  the host check exactly as before. Frozen runs keep their run-local tool
  bytes. A kit with Sheets whose loose Part is under 15 mm now needs
  `spares` before its next round or Proof passes; this is the owner's rule
  that every Part under 15 mm has a spare, not a new limit.

## Amendment 2026-11-16: every kit Part is one connected solid

- **Problem.** The Amsterdam kit's loose Part T03, the rotating main plate,
  builds as 4 disjoint solids: 3 paving bars are cut free of the plate.
  Factory splits the print STEP by solid, so it would print 3 stray bars
  that no Manual step uses. Nothing checked this. A loose copy was its own
  leaf but could hold any number of solids. A Part on a Sheet was only
  caught if its stray piece also missed every gate, through the fused-Sheet
  rule of decision 4.
- **Gate.** Each printed Part's `print_parts()` shape must be exactly one
  connected solid: one solid with one outer shell, where a void inside does
  not count. The rule applies three times:
  - `kit_sheets.py check` (decision 3) applies it, in a kit with Sheets, to
    every printed Part, loose or not. It also applies it to every copy a
    Sheet places.
  - `kit_print.py layout` (decision 4) refuses a loose Part of several
    pieces in every kit, with or without Sheets, and writes nothing.
  - The host's `workshop.make.kit_print` refuses a sealed layout whose
    `loose/<Part>#n` leaf is not one connected solid, as it already refused
    such a Sheet leaf. It formerly required only that the leaf hold a solid.

  Each failure names the Part and its piece count.
- **Unchanged.** A kit whose Parts are each one body passes as before.
  Frozen runs keep their run-local tool bytes. The host check applies on
  Make acceptance; no kit layout has been accepted or published yet.

## Amendment 2026-11-17: a snap joint

- **Problem.** The Amsterdam kit fixes each canal house to quay-main T03
  with two split-arrow clips. Their barbs catch 0.35 mm a side under a
  sleeve at Z 3.5. The owner approved this as the house's knock-proof hold.
  The rigid insertion sweep of ADR 0092 decision 8 cannot pass a barb: at
  `kit_tree --final`, steps S72 to S74 fail with 0.82 mm3 at the first
  sample above the seat. The seated pose is clear. No joint kind
  (peg-socket, tab-slot, pin-hinge, foam-tape, glue) described a snap.
- **Contract.** A new joint kind, `snap`. A snap step names its snap:
  `{"part", "catch", "catch_mm", "region_mm"?}`.
  - `part` is the printed Part that carries the barb. It is a leaf of
    exactly one later input, never of the base, and that input's direction
    lies along one axis of the assembly frame.
  - `catch` is the printed Part the barb clicks past. It is a leaf of the
    base or of an input before the snapping one.
  - `catch_mm` is the barb's catch a side, above 0 and at most
    `MAX_SNAP_CATCH_MM` = 1.0 mm.
  - `region_mm` is optional: a box in the assembly frame where the overlap
    must lie.

  The host's contract parser refuses a field on any other joint, a missing
  or malformed snap, and a deeper catch.
- **Gate.** Each copy of the snapping input is checked by `kit_tree.py` in
  every scope that sweeps it: component rounds, assembly rounds and
  `--final`.
  - Its bodies are swept as before against everything already assembled
    except the catch, at 0.001 mm3.
  - Its bodies other than the snapping Part are swept against the catch at
    0.001 mm3.
  - The snapping Part's overlap with the catch is measured as solids at
    every sample, from the seat outward. Each solid's axis-aligned extent
    across the direction, its smaller side, is its depth. Each depth must
    be at most `catch_mm` (plus 0.001 mm of float noise), and each solid
    must lie inside `region_mm` when it is given. An axis-aligned box never
    reads a barb shallower than it is.
  - At the seat the pair must overlap no more than 0.001 mm3: the barb
    sits clear under its catch.
  - A declared snap whose pair never overlaps on the way in fails as no
    snap. The exemption cannot be declared where nothing needs it.

  Each pass is recorded in the report's `snaps` with its depth, overlap,
  overlapping samples and seated volume. `inspect interfere` (2026-11-16)
  is unchanged.
- **Host.** Before Make is accepted, `workshop.make.kit_tree.check_snaps`
  reads the final report without geometry. It requires:
  - one record for every copy of every snap step across Components, for
    the sealed Part, catch, depth and region;
  - each record passed, overlapped at least once, reached no deeper than
    the catch, and had a clear seat;
  - no record for a step that declares no snap.

  A snap wholly inside one Component is checked in that Component's rounds
  and is not in the final report, like any other step there.
- **Unchanged.** Every other joint and every contract without `snap` is
  swept exactly as before. Frozen runs keep their run-local tool bytes.
  Implemented and tested on deterministic fakes and one build123d probe;
  not yet run on a live kit seal.

## Amendment 2026-11-17 (later): several snap pairs, barb ramps, and a failed union

- **Problem.** The Miami Deco kit is the second kit with snaps. Its
  `kit_tree --final` failed 11 times with no visible defect:
  - The phone hotel snaps in on two keels, Q11 and Q12, and the pool hotel
    on two walls, A06 and A07. Each barb catches T01-tray, but a step could
    declare only one pair, so the second barb of each still blocked.
  - The barbs' 60 degree ramps, at the seat inside the declared region,
    read as non-parallel joints, four per step.
  - At the kiosk seat, the union of the moving group had an inconsistent
    volume. The drum and its stripe touch with no overlap, yet OCCT's fuse
    of the two came out 2.5 mm3 larger than their sum. Nothing could be
    swept.

  The owner approved all three changes on 2026-11-17.
- **Contract.** A snap step's `snap` is one pair, as before, or a
  non-empty list of pairs, each `{"part", "catch", "catch_mm",
  "region_mm"?}` with every rule of the single pair. A list may not name
  the same (part, catch) twice. The single-object form is unchanged.
- **Gate.** Every pair is checked like the single snap: its catch depth,
  its region, overlap somewhere on the way in, and a seat of 0.001 mm3 or
  less. Each pair is recorded in `snaps`, with id suffix `.snap` for a lone
  pair and `.snap1`, `.snap2`, and so on for a list. Every moving body is
  swept at 0.001 mm3 against every catch it is not declared to snap into.
  That includes a snapping Part against another pair's catch, and every
  other assembled Part, as before.
- **Barb ramps.** A flat face of a pair's snapping Part is exempt from the
  non-parallel joint check when both of these hold:
  - its bounding box lies wholly inside that pair's `region_mm` (plus
    0.001 mm);
  - it mates a face of that pair's catch.

  Such a face is recorded in the pair's `ramp_faces`. A pair without
  `region_mm` exempts nothing. Faces of other Parts, faces against other
  Parts, and faces reaching outside the region are judged as before.
- **Failed union.** When the moving group's solids cannot be fused into one
  material, the sweep falls back to one solid at a time. This covers an
  invalid union and a volume that is non-finite, negative or inconsistent
  (`check_motion.rigid_material` raises). Each solid is swept against every
  obstacle, held to the overlap limit divided by the number of solids.
  A solid's overlap with an obstacle is at least its share of the union's
  overlap, so the fallback passes nothing the fused sweep would refuse. Each
  fallback is recorded in the report's `fallbacks`, with the reason, the
  solid count, the limit per solid and the outcome.
- **Host.** `check_snaps` requires one record per copy for every declared
  pair across Components, matched by step, part and catch. It refuses a
  record for a pair the sealed tree does not declare.
- **Unchanged.** A contract with one snap object, and every other joint,
  are checked exactly as before. Frozen runs keep their run-local tool
  bytes. Implemented and tested on deterministic fakes and build123d boxes.

## Not decided here

- The gate and fit constants are the Amsterdam project's, set by the owner
  on 2026-11-13/14 and awaiting a printed test sheet.
- Whether Factory can print one layout STEP as several plates; the pilot
  finds out.
- Make writing the Rolife-quality Manual itself.

## Implementation order

1. This ADR.
2. Decision 2.
3. Decision 1 (contract) and 3 (the Sheet gate).
4. Decision 4.
5. Decision 5.
6. The pilot: the Amsterdam kit's contract and Proof, seal, and
   `build-a-toy --agent claude`; every failure is fixed the same way.
