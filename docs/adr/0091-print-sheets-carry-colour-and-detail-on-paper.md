# ADR 0091: Print Sheets carry colour and detail on paper

- Status: Proposed; not yet implemented
- Date: 2026-10-23
- Amends: ADR 0089 (what a Design Contract seals; schema 6 keeps schema 5),
  ADR 0062/0063 (what Make delivers beside STEP and what the CAD gate checks),
  ADR 0061 (what Spark Release packages)
- Relates to: ADR 0076/0077 (what the Component Reviewer sees), ADR 0084
  (Reference Conflicts), `docs/research/book-nook-kits/`

## Context

Each Component prints in one filament colour. A toy whose concept is
multi-coloured and finely detailed comes out wrong. Night Charms Hall's first
build (r00) shows how:

- Every multi-coloured object (portrait, notice board, books, cabinet
  contents) was merged into one single-colour part.
- The contract had already simplified those props until they printed, so
  they look coarse next to the concept.

Commercial assembly kits solve this with material, not paint. Robotime's 2026
Rolife manuals were read for this ADR (`docs/research/book-nook-kits/`):

- Pictures, notices, labels, textures and skies are printed paper.
- Books are spine strips, or blocks wrapped in printed covers.
- Open books are accordion-folded paper.
- Glazing is clear film.

The kit ships these sheets; the buyer cuts and applies them.

Workshop has no such artefact. A Design Contract seals Reference Images and
Guide Images, and Make delivers only STEP. Nothing declares a printed piece,
checks that the plastic it lands on fits it, or ships the sheet.

## Decision

1. **Two terms.** A **Print Sheet** is one printed A4 sheet of one stock that
   the maker prints and ships in the box. A **Print Piece** is one cut-out on
   it, applied to one Unique Geometry; the buyer cuts, folds and applies it.
   Both are defined in `CONTEXT.md`.

2. **Schema 6 and stocks.** A schema 6 Design Contract keeps schema 5 and
   adds an optional `print` section. Contracts without it, schema 1 to 5
   contracts and frozen runs are unchanged. Any toy may declare one.

   The section names the stocks it uses, with the caliper each is computed
   at:

   | Stock | Default | Caliper |
   |---|---|---|
   | `paper` | matte couche, 120 gsm | 0.10 mm |
   | `sticker` | paper decal with liner | 0.15 mm |
   | `card` | Ivory (FBB), 300 gsm | 0.45 mm |
   | `film` | laser OHP film, 100 µm | 0.10 mm |

   The defaults come from what Vietnamese print shops stock. They are
   estimates until the maker measures a sample, and the contract records the
   values it used.

3. **Six ways a piece is used.** Each piece names its stock, its art file,
   one way, and its host `<geometry>[#n]` with the feature it lands on:

   | Way | What it is | Size it declares |
   |---|---|---|
   | `flat` | Paper or film laid into a recess | Recess size |
   | `sticker` | Sticker laid into a recess | Recess size |
   | `wrap` | Wrapped round a block (book cover) | Block's three sizes |
   | `sphere` | Joined gore strip round a sphere | Sphere diameter and gore count (≥ 8) |
   | `fold` | Accordion pages on a face (open book) | Page size and page count |
   | `stand` | Card cut-out standing in a slot | Outline size and slot length |

   - **Recesses.** `flat` and `sticker` pieces always sit in a recess about
     0.4 mm deep, sized to the piece.
   - **Sizes.** Every size is in mm, and the contract is the truth.
   - **No free pieces.** A piece with no host is refused.

4. **Art is approved and sealed.** `design-a-toy` authors each piece's art.
   Patterns come from CC0 stock (for example ambientCG or Poly Haven), and
   the contract records each source URL and licence.

   The owner approves two things in the same Stage 4 review as the
   Reference Images:
   - every piece's art;
   - a proof of every sheet.

   Art files seal like Guide Images (ADR 0089, decision 2), as
   `print-NN-<slug>`, bound by sha256. One contract yields one fixed set of
   sheets; there are no per-copy variants.

