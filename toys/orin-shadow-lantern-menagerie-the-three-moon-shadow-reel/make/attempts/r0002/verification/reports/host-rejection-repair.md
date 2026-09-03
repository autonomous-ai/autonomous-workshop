# Host CAD gate rejection repair

- Current Make subject: `16aee19a31ed4427acee5149e5f45b87fcfbe013feb183d2d678ba6ba4d58226`
- Authoritative rejection: `13f513a6f2a65ef7b9677c26abe35c932040da0ceaee67b6b544274e56d55619`
- Failure code: `declared-cad-output-changed`
- Rejected primary STEP SHA-256: `5683d57d030083eca4df969f4888e7cfad8aad892344b19fb5577634862c400f`
- Repaired primary STEP SHA-256: `f58a818f8b91e75b6708c3bd50b0b7b0e78cfec4c027fc1c767c760ef899e04f`

## Exact failure addressed

The host's isolated fresh verifier stopped when project-local
`measure/check_fit.py` imported `lantern_menagerie_lib.py`, whose `import
cadfits` could not resolve outside the source skill tree. The CAD project now
contains `cadfits.py` with the exact fit classes and derivation API used by the
model. Its SHA-256 is
`08ea3b1f26b6e57cf9e0185c9c26d9c7bb15477e7adfea1130d937b2b77040b9`;
the referenced skill-source implementation SHA-256 is recorded in that file.

The repaired project was copied without generated `__cadgen__` cache files and
run through the host-equivalent command:

```text
verify_project <isolated-cad-project> --fresh --exports --strict-fit
```

The complete 22-step workflow passed in 97.78 seconds. In particular, the
direct isolated `measure/check_fit.py` hook returned 0; specification, both
motion sweeps, STEP validation, assembly interference, part mesh, print-bed,
and thickness checks also returned 0. The exact generated report is
`verification-pipeline.md`.

## Exact-output determinism

The four printable part STEP and STL files remained byte-identical to the
prior proposal. The assembly's prior presentation colours were removed from
the source-level STEP assembly because OpenCascade emitted presentation
entities in varying order across clean processes. Two independent cache-free
project copies then generated the same assembly SHA-256:

```text
f58a818f8b91e75b6708c3bd50b0b7b0e78cfec4c027fc1c767c760ef899e04f
f58a818f8b91e75b6708c3bd50b0b7b0e78cfec4c027fc1c767c760ef899e04f
```

The final full isolated workflow generated that same hash. Presentation colour
remains in the inspected deterministic PNG render, while the primary STEP is
byte-stable. These are digital checks only and do not add any physical claims.
