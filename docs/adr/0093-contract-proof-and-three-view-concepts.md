# ADR 0093: A Contract Proof checks the contract, and concepts are drawn from three sides

- Status: Accepted by the owner on 2026-10-26. The host half is implemented
  and deterministically tested: decision 6 (no row limits at seal, in
  `verify_project` or in the finalizer; requirement ids run to `R999`),
  decision 7 (Design Contract schema 8: every geometry names its prose
  `###` sections, sealed as `prose`, which a component round writes into
  its worker's `summary.json` `contract` and never into the review packet)
  and decision 5's host check (schema 8 refuses a geometry no Guide Image
  names). Schema 8 is schema 7 with the Assembly Tree optional, so kits and
  other toys share it. Decisions 1 to 4 and decision 5's three-view drawing
  belong to `design-a-toy` and `brainstorm-concepts` and are not built here.
  Nothing is validated by a live run yet.
- Date: 2026-10-26
- Amends: `design-a-toy` Stage 3's rule that no image is built from the
  contract's numbers; ADR 0072 (row limits); ADR 0080 (what a Component
  Worker receives); ADR 0089 (Guide Images become required for every
  Component)
- Relates to: ADR 0083 (Reference Camera), ADR 0084 (Reference Conflicts),
  ADR 0091 (Print Sheets), ADR 0092 (kits)

## Context

A Design Contract and its Reference Images drift apart in two directions.

1. **The contract says less than the image.** Night Charms Hall r00 and
   the NCH cabinet pilot (`toys-spec/nch-cabinet-pilot/` on the kit pilot
   branch) show where the detail is lost:
   - A Unique Geometry may carry at most 4 requirement rows
     (`src/workshop/wish/design_contract.py`), and a kit Component of 13
     Parts packs its inkwells, jar, feather fan and books into one row.
   - The detail lives in the prose, which no one in Make reads. The
     Component Worker is told "Do not read the Design Contract; those rows
     are your whole contract", views its reference image once, and decides
     whatever the rows leave open. The reviewer sees rows and Interface
     text only (ADR 0084).
   - Stage 3b checks that each contract number appears in the image, never
     that each thing the image shows has a number. Drawing the pilot
     contract's numbers into exact images needed 17 guesses, the feather
     fan almost entirely guessed.
2. **The image shows more than the contract or the printer allows.**
   - AI images do not hold millimetres. In the pilot, ref-02 drew the door
     about 2 mm too tall and ref-01 drew the inkwells about 20% too tall;
     flat lays plateaued at 4-7 major errors over eight rounds.
   - Stage 3c checks each feature against the print minimums, but never
     asks whether a prop still reads as itself at those minimums (a 1.2 mm
     feather prints, as a flat stick). It resolves every problem without the
     owner, who sees one line of text at Stage 4 beside an image that still
     shows the fine detail. Hall's props were simplified this way and looked
     coarse beside the concept.
   - Its order (bigger toy, bigger detail, stance, reshape, leave out) never
     offers paper, although ADR 0091 exists.
   - Some contradictions are in the numbers alone. Hall's cabinet door
     (19.5 x 25.3) could not cover its face (21.6 x 30.8). No image showed
     it, because the stair hid the door.

The owner approves images and never reads the contract, so its words were
never reviewed against what they describe.

## Decision

1. **Contract Proof.** Before Stage 4, a fresh subagent that has seen no
   image or note reads only `CONTRACT.md` and models every Part in CAD at
   its true size. The Proof:
   - lists every number it had to choose; the list must reach zero, each
     guess becoming a contract number, or the word "free" where the choice
     truly does not matter; only a choice that changes what can be seen or
     how a mechanism or motion works counts as a guess (owner, 2026-10-27),
     and any other choice is the Proof's to make freely;
   - is rendered at each reference's camera beside the AI image, with a 50%
     overlay, and every difference is resolved as Stage 3b resolves a
     disagreement (an image that looks better amends the contract;
     otherwise the image is edited);
   - shows contradictions inside the numbers;
   - runs Make's own print gates (`check_thickness`, `check_overhang`)
     instead of Stage 3c measuring scaled AI images;
   - is rendered per Part from several sides, and those renders are sealed
     as that Component's Guide Images.
   Stage 3's "never build an image by hand" stays true of Reference
   Images: a Proof is never a Reference Image, and nothing compares it with
   the model.
2. **The owner approves the Proof.** Stage 4 shows each AI reference beside
   its Proof, so the owner approves what will print, not only the concept.
3. **A difference the image keeps.** When an image still disagrees with the
   contract after the edit cap and the contract is right, the image stays
   and the Part's row names the difference ("the reference draws the door
   taller; 24.5 holds"). The reviewer then lists it as a Reference Conflict
   from the first round.
