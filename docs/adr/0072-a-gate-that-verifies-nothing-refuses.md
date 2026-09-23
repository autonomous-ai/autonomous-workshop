# ADR 0072: A gate that can verify nothing must refuse

- Status: Accepted; Delivery 1 implemented and deterministically tested, Delivery 2 is the accepted target still to build
- Date: 2026-09-24
- Owners: Make round tool, CAD skill (`verify_project`), native finalizer
  (`stage_proposal.py`), Workshop CLI (`wish`, `fix`)
- Relates to: ADR 0022 (blind review), ADR 0026 (critical form requirements),
  ADR 0056 (alpha-aware likeness reference), ADR 0063 (component-first Make),
  ADR 0065 (correction runs)

## Context

`ad-astra-antisol-v01` sealed eight reference images with its Wish. Its CAD
project held twenty images under `ref/`. Its assembly round state records
`"likeness": {}`, and every component round records `"refs": []`. No
silhouette was ever scored against any reference, and every round reported a
pass. The toy was published.

Three defects produced that pass. They share one shape: nothing records the
difference between what was checked and what should have been checked.

1. **References reach the round tool through prose.** `make_round` takes
   `--ref`, or scrapes `LABEL=ref/PATH` lines from `*_spec.md`. The sealed
   `wish-references/` list is never consulted. The spec template's Likeness
   handoff is a markdown table, which that regex cannot match, so even a
   completely filled template yields no references. An empty list reaches
   `all(item["ok"] for item in likeness)` and passes. The final verifier's
   likeness gate sits behind an opt-in `--image-derived` flag that nothing
   requires.
2. **The reviewed party writes the review's checklist.** The finalizer
   enforces every row of `critical_form_requirements` strictly: any row
   without `matches: true` refuses the stage. The Manager writes that list
   after the Wish is revealed, and the list only has to be nonempty.
   `wren-coil-moon-fan` shipped three rows.
3. **Component evidence cannot be cited.** Schema v8 binds exactly two image
   hashes, `iso_sha256` and `signature_sha256`. Each component round already
   writes a `visual-packet.json` that hashes front, top and iso views and
   their sources. None of that is bound into the review. A requirement about
   one component can be marked matching with evidence that the two hashed
   images cannot show.

ADR 0065 adds a fourth instance. A correction run reviews against its
correction brief rather than the toy's original intent, so a correction can
satisfy the brief and silently break a requirement nobody restated.

ADR 0022's blind-then-reveal split, the image hashing and the round allowance
all work as designed. The failures are at the seams between them.

## Decision

A gate whose input can be empty must treat empty as a refusal, never as a pass.
The fixes below apply that rule. Items that correct a defect apply to every new
run. Items that add a capability apply only to Contract Mode. Frozen runs keep
their materialized tool bytes and are unaffected by either.

### Every new run

- `make_round` resolves the sealed references from `WISH.json` itself. The spec
  ledger is used only for references the agent found on its own, which no
  sealed record lists. The ledger parser also accepts the template's table
  row, for backward compatibility.
- An assembly round scores every sealed reference, except one that a
  current, passing component round has already scored at or above the floor.
  That exception matters because `design-a-toy` makes one image per Unique
  Geometry, so most sealed references show a single Component, and scoring
  those against the whole object would fail every run. A sealed reference
  that is missing or no longer matches its hash, or a `WISH.json` that cannot
  be read, fails the round. Component rounds keep ADR 0063's rule of scoring
  no implicit whole-object reference.
- The Make finalizer refuses a toy that sealed references unless the final
  verifier ran with `--image-derived`. This is not yet built: it ships in
  Delivery 2.

These change outcomes for new runs made without a Design Contract. A new run
that attaches references and never scores them, which passes today, will be
refused. That is intended: the old pass was the defect.

### Contract Mode

`workshop wish --contract FILE` and `workshop fix --contract FILE` seal a
Design Contract inside the Wish objective. The run refuses to start if the
contract cannot be parsed, because a malformed contract that quietly fell back
to the old behaviour would recreate this ADR's defect.

