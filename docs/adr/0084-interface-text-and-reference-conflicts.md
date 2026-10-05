# ADR 0084: The reviewer reads Interface text, and the Design Contract wins over its references

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-10-02
- Owners: the Design Contract (`wish/design_contract.py`,
  `.claude/skills/build-a-toy/CONTRACT-FORMAT.md`, `design-a-toy`), the
  `make-round` skill and `cad/scripts/verify_project`, the Component
  Reviewer and Component Worker definitions
  (`src/workshop/make/agents/`), product-run Make instructions
  (`references/make.md`), the Make finalizer (`stage_proposal.py`), the
  host's receipt (`workflow/native_run.py`, `cli/main.py`)
- Amends: ADR 0076 and ADR 0081 (what a review may list and what it costs),
  ADR 0077 (the review request), ADR 0082 (what an Interface records)
- Issue: #83

## Context

A Component Reviewer judges form against the Component's reference image.
The Design Contract reached it only as the Component's requirement rows,
which the Workshop Manager copied into its request. An Interface carried no
text (`id`, `kind`, `components` and its envelope or poses), so the joint
features it imposes (a plug, a socket, a seat face) lived only in the
contract's prose and the reviewer never saw them. Its rule "a feature a row
requires that the reference does not show is not a difference" never
applied to them.

When a reference image disagreed with the contract, nothing handled it. The
reviewer listed the difference, the Component Worker kept the contract and
did not repair it, and each round spent a Shape Round until the cap turned
the disagreement into a Component Acceptance.

In Broken God attempt 13 (`wish-20261002-055840-9aa34bc3`, 32 recorded
reviews) the gear-staff spent 6 reviews and 5 Shape Rounds on "a bare 3.7 mm
shaft stub below the ferrule; remove it", which Interface `staff-base`
requires and `ref-10` does not draw; the heart-core spent 6 reviews and 5
Shape Rounds on "the retaining flange is a 45-degree cone; make it a flat
riveted disc", which Interface `heart-chest-seat` requires and `ref-06` does
not draw. Both were locked by Component Acceptance. 11 of 159 recorded
differences said "keep as is" (a repair below the print limits) and still
counted as differences.

## Decision

1. **The Design Contract wins.** A reference image that shows what the
   Design Contract forbids is a **Reference Conflict**, not a difference: it
   costs no Shape Round, does not stop the run, does not block an agreeing
   review, and is reported to the person when the run ends so the image can
   be corrected.
2. **Design Contract schema 4: every Interface carries `text`**, required
   and non-empty, with no maximum length. It states in words what the
   Interface imposes on each Component it joins:

   ```json
   {"id": "staff-base", "kind": "static", "components": ["gear-staff", "gear-base"],
    "text": "The staff's bottom 10 mm, a bare Ø3.7 shaft below the ferrule, sits in a Ø3.9 × 10 socket in the base at X −40, Y −32."}
   ```

   Schema 4 keeps schema 3's Reference Cameras and Display Pose comparison
   (ADR 0083). `text` is refused before schema 4. It informs the reviewer
   and the worker; no gate measures or scores it, and Interface checks stay
   numeric (ADR 0082).
3. **`make_round` delivers the contract, not the Manager.** Under a schema 4
   contract a component round writes, from the sealed contract, the
   Component's geometry row, its requirement rows and the `id`, `kind`,
   `components` and `text` of every Interface that names it (`<id>` or
   `<id>#<n>`) as `contract` into `visual-packet.json`, bound by the packet
   hash, and into `summary.json` for the Component Worker. The Component's
   contract-row hash, which decides whether a review carries to a later
   round, covers those Interfaces. The Manager's review request becomes the
   packet path and its sha256 only.
4. **The reviewer's answer gains `reference_conflicts`**, a list beside
   `differences` (at most 12): each entry names the reference `file` this
   round compared, what the `reference` shows, and what the `contract`
   requires, quoting the row or Interface text. `agrees` may be true while
   the list is non-empty. `--record-review` validates it like
   `camera_mismatch`: each entry has all three fields and names a reference
   the round compared. A disagreeing review whose only findings are
   Reference Conflicts is refused, because such a review agrees; no Shape
   Round is spent on it. The Component Worker is not told: `review.json`,
   which it reads, is written without the list, which the round keeps in
   `reference-conflicts.json` and the summary. Nothing is repaired. The
   conflicts carry with the review they belong to.
5. **"Keep as is" is not a difference.** The reviewer does not list a
   difference whose repair would go below the print limits; if only such
   entries remain, the review agrees.
6. **Reporting.** The final verifier notes each Reference Conflict of a
   current component review and writes them to `component-acceptance.json`,
   bound to its report, as `reference_conflicts`. The Make finalizer copies
   them into `product.json`; the host checks their shape, seals them into
   the Make gate receipt, and reports them where Component Acceptances are
   reported: the run's final receipt and `workshop status --json`
   (`reference_conflicts`), one entry per Component, reference and conflict,
   and one line each in the text status.

`design-a-toy` Stage 3b also gains a joint-feature check: an image whose
Reference Camera can see a joint feature an Interface puts on its Component
must show it as contracted.

## Consequences

- The reviewer judges joint features from the sealed contract text, so a
  feature the image cannot show is no longer a difference, and one the image
  draws wrongly is reported instead of spending Shape Rounds.
- A wrong reference image no longer costs a Component its five Shape Rounds
  and a Component Acceptance; it costs a report line, and the person
  corrects the image for the next run.
- Every schema 4 Interface needs words as well as numbers. The words can
  disagree with the numbers; nothing checks that, and the numbers still
  decide every gate.

## Compatibility

Schema 1 to 3 contracts parse as before. Their packets carry no `contract`,
so the Manager still adds the Component's rows to the request, and their
contract-row hash is unchanged. A frozen run keeps its materialized
`make_round`, verifier, finalizer and agent definitions on resume, so it
never records a Reference Conflict. A receipt with none reports an empty
`reference_conflicts` list.

## Rejected

- Letting the image win, or asking the person mid-run: the contract is what
  the person approved last and the one the gates read.
- Scoring or measuring Interface text.
- Correcting the Broken God package here; its owner does that before
  attempt 14.