5. **Cuttable by scissors.** Every piece is checked:

   | Rule | Limit |
   |---|---|
   | Outline | Straight edges, circles or ovals |
   | Shortest edge | ≥ 5 mm |
   | Gap between pieces | ≥ 3 mm |
   | Printing | One side only |

   Small shelf books are declared as one spine strip, never one piece each.
   A `sphere` strip is the only exception: it is one piece with curved
   outlines and points.

6. **A deterministic layout.** A Make skill tool lays every piece out on A4
   pages, one stock per page. A stock may take several pages, numbered
   `<stock>-<n>`.

   - **Derived outlines.** `wrap`, `sphere` and `fold` outlines come from the
     declared sizes, the stock's caliper and a glue overlap.
   - **Marks.** Each page prints cut lines solid and fold lines dashed, with
     each piece's id beside it and a 1:1 scale bar.
   - **Outputs.** The tool writes a PDF and a PNG preview per page.
   - **Same inputs, same bytes.** No agent places pieces.

7. **A print-piece gate.** `verify_project` gains a gate that fails unless:
   - every host feature measured on the B-rep matches the declared size
     within ±0.5 mm (recess, block, sphere, fold face, and slot width =
     caliper + clearance);
   - every piece's art is at least 300 dpi at its printed size;
   - every piece is on a sheet, inside the printable margin, and overlaps
     none;
   - every scissors rule in decision 5 holds.

   The host reruns the same gate at Release on the sealed bytes, exactly as
   it reruns `--print-gates` (ADR 0063). A failure refuses the release.

8. **The reviewer sees the art.** A component round renders a Component that
   hosts pieces with their art applied to the host features, so the
   Component Reviewer compares it with the Reference Image as the buyer will
   see it.

   - **Who wins.** For the content of a printed area, the sealed art wins;
     the Reference Image wins for its placement, size and overall colour.
   - **Not a difference.** A drawing that differs from the reference inside
     a printed area costs no Shape Round, as with a Reference Conflict (ADR
     0084).
   - **Workers.** Component Workers are given the art and sizes of the
     pieces their Component hosts.

9. **Release ships the sheets.** The sheet PDFs travel beside the STEP files
   in the Make output and the Release package, hash-bound like them. Spark
   Release still creates no new PDF (ADR 0061). It packages the sheets Make
   produced and the gate passed.

## Not decided here

- Splitting a concept into kit parts (colour per part, sub-assemblies, bags,
  bought parts) and a Rolife-style assembly manual. The owner wants these
  designed together, later. See
  `docs/handoff/2026-10-23-kit-manual-and-part-split.md`.
- Two-sided printing, printed folding boxes, and pre-cut (die-cut or plotted)
  pieces.

## Consequences

- **Detail moves to paper.** Colour and fine detail that one filament cannot
  carry go onto paper, so Components can stay single-colour and printable
  without looking coarse.
- **Fit is checked twice.** Fit between paper and plastic is checked by Make
  and again by the host, so a mismatch like r00's door-against-face shows up
  as a gate failure, not in the box.
- **Image budget.** Contracts gain sealed art files. A book nook may need
  dozens, which counts against the 99-image / 48 MiB budget; the
  implementation must say whether that budget grows.
- **Render cost.** Applying art in renders adds a texture step to component
  rounds that host pieces.
- **Stock values are estimates.** Changing paper later edits one contract
  value per stock, which re-runs the gate.

## Implementation order

Each step is its own PR with contract and failure-path tests:

1. Schema 6 and sealing the art.
2. `design-a-toy`: authoring the art, the CC0 sources and the sheet proof in
   Stage 4.
3. The layout tool and the `verify_project` gate.
4. Renders with the art applied, and the reviewer and worker packets.
5. The host's Release rerun and packaging.

Night Charms Hall is the first toy to use it.
