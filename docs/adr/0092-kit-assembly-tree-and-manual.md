# ADR 0092: An Assembly Tree splits a toy into kit Parts and writes its Manual

- Status: Accepted (owner, 2026-10-23). Implementation steps 2 (issue
  #135), 3 (issue #136) and 4 (issue #137) are implemented: schema 7 parses
  and lints, the catalogues ship seeded and unconfirmed, design-a-toy
  drafts the tree, Make's tree gates (decision 8), the pilot's stop on a
  contract tree defect (decision 10, split from labelling slips by the
  owner on 2026-10-23) and the not-printed colour and list of Bought Parts
  (decision 5, owner, 2026-10-23) exist, and final verification writes the
  Manual (decision 9), which the host checks and Release ships. `workshop
  wish|fix` now seal schema 7 contracts. The gates are tested on
  deterministic fakes; the Manual also on a small real build123d project.
  No live run has exercised any of them yet (steps 5-7).
  Owner decisions of 2026-10-26 after the cabinet pilot's design (Q31,
  Q33-Q37) amend decisions 1, 3, 4, 6, 7 and 8: design approval drops the
  AI-drawn exploded views, and furniture, boxes, shell and frames are flat
  Panels joined by tab and slot. Schema 7 states and lints each printed
  Part's form and panel thickness; no Make gate measures a built panel's
  thickness yet.
  Owner decision of 2026-10-28 after the cabinet pilot's first Make run
  adds decision 11: each printed Part is print-gated alone, in its print
  stance, from the Component's `print_parts()`. It is implemented in
  `make_round` and final verification and tested on deterministic fakes and
  a small real build123d cabinet.
- Date: 2026-10-23
- Amends: ADR 0091 (what a Print Piece lands on; its id form), ADR 0082
  (Components are subtrees of the Assembly Tree), ADR 0088 (insertion paths
  come from the tree), ADR 0061 (Make, not Release, authors the Manual PDF
  that Spark Release packages), design-a-toy's "one colour per Component"
- Relates to: ADR 0089 (Guide Images), `docs/research/book-nook-kits/`
  (especially `rolife-assembly-trees.md`),
  `docs/handoff/2026-10-23-kit-manual-and-part-split.md`

## Context

Night Charms Hall's first build (r00) came out as 14 Components, each one
printed object in one filament colour. Its contract called the desks and
portrait "one multi-colour print", so the black hat, crystal ball, brass
stand and books were merged into the oak desk. Its cabinet door did not fit
its face. Its `## Assembly and wiring` section was four prose paragraphs, not
a manual a buyer could follow.

The owner is moving book nooks toward Robotime's Rolife assembly-kit style,
still 3D printed. Print Sheets (ADR 0091) settle how colour and detail travel
on paper. Two linked problems were still open:

- how a concept is split into the pieces a buyer assembles;
- the Rolife-style manual those pieces are assembled from.

A split that cannot be explained in a clear manual step is a bad split, so
both are decided together. Six 2026 Rolife manuals were read page by page
(`docs/research/book-nook-kits/rolife-assembly-trees.md`).

## Decision

1. **Terms** (in `CONTEXT.md`):
   - **Part**: one thing the buyer handles. It is a printed body in one
     filament colour, a Print Piece, or a Bought Part.
   - **Assembly Tree**: Parts are its leaves, every inner node is an
     **Assembly Step** producing one **Sub-assembly**, and the finished toy
     is its root.
   - **Check Step**: a light test that is connected and then taken apart.
     It stands outside the tree.
   - **Manual Page**: one page presenting steps. One step may span pages,
     and one page may hold several steps.
   - **Manual**: the Rolife-style assembly book written from the tree.
   - **Panel** (owner decision 2026-10-26, Q33): a flat printed Part of the
     toy's one standard thickness, joined to other Panels by tab and slot.

2. **What the tree holds.**
   - An Assembly Step may have one input (fold, cut to a gauge, bend, roll)
     and may be made N times.
   - Joining LED leads is an Assembly Step. It sits at or above the smallest
     Sub-assembly holding every lamp it joins.
   - A step that encloses a lead declares where the lead comes out.
   - Applying a Print Piece is an Assembly Step. It may come anywhere after
     the piece's host exists, including after the host has been joined.
   - Tools, tape and jigs appear only in material lists.
   - Rolife does all of these (TGB18, TGE05 wiring splices; TGE05 light
     test; DH201 "Part A–I").

