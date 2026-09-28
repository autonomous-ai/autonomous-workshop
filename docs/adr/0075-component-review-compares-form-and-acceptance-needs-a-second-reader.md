# ADR 0075: Component review compares form, and acceptance needs a second reader

- Status: Accepted; implemented and deterministically tested
- Date: 2026-09-28
- Owners: Make round tool (`make_round`), image-to-cad (`render_views`),
  product-run Make instructions
- Supersedes: the stall-out and acceptance rules of ADR 0074, and its rejected
  alternative "reject visual feedback copied from an earlier round" in its
  verbatim form
- Relates to: ADR 0022 (blind review), ADR 0060 (visual feedback in Make
  rounds), ADR 0074 (every Component scored against its own image)

## Context

Broken God round 0 was rerun under ADR 0074
(`wish-20260927-120051-4515ea20`). Every Component was now scored against its
own image, and the run completed. Seven of ten Components still finished below
0.90 and were accepted by the Workshop Manager. Several looked crude next to
their images: a chest cage that reads as a solid block, blocky legs, and a thin
spiky wing. Reading the round evidence showed four defects in the round
itself:

1. **The review never put the model beside its image.** The packet held front,
   top and iso views of the model and only a hash of the reference. Nothing
   asked whether the form was simplified. Every round recorded `findings: []`.
2. **Reruns that changed nothing counted toward the stall-out.** The streak
   read only the IoU history. arm-left held 0.6689 for ten rounds: its geometry
   changed in three of them, and the rest were reruns for clearance, triangle
   budget or print checks. It was stalled out at a rerun with no edit and
   accepted at another. gear-staff was stalled out and accepted the same way.
3. **Observations were copied.** With unchanged renders, the Manager recorded
   "front/top/iso are byte-identical to the previous round's packet, which was
   inspected and passed:" followed by the previous observation, once nested
   twice.
4. **The Manager accepted its own work.** The agent that wrote a Component, or
   the Manager that assigned it, judged that the remaining gap was acceptable.
   No second reader looked.

The summary also reported only the IoU number. `check_likeness` already
computes where the silhouette misfits by height, but no round showed it.

## Decision

### The review compares form

- For every reference a round scores, `make_round` composes `compare-NN.png`:
  the reference beside the model's shaded render at the pose the likeness gate
  matched, both at one height, as the gate normalises them. The images are in
  `visual-packet.json` (schema 2) and are hash-bound like the views. A scored
  reference with no matched render leaves the round's visual status `error`.
- Below the floor, visual feedback must carry `differences`. Each difference
  names a feature, what the reference shows, what the model shows, and a
  decision, `repair` or `keep`, with its reason. There are at most 12. An empty
  list below the floor is refused. A difference to repair cannot pass.
- Feedback whose observation contains the previous round's observation
  verbatim is refused, when that observation is at least 40 characters long.
  This catches the literal copy Broken God recorded. A paraphrase is still not
  detected: that would need a model judge, which the host may not contain.

### The summary says where the shape misfits

`render_views` reports the three worst height bands of each match, and the
round summary shows them below the floor as model width over reference width
at each height.

### Only a rerun that changed the geometry counts

A round's identity is the Component's B-rep identity, or every part's for the
assembly. The streak skips a pair of rounds whose identity did not change: it
neither counts nor resets. A round with no recorded identity counts as
changed, as every round did before. Three rounds that change the geometry
without raising IoU by more than 0.005 are still a stall-out.

### Acceptance needs an independent reviewer

`--accept-likeness REASON` now also requires `--acceptance-review FILE`, a
review of the latest round:

```json
{"round": 7, "comparisons": {"<path>": "<sha256>"},
 "reviewer": "<name>", "agrees": true, "reason": "<why>"}
```

The acceptance is refused, and recorded as refused, when:

- the image has not stalled out;
- the review names another round;
- its comparisons differ from that round's packet or have changed;
- the reviewer is the Workshop Manager;
- the reviewer did not agree;
- the geometry changed after the reviewed round.

The acceptance records the review, and a recorded acceptance without a named
non-Manager reviewer no longer counts anywhere, including in `verify_project`'s
component coverage. The instructions tell the Manager to spawn a fresh subagent
that did not author the Component and to show it only the comparisons and that
geometry's contract lines.

The host cannot prove who the reviewer was. The rule forces a second reading
to exist and be recorded against exact images. It does not authenticate the
reader.

### Scope

- The comparison, the summary bands, the stall rule and the copy check apply
  to every new round.
- The differences requirement applies wherever a scored reference is below
  the floor.
- The acceptance review applies to component acceptances in `make_round`. The
  assembly image's acceptance at final verification (`verify_project
  --likeness-accept-mismatch`) still follows ADR 0074. Its stall history lives
  in `check_likeness` and records no geometry identity. That remains open.
- Frozen runs keep their materialized tool bytes and are unaffected.

## Alternatives considered

- **The authoring agent reviews its own acceptance.** Rejected by the owner.
  The authoring agent's self-review is what recorded empty findings for crude
  Components.
- **A reviewer for every round, not only for acceptance.** Rejected as too
  costly. Every round already has the comparison and, below the floor, the
  differences list. The second reader is spent where the floor is waived.
- **Show the blind critic the reference images.** Still rejected, as in ADR
  0074: the blind critic stays blind. The acceptance reviewer is a separate
  reading of the comparison, not the critic.
- **Refuse any rerun without an edit.** Rejected. Reruns are legitimate for
  clearance, print and budget checks. They simply do not count as attempts.

## Consequences

- A Component can no longer stall out on reruns that tried nothing.
- A crude Component must be named as different from its image, difference by
  difference, before any round below the floor can pass visual review.
- Every Component acceptance carries a reviewer's name and reason as well as
  the Manager's. Each acceptance costs one extra subagent reading.
- Tests: `tests/make/test_make_round.py` (`ContractComponentLikenessTest`).
