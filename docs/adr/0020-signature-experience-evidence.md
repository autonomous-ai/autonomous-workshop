# ADR 0020: Require signature-experience evidence and batch manual review

- Status: Accepted
- Date: 2026-08-30
- Owners: Make, Release, product-run instruction, and public archive maintainers
- Relates to: ADR 0012 (native runtime), ADR 0013 (manual-first Release), ADR 0019 (Spark economics)

## Context

The first low-reasoning production Spark challenger, Starling Gate, reduced
gross input from Moonchase Fox's 24,616,026 to 7,144,631 and reasoning output
from 31,839 to 2,884. It passed every deterministic CAD and publication gate,
but its exact product imagery read as a generic arch with cutouts rather than
the promised bird-to-shooting-star transformation. Release then spent
3,897,515 input tokens—more than Make—producing and reviewing a clean manual
whose copy asserted a signature experience that its images did not prove.

The run exposed three gaps. Inventor selection favored fabrication convenience
over ownership of the hardest creative problem. Make required a hero render but
not visual evidence of the interaction or reveal. Release rendered and opened
pages through repeated tool cycles instead of producing one compact review
packet.

## Decision

The first active creative Goal names the Wish's hardest-to-fake magic before
ranking Inventors. It selects the Inventor whose Taste and method own that
perceptual, motion, rules, transformation, or emotional problem. Shared domain
skills handle fabrication constraints after creative ownership is established.

Newly materialized Make finalizers require two exact verified-product PNGs:

- `snap/iso.png`, the chromatic hero at least 800 by 800 pixels;
- `snap/signature.png`, a chromatic sheet at least 1200 by 800 pixels containing
  two to five exact STL poses or views that make the signature interaction,
  reveal, or anti-generic detail legible without a title.

The deterministic CAD renderer can generate both images from one mesh load and
one command. The host checks only exact paths, file identity, format,
dimensions, color mode, and useful tonal variation. It does not score beauty or
interpret the experience. Native Codex inspects the sheet and repairs geometry
when it does not communicate the promise. Both files are sealed in Made and
preserved by the public toy archive.

Release gains a deterministic `review_manual` tool that renders every PDF page
in color and grayscale, creates two contact sheets, and emits compact
hash-bound JSON in one process. The root Manager inspects the sheets first and
opens an individual page only for a specific defect. One bounded independent
visual editor receives the sheets and minimal sealed facts, not the whole
workspace. The tool does not judge, score, lay out, or revise the manual.

## Alternatives considered

### Raise Spark reasoning effort again

Rejected. More reasoning did not structurally require proof of the signature
experience and produced the 24.6M-token baseline.

### Add a Python aesthetic or semantic judge

Rejected. A model or heuristic beauty score would move cognitive orchestration
into the trusted host. Exact files remain host-verifiable; creative judgment
remains native-agent work.

### Let Release invent a stronger visual story

Rejected. Release may teach the product but cannot compensate for geometry that
does not embody the Wish.

## Consequences

Make carries one additional sealed PNG and a small deterministic inspection
obligation. In exchange, the cheapest stage that can still repair geometry must
prove the product's central experience before Release. Manual review becomes
fewer, richer tool cycles while retaining full color, grayscale, and independent
inspection.

## Compatibility and migration

The finalizer is materialized into each private run. New runs receive the
two-render contract; frozen older runs retain their existing one-render
protocol when resumed. Public archives already preserve every Made `snap/`
file, so no archive schema migration is required.

## Verification

- Renderer self-check proves one command writes valid hero and signature PNGs.
- Finalizer tests reject missing, linked, malformed, grayscale, flat, or
  undersized required images.
- Manual review tests prove complete color/grayscale page and contact-sheet
  output bound to the exact PDF hash.
- Packaging tests prove the executable review tool ships with the skill.
- The next production challenger must pass the new contract and beat Starling
  Gate on signature-experience legibility while continuing toward the
  2,461,602 gross-input target.
