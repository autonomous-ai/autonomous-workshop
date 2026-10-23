# Handoff: kit assembly manual and splitting a concept into kit parts

Written 2026-10-23. This is a **brainstorm** handoff, not an implementation
task. The owner wants to think through two linked problems with an agent in a
fresh session before anything is built.

The owner writes in Vietnamese. Reply in Vietnamese and keep it short. They
judge toys by images, never by contract rows. Ground every claim in a source
you actually opened: the owner caught invented web sources once already.

## Update (2026-10-23, later): Print Sheets are on main

**Read this first.** Since this handoff was written, the Print Sheets
feature has been built and merged into `main` (PR #134, which lands #128 to
#133). The decisions in "Already decided" below are now code. The design is
in `docs/adr/0091-print-sheets-carry-colour-and-detail-on-paper.md`; the
terms Print Sheet and Print Piece are in `CONTEXT.md`. It has passed its
tests but has not yet been validated by a live run.

### What Workshop now does

| Where | What |
|---|---|
| Design Contract schema 6 | A `print` section declares `stocks` (paper, sticker, card, film, each with a caliper), sealed `art[]` (`print-NN-<slug>`, CC0 stock only, source recorded) and `pieces[]`. Each piece has `id`, `art`, `stock`, `way` (flat, sticker, wrap, sphere, fold or stand), `on` (a Unique Geometry or `<id>#<n>`), `where`, its sizes in mm and an optional `count`. `workshop wish/fix --print-art` seals the art. Guide Images are optional from schema 6. |
| Layout | `print-details/scripts/print_sheets.py` lays the pieces out on A4 sheets, one stock per page, numbered `<stock>-<n>`. It writes a print-at-100 % PDF with cut and fold lines, piece ids and a scale bar, plus a PNG per sheet. It is deterministic. |
| design-a-toy | Stage 1 decides colour per part and what goes on paper. A new "Print Sheets" section covers which way to use, CC0 art and the proof made with the same tool. Stage 4 shows the art and the sheets. |
| Parts | Component Workers place each piece with `pd.print_recess`, `print_slot`, `print_block`, `print_sphere` and `print_fold`. These read the sizes from the installed contract (`print/pieces.json`). A recess is 0.6 mm deep and 0.2 mm larger than its piece; a card slot is the caliper plus 0.3 mm wide. |
| Gates | `make_round` runs a `paper` gate on every part that hosts a piece. Final verification runs it again and lays out the sheets into `print/sheets/`. Before accepting Make, the host checks the install, the art hashes and the layout on the sealed bytes. |
| Review | Each part's renders draw the art where the buyer applies it, including in the Display Pose. The reviewer judges a printed area's place, size and outline, never its drawing. Assembly renders show no art. |
| Release | The toy archive ships `make/print/` beside the STEP files: `pieces.json`, `art/`, `sheets/print-sheets.pdf` and one PNG per sheet. |

### What it means for this brainstorm

- **Every printed piece names the part it lands on** (`on`) and the feature
  that receives it. So a part split has to say which part carries each
  recess, slot, block or ball, and a manual step that applies a piece can
  name both the piece id and the part.
- **Ids already exist for the manual.** Sheets are `<stock>-<n>` and pieces
  have contract ids. A Rolife-style manual can cite them; there is no
  part-ID scheme for printed plastic parts yet.
- **Still not modelled (all still open here):**
  - a filament colour per part;
  - sub-assemblies, bags and bought parts (wire, beads, LEDs, film sold
    pre-cut);
  - two-sided print, folding boxes and die-cut pieces;
  - any assembly manual. Spark Release still makes no new PDF.
- **Night Charms Hall waits.** Its rework as the first schema 6 toy waits
  until this brainstorm ends, so the part split and the Print Sheets are
  designed together.

## The two problems

The owner is moving book nooks (and later other toys) toward the assembly-kit
style of Robotime's Rolife line, while staying 3D printed. Two problems are
open, and the owner thinks they have to be solved **together**:

1. **Splitting a concept into kit parts.** Going from an approved concept
   image to the set of separate pieces a buyer assembles:
   - which pieces are printed, and in which single filament colour;
   - which become Print Pieces;
   - which are bought parts (wire, beads, LEDs, clear jars);
   - how the pieces join, in what order, and in which bag.
2. **The assembly manual.** A Rolife-style instruction book the buyer follows
   to put those pieces together.

They are linked because the manual's steps, bags and material lists come
straight out of the part split, and a split that cannot be explained in a
clear manual step is a bad split.

## Why this came up

Night Charms Hall is the Halloween book nook in `toys-spec/halloween-book-nook/`.
Its first build (round r00, STEP files in `build-a-toy/r00/step-final/`)
came out as 14 Components:

- case, front-arch, window-wall, gallery-rail, stair;
- cabinet, cabinet-door, portrait, notice-board;
- teacher-desk, student-desk ×6, torch ×2, flame ×2, cover.

The owner compared it with the concept and found three problems:

| Problem | Cause |
|---|---|
| Colours were wrong | Each Component prints in one filament colour, so any multi-coloured object had been merged into one single-colour part. |
| Small props were very coarse: portrait, notice board, wand, feather, books, cabinet contents | The contract had simplified them so they could print. |
| The cabinet door did not fit the cabinet | 19.5 × 25.3 door against a 21.6 × 30.8 face, sized to fit between the hinge lugs. |

Today's split is "one Unique Geometry per visible object, printed in one
piece". The contract's `## Assembly and wiring` section is four prose
paragraphs, which is not a manual.

## Already decided (do not re-open without the owner)

**Print Sheets** is a separate feature being designed in parallel. Its decisions are recorded in
`CONTEXT.md` (**Print Sheet**, **Print Piece**) and are summarised here:

- **Who prints.** The company prints A4 sheets, one side only, and ships them
  in the box. The buyer cuts them with scissors, folds them and applies them.
- **Stocks.** Four: thin paper, sticker, card, and printable clear film.
- **Piece types.** Six:
  - flat into a recess;
  - sticker;
  - wrapped round a block;
  - sphere gore strip;
  - folded pages;
  - standing card in a slot.
- **Cutting limits.** Straight or round/oval outlines, edges ≥ 5 mm, gaps
  ≥ 3 mm. Small shelf books become one spine strip.
- **Art and dimensions.** design-a-toy authors the art; patterns come only
  from CC0 stock, with the source recorded. The contract's mm sizes are the
  truth, and the STEP must match them within ±0.5 mm.
- **Checks and release.** A gate in Make's `verify_project`, rerun by the
  host at Release. The PDF ships beside the STEP.
- **Status.** Built and on `main`; see the update above. Paper defaults
  are VN print-shop stocks: matte couche 120 gsm (0.10 mm), paper decal
  (0.15 mm), Ivory 300 gsm (0.45 mm), laser OHP film 100 µm (0.10 mm).

Print Sheets settle *how* colour and detail travel on paper. They do not
settle the part split or the manual, which is this handoff.

## Research to start from

`docs/research/book-nook-kits/`:

| File | What it covers |
|---|---|
| `README.md` | The eight carry-over rules |
| `rolife-2026-book-nooks.md` | TGB18 and TGE05, glue-free press-fit nooks |
| `rolife-2026-houses.md` | DH201, DH102, DG186, TGB19, including manual layout |
| `rolife-dh103-pagestory.md` | The owner's reference kit (no public manual) |
| `sources/` | The PDFs and page tiles, kept out of git; run `fetch-sources.sh` if missing |

Rolife conventions that bear directly on both problems:

- **Colour.** Colour comes from the material, never from paint.
- **Part IDs.** An ID is sheet letter + number; letters are grouped by
  material (boards A–K, paper and stickers M/N, bagged P).
- **Bags.** Parts are bagged by build stage.
- **Manual sections.** One section per prop or furniture item, each with a
  three-column material list (rigid parts / paper and stickers / other
  parts).
- **Manual order.** Props first, then shell, lighting, front and roof, with a
  light test at the very start.
- **Symbols.** 1:1 cut and tape gauges, a mark for the printed side, peel
  icons, correct/incorrect marks, lettered sub-assemblies, and a completion
  photo.
- **Joining.** Book nooks press-fit with tabs and foam-tape pads; the houses
  glue every joint.

## Workshop constraints to respect

Read `AGENTS.md`, `CONTEXT.md` and the ADRs it lists before proposing changes.

- **Building blocks.** A **Design Contract** names **Unique Geometries**;
  Make builds each as a **Component** with its own reference image, review
  and print gates. **Interfaces** (ADR 0082, 0084) record how Components
  join. A part split has to land in these concepts or change them
  deliberately.
- **Geometry format.** Workshop writes only STEP (ADR 0062).
- **Release adds nothing.** Spark Release is host-only and creates no new
  PDF or native turn (ADR 0061). A manual is therefore either authored
  before Release (in design-a-toy or Make), or it needs an ADR that changes
  this.
- **Review cost.** Every Component costs a Component Worker, reviews and
  tokens. A kit with hundreds of pieces cannot mean hundreds of reviewed
  Components. Compare Rolife's approach: one sheet of many identical boards
  is one design decision.
- **Guide Images.** These already exist for explaining a design (ADR 0089)
  and may be a seed for manual pages.

## Questions to brainstorm (open, in no order)

**Unit**
- What is the unit of the split? Today it is one Component per visible
  object.
- Should a kit be organised by sub-assembly (desk, cabinet, stair) holding
  many small Components?
- Should there be plates of many small parts, like Rolife boards?

**Who decides**
- Does design-a-toy split the concept with the owner approving, or does Make
  propose it?
- What does the owner review: an exploded view, a parts plate, a bag list?

**Colour**
- How does a filament-colour budget (how many colours, which colour per part)
  enter the contract and get checked?

**Joints**
- Which joint vocabulary does a printed kit use: press-fit tab/slot, pins,
  foam tape, glue?
- How do those joints map onto Interfaces?

**Bought parts**
- Is there a fixed library of bought parts (wire, tube hinge, beads, LEDs,
  battery box)?
- Are they declared in the contract like Print Pieces?

**The manual**
- What is its source of truth?
- Is it generated from the contract and the STEP (exploded renders per step,
  material lists from declared pieces), or written and illustrated by an
  agent?
- Which parts can be deterministic, and which need judgement?

**Checking**
- How is a manual checked?
- Ideas to weigh:
  - every part appears in exactly one step;
  - every step's parts already exist;
  - every Print Piece is used;
  - a step order in which each joint is reachable.

**First target**
- Is Night Charms Hall the pilot, or should something smaller come first?

## Suggested way to run the session

Use the grilling / domain-modeling skills: one round of decisions at a time,
a recommended answer for each, and facts looked up rather than asked. Record
new terms in `CONTEXT.md` as they settle. Offer an ADR only for hard-to-reverse
trade-offs. End with a written plan; do not start implementation in the
brainstorm session.
