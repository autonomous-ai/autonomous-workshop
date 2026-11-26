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
  - The 2026-11-23 amendment (the printed-only scene is the viewer model,
    the layout ships under `parts/`, and the printed piece count is sent):
    implemented, deterministic tests only, until the Amsterdam Listing
    Update below records its live result.
  - The 2026-11-26 amendment (a kit may declare it ships no spares,
    `"spares": "none"`): implemented, deterministic tests only. Its first
    user, the New York mini-city kit, has not sealed it yet.
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

## Amendment 2026-11-19: press inputs and seat faces

- **Problem.** The Miami Deco kit's sealed Proof failed its per-Component
  tree steps in every Make component round. ADR 0098's 2026-11-18
  amendment makes the seal run those steps. Two groups of failures were
  no defects:
  - Press ribs: lounger tabs, umbrella canopies, palms, shrubs and the
    dish. Ribs 0.05 mm a side bite their sockets by design. The sweep read
    them as 0.085 to 1.37 mm3 of collision at the first step out of the
    seat.
  - Seat faces: the pen band and eyebrows, phone ledge ribs, front roof,
    bands and pool bay halves. Each slanted flat face (45 to 75 degrees),
    or round face whose axis is across the direction, rests on its stop.
    `nonparallel` judged them as non-parallel joints, though each sweep
    was clean.

  The owner approved both rules on 2026-11-19.
- **(d) Press input.** A moving input of a `peg-socket`, `tab-slot` or
  `pin-hinge` step may declare `press_mm`, above 0 and at most 0.1: its
  ribs' bite a side.
  - Its insertion sweep uses the Part offset inward by `press_mm`
    (`CadGeometry.pressed`, build123d `offset`). The 0.001 mm3 limit is
    unchanged.
  - A Part the kernel cannot offset into one valid, smaller solid is
    refused.
  - The condition carries `press_mm`, and each press is recorded in the
    report's `presses`.
- **(e) Seat face.** A flat joint face at an angle to the direction, or a
  round face whose axis is off it, is accepted only as a seat face. Both
  of these must hold:
  - the input's outward normal has n.d > 0 at each of 5 x 5 sample points
    over the face's parameter range. The face leads into its stop and parts
    from it as the input backs out;
  - the input's sweep is clean.

  A face the kernel cannot read is no seat. Each seat is recorded in the
  report's `seats`.
- **Evidence.** On the sealed Miami Proof, each failing case was rerun with
  the input shifted 0.3 mm sideways. That is a real collision, and every one
  still fails:
  - under (d): the shrunk lounger fails at 0.757 mm3, the canopy at 0.879,
    the palms at 10.5 and the dish at 0.175;
  - under (e): the pen band fails at 1.84 mm3, the ledge rib at 0.151, the
    bay half at 0.725 and a band at 0.089.

  The tests (`tests/make/test_kit_tree_press_seat.py`, real build123d
  solids) cover these cases:
  - a press and a seat each shifted 0.3 mm sideways fail;
  - a bite deeper than the declared press fails;
  - a seat whose sweep is blocked fails;
  - a face that does not lead into its stop, and a whole rod, fail.
- **Unchanged.** Every input without `press_mm`, and every parallel joint,
  is checked exactly as before. The rules do not clear these failures,
  which the design fixes instead:
  - overlaps a shrink does not remove;
  - faces with n.d at or below 0;
  - simultaneous moves.

  Frozen runs keep their run-local tool bytes.

## Amendment 2026-11-19 (later): a joint's faces face each other

Owner decision 2026-11-19 (rule h). The non-parallel check paired any two
parallel faces of one kind within 0.3 mm, judging by `abs(n.m)`. So it also
paired faces of neighbouring Parts that face the same way: one flush surface
running across a seam, such as a sloped roof continued by the next plate, a
riser's face beside the ledge it meets, or a drawer front flush with the
drum's outer wall. It also paired opposed faces that meet only along an edge.
Neither is a joint. Nothing slides on such a pair, and a real collision
between those Parts is the sweep's to find.

