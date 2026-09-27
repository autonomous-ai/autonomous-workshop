# Make ships crude components because nothing checks them against their references

- Status: Fixed by ADR 0074 (`docs/adr/0074-every-component-scored-against-its-own-image.md`).
  See "Decision" below for what was kept and what was dropped.
- Priority: High. It defeats Contract Mode's likeness promise for every
  component after the first.
- Evidence run: `wish-20260926-041321-3f83a63c` (Broken God round 0, Spark,
  `claude-opus-5-5`, effort medium, `--check-motion true`). The workspace and
  transcript live under `~/.local/share/autonomous-workshop/` and
  `~/.claude/projects/`; they are not tracked.

## Observation

The run finished Make in the `waiting` state. The need it raised was for a
person to accept ref-01's whole-statue likeness: IoU 0.483 against a 0.90
floor. Every other final gate passed.

Scoring each component against its own sealed reference afterwards (with
`render_views.py --match`) gave:

| Component | IoU | Component | IoU |
|---|---|---|---|
| gear-base | 0.955 | arm-left | 0.661 |
| spine-housing | 0.924 | gear-staff | 0.654 |
| heart-core | 0.923 | wing | 0.603 |
| crest-helm | 0.848 | legs-pelvis | 0.520 |
| chest-cage | 0.826 | arm-right | 0.466 |

The parts that failed look crude:

- arm-right is two boxes arranged in a Z;
- arm-left's forearm is a box, with no visible claws;
- the feet are plain blocks.

The run passed anyway, and no gate reported any of it.

## Root causes

**1. Component likeness is opt-in.**

- `src/workshop/make/skills/make-round/scripts/make_round:1031-1038` scores a
  component round only when the agent passes an explicit `--ref`. It passes
  no spec paths and skips the sealed references, citing ADR 0063.
- The agent passed `--ref` once (wing r1, IoU 0.627) and then dropped it for
  every round of every component. All ten final component summaries show
  `refs: []` and `ok: true`.
- `references/make.md:159-167` tells the agent to score each component's
  sealed reference in that component's round, but nothing enforces it.

**2. Self-review runs with no reference image.**

- Without `--ref`, `visual-packet.json` carries `"references": {}`.
- The `visual-feedback.json` verdicts are identical across rounds r2 to r5
  and restate the contract text rather than describing the render. For
  example, arm-right is recorded as "pauldron block … fist block, pass".
- `--record-visual` rejects only a repeat on the same packet. It accepts text
  copied from an earlier round.

**3. The Manager overrides the blind critic.**

- `snap/SIGNATURE-REVIEW.json` records the critic reading:
  - arm-right as "two stacked shoulder blocks … rectangular beam";
  - the feet as "a block".
- The Manager still recorded `matches: true` for R23 and R24 and for the
  legs requirement.
- The host never cross-checks what the critic read against the requirement
  it was asked about.
- The critic never sees the reference images.

**4. The final verification scores only the assembly reference.**

- The pipeline passed `--likeness-ref ref-01` alone. That contradicts
  `make.md` step 8.
- The agent's justification, "compared in each part's own review instead",
  was false.
- Assembly rounds r1 to r6 scored every sealed reference against the whole
  statue. They all failed, and the failures were ignored. Scoring a component
  reference against the assembly is also meaningless.

**5. Likeness self-acceptance is mislabelled.**

- `verification-pipeline.md` records "raw floor failure accepted by user".
- Its reason text says "Accepted by the Workshop Manager, not a person".
- The stage still ended `waiting`, so the host did catch ref-01. Nothing
  caught the components.

**6. Agent judgment and instruction pressure.**

- The arms, legs, helm and staff were all written between 05:30 and 05:37,
  then touched only for print-gate fixes.
- The effort went to the wing (11 rounds), the helm (15), the chest and the
  motion-heavy assembly rounds.
- The Spark instruction "spend additional cycles only on a concrete failing
  check" (`.agents/product-run/.agents/skills/autonomous-workshop/SKILL.md:98-100`)
  worked against `image-to-cad/SKILL.md:620-624`, "Do not downgrade organic
  silhouette features to boxes". An unscored reference never counts as a
  failing check.

