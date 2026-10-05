# ADR 0086: Spark Make expands the Wish before building

- Status: Accepted
- Date: 2026-09-25
- Relates to: ADR 0016 (selectable effort routes), ADR 0063 (component-first
  Spark Make), ADR 0072 (Design Contract)

## Context

Spark runs straight from Wish to Make with no Invent stage, so a short Wish
reaches CAD with most of the decisions that shape a printed object still open:
which parts must read as distinct, the pose, the spaces that must stay open,
the overall size, which forms are primary, how the parts split and join, and
what to give up when print constraints bite. Make then settles them one edit at
a time, late and generically.

The Ossuary Drake run (`toys/nox-carver-ossuary-drake`) was launched with a
detailed Wish the operator had first expanded by hand along exactly those
lines, and the operator judged its result better than runs from short Wishes.
Nothing here measures that; it is the operator's comparison.

The first three runs with the step (2026-09-25, all centaur Wishes, none with
reference images) wrote the expansion but built every form from text alone,
and the expansion recorded no construction choice. The operator's own tools
built on the same Claude runtime (Panda, Panda Social) create noticeably more
faithful models when a reference image is attached; they turn the image into a
durable, measured, visible-versus-inferred record and choose each form's
construction family from it before writing geometry.

Two ways to automate that expansion break the architecture. The host cannot
rewrite the Wish, because the Wish is sealed byte for byte. Python cannot call
a model to do it, because structured model calls and prompt chains are not
extension points. A new lifecycle stage would change every frozen route.

## Decision

New Spark Make, outside Contract Mode and outside an early-proof turn, begins
with a native step: once the Inventor is selected and before any component
source exists, the Manager writes `<cad-project>/WISH-EXPANSION.md` following
`references/wish-expansion.md`, in four paragraphs covering what must be
recognisable, pose and reading, size and form discipline, and function and
printing.

- The sealed Wish is unchanged and remains the objective. The expansion keeps
  every explicit Wish requirement exactly and fills only what the Wish leaves
  open, with one concrete choice each.
- The expansion's defining parts and negative spaces join the Wish's own
  explicit requirements in the blind review's `critical_form_requirements`. The
  review still judges against the actual Wish, and a choice the Wish does not
  require never fails a faithful build.
- Paragraph 3 names each primary form's construction family from the
  `image-to-cad` operation table, because a form built in the wrong family
  cannot be repaired by parameter edits.
- When the Wish has reference images, or Make fetches them for a named object,
  the expansion ends with a `## Reference reading`: each image opened and
  measured with `image-to-cad`'s `measure_image.py`, and one line per defining
  part tagged `[observed]` with its image and measured ratio, or `[inferred]`
  with its basis. Size still comes from the Wish, never from pixels, and a
  conflict with the Wish follows the Wish. Pixels do not survive compaction;
  this record does.
- Paragraph 4 splits only at the object's natural seams. A Spark component is
  such a piece, never a pre-planned print half: the centaur run
  `wish-20260925-084423-0b67ec83` split about 11 pieces into 23 `_a`/`_b`
  halves to pass `check_overhang` support-free, and spent 101 component
  rounds, thickened its bow string from 1.4 to 2.1 mm, and still sculpted
  round forms. A piece that fails overhang is reoriented, then reshaped
  (keel, chamfer or hidden flat land), then split at a natural seam, and only
  then split on a plane with the reason in `GEOMETRY-NOTES.md`. The overhang
  gate, its 45 degree angle and the support-free rule are unchanged.
- Every such Make obtains references before expanding, not only for a named
  object: the sealed images, then a bounded image search (official images for
  a named object; the subject's real anatomy and sculpted examples of the
  requested style for an original one, never copied and never a likeness
  target), then, on a runtime with a built-in image tool such as Codex's
  `image_gen`, a generated concept whose side and top views are edits of its
  first view. No image API is called with a key and no Python calls a model.
  Found and generated images feed the reference reading and the Manager's
  visual judgement, not `make_round --ref`. The build is text-derived only
  when none is usable. The operator's runs have been better whenever a
  reference existed; the 2026-09-28 centaur runs on both runtimes had none.
- Paragraph 3 translates every style word of the Wish into section shape,
  edges (with a largest fillet radius), silhouette and proportion, with the
  values decided by the selected Inventor's Taste, and carries them into
  `critical_form_requirements`. The pipeline requires the translation; the
  Taste supplies it. Nox Carver's Taste now states a hard, angular,
  gaunt dark-fantasy shape language and caps fillets on primary forms at
  1.5 mm, because both 2026-09-28 expansions still planned "rounded"
  masses. The make-round review judges shape language beside silhouette.
- The constitution carries a one-line form of the step, because compaction
  drops references and re-emits the constitution.

Forge and Quest are unchanged: their sealed Invent concept already does this
work. Contract Mode is unchanged: the Design Contract is the full
specification.

## Consequences

- No host gate checks that the file exists or what it says. It is native
  guidance, like the component funnel it feeds; adding a presence gate is a
  separate decision.
- The expansion is part of the sealed CAD project, so a published archive
  shows it. It paraphrases the Wish, as `*_spec.md` briefs already do.
- Frozen runs keep the template they materialized and never see the step.
- Whether the step improves short-Wish runs is unmeasured. The comparison to
  make is a short Wish run with and without it, judged by the blind review
  and by the operator.
