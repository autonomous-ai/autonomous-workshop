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
  each time the toy uses it, laid apart in rows; no Bought Part. Its leaves
  are named `<Sheet>/frame` (frame, runners and gate bars),
  `<Sheet>/<Part>#n` and `loose/<Part>#n`, in their filament colours.
  `measure/kit/print.json` records the STEP's hash, the tree it was laid
  out for, each Sheet's copies, the loose copies and the leaf names.
- Before Make acceptance the host (`workshop.make.kit_print`) checks, on
  the sealed bytes, that the record is for the sealed tree and names the
  sealed STEP; that its Sheets and loose copies are exactly what the tree
  gives; and that the STEP's leaves are exactly those names, so no Bought
  Part body is in it, each holds a solid, and copies of one Part match in
  volume and area. A kit with Sheets must have a layout. A kit without
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