**7. Undocumented extent deviations.**

- The chest-cage and spine-housing depths (5 and 21.5, against 18 and 16)
  were deliberate. `broken_god_spec.md` Assumption 2 moves the gear plane into
  the spine so both halves print support-free.
- The arm-right depth (12.2 against 18) has no record.

## Decision (2026-09-27, owner)

| Candidate | Outcome |
|---|---|
| 1. Refuse a component without its reference | Done, as automatic scoring: a Contract Mode component round always scores its `geometry:<id>` image, 0.90 floor |
| 2. Put the reference in the packet | Done, follows from 1 |
| 3. Reject copied feedback | Dropped: feedback was paraphrased, not copied; a paraphrase check needs a model judge |
| 4. Require every sealed reference at the end | Done: `verify_project --image-derived` and the finalizer account for every sealed image |
| 5. Show the critic the references | Dropped: the critic stays blind (ADR 0022); IoU owns likeness |
| 6. Block self-acceptance | Changed: the Workshop Manager may accept, only after a stall-out, with a reason reported when the run ends |
| 7. Reword the Spark cost line | Done |
| (new) Assembly scores component images | Removed: a component image is never scored against the whole object |

Floor stays 0.90. No new round allowance: acceptance reuses the existing
three-round stall-out rule.

## Fix candidates (as originally listed)

1. **Refuse a component without its reference.** In component scope, when the
   sealed Wish has a reference whose `shows` is `geometry:<id>` for this
   component, `make_round` either scores it automatically or refuses to pass
   without it.
2. **Put the reference in the packet.** Always include the matched component
   reference in `visual-packet.json`.
3. **Reject copied feedback.** Refuse visual feedback that repeats the
   previous round's text verbatim, or that only restates requirement text.
4. **Require every sealed reference at the end.** In Contract Mode, the
   finalizer or host requires a passing likeness for every sealed reference.
   A component reference passes in its own component round and the assembly
   reference in the final verification. Any reference below the floor fails
   the stage.
5. **Show the critic the references.** Send the blind critic the
   per-geometry reference images. Refuse `matches: true` when the critic's
   read contradicts a form requirement.
6. **Block self-acceptance.** Refuse `--likeness-accept-mismatch` text that
   is not a recorded person decision. Never label a Manager acceptance as
   "user".
7. **Reword the Spark cost line.** An unscored or failing sealed reference
   counts as a concrete failing check.

Every one of these is a runtime or tool change. The AGENTS.md working rules
apply: contract and failure-path tests, and no weakened gates.

## Related state (Broken God)

These files are untracked local work, not part of this fix:

- `toys-spec/broken-god/build-a-toy/ledger.json` records every round attempt,
  this investigation, and the component IoU table.
- `toys-spec/broken-god/build-a-toy/drafts/CONTRACT.amend-b.md` is a draft
  contract amendment awaiting the owner's approval. It re-proportions the
  statue to follow ref-01, which the owner prefers over the old contract. The
  previous contract is backed up in `build-a-toy/CONTRACT.v2-amend-a.md`.
- The v1 reference images in `build-a-toy/refs-v1/` already match amendment B
  for legs, chest and arm-left. Refs 05, 07, 09, 10 and 11 must be
  regenerated.
- The `design-a-toy` skill gained a Stage 3b "Reconcile every image with the
  contract" step. It is uncommitted.
- Run `wish-20260926-041321-3f83a63c` is left `waiting`. It will be superseded
  by a new round 0 once amendment B is approved.

## Suggested skills for the next session

- `mattpocock-skills:grill-with-docs`, then `mattpocock-skills:to-spec` and
  `mattpocock-skills:to-tickets`: to turn the fix candidates into a decided
  plan checked against `docs/adr/`.
- `mattpocock-skills:tdd`: for the `make_round` and finalizer changes.
- `design-a-toy`: Stage 3b, to regenerate references 05, 07, 09, 10 and 11
  after amendment B is approved.
- `build-a-toy`: to rerun round 0 on the amended contract.