4. **Printability is the owner's choice, proposed by the agent, while the
   chosen Concept Image is still being edited.** For each fine detail at
   risk, the agent judges it against the print minimums and shows true-size
   renders of two or three ways (solid at the minimum, on a Print Sheet,
   enlarged, left out) with its recommendation. Nothing is resolved without
   the owner. Stage 3c's order puts paper before enlarging.
5. **Three sides.** The chosen Concept Image is drawn from three cameras
   the agent picks for the most information, and each Component's image is
   a three-view sheet: one view is its Reference Image, the other two its
   Guide Images. Views that disagree with each other are disagreements;
   the Proof is overlaid on all three. The Component Reviewer still compares
   one view.
6. **No row limits.** The 16 assembly rows and 4 rows per Unique Geometry
   go. A kit writes one row per Part for what can be seen.
7. **The worker reads its prose.** The contract's prose is split into one
   section per Component or Part, and the host delivers a Component's
   sections to its worker with its rows. Rows still win; the reviewer still
   judges by rows and the reference. This needs a new contract schema;
   older contracts and frozen runs keep what they sealed.

## Considered options

- **The Proof's CAD source as Make's starting skeleton.** It would spare
  Make translating the same words into CAD a second time, but moves
  modelling out of the run and hands Make code that has passed no print
  gate and uses no print-details library. Deferred until one pilot run
  under this ADR measures component rounds and how close the Proof came to
  the final model.
- **Dropping the contract and building from images.** Rejected: images
  carry no scale, hidden joints, motion, kit tree or print pieces, which
  Make met to 0.1 mm from the numbers in Hall r00.
- **The reviewer comparing all three views.** Rejected for now: nearly
  three times the review cost and a change to ADR 0083's camera mechanics,
  while rows and Proof Guide Images already fix the worker's guessing.

## Consequences

- `design-a-toy` gains the Proof and the three-view step and loses its
  "never build by hand" rationale for checks; `brainstorm-concepts` or Stage
  1 gains the printability choice.
- `design_contract.py` drops both row limits, and the new schema adds prose
  sections the host can address. The component worker's instructions and
  round summary carry those sections. Because the worker builds from them,
  a Component's sections join its contract-rows hash and carry key: an
  owner amendment that changes a section's text unlocks every Component
  whose geometry names it, as a changed row does (owner decision
  2026-10-26).
- Every Component has Guide Images, so ADR 0089's "may" becomes "does".

## Amendment: the toy README carries the assembly prose (2026-11-03, B18)

A toy with Bought Parts or hand assembly (the beaver coaster keeper's pin,
spring and cork discs) shipped a toy README with no way to assemble it: the
README Release writes (`workshop.release.public_example`) is host-written,
and only a powered toy's Electrical assembly text (ADR 0095, 2026-11-01)
had a path into it. Owner decision 2026-11-03:

- When the sealed contract's `prose` holds a section headed exactly
  `Bought Parts and assembly`, the toy README gains a
  `## Bought Parts and assembly` section with that text verbatim, before
  any Electrical assembly section. It is copied, never rewritten: no model
  text reaches it.
- The host composes it from sealed bytes: the contract in `WISH.json`,
  checked against the run's Wish hash, with every owner amendment the host
  recorded applied (only an owner amends prose; an in-run Contract
  Amendment cannot). A projection that cannot read it fails closed like any
  other projection error and leaves the sealed Release unchanged.
- A contract without that section, a contract before schema 8, and a run
  without a Design Contract get the README they did before. The section
  reaches the sealed `prose` only when a geometry names it in
  `prose_sections`, as every section the worker reads does.
- `workshop publish` re-projects the toy directory, so an existing
  unreleased build gains the section at publish without another build.

## Amendment: the design notes carry the print material and assembly (2026-11-04, B23, B24)

The Beaver Coaster Keeper's page says PLA, but its contract prints in PETG, and
the page shows no assembly steps. Factory owns both: `print_specs.materials`
is the default of its own slicing, and the page a buyer reads is Factory's
landing page, drafted from what it is sent. Workshop never sent the material
or the steps in `project.json`, the design notes the drafter reads in full.

- A new Spark page may seal an optional `design_notes` object, which the
  Factory adapter copies into `project.json`. Its `print_settings` is the
  sentences of a prose section whose heading starts with `Print` that name
  PLA, PETG, ABS, ASA or TPU, with line wraps closed up. Its `assembly` is
  the `Bought Parts and assembly` text. Nothing else is rewritten, and
  owner amendments apply as in the 2026-11-03 amendment.
- A contract states its material only in prose, so a contract with no such
  sentence sends no `print_settings`; no default is assumed.
- The notes live in the sealed page, so a Release already sealed keeps its
  exact bytes, and its Factory intent stays valid. A page without notes is
  unchanged.
- This informs Factory's drafter; it does not set a field. Whether a page shows
  the material or steps stays Factory's, and no Workshop gate claims it.
