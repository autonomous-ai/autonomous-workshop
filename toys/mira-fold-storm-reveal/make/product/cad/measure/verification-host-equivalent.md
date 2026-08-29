# Host-equivalent CAD verification

- Invocation layout: temporary parent containing the CAD directory as
  `project`
- Command: `verify_project project --fresh --exports --strict-fit`
- Result: **PASS** (exit 0)
- Bed: 220 x 220 x 220 mm
- Nozzle: 0.4 mm

Passed phases:

1. project layout and all four explicit STEP generators;
2. strict bed fit for the three printable entries;
3. isolation-safe local fit derivations;
4. six declared motion conditions, including two blocked over-travel stops;
5. assembly and part refs plus kernel validation;
6. seated assembly interference inspection;
7. assembled GLB export;
8. STL export, mesh validation, and thickness checks for all three print
   targets.

The host-layout run regenerated the combined and part STEP/STL/GLB files
byte-identically. It also produced the path-canonical `project/...` thickness
reports now shipped in this project. The exact hashes and the diagnosis of the
prior `declared-cad-output-changed` rejection are recorded in
`measure/reproducibility.md`.

The variable `measure/verification-pipeline.md` file records the run timestamp,
durations, and command transcript. It is retained as execution evidence but is
not represented as a reproducible declared CAD output.

No physical print, printer-specific fit, retention, torque, wear, durability,
or human response is claimed.