A pair is now a joint only when its faces face each other. Some sample point
of the input's face (5 x 5 over its parameter range) lies on that face and
within 0.3 mm of the other face, its foot on the other face's surface lies
inside that face, and the two outward normals there are opposed (n.m < 0). A
pair the kernel cannot read is judged as before. Nothing else changes: the
0.001 mm3 sweep, the 2 degree parallel tolerance, seat faces and snap ramps.

Evidence (Miami Deco Build Kit Proof, `kit_tree --component`): a riser, a back
rest, a roof and a drawer front were flagged only on such pairs. The same Part
shifted 0.3 mm sideways still fails its sweep, by 0.30, 0.276, 0.247 and
46.93 mm3. The tests run on real build123d solids
(`tests/make/test_kit_tree_facing.py`):

- a slope flush across a seam passes;
- the same Part shifted 0.3 mm into its neighbour fails;
- a slope facing its mate is still judged;
- opposed, same-facing and edge-only flat faces, a peg and its bore, and two
  flush drums are each classified.

## Amendment 2026-11-19 (later): the tilt hold and walls before the base

Two owner rules in `docs/agents/owner-rules.md` "Assembly kits" were checked
only by eye. The Amsterdam kit's trees and houses fell over when the owner
bumped the tray, and its first pen tower order slid a wall between two fixed
walls. Amsterdam's per-toy `hold_check.py` measured the first by hand. The
kit tree gate now checks both deterministically. The wall order is checked
in the Component or assembly round that owns the step. The tilt hold is
checked where the whole toy is built.

- **(i) Tilt hold.** A unit is each copy of a moving input of a `peg-socket`,
  `tab-slot`, `pin-hinge` or `snap` step whose direction lies within 45
  degrees of -Z, so the input is set down from above. Its host is every
  other body of the finished toy, so a part that a later step clamps is held
  by that part. The check covers every step, Component-internal ones
  included. It runs in assembly rounds and final verification, and never in
  a component round, which cannot see a clamp from another Component.
  `glue` and `foam-tape` steps hold by adhesive, so they are no unit.
  `CadGeometry.hold` measures, in the assembly frame with +Z up:
  - the bearing level: the highest downward flat face of the unit (normal Z
    at most -0.5, area at least 0.5 mm2) within 0.06 mm of the host, or of
    the toy's lowest level, the table it stands on. The footprint is the
    plan bounds of those faces. A unit that rests on no face tips at 0;
  - H, the height above that level, and d, the reach below it;
  - per way (+X, -X, +Y, -Y), the tip: the tilt at which the centre of
    mass passes the footprint's edge;
  - lift: whether a 0.3 mm lift meets the host by more than 0.002 mm3
    beyond the seat's own overlap, as a snap or detent would;
  - per way, slide: whether a 0.3 mm push that way does;
  - per way, catch: the least of 1, 2 and 3 degrees, turned about that
    footprint edge with the far side lifting, at which it does.

  The unit stays at a 45 degree tray tilt when its lift is held. Otherwise
  every way must either tip at 45 degrees or more, or catch within 3 degrees
  with its slide held. Only what this verdict needs is measured, and the
  rest is recorded as null:
  - a unit that tips at 45 degrees or more every way moves nothing;
  - otherwise the lift is measured, and a held lift ends it;
  - each way that tips sooner has its slide measured, and its catch only
    when the slide is held: first at 3 degrees, then down the samples.

  The cost is at most 18 measures a unit. Each measure moves only the
  unit's bodies within reach of the host, and only against the host bodies
  within reach of them. A unit that does not stay fails the round with its
  H, d and failing ways. Every unit is recorded in the report's `holds`.
