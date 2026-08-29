# Host-equivalent CAD verification

- Canonical CAD project: `cad_project/`
- Isolated invocation target: `project`
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

The complete pre/post inventory and exact persistent output hashes are in
`measure/reproducibility.md`. The submitted `cad_project/` deliberately omits
the disposable `__cadgen__/` tree and the runtime-specific
`measure/verification-pipeline.md`. A fresh verifier creates both only inside
its isolated temporary copy; every persistent file that existed before the
run remains byte-identical afterward.

No physical print, printer-specific fit, retention, torque, wear, durability,
or human response is claimed.
