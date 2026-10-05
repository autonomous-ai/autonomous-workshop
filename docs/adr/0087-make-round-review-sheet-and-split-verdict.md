# ADR 0087: Make rounds review one sheet and judge plan and reference apart

- Status: Accepted
- Date: 2026-09-28; renumbered from 0082 and amended for ADR 0076, ADR 0081
  and issue #77 on 2026-10-05
- Relates to: ADR 0060 (make-round visual feedback), ADR 0063 (component-first
  Spark Make), ADR 0075 (form differences), ADR 0076 (independent Component
  Review), ADR 0077 (Component Reviewer), ADR 0081 (Shape Rounds) and its
  issue #77 extension (proven reviewer reads)

## Context

A `make_round` visual packet held three dead-on views: front, top and iso. The
centaur runs of 2026-09-25 (`wish-20260925-084423-0b67ec83`) passed many
component rounds whose legs were lofts of near-circles and whose horse body was
a lofted ellipse; nothing in the packet showed the side profile, and a dead-on
view flattens depth along its own axis. The feedback record was a pass/fail
status and free prose, so a round could pass without ever saying whether the
build matched its plan or its reference images.

The operator's Panda Social agent renders six tilted three-quarter views plus
axis views, asks for a fixed judging order (silhouette and stance, proportion,
surface detail), and accepts a form only on a structured verdict with separate
plan and concept judgements. It names the common failures and tells the agent
to change construction family when a silhouette is wrong.

## Decision

- `render_review` gains the tilted views `iso_front`, `iso_back`, `iso_left`,
  `iso_right` (about 25 degrees off a face, 24 degrees up), `iso_top` and
  `iso_bottom` (55 degrees), and `--sheet`, which writes every rendered view
  labelled in one `sheet.png`.
- Every `make_round` renders `iso`, `front`, `left`, `top`, `iso_front`,
  `iso_back`, `iso_left`, `iso_right` and `iso_bottom` plus the sheet. Its
  `visual-packet.json` binds `sheet.png` alone: every view reaches a reader
  inside the sheet, whose hash binds them, and the single views stay on disk
  at full size beside it. A Component Reviewer, whose reads the host checks
  image by image (issue #77), opens one image plus each `compare-NN.png` per
  packet rather than ten. A geometry-scoped blind read (ADR 0072) cites the
  view `sheet`; the finalizer and verifier still accept `front`, `top` and
  `iso` for a packet from before this change. The Manager opens the assembly
  sheet at most once per round.
- Visual feedback adds two required fields. `matches_plan` is a boolean
  judgement against the plan the object is built from (`WISH-EXPANSION.md`, the
  sealed concept, or the Design Contract). `matches_reference` is a boolean
  exactly when the packet has comparison images and `null` otherwise. `pass` is
  refused unless `matches_plan` is true and `matches_reference` is not false.
- A Component Review (ADR 0076) carries the same two fields beside `agrees`,
  and an agreeing review is refused unless `matches_plan` is true and
  `matches_reference` is not false, so a review cannot lock a Component
  (ADR 0081) while saying it misses its plan. A disagreeing review still
  lists its differences. A camera mismatch carries neither field.
- The pending packet's detail and the make-round skill give the judging order,
  name the common failures, and say that a wrong silhouette is usually repaired
  by a different construction family.

- Spark previews the rough whole once before any component loop.
  `make_round --preview-assembly` renders the combined entry's sheet under
  `measure/assembly-previews/pNNNN/` and nothing else: no gate, review,
  round history, state or pass. It runs only from the root, like an
  assembly round, and refuses every other mode flag. The Manager fixes proportion, scale and
  placement between parts there, and previews again only after a component's
  size or placement changes. The gated assembly review of ADR 0063 still
  follows every component pass. Panda reviews the assembled object on every
  pass; the centaur run above refined its head for 21 isolated rounds before
  any assembled view could show its size against the body.

Python still only renders and hashes. It makes no visual judgement, calls no
model and lowers no gate.

## Consequences

- A full centaur assembly renders its nine views and sheet in about 39 s, up
  from three views; the Manager opens one image per round instead of three.
- A preview rebuilds the whole object from source: a cold 23-part centaur
  took about six minutes on a loaded host. It is meant once, not per round.
- Views are named by axis, not by the object's facing: for a subject lying
  along X, `front` shows its side.
- Feedback written for the old four-field schema is refused by the new tool.
  Frozen runs keep the tool and skill bytes they materialized.
- Cross-sections, and a bound on looks per component, are separate decisions.
- The Component Reviewer, not the Manager, opens a component round's sheet
  and returns `matches_plan` and `matches_reference` beside `agrees`. The two
  verdicts say whether the model meets the plan and the references; the
  review's `differences` say where it does not. No likeness score is computed
  (ADR 0076): `compare-NN.png` shows the reference beside the model, and the
  sheet joins it in the packet the reviewer reads.
- Reviews written for ADR 0076's schema without the two fields are refused by
  the new tool. Frozen runs keep the tool and agent bytes they materialized.
