# ADR 0104: A printed kit ships its sheets, its Bought Parts and its approved Manual

- **Status:** Proposed (builder, 2026-11-14), for the Amsterdam kit pilot.
  Each decision below says what is implemented on main and what no live run
  has exercised yet; this header is updated as each step lands.
  - Decisions 1-5: not implemented yet.
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
   (`manual/AMSTERDAM-KIT-MANUAL-standalone.pdf`).

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
- **Why not a Sheet Part and a "cut from sheet" step in the tree.** That was
  the first proposal. ADR 0092's tree holds each Part as one leaf and makes
  every step produce one Sub-assembly; a cut step would turn one leaf into
  many, which the counting, reconciliation, insertion and Manual code all
  assume cannot happen, and a Sheet has no body in `assembled.step` to
  reconcile. A Sheet is a print form of Parts, like `print_parts()` (ADR
  0092 decision 11), so it sits beside the tree, as Check Steps do. The
  Manual's "cut from the sheet" instruction is read from it.
- **Geometry.** Each Sheet is a CAD file `sheet_<id>.step.py` in the
  project (so in an Approved Proof's manifest) defining `sheet()`, which
  returns `{"frame": shape, "parts": [{"id", "shape"}], "gates": [{"part",
  "x", "y", "d"}]}`: the frame with runners, tags and gate bars fused; every
  Part copy in its print stance at its place on the plate; and each gate's
  cut point on the Part outline with `d` = +1 (runner below) or -1 (runner
  above). The project's `sheets.py` packs and gates the Amsterdam sheets
  this way already; only its return shape is new.

### 2. A kit's Bought Parts are sealed and billed

- The `bought-parts` block (ADR 0095 amendment) is allowed in a schema 10 or
  later kit. Its parser holds it to the tree: every catalogue entry a tree
  leaf names, unless the electrical section counts it, is listed with at
  least the tree's count (more are spares); any other entry is a tool or
  consumable the tree's `materials` lists, such as the nippers and glue the
  box includes. Self-prepared materials are left out of the block.
- `sealed_bought_lines` bills the block as before. A kit whose tree holds
  Bought Parts but whose Wish sealed no block now bills them unpriced, by
  the tree's count, so `factory_extra_materials` refuses the publication
  instead of leaving their cost out. This is a stricter Release; it relaxes
  nothing.
- The catalogue adds `nipper-mini` (tool, 150 US cents, the owner's own
  estimate on the kit proposal page, unconfirmed).
- The block stays out of the Proof's seed hash, so the owner can price a
  sealed kit without re-sealing its Proof.

### 3. Sheet checks are deterministic print gates in `make_round`

A new gate, `check_sheet`, runs on each Sheet in assembly rounds and final
verification (a Sheet spans Components). It ports the project's
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

The ordinary print gates (`check_mesh`, `check_overhang`,
`check_thickness`) still gate each Part alone; `check_sheet` adds to them.
Its rows enter `verification-pipeline.md` like every gate, so a failing row
blocks Spark Make's finalizer, and the Proof's `--print-gates-only` runs it
too.

### 4. A kit's Factory primary is its print layout

- Final verification seals `measure/kit/print.step`: every Sheet as built
  and every loose Part copy in its print stance, laid apart; no Bought Part.
  `measure/kit/print.json` records its hash and, per printed Part, the
  copies it holds. The host checks before Make acceptance that the counts
  cover the tree (plus spares), that no body is magenta or `bought_`, and
  that the hashes match.
- The Factory adapter ships that file as the primary, so Factory weighs
  the filament the maker prints, frames included. The not-printed check of
  `_assert_printed_bodies_only` reads the kit file's real `bodies` key and
  applies when the scene itself would cross; the magenta and `bought_`
  scans still run on whatever crosses.

### 5. An owner-approved Manual is sealed with the Proof and shipped

- `seal_proof.py` takes the owner-approved Manual PDF and seals APPROVAL
  schema 5 with `kit_manual: {file, sha256}` (`approved/kit-manual.pdf`).
- Make still plans the Manual from the tree (`manual.json`, all of its
  coverage checks), but when the seed seals a Manual, `kit_manual.py` writes
  those exact bytes as `manual/manual.pdf` and records `source:
  "owner-approved"`. `verify_made_manual` binds the PDF to the sealed hash
  instead of the generated one.
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
3. Decision 1 (contract) and 3 (`check_sheet`).
4. Decision 4.
5. Decision 5.
6. The pilot: the Amsterdam kit's contract and Proof, seal, and
   `build-a-toy --agent claude`; every failure is fixed the same way.