- **(j) Walls before the base.** A wall is a printed plate Part: its smallest
  bounding extent is at most 3.5 mm and under a third of the next. It counts
  as set on a base when it is placed as a leaf input of its own, standing
  across an earlier printed Part (the base's thin axis differs from the
  wall's) within 0.3 mm. A wall goes in between parts already fixed when it
  touches two walls set on the same base before it that flank it. They
  stand on opposite sides of it across its direction, each one's centre
  outside the wall's own extent on that axis, and each runs alongside it for
  at least half its length along that direction. The round fails with
  the steps and the walls that meet it: "join these walls to each other
  first, then set them on <base>". It is recorded in `wall_orders`. Several
  wall cases pass:
  - one wall alone, or two walls meeting in a corner;
  - a plate set on the tops of walls, such as a floor or a lid;
  - walls that do not touch each other;
  - walls joined as a Sub-assembly and then set on the base, since a
    Sub-assembly input is no wall.
- **Evidence.** `tests/make/test_kit_tree_hold_walls.py` runs on real
  build123d solids. A 40 mm column on a 4 mm peg 0.1 mm loose a side gives
  three results:
  - 1 mm deep, it falls: tip 14 degrees, no catch by 3 degrees;
  - 6 mm deep, it stays: catch at 2 degrees, slide held;
  - with a ring under the base that a lift meets, it stays.

  A low wide block stays by its 45 degree-plus tip angle. A box of four walls
  pressed onto a base one at a time fails, and so do the same walls in one
  step. The same walls joined first and then set on the base pass. A shelf
  slid down between two fixed sides fails, and the same shelf set on their
  tops passes. On the approved Amsterdam Canal Proof, all 58 units stay at
  45 degrees, measured in 135 s, and no wall order fails. On the Miami Deco
  Proof, all 51 units stay, in 73 s, counting the plaza that rests on the
  table. Its hut walls fail rule j: four walls are each set on the deck, the
  last between fixed ones. That is a real order to fix in its tree. The first
  draft of rule j flagged the Amsterdam phone house's first floor. That floor
  spans its six walls and drops 1.9 mm onto their top tabs. The flank test
  above clears it.
- **Unchanged.** Every existing sweep, press, seat, snap and joint face rule.
  Backends without `hold` or `touching`, which are only the deterministic
  test fakes, measure nothing. The 45 degree, 3 degree and 0.3 mm values are
  the Amsterdam prototype's. Frozen runs keep their run-local tool bytes.

## Amendment 2026-11-19 (later): a press Part the kernel cannot offset

- **Problem.** The Miami Deco kit's boardwalk presses its three peg holes'
  crush ribs, 0.05 mm a side, onto the tray's pegs. Its `press_mm` sweep
  was refused because build123d's `offset` cannot shrink the 613-face
  Part, nor even the bare 450-face solid it is built from. The step could
  not pass at all, however exact the fit.
- **Rule.** When the kernel cannot offset a press input's Part, each
  obstacle is shrunk instead. It is cropped to the box round every pose of
  the sweep (`crop_to_sweep`) and offset inward by the same `press_mm`,
  joined by intersection (`CadGeometry.pressed_obstacles`). The unchanged
  Part then sweeps against those obstacles at the unchanged 0.001 mm3
  limit. Either way, an interference no deeper than the press is cleared,
  whichever side shrinks:
  - an arc join would round a socket's inner corners and put material back
    where the Part's square corners sit, so the join is by intersection;
    where the kernel refuses that join, the arc join is taken, which leaves
    more material and so is never looser;
  - a crop's own cut faces lie the crop's 1 mm margin beyond every pose, so
    their offset reaches none.

  The condition records `press_offset: "obstacles"`, and its `presses` row
  records `offset: "obstacles"`, where the Part's own offset records
  `"input"`. A step where neither offset can be made is still refused.
- **Evidence.** `tests/make/test_kit_tree_press_seat.py` makes the Part's
  own offset refuse. The shrunk socket passes the 4.1 mm peg in its 4.0 mm
  socket at a 0.06 press. The same peg shifted 0.3 mm sideways fails, and a
  4.4 mm peg fails. Refusing both offsets is still refused. With the
  intersection join refused, the arc join still fails the square peg and
  passes a round one. On the Miami tray, cropped to the boardwalk's sweep,
  the obstacle is 25 faces and offsets cleanly; the whole 386-face tray
  does not. The boardwalk's step then passes its component round.
- **Unchanged.** Every Part the kernel can offset is swept exactly as
  before, and so is every input without `press_mm`.

## Amendment 2026-11-23: the viewer shows the assembled kit; the layout is priced under `parts/`

- **Problem.** Decision 4 shipped the print layout as the root
  `assembled.step`, the only STEP. The shop's 3D viewer loads the design's
  primary STEP, so the Amsterdam listing showed nine flat Sheets and the
  loose Parts laid out in rows, not the canal it builds. The joinery house
  listing shows its assembled model with a pieces file beside it: a root
  scene and one STEP under a parts directory.
- **Factory's rules this relies on** (panda-social-backend origin/main
  `2a00b3d`, read 2026-11-23). The slicer (`internal/slicer/tree.go`)
  prices only the shallowest `parts/` or `*_parts/` directory when one
  exists and drops the `assembled.*` roll-up. The importer
  (`services/import_extract.go`, `detectPrimaryByExt`) ranks any file
  stemmed `assembled` or `asm` first as the primary, wherever it sits, so
  no `parts/` file may be named so. A version import without
  `piece_count` drops an earlier declared count (`services/import_version.go`).
