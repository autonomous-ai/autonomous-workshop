# Seeded Make (ADR 0096)

Read this when run-root `MAKE-OPTIONS.json` has `seed`. The owner approved
this toy's shape in design. The read-only run-root `seed/` holds that
Approved Proof:

- its CAD project: `params.py`, `features/`, `part_<id>.step.py` and
  `samples/`;
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
5. Run the Interfaces, the assembly round and `--full` as in any Spark Make.

## Rules

- Never rule on shape: the approval decided it. Do not edit an approved
  Component to improve it.
- A Contract Contradiction is a need, as in any run.
- Never write under `seed/`.
- Before it accepts Make, the host diffs every delivered STEP against
  `seed/approved/` and reports every deviation.
