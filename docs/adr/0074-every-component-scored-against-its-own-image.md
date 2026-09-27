# ADR 0074: Every Component is scored against its own sealed image

- Status: Accepted; implemented and deterministically tested
- Date: 2026-09-27
- Owners: Make round tool (`make_round`), CAD skill (`verify_project`), native
  finalizer (`stage_proposal.py`), Workshop host receipt and CLI
- Relates to: ADR 0022 (blind review), ADR 0063 (component-first Make),
  ADR 0072 (a gate that verifies nothing refuses), ADR 0073 (B-rep identity)

## Context

Broken God round 0 (`wish-20260926-041321-3f83a63c`, Contract Mode, Spark)
sealed eleven images: one `assembly` image and one `geometry:<id>` image per
Unique Geometry. Make finished. Scored afterwards against their own images,
five of the ten Components were below 0.70 IoU, and arm-right (0.466) was two
boxes arranged in a Z. No gate reported any of it. The backlog note
`docs/backlog/make-component-fidelity-gaps.md` gives the full diagnosis. The
defects that matter here are these:

1. **Component likeness was opt-in.** A component round scored an image only
   when the agent passed `--ref`. The agent passed it once, then stopped.
   Every component summary recorded `refs: []` and passed.
2. **The Manager reviewed components without the image.** With no `--ref`
   the visual packet carried no reference, so self-review compared the render
   with the contract text instead of the picture.
3. **The assembly scored component images against the whole statue.** ADR
   0072 scores every sealed image a component round did not cover. An image of
   one arm scored against the whole object fails every time and measures
   nothing, so the agent learned to ignore those failures.
4. **The final verifier scored only what it was given.** The run passed only
   the assembly image. Nothing required the others to be accounted for.
5. **Acceptance was mislabelled.** `verify_project` recorded a Manager
   acceptance as "accepted by user". The finalizer also accepted only a literal
   `PASS (exit 0)`, so any accepted likeness failure blocked Make outright.
6. **The Spark cost instruction pulled the other way.** "Spend additional
   cycles only on a concrete failing check" read an unscored image as no
   failing check at all.

## Decision

A sealed image is always measured against the geometry it shows, and a
failure below the floor is either repaired or explicitly accepted on the
record. It is never silently dropped.

### Contract Mode Make

- **A component round scores its own image.** When the sealed Design Contract
  has an image labelled `geometry:<id>`, the round for `part_<id>.step.py`
  scores it automatically, with no `--ref`. A score below the floor fails the
  round. The image is in `visual-packet.json`, so the Manager's review compares
  the render with the picture.
- **The assembly never scores a component image.** An assembly round lists a
  `geometry:<id>` image as `scored_by: component:<id>` when a current component
  round covers it. Otherwise the image is `missing`, and the round fails with
  the command that fixes it.
- **The floor stays 0.90** for component and assembly images alike.
- **The final verifier accounts for every sealed image.** `verify_project
  --image-derived` refuses a `--likeness-ref` that is a component image, and
  refuses to run unless every sealed `assembly` image is given. After its build
  it fails unless every `geometry:<id>` image has a current component round
  that passed or was accepted. It identifies the Component the way `make_round`
  does: by the B-rep identity `gen` reports, or, when `gen` built nothing, by
  the STEP bytes that round wrote.

### Acceptance

- **Only a stalled-out image may be accepted.** Stalled out uses
  `check_likeness`'s existing rule: three consecutive rounds that raise IoU by
  no more than 0.005, where an improving round resets the count. Component
  rounds keep that history. `make_round --component ... --accept-likeness
  REASON` accepts a stalled-out image and refuses one that has not stalled.
  The final verifier's `--likeness-accept-mismatch REASON` already applied the
  same rule to the assembly image.
- **The Workshop Manager accepts, with a reason, on the record.** Acceptance is
  recorded as `accepted_by: workshop-manager`, never as the person's decision.
  The raw score stays a failure in every likeness report.
- **Every acceptance is reported when the run ends.** `verify_project` writes
  `measure/likeness-acceptance.json` beside its report, bound to the report's
  sha256. The finalizer:
  - validates that record;
  - copies its acceptances into `product.json` as `likeness_acceptances`;
  - refuses the field when the verifier wrote no record;
  - requires the record in Contract Mode;
  - accepts `PASS (N accepted failing gates)` only when every accepted gate
    is `check_likeness` and the record holds an assembly acceptance.

  The host validates the list again, seals it in its Make gate receipt, and
  puts it in the run receipt. `workshop wish`, `resume` and `status` print one
  line per acceptance: the label, the IoU against the floor, and the reason.
  `--json` carries the same list.

### Instructions

- Spark's cost line now says that an unscored or below-floor sealed image is a
  failing check, and that an organic feature built as a plain box is a visible
  defect.
- `references/make.md` states the component naming rule, the acceptance rule
  and the final verifier's Contract Mode inputs.

### Scope

- The component, final-verifier and finalizer requirements apply to Contract
  Mode only.
- The Manager-acceptance labelling and the finalizer's accepted-PASS path
  apply to every new run, since the old label was simply wrong.
- Frozen runs keep their materialized tool bytes and are unaffected.

## Alternatives considered

- **Refuse a component round that omits `--ref`.** Rejected. It still leaves
  the choice of image to the agent. Scoring automatically leaves it no choice.
- **A lower floor for Components.** Rejected by the owner. The floor stays
  0.90, and the pressure goes into repair or an explicit, reported acceptance.
- **Only a person may accept.** Rejected by the owner, in favour of a Manager
  acceptance that must follow a stall-out, carry a reason, and be reported at
  the end of the run. The stall-out is something the host can check. The
  reason is not, and is only reported.
- **A new per-component round allowance before acceptance.** Rejected. The
  stall-out rule already exists, is tested, and still forces real repair
  attempts before an acceptance.
- **Show the blind critic the reference images.** Rejected. It would end the
  critic's blindness (ADR 0022). Likeness to the image is measured by IoU.
- **Reject visual feedback copied from an earlier round.** Rejected. Broken
  God's feedback was paraphrased, not copied, and detecting a paraphrase needs
  a model judge, which the host may not contain.

## Consequences

- A Contract Mode run can no longer ship a Component that no gate compared
  with its image.
- A Component file must be named after its Unique Geometry id.
- A toy may still ship below 0.90, but only after three repair rounds that did
  not move the number, and never silently: the person sees every acceptance
  and its reason.
- The finalizer's geometry-row check (ADR 0072, issue 55) still compares a
  Component's STEP sha256 with the recorded identity.
  `current_passing_component_round` now also accepts the STEP bytes the round
  wrote, which fixes that check whenever the STEP was not rewritten after the
  round. A rebuild that changes the bytes without changing the shape (ADR 0073)
  can still make it refuse. That remains open.
