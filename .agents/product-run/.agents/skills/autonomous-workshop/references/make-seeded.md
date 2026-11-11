# Seeded Make (ADR 0096)

Read this when run-root `MAKE-OPTIONS.json` has `seed`. The owner approved
this toy's shape in design. The read-only run-root `seed/` holds that
Approved Proof:

- its CAD project: `params.py`, `features/`, `part_<id>.step.py` and
  `samples/`, and what final verification reads: the `*_spec.md` and
  `measure/check_fit.py`, `measure/check_spec.py` and
  `measure/check_landmarks.py` (a Proof sealed before these were required
  may lack them; then write them as make.md says);
- `approved/part_<id>.step`;
- `CRITIC.json`, `CONCEPT-CHECKLIST.md` and `APPROVAL.json`.

Make certifies that build. It does not model the toy again.

## When the host ran the batch (ADR 0098)

When `MAKE-OPTIONS.json` `seed` has `batch`, the host has already run
every seeded check as one batch before your turn, and you were started
only because a check failed:

- `STAGE.json` `inputs.seeded_batch_failure` lists every failing step:
  its id, its command, its layer and the tool's own output. Steps not
  listed passed; never rerun them.
- Repair only what the failing steps name, under this file's rules, and
  rerun only those steps to see them pass.
- The host writes `parts/<occurrence>.step` itself (the `parts` step). If
  it fails, it names each occurrence no Component STEP holds, or that more
  than one holds; fix that assembly label in the CAD source, never by
  writing a part file by hand.
- Propose with the finalizer as usual. The host reruns the whole batch as
  Make's gate (unchanged inputs reuse their passing result); a failure
  comes back as a new `seeded_batch_failure`.

Without `batch`, follow the order below.

## Order

1. Copy the seed's project files into your CAD project. Leave out
   `approved/`, `APPROVAL.json`, `CRITIC.json` and `CONCEPT-CHECKLIST.md`.
   Install `features/print_details.py` from the library as usual. If its
   bytes differ from the seed's, keep the library's and rebuild; a shape
   that changes is then a deviation.
2. Run the Shared Helper freeze (`--shared-helpers`) as in any run.
3. Run one component round per Component yourself, each as its own plain
   Bash command. The guard passes you a `--seed-nonce`. A round that is the
   approved Component locks with `review.carried_from: "seed-approval"`:
   nothing renders, and you ask no reviewer.
4. For a round make_round refuses as a deviation, spawn one Component
   Worker for that Component only, under the usual worker and review rules.
   A worker's round within `proof_diff` tolerance (`seed-diff.json`) locks
   by the approval. One over tolerance waits for its Component Review.
   When `MAKE-OPTIONS.json` `seed` has `review: "approved-proof"` (ADR
   0102), that review is against the Approved Proof, not a Reference Image:
   the round's packet has `basis: "approved-proof"` and each
   `compare-NN.png` shows the approved Component beside the changed one at
   a Reference Camera. Send the reviewer the packet path and hash as usual.
   It agrees when the shape is the approved one or differs only where the
   forcing gate needed. Otherwise it lists differences `{feature, approved,
   model}` for the worker. It has no camera mismatch and no Reference
   Conflict. Tell the worker to repair toward `seed/part_<id>.step.py` and
   `seed/approved/part_<id>.step`, never toward a reference image. Nobody
   in such a run opens `wish-references/` for a Component.
5. Run the Interfaces and the assembly round, and render `snap/iso.png` and
   `snap/signature.png` as in any Spark Make. When every Component carries,
   the assembly round's `visual.status` is `carried` (from
   `seed-approval`): the approval's review stands for this assembly, so it
   waits for no look and record no `--record-visual`. A round of the same
   sources and references as one you already recorded a visual pass on
   carries that pass the same way. Otherwise the look is `pending` as in
   any run, and its `detail` says why the approval's review did not carry.
   When `seed` has `review: "approved-proof"` and the seal recorded
   `assembly_renders` (ADR 0102, 2026-11-11 amendment), that pending look
   is beside the Approved Proof's own assembly, not a Reference Image: the
   packet has `basis: "approved-proof"` and each `compare-NN.png` shows the
   sealed `seed/approved/assembly/az<AZ>_el<EL>.png` beside the model at
   that camera. Record it with `matches_approved` (never
   `matches_reference`) and differences `{feature, approved, model,
   decision, reason}`. The host refuses a look in such a run that was
   taken against the references.
   With a seal of schema 4 (ADR 0103) every `wish-references/` image, and
   every Guide Image, is itself a render of the approved Proof; the AI
   drawings stay out of the run. Both looks show those sealed images on the
   approved side, in the same packets and answers.
6. Carry the assembly review instead of the blind review: `make_round
   <cad-project> --carry-assembly-review --concept-sha256 <Invented concept
   hash>`. It writes `snap/SIGNATURE-REVIEW.json` from the sealed
   `CRITIC.json`; never edit it. It carries when every Component is locked
   exact, locked within `proof_diff` tolerance, or changed and locked by an
   agreeing Component Review (the partial carry): the critic's verdict
   stands for the approved Components and the review names each changed one
   with its basis. It exits 1 when a Component has none of these (an open
   round, a Component Acceptance): then run the blind review as in make.md.
   A moving toy still needs its motion review, from a critic of its own.
7. Run `--full` as in any Spark Make. On a round whose look is carried,
   run `--full` alone, with no `--record-visual`.

## A locked Component a check fails

When final verification or another deterministic check fails a locked
Component for something no render shows (an invalid or self-intersecting
solid, a print stance off the bed, a gate), unlock it with the check's own
words, never as a visual finding:

```
make_round <cad-project> --component part_<id>.step.py --record-unlock UNLOCK.json
```

with `UNLOCK.json` `{"assembly_round": N, "verification": {"log":
"measure/...", "quote": "..."}, "reason": "..."}`: `log` is the file under
`measure/` the check wrote (the round's `verify.log`,
`measure/verification-pipeline.md`), and `quote` its words verbatim, naming
the Component. Then spawn its Component Worker. A repair within `proof_diff`
tolerance relocks on the approval with no review.

If a final verification is killed by a signal (`killed_by` in the round
summary, exit -9), no gate failed: rerun the same `--record-visual FEEDBACK
--full` on that round when the machine has memory free. It reruns only the
verifier. Never install another Python or toolchain for it. Before any second
final verification, write in `MAKE-NOTES.md` which row stopped the first and
why.

## Rules

- Never rule on shape: the approval decided it. Do not edit an approved
  Component to improve it.
- Work only inside the run root. Never read or run the Workshop source
  checkout, and never install a Python, a package or a toolchain from the
  network: the run's tools are the ones it was given. The guard refuses
  both and the host reports each attempt.
- A Contract Contradiction is a need, as in any run.
- Never write under `seed/`.
- Before it accepts Make, the host diffs every delivered STEP against
  `seed/approved/` and reports every deviation. It refuses a carried
  assembly review whose bases do not cover a deviation it measured: one
  over tolerance needs a Component Review. Under `review:
  "approved-proof"` it also refuses a deviation whose Component Review was
  not taken on its round's approved-proof packet.