3. **Components are chosen subtrees.**
   - A Component is one contiguous subtree, chosen by the Design Contract
     as the unit with its own reference image, worker and review.
   - Every Part belongs to exactly one Component.
   - Steps above Components are joins between Components, recorded as
     Interfaces as today.
   - The tree serves the Manual and the Components bound review cost.
     Night Charms Hall's teacher's desk stays one Component, now of seven
     Parts in four colours, rather than becoming seven Components.
   - Considered and rejected: one Component per single-colour Part. It
     would roughly double Night Charms Hall's Components and their review
     cost without improving the manual.
   - Flat-pack does not change the cut (owner decision 2026-10-26, Q36). A
     cabinet built from Panels stays one Component, of about six panel
     Parts plus its props, not one Component per Panel.

4. **Colour per Part, from stock.**
   - Each printed Part names one colour from a fixed catalogue of the
     filaments the maker stocks. A colour outside the catalogue needs the
     owner's approval.
   - There is no cap on the number of colours. Printing each Part
     separately removes any per-print slot limit.
   - Concept Image and Reference Image prompts restrict plastic to
     catalogue colours. Paper areas are free.
   - design-a-toy samples each Part's colour on its reference image and
     regenerates the image on a large miss.
   - Component renders colour each Part, and the Component Reviewer may
     list a wrong colour as a difference.
   - **A Panel is one filament colour** (owner decision 2026-10-26, Q37).
     Relief detail, such as a door's arch moulding or a frame, prints on
     the Panel's face; texture and colour go on Print Pieces.

5. **Bought Parts come from a catalogue.**
   - The catalogue lists battery boxes, LEDs, pins, screws, clear jars,
     beads, wire, foam tape and tweezers, each with its size limits, pack
     size and source.
   - A Bought Part outside it needs the owner's approval.
   - Consumables carry spares by pack size. Wire is cut to 1:1 gauges.
     Printed Parts are not printed spare in the pilot.
   - **Bought Parts are visibly not printed** (owner decision Q29,
     2026-10-23).
     - Every Bought Part body in every STEP and render carries one
       reserved colour, pure magenta `#ff00ff`, which no filament may
       take. It is one named constant (`BOUGHT_PART_HEX`) in the
       catalogue validator and in the run-local tree gate, held equal by a
       test.
     - The catalogue validator refuses a filament of that colour, or one
       the colour gate cannot tell from it. The colour gate refuses a
       printed Part in it and a Bought Part without it.
     - Final verification writes `measure/not-printed.json`: every Bought
       Part body of the toy (`<id>#n`, numbered across the toy) with its
       catalogue id. It is read from the tree, so it is deterministic, and
       reconciliation proves the bodies match it. The host checks it
       before Make is accepted, the receipt carries it, Release ships it
       beside the STEP files (`make/models/cad/not-printed.json`), and
       the Manual's front page and bought column say these are bought,
       not printed. Its pictures draw them in neutral grey, as the buyer
       sees them.

6. **The contract declares the tree (schema 7).**
   - Every Part and Assembly Step has an id of a code plus a kebab-case
     mnemonic:
     - printed Parts `A03-hat`, every letter except M, N, P and S, one per
       filament colour (the owner's decision on 2026-10-23; it replaced
       "the letters A–K grouped by filament colour");
     - Bought Parts `P02-steel-pin`;
     - Print Pieces `M01-spine-strip`, with M/N, a change to ADR 0091's id
       form;
     - steps `S07-teacher-desk-items`.
     A Sub-assembly takes its step's id.
   - Each step declares:
     - its inputs and output, and its count;
     - its joint kind: press-fit peg/socket, tab/slot, steel-pin hinge, or
       foam tape (glue is a last resort with a stated reason);
     - for each input, one straight insertion direction;
     - for each enclosed lead, its route;
     - one short English instruction;
     - optionally, an error-prone mark, which earns a correct/incorrect
       picture.
   - A Print Piece's `on` names a printed Part, a Bought Part or a
     Sub-assembly. This amends ADR 0091, where it names a Unique Geometry.
   - **Panel or solid** (owner decisions 2026-10-26, Q33 and Q34).
     - Every printed Part names its `form`: `panel` or `solid`.
     - The tree states the toy's one panel thickness, `panel_mm`, default
       2.0 mm (five 0.4 mm lines), to be tuned after the pilot.
     - A panel is `panel_mm` thick unless it states its own `thickness_mm`
       with a `thickness_reason`; the lint lists every such panel for a
       verdict. A solid takes neither.
     - The parser checks only what the contract states. Matching a built
       body to its panel thickness is Make's.
     - A schema 7 draft written before this decision adds `form` to each
       printed Part before it is sealed; a run already sealed keeps its
       contract.
   - **Tab and slot are press-fit and glue-free** (owner decision
     2026-10-26, Q35). The clearance is one shared printer parameter, not a
     contract field: `TAB_SLOT_CLEARANCE` in the `print-details` library,
     0.15 mm per side. It is an estimate, pending research into Rolife's
     fit, to be replaced by a printed fit coupon (several tab and slot
     pairs at stepped clearances) in the pilot.
   - Schemas 1–6 and frozen runs are unchanged and get no Manual.