- The contract names its references and their labels. In Contract Mode those
  labels come from the contract, not from the Manager.
- The host copies the contract's visual requirements into the review at the
  reveal step. The Manager no longer writes the list. The blind first pass is
  unchanged: the critic still gets renders only, with no list and no intended
  answer.
- Signature review schema v9 adds `requirements_source`, set to `contract` or
  `manager`. That lets a reader see whether a short list was complete or only
  what the Manager chose to write.
- Every visual requirement has a Requirement Scope, either the assembly or one
  Unique Geometry. The contract names geometries, not Components, because it
  is approved before Make has created any Component. A geometry-scoped row
  binds the `visual-packet.json` of a Component built to that geometry, by
  hash, and names which view its evidence came from.
- Blind reads are counted per Unique Geometry, not per Component, and only for
  geometries that carry a geometry-scoped row.
- Geometry-scoped repairs have their own allowance. A repair invalidates only
  the reads whose Component sources changed, determined by the source hashes
  already recorded in `visual-packet.json`, on the same reasoning ADR 0069
  uses to carry byte-identical parts forward.
- When the blind read never mentions a requirement, the Manager may ask the
  critic one narrow blind question about the relevant image, keep the answer,
  and cite it.
- A correction run in Contract Mode reviews against the whole contract, not
  only its brief.

### Limits

- **Assembly-scoped rows: at most 16.** This number comes from commit
  `deed467e`, which added it with ADR 0026 as an input guard. ADR 0026 does
  not mention it and no test pins it. It is kept here as a guard on
  agent-supplied input, not as a design limit on how many requirements a toy
  may have.
- **Geometry-scoped rows: at most 4 per Unique Geometry.** This is also a
  chosen guard. It is bounded by the review turn, not measured against it.

Both limits are checked when the contract is sealed, before any run time is
spent. Raise either one once a real contract needs more and the cost of a
review turn has been measured against it. The number that actually matters is
the total count of blind reads.

## Consequences

- A toy cannot pass likeness without ever having been scored against the
  references it sealed.
- In Contract Mode, requirement coverage is part of the review's structure
  rather than a claim someone has to check. A contract with 11 requirements
  produces a review with 11 rows.
- The contract is approved once, before any image is generated, where the
  person already approves the spec. Its row limits are visible there, and
  exceeding them is refused before a run starts.

**Known residual risk.** The finalizer does not check that `blind_evidence` is
traceable to the preserved blind reads. A substring check was considered and
declined. In `wren-coil-moon-fan`, two of three rows already quote the blind
read verbatim, and the third is the Manager's own narration. With that check
declined, a targeted blind re-read happens only when the Manager decides to
ask for one, and prose that no blind read supports can still pass. **Revisit
this if Contract Mode archives show repeated cases of the Manager choosing
wrongly.** The fix would require every `blind_evidence` to contain a verbatim
span of the preserved `blind_*` fields. That is a deterministic containment
check, and it does not interpret prose.

## Delivery

1. Resolving references from `WISH.json`, accepting the template's table row,
   and the assembly round refusal. These changes are small and apply to every
   new run.
2. Signature review schema v9, Contract Mode, `--contract` on `wish` and `fix`,
   the finalizer's `--image-derived` refusal, and the Design Contract in
   `design-a-toy`.

## Verification

- Round-tool tests: an assembly round with sealed references and an empty
  ledger scores those references rather than passing on an empty list; a
  reference that cannot be resolved refuses; a component round still skips
  whole-object references; a table-row ledger yields its references.
- Finalizer tests (Delivery 2): a toy with sealed references whose verifier
  did not run `--image-derived` is refused.
- Contract Mode tests (Delivery 2): a contract that cannot be parsed refuses at `wish`; a
  contract over either row limit refuses at `wish`; a schema-v9 review whose
  rows differ from the sealed contract's requirements is refused; a
  geometry-scoped row without a bound packet is refused; a correction run
  reviews against the whole contract.
