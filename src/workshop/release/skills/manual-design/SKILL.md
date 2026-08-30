---
name: manual-design
description: Design and verify the self-contained printable MANUAL.pdf intended for the physical toy's box. Use during Workshop Release; not for manufacturing notes, evidence reports, or product-page copy.
---

# Manual design

Create the customer artifact that makes the toy understandable and delightful
at unboxing. The finished `MANUAL.pdf` must teach the complete supported use or
play experience without a website, phone, QR code, or prior explanation.

## Design from the exact product

- Inspect the Wish, selected Taste, sealed product facts, exact geometry,
  component inventory, and passing Playtest findings before designing.
- Before laying out pages, commit to a short creative brief: the emotional
  promise, physical format and rationale, product-specific visual motif,
  palette, typography, and teaching arc. Use it to make the manual feel like
  part of this toy rather than documentation wrapped around it.
- Read [references/product-manual-visual-system.md](references/product-manual-visual-system.md)
  before layout. It captures the reusable visual grammar observed in the
  Workshop's strongest manuals and the report-like failure modes to reject.
- Depict only included parts and supported interactions. Prefer renders,
  silhouettes, exploded views, and diagrams derived from the exact product
  artifacts; do not invent geometry or imply unverified physical performance.
- Put an exact product-derived visual on the cover. A title over empty space,
  ASCII art, or an unstyled technical-report/manpage fallback is not an
  acceptable substitute for art direction.
- Choose the physical format to suit the toy and box: a card, foldout, leaflet,
  or booklet may each be right. Decide page size, orientation, page count,
  binding, margins, and bleed deliberately instead of defaulting every toy to
  one template.
- Use the smallest complete physical format and never add pages merely to make
  the guide feel substantial. A simple one-piece toy will often fit a
  double-sided card or two to four small pages; games, assemblies, or products
  with real rule complexity may earn a longer booklet. Treat these as design
  heuristics, not fixed page-count gates.
- Choose an authoring method that gives the concept the strongest print result.
  HTML/CSS-to-PDF, vector-native layout, and programmatic drawing are all valid.
  Do not force a generic visual template across products.

## Teach the whole experience

Use the structure and voice that best fit the product, but make these needs easy
to find:

- an exact visual inventory with quantities and ownership or orientation cues;
- assembly or setup expressed as short physical actions;
- complete first-use, operation, and reset guidance;
- for games, a guided first play plus complete turns, choices, rules, scoring,
  and end conditions;
- likely mistakes, ambiguous cases, and concise troubleshooting;
- pack-away, care, and evidence-supported safety guidance.

Keep production material out of customer copy: no slicer settings, tolerances,
calibration, CAD implementation, evidence plumbing, provenance logs,
verification mechanics, or publication workflow. Those belong in technical
artifacts. A phone or QR code may offer optional enrichment, but never carry an
essential step or rule.

## Make print carry the meaning

- Establish a clear reading path, strong hierarchy, generous usable whitespace,
  and one obvious action or decision per instructional panel where practical.
- Let the Wish, product character, and selected Taste shape the visual language.
  Use original composition rather than imitating a branded manual.
- Never encode essential state by color alone. Repeat it with names, shapes,
  symbols, counts, patterns, or position so the guide remains complete in
  grayscale and for readers with color-vision differences.
- Keep type and diagrams legible at the chosen physical size. Preserve actual
  text rather than outlining it when the authoring method permits.
- Embed every font and asset needed to render the PDF. The final file must not
  depend on local paths, remote images, active scripts, or external resources.
- When using ReportLab's bundled fonts, resolve them from the installed module,
  for example `Path(reportlab.__file__).resolve().parent / "fonts"`; never
  hardcode a user-specific or version-specific `site-packages` path in the
  editable manual source.
- Treat a missing creative dependency as a design problem to solve with
  available vector drawing, CAD renders, or bundled fonts. Do not silently
  fall back to stock Times, an operating-system fallback font, or a generic
  word-processor layout.

## Inspect the artifact, not just its source

Render the complete PDF review packet in one command:

```bash
.agents/skills/manual-design/scripts/review_manual MANUAL.pdf \
  --output-dir <new-review-directory>
```

It writes every page in color and grayscale, two contact sheets, and compact
hash-bound JSON. It is deterministic review plumbing, not an aesthetic judge.
Inspect both contact sheets first, then open individual pages only for a
specific suspected defect. Use a new directory for each revision so stale
pages cannot masquerade as current evidence. Check page order, cropping, bleed
and safe margins, text size, contrast, alignment, diagram accuracy, visual
consistency, and any accidental blank, clipped, or overlapping content. Do not
add a network service or a license-incompatible runtime dependency merely to
render it.

Use Make's `snap/signature.png` as the minimum visual test of the product
promise: the manual must teach the signature experience with exact product
imagery, and a reader should still understand the reveal or interaction when
the headline is hidden. Do not let Release copy assert magic that Make's exact
views fail to show.

Read the guide once as a first-time owner and once as an operation or rules
reference, as applicable. Revise the source and repeat both visual inspections
until the result is clear, complete, accurate, and excellent. Save the final
self-contained customer file as `MANUAL.pdf`; editable sources may accompany it
but do not replace it.

After the first complete render, ask one bounded independent native
visual-editor subagent to inspect the exact color and grayscale contact sheets
plus only the brief and sealed product facts needed for accuracy. Do not give it
the whole workspace or ask it to redesign the manual. Resolve at least one
concrete finding, rerun the one review command, and perform the first-time-owner
pass again. The root Manager owns the final decision.

When `STAGE.json` names `MANUAL-DESIGN.json` as required Release evidence, read
`.agents/skills/autonomous-workshop/references/manual-design-evidence-v1.md` and
write that canonical file beside `MANUAL.pdf`. Bind the exact final PDF hash,
the creative brief, exact Made visual sources, every reviewed color and
grayscale page, the independent finding, and the resolved revision. This is a
workflow proof, not a beauty score; never claim a review that did not occur.