7. **design-a-toy owns the split.**
   - It drafts the tree and the Component cut after the concept is chosen
     and before Reference Images, following Rolife's ordering rules:
     - dress furniture outside, then place it;
     - dress walls while open;
     - lay wiring before closing;
     - front and roof last;
     - a light test first.
   - **Flat-pack** (owner decision 2026-10-26, Q33). Furniture, boxes, the
     shell and frames are drafted as separate flat printed Panels joined by
     tab and slot, as Rolife does (TGB19 page 14: a shelf from two slotted
     side panels, L28, with its shelves and bars, L37; page tile
     `docs/research/book-nook-kits/sources/manuals-2026/tiles/TGB19/TGB19-14.png`,
     kept out of git, see that directory's README). Each Panel prints
     flat without support, and its relief prints face-up and crisp. Small
     round or 3D props (inkwells, a ring pull, a feather fan, a crystal
     ball, a hat) print as solid Parts.
   - *Amended by the owner, 2026-10-26 (Q31).* The owner approves the tree
     at design time from the Reference Images and one "in the box" flat lay:
     every Part, its count and colour, with no arrows. There are no
     AI-generated exploded views. Exploded views with arrows come only from
     the deterministic Manual (decision 9), rendered from the built STEP,
     and the owner reviews them in the Manual after the build. Reason: in
     the pilot, eight regenerate-and-review rounds never produced a correct
     exploded view; the models mirrored Parts and misplaced or reversed
     arrows (`toys-spec/nch-cabinet-pilot/PILOT-NOTES.md`, items 13-15).
     This replaces "one exploded view per Component showing its Parts and
     colours".
   - Make may not change the tree.

8. **Deterministic tree gates.**
   - **Three-way reconciliation.** Every STEP body, every Print Piece and
     every catalogued Bought Part the contract cites matches exactly one
     leaf. A missing, extra or duplicated Part fails, and so does a
     duplicated id or mnemonic. design-a-toy checks the Print Sheet and
     catalogue sides at approval. Decision 10 says which failures stop
     the run.
   - **Colour.** Each printed Part is in its filament's colour, and each
     Bought Part in the reserved not-printed colour (decision 5).
   - **Insertion.**
     - Each input is inserted alone. Moving several inputs at once is
       refused.
     - A box of Panels closes the same way (owner decision 2026-10-26,
       Q36): each Panel enters alone, and the last one slides in along
       grooves, so no step needs simultaneous moves.
     - Every joint an input engages is parallel to its declared direction.
     - Each step becomes `assembly_sequence` /
       `linear_motion_collision` conditions (ADR 0088), in Manual order.
     - Each input starts outside the current Sub-assembly's bounds and is
       swept to its seat against only what is already assembled. Overlap
       above 0.001 mm³ fails; seated contact on the step's joint faces is
       allowed.
     - Sampling is no coarser than the thinnest wall.
     - Starting outside means a corridor the size of the input stays open
       behind it. That stands in for hand and tool reach; nothing models a
       hand.
   - **Lead route.** A sphere the lead's diameter plus clearance is swept
     along each declared route.
   - **Where each check runs.**
     - A check wholly inside one Component runs in that Component's round.
     - A check across Components runs in assembly rounds and final
       verification.
     - The same split decides where the `paper` gate checks a Print Piece
       whose host is a Sub-assembly.

9. **Make writes the Manual, deterministically.**
   - It renders the Manual PDF from the contract's tree and the built
     STEP, and seals it with the STEP; Release adds nothing (ADR 0061).
   - Content:
     - a front page of included tools (tweezers, foam tape and dots, a
       screwdriver when there are screws or a battery box, printed jigs)
       and self-prepared ones (scissors, batteries), with warnings, every
       Bought Part under "Bought, not printed" (decision 5, Q29) and
       "check all Parts first";
     - the light Check Step;
     - one section per Component, with its bag and a three-column material
       list (printed / paper / bought, not printed);
     - the join sections above the Components;
     - exploded renders per step, 1:1 gauges, printed-side and peel marks,
       Sub-assembly labels, correct/incorrect pictures where marked, and a
       completion picture;
     - an after-sales contact from company configuration.
   - Text is short English. Every judgement lives in the contract; Make
     writes no prose.
   - As implemented (issue #137): `make-round/scripts/kit_manual.py` runs
     in final verification after the tree gates and Print Sheets and writes
     `manual/manual.pdf` and `manual/manual.json`.
     - The light Check Steps are the tree's `checks` (`{id, text, parts}`,
       lamps and their power); a tree with a lamp tests every lamp in one.
     - A Component's section is every step wholly inside it; a step across
       Components is its own join section; a step holding no Part (a fold
       of a Print Piece) joins the section of the step it feeds. So every
       leaf is in exactly one material list. Bags are numbered by section.
     - The screwdriver is added when a Bought Part is a screw (a fastener
       with a `thread` size) or a power source; scissors when there are
       Print Pieces; batteries for each power source. Printed jigs are not
       in the schema yet, so none is listed.
     - Gauges are drawn 1:1 for every Bought Part with a catalogue
       `length`.
     - Pictures are the build's own bodies, built as the final tree gate
       builds them and shaded by `render_review`'s software rasteriser from
       one fixed camera. An exploded picture backs each moving input out
       along its insertion direction. The incorrect picture of an
       `error_prone` step is the same view with each moving input turned
       half a turn about the axis across its direction; when that changes
       no visible pixel, or nothing moves, a fixed placeholder says so.
     - The after-sales contact and warnings are company configuration,
       `make-round/company.json`; its contact is an owner placeholder until
       the owner confirms it, and the receipt says so.
     - The host checks the report and the PDF hash; a route whose host
       reruns final verification also proves the Manual byte-identical.

10. **Tree defects are watched in the pilot.** Every missing, extra or
    duplicated Part, whether a gate or an image review catches it, stops
    the agent so it can report to the owner instead of repairing the tree
    itself. Each one is logged in the toy's `TREE-ISSUES.md`. After the
    pilot the owner decides which kinds may be repaired automatically.

    *Amended by the owner, 2026-10-23 (Q28).* Two kinds are told apart:
    - A **contract tree defect** is the sealed tree itself failing to
      hold together. Examples: a Print Piece or Bought Part the tree
      cannot account for against the Print Sheet or catalogue side, a
      leaf that is an input of two steps, a Part in no step or no
      Component, or a leads step below its lamps. It is unchanged: it
      stops the run with a need to the owner, is recorded in
      `measure/tree-defects.json` (every later round of that tree
      refuses), is logged in `TREE-ISSUES.md`, and is never repaired in
      the run.
    - A **labelling slip** is a sound tree that the built bodies do not
      match: a body with a wrong or unknown Part label, a missing or
      duplicated body, a Part built in another Component, or a wrong
      colour. It is an ordinary gate failure. The Component Worker
      repairs it in its next round, or the Manager in the next assembly
      round, like any other gate. It records nothing, refuses no later
      round and does not stop the run; final verification and the host
      still refuse a Make with one open. A review that sees a Part
      missing from a model of a sound tree lists it as an ordinary
      difference.

11. **Each printed Part is print-gated alone, in its print stance** (owner
    decision 2026-10-28). Decision 8 said nothing of the print gates, so
    they measured a kit Component as a part: its `gen_step()` compound, in
    the Display Pose it is built in. In the cabinet pilot's first Make run
    (`wish-20261028-051153-3f1061cd`, schema 8, an `assembly_tree`), the
    flat top board B04 and shelf B05 failed `check_overhang` as inner
    ceilings, 366 and 253 mm2 over air, and a 0.80 mm web read 0.66 mm in
    `check_thickness` on the larger model's coarser grid. Each kit Part
    prints alone, on its own.
    - A kit Component's file also defines `print_parts()`, returning
      `{Part id: shape}`: every printed Part of the Component, once per
      Part id (copies are the same Part), each alone in its print stance,
      bottom at Z 0, centred in X and Y. Bought Parts and Print Pieces are
      not in it. It is the Contract Proof's `print_<Part>` convention.
    - Component rounds, assembly rounds and final verification run
      `check_mesh`, `check_overhang` and `check_thickness` on each of those
      Parts separately (`make-round/scripts/kit_print_parts.py` writes one
      generated entry per Part under `__cadgen__/print-parts/`). The
      Component passes its print gates only when every Part does; each
      failure names its Part and region.
    - A kit Component without `print_parts()`, or whose `print_parts()`
      leaves out a printed Part of its tree or names a Bought Part, a Print
      Piece, a copy, another Component's Part or an unknown Part, fails the
      round with the repair, a free repair like a print gate. Nothing ever
      gates the assembled Component in its place.
    - A round reuses a Part's passing gates only while the Part's B-rep
      identity, the tools and the conditions are unchanged, so a Part
      turned to another stance is gated again even when the assembled
      Component did not move.
    - The tree, Interface, Keep-out Envelope, motion and paper gates and the
      review renders still read the assembled Component.
    - Non-kit Components and frozen runs are gated as before.

## Not decided here

- Whether Night Charms Hall keeps its 14 Components or is cut differently.
- Folding paper boxes (`way: box`, a net from `box_mm`) and Print Pieces that
  are Parts of their own with no host. Rolife uses both (TGB19 U boxes, DH201
  kettle, DG186 K boxes).
- Hand or tool reach beyond the insertion corridor; tool-specific steps.
- Two-sided print, die-cut pieces, and spare printed Parts.
- Rolife's actual tab-slot fit. `TAB_SLOT_CLEARANCE` (0.15 mm per side) is an
  estimate until the pilot's fit coupon (Q35).
- A Make gate that measures each built panel against its stated thickness,
  and whether `panel_mm` moves from 2.0 after the pilot (Q34).

## Consequences

- Colour stops being "not gated". A Component's renders carry Part colours,
  so a multi-coloured object no longer has to merge into one colour or move
  wholly to paper.
- A forgotten Part that is absent from every source (tree, STEP, sheets,
  catalogue) passes the gates. Only the "in the box" image, the Component
  Reviewer and the owner's review of the Manual's exploded views after the
  build catch it (Q31). Decision 10 measures how often
  this happens.
- Since Q28, `TREE-ISSUES.md` logs only contract tree defects. Labelling
  slips appear in round summaries like any failing gate, so the pilot no
  longer counts how often workers mislabel bodies as a tree issue.
- Since Q29, every render and STEP shows Bought Parts in magenta rather
  than their real look. A Component Reviewer compares them by form, not
  colour, and the not-printed list travels with every STEP.
- Insertion checks run per step, not only per Coupled Interface, so assembly
  rounds sweep more conditions.
- Two catalogues, filaments and Bought Parts, become owned data the owner
  maintains.

## Implementation order

1. This ADR, accepted.
2. design-a-toy and `CONTRACT-FORMAT.md`: schema 7, the tree, ids, the
   catalogues, palette-limited image prompts, in-the-box approval image
   (exploded-view approval images were dropped by Q31).
3. The tree gates: reconciliation, insertion, lead route.
4. The Manual generator.
5. Pilot: Night Charms Hall's cabinet. One Component of several Parts, with
   a spine-strip Print Piece, a bought jar and inkwells, and the steel-pin
   hinge. Build it, generate its Manual section and review it.
6. The deferred items above that the pilot shows are needed: folding boxes,
   hostless Print Pieces, and any reach or spare-part rules.
7. All of Night Charms Hall, including whether to re-cut its Components.

Each step is its own GitHub issue.