- **Rule.**
  - Final verification's `kit_print.py layout` also writes
    `measure/kit/scene.step`: the toy's assembly STEP without exactly the
    leaves `measure/not-printed.json` lists (`bought_model.py
    write_printed_only` with a name predicate). A Part the scene holds
    once may be listed with its `#1`; a listed body that is not exactly
    one leaf fails the layout. A group whose every leaf is listed goes
    with them, so no empty group is left as a body. `print.json` records it under
    `printed_scene` (`step`, `sha256`, `scene`, `scene_sha256`,
    `removed`). Final verification does not count it as a stray STEP while
    `print.json` names its exact bytes.
  - The STEP is sealed by Make and checked by the host, not derived at
    Release. Open CASCADE writes a scene's colour entities in a
    pointer-dependent order, so a host-side cut gives other bytes on every
    run, and the Listing Update's preview and confirm must bind the same
    primary.
  - Before Make acceptance the host (`workshop.make.kit_print`) checks that
    the record was cut from the sealed `assembled.step`, removed exactly
    the sealed tree's not-printed bodies, and is sealed with its hash. It
    also checks that the file holds exactly every other scene leaf, each
    with the scene's volume and area (`check_printed_scene`). The Make
    record then adds `printed_scene_path`, `printed_scene_sha256` and
    `pieces`: every printed Part as many times as the toy uses it, spares
    left out.
  - The Factory adapter ships that scene as the root `assembled.step`, the
    primary the viewer shows, and the print layout byte for byte as
    `parts/kit-print.step`, the one set Factory prices. The handoff check
    requires exactly those two STEPs, with the layout bound by hash in the
    product facts' `print_layout`. The magenta and `bought_` scans read
    both files. The manual is unchanged. The first import and every
    Listing Update send `piece_count`, bound in the ledger intent and the
    Listing Update's confirmation code. The receipt records what Factory
    reads back; no gate depends on it.
- **Not in Workshop.** The listing's hero pill ("153 Pieces | Advanced
  Level | Building Instructions" on the joinery house) is hand-written in
  the design's `landing_page_ref` HTML (`lp-kit-1117`). It is not drawn
  from `piece_count` or `manual_ref`, so a kit gains it only when that
  page is edited.
- **Unchanged.** A kit record without `printed_scene` (every run made
  before this amendment) keeps decision 4's single layout primary, and so
  does every non-kit. No gate is relaxed: the layout is still the exact
  sealed file and still the only thing Factory weighs.

## Amendment 2026-11-26: a kit may ship no spares

- **Problem.** Decision 3 and the 2026-11-16 amendment ask one spare of
  every printed Part under 15 mm. The New York mini-city kit has hundreds of
  tiny Parts: spares would nearly double the kit, its plates and its price.
  The owner decided (2026-11-26) that such a kit may ship none.
