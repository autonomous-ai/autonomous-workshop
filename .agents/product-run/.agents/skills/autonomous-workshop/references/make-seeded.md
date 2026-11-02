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
5. Run the Interfaces and the assembly round, and render `snap/iso.png` and
   `snap/signature.png` as in any Spark Make.
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
7. Run `--full` as in any Spark Make.

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
verifier. Never install another Python or toolchain for it.

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
  over tolerance needs a Component Review.
