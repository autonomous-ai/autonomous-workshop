# Isolated CAD gate repair

- Stage subject: `9d0a62ab5e61485d61840d3ddc69641b3b2e983d8d73f5736ce252186137be4f`
- Rejected failure: `ModuleNotFoundError: No module named 'cadfits'` while the
  host ran `measure/check_fit.py` from an isolated project copy.
- Repair: removed both audits' workspace-relative path traversal and added a
  project-contained compatibility fallback. Normal CAD launchers still use the
  canonical Workshop `cadfits` module.
- Canonical compatibility target SHA-256:
  `f69cb9f34a6c78714827a7276e005dae0bf2f7a01dd30cbbce49541fb524f3fb`.
- Fallback source SHA-256:
  `df4ae9bd859156bea225a9265e0e9294abca6cffe4a6bf7809c3f7e5dbb673c9`.
- Repaired `moon_relay_lib.py` SHA-256:
  `59975a3b57ee51d8f21f9a2879cd1b48d5cbe8b0595866ca1378233f2f747dc2`.
- Repaired `measure/check_fit.py` SHA-256:
  `2af403524397158f7848bd7975c9a897095f684931a3e8b12669833ea27126cf`.
- Repaired `measure/check_spec.py` SHA-256:
  `867312852f061449990f98482b61105e0b5b6751aaaa9cdaa4370076f5b17f77`.

## Host-equivalent proof

A fresh copy of only `cad/moon_relay` was placed at a different path and run
through `verify_project <copied-project> --fresh --exports --strict-fit`.
Result: **PASS** (exit 0). The relocated `check_fit.py` and `check_spec.py`
both returned exit 0; the complete pipeline also passed generation, strict
print fit, motion, STEP validation, interference, STL mesh, and thickness
checks. The generated isolated pipeline report had SHA-256
`6c4cb71ea7882fa817a438f065d40630432162d1d55cc9cee2d713e01d5fa7ef`.

The same complete command was then run against the canonical product project
and passed. Its report is `measure/verification-pipeline.md`.

## Geometry preservation

The repair changes dependency resolution only. All three regenerated printable
part STEP hashes and all four STL hashes remain identical to the rejected
proposal. An `inspect diff` between the declared `assembled.step` and the
regenerated project assembly reports `topologyChanged=false`,
`geometryChanged=false`, and `bboxChanged=false`; both have three shapes,
97 faces, 240 edges, and bounds 92 × 54 × 25 mm.

This is digital evidence only. It does not claim a successful print or
physical fit.
