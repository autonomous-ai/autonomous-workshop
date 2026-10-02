# ADR 0076: A Component passes on an independent review, not a likeness score

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-09-29
- Owners: Make round tool (`make_round`), final verifier (`verify_project`),
  Make finalizer (`stage_proposal.py`), Workshop host (`native_run.py`),
  product-run Make instructions
- Supersedes: the silhouette-likeness parts of ADR 0072 (sealed references are
  scored), ADR 0074 (every Component scored against its own image at the 0.90
  floor, stall-out acceptance) and ADR 0075 (stall-out counting, acceptance by
  `--accept-likeness`, differences required below the floor)
- Keeps: ADR 0072's rule that every sealed reference reaches a reader and a
  missing or changed one fails the round; ADR 0074's rule that a Component's
  image is never judged against the whole object and that the final verifier
  accounts for every sealed image; ADR 0075's composed comparison images, its
  refusal of copied observations and its rule that a second reader, never the
  Workshop Manager, decides whether a Component's shape is acceptable
- Relates to: ADR 0022 (blind review), ADR 0060 (visual feedback in Make
  rounds), ADR 0073 (carry-forward compares B-rep identity)

## Context

Run `wish-20260928-142712-25fb17ef` built every Component against its own
sealed image under ADR 0074 and ADR 0075. No Component reached the 0.90 IoU
floor. The score did not track shape:

- heart-core stalled out at round 4 with its print gates passing, yet the
  Manager kept repairing it to round 19 with IoU flat at about 0.866.
- arm-right scored 0.746 at round 1, 0.32 after it was laid flat for printing,
  and 0.57 at the end, although its shape was close to its image by then. The
  number measured the pose match, not the arm.

A silhouette score cannot see the defects a person sees (a block where the
image has a cage, a limb half as thick), and it moves for reasons that are not
the shape (print orientation, camera search). Spending repair rounds to raise
it made the run longer without making the toy look more like its images.

## Decision

1. **No likeness score anywhere in the Workshop pipeline.** `make_round` no
   longer runs `render_views --match`; `verify_project` no longer runs
   `check_likeness` and takes no `--likeness-ref`, `--likeness-min`,
   `--likeness-accept-mismatch` or `--likeness-accept-regression`. The
   vendored `render_views.py` and `check_likeness.py` stay on disk with their
   upstream bytes, but nothing in the pipeline asks them for a verdict.
2. **Every reference is shown, not scored.** Each round's visual packet holds
   front, top and iso views plus one `compare-NN.png` per reference: the
   reference beside the model, rendered by `render_review` at the reference's
   declared `@AZ,EL` camera, or from the front when none is declared.
3. **A Component passes on build, print and an independent review.** A
   component round passes when every part builds, its thickness and overhang
   gates pass (or are UNVERIFIED as before), and a reviewer who is not the
   Workshop Manager recorded that the model looks like its reference
   (`make_round --component ... --record-review REVIEW.json`). The review is
   bound to the round's packet hash, its images and the sources; it is refused
   for an older round, changed evidence, failed checks, a second review of the
   same round, or a reviewer named as the Manager. A disagreeing review must
   list its differences; that list is the next repair. Component rounds no
   longer take the Manager's own `--record-visual`.
4. **Five shape rounds, then the review decides.** A *shape round* is a
   component round that changes the geometry of a Component whose previous
   round passed its build and print checks. Rounds that repair build or print
   failures, and reruns that change nothing, are not counted. After five,
   `make_round` refuses another round for that Component until the latest
   passing round is reviewed. An agreeing review then passes it; a
   disagreeing one is recorded as a *component acceptance*
   (`{reviewer, reason, shape_rounds}`) so the run cannot deadlock. Once that
   review exists, further rounds may still run, for example when an assembly
   repair changes the part.
5. **Acceptances reach the person.** In Contract Mode the final verifier
   requires, for every sealed `geometry:<id>` image, a current passing
   component round, and writes `measure/component-acceptance.json` beside its
   report (bound to the report's hash, an empty list when none). The Make
   finalizer seals it into `product.json` as `component_acceptances`; the host
   validates it into the Make gate and the run receipt; the CLI prints each one
   when the run ends. An acceptance is never recorded as the person's
   decision.
6. **The assembly keeps its reviews.** Assembly rounds keep the Manager's
   `--record-visual`, the blind review and `--full`. Sealed images that show
   the whole object are composed beside the assembly for those reviews.

Frozen runs keep the tool bytes they materialized; the host still reads their
`likeness_acceptances`.

## Consequences

- A Component's pass rests on a reader's judgement, which a number cannot
  replace but also cannot audit. The review is only as independent as the
  Manager's choice of reviewer; the tool refuses the Manager's own name but
  cannot prove who wrote the file.
- The shape-repair allowance bounds cost: at most five shape rounds per
  Component before the review is final.
- The final report no longer carries a likeness table, so a run cannot quote a
  likeness figure. Claims of resemblance come from the recorded reviews.
- Whether independent review produces toys that look more like their images
  than the IoU floor did is not yet shown. It needs a live run before this
  experiment is merged.

## Rejected alternatives

- **Keep IoU as advice.** A number shown beside the images anchors the
  reviewer on the metric this decision found unreliable, and the Manager would
  still repair toward it.
- **Fix the pose search instead.** The arm-right drop came from a print pose,
  but heart-core's flat 0.866 did not; the silhouette cannot see the defects
  that mattered in either case.
- **Let the Manager decide at the cap.** ADR 0075 already found the Manager
  accepting its own work; the reviewer still decides, and at the cap its
  disagreement is recorded rather than repaired again.