- **Contract.** `assembly_tree` may add `"spares": "none"`, its only
  value, meaning the kit ships no spare piece. It is set only with the
  owner's approval (owner rule "Minimum loose part size"). With it, no
  printed Part may declare `spares` and no Sheet may carry more copies of a
  Part than the toy uses: either is refused as inconsistent, so the kit
  truly ships none. Any other value is refused.
- **Gate.** `kit_sheets.py check` asks no spare of a kit that declares it,
  and fails a Part that still declares `spares` or that its Sheets carry
  beyond the toy's count. Its report adds `"spares": "none"`. The size,
  one-solid, flat-plate, bed, separation, nipper and fragile-tip rules are
  unchanged and still apply to every Part.
- **Record and receipt.** `kit_print.py layout` writes `"spares": "none"`
  into `measure/kit/print.json`; the host's `workshop.make.kit_print`
  refuses a record that states it when the sealed tree does not, or omits
  it when the tree does, refuses a declared-none tree with any spare copy,
  and carries `"spares": "none"` into the Make receipt's `kit_print` check.
  `kit_manual.py` writes `"spares": "none"` into `manual/manual.json` and
  prints "This kit has no spare parts" on the front page; the host's
  Manual check holds the report to the tree the same way and carries the
  field into the receipt's `kit_manual` check. The generated Manual never
  drew spare marks, so there is no `+` legend to drop. An owner-approved
  Manual (decision 5) ships its own bytes as before.
- **Unchanged.** A tree without `spares` parses, gates, lays out, writes
  its Manual and passes the host checks byte for byte as before. The Bought
  Parts block may still list more Bought Parts than the tree holds; this
  amendment concerns printed pieces only. Frozen runs keep their run-local
  tool bytes.

## Amendment 2026-11-26 (later): a press offset round its overlaps

- **Problem.** The Kyoto Gion Canal kit declares `press_mm: 0.1` on 63
  inputs. In its component round every one was refused: build123d's
  `offset` returns a null shape or an offset error for the Part (an
  abutment of 74 faces, a cherry trunk of 278, a roof, a gravel bed) and
  also for its obstacles cropped to the sweep (the path, the tray). Miami's
  simpler Parts passed. The fits themselves are sound: on the bridge
  abutment the deepest rib bites about 0.035 mm.
- **Rule.** When neither the Part nor its obstacles can be offset whole,
  the Part is offset only round where it can bite
  (`CadGeometry.pressed_local`):
  1. At every pose the sweep samples (the same `steps` and `translation`),
     the Part's overlap with each obstacle is measured by a boolean common.
  2. Each overlap's box, taken back into the Part's own frame, is a window.
     A box inside another drops. A box longer than 8 mm on a side is split
     into tiles that cover it.
  3. Each window is grown by a margin M > `press_mm` (`press_mm` + 0.3 mm,
     else + 0.15, else + 0.6). The Part is cut to it, and each cut solid is
     offset inward by `press_mm`. Where the kernel cannot offset a cut
     either (Kyoto's crops are small flat solids with features 0.05 to
     0.1 mm thin, which the press removes whole and the offset cannot), the
     cut is shrunk by booleans instead (`CadGeometry.eroded`): its common
     with copies of itself moved `press_mm` along each of its face normals,
     both ways, plus nine sampled normals of each curved face, one per
     10 degree cone. A point survives only if every point `press_mm` from
     it along those directions is in the cut; the arc offset keeps it only
     if every point within `press_mm` is. So this keeps everything the
     offset keeps: on a flat face it is the offset, and beside a concave
     edge or a curved face it keeps a little more, which can only fail
     more. A common the kernel reports as not done, a result that is not a
     valid solid no larger than the cut, or a result missing any point of
     a 6 x 6 x 6 grid that lies deeper than `press_mm` + 0.001 in the cut
     (a boolean silently dropping material, which would loosen the gate)
     is a refusal. The result's split faces are merged
     (`ShapeUpgrade_UnifySameDomain`, as build123d's own booleans do)
     before that check.
  4. The rest of the Part, outside every window, is kept unshrunk.
  5. The shrunk windows and the unshrunk rest sweep together against the
     unchanged obstacles at the unchanged 0.001 mm3 limit. Where the
     kernel cannot sweep them as one (its common returns invalid
     geometry), they sweep solid by solid, each held to the limit over the
     number of solids, as a group whose union fails already does
     (`_sweep_each`): a union's overlap is at most the sum of its solids',
     so this is never looser, and it is recorded in `fallbacks`.

  Why this is the same gate. A point of an overlap lies at least M from
  its window's cut faces. So it is deeper than `press_mm` inside the cut
  exactly when it is deeper than `press_mm` inside the whole Part. The
  windows' offsets therefore overlap the obstacles exactly where the whole
  Part's offset would, at every sampled pose, and hold nothing the whole
  offset does not. The rest sweeps unshrunk: it overlaps nothing, and were
  an overlap missed it would fail there rather than pass.

  A bite deeper than `press_mm`, a sideways slip, or a collision anywhere
  else on the Part fails exactly as before. The rule is the input offset's
  own: an overlap no deeper than `press_mm` passes wherever it lies, as it
  always has. Seated contact at the seat is judged as before. An overlap
  the kernel cannot measure, a window it cannot cut or offset at any
  margin, by offset or by booleans, or a rest it cannot cut is a refusal,
  never a pass. The condition records `press_offset: "local"`,
  `press_windows` and, when booleans shrank a cut, `press_eroded` (how
  many cuts), and its
  `presses` row records `offset: "local"`.
- **Order.** The input's own offset first, then the obstacles' (2026-11-19,
  press obstacles), then the windows. A Part the kernel can offset whole is
  swept exactly as before and never reaches the windows.
- **Evidence.** `tests/make/test_kit_tree_press_seat.py`:
  - A peg with a name embossed on its top, which the kernel itself cannot
    offset (a null shape, as in Kyoto), passes a 0.05 mm rib bite in a
    4.0 mm socket at `press_mm` 0.06.
  - Fails: a 0.3 mm bite a side, a 0.3 mm sideways shift, and an arm 5 mm
    off the socket that ploughs 1 mm into the base.
  - With every offset refused, the same peg passes by booleans; the
    0.3 mm bite, the sideways shift and the arm still fail by booleans.
  - The boolean shrink of a box equals the arc offset; for an L-shape, a
    cylinder and a filleted box nothing of the arc offset is missing.
  - Refused: no shrink anywhere, a boolean the kernel reports not done, and
    a boolean that silently returns nothing (caught by the grid check).
  - Windows the kernel cannot sweep as one pass solid by solid at half
    the limit each, a biting piece still fails, and no other group takes
    that path.
  - A plain peg never reaches the windows.
  - Where the whole offset can be made, the windows give the same verdict
    and overlap at depths 0.03, 0.06 and 0.12.

  On the Kyoto bridge abutment, at depths 0.01 to 0.04, the whole offset and
  the windows gave identical verdicts and overlaps (0.007218, 0.004124 and
  0.001869 mm3, then clear). On the whole Kyoto component round, the
  windows alone left 42 press inputs refused: the kernel could not offset
  their small flat cuts either. Rerun on the 38 steps holding them, with
  the boolean shrink and the solid-by-solid sweep, 52 of their 53 press
  inputs pass (41 by windows, 40 of which needed the boolean shrink on at
  least one cut; 2 by obstacles; 8 by the whole offset, which the kernel
  makes on some runs and not others; and S103's second lantern hat once
  its pieces swept one by one). The one left, S131 in S145, offsets whole
  and still collides 0.549 mm3 with the annex end wall at step 47 of 244:
  a real collision, not a press. Kyoto's other blocked inputs and its
  non-parallel joints are outside this amendment.
- **Unchanged.** Every input without `press_mm`, and every Part or
  obstacle set the kernel can offset whole.

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
