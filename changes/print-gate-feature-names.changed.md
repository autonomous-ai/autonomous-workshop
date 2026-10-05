- Print gates name the failing feature and blunt free edges are a rule
  (issue #82). `check_thickness` and `check_overhang` now report, for each
  failing region, the nearest print-details feature (its kind, name and the
  line that made it), else the nearest B-rep face, with its distance to the
  limit: how far a wall is under the minimum wall, how far an overhang is
  past the slope and ledge limits. Failing regions are always listed first.
  Thresholds and verdicts are unchanged.
- An open tessellation is no longer refused with "fix the solid in the
  generator". An invalid B-rep fails with its bad faces and their locations;
  a valid one is re-tessellated once at a quarter of the deviation and
  measured if that closes it; one that stays open is `UNMEASURABLE MESH`
  (exit 4), a separate verdict that is not a print failure and never passes
  a round. `check_mesh`, which final verification runs before the other two,
  reads the same mesh, so a part a component round measured after the finer
  retry is not refused at the end; `verify_project` still counts any nonzero
  exit, `UNMEASURABLE MESH` included, as a failed mesh gate.
- print-details tags every feature it makes in `PRINT_DETAIL_TAGS` and gains
  `bore` (a teardrop bore through a wall, vault or pointed roof),
  `blunt_tip` (a point, chisel, keel or ridge cut back to a land one minimum
  wall across) and `rib_end` (a hand-built rib or offset layer ended square,
  or ramped where it would look down). Each passes both gates in the
  library's self-check.
- `make_round` lists each failing feature on its `wall`/`over` lines, records
  a **Repeated Print Defect** (the same feature failing a part's previous
  round) under `repeated_print_defects` with an `again` line, and reports the
  `UNMEASURABLE` verdict. design-a-toy writes the blunt-free-edge rule into
  every contract; the Component Reviewer may no longer ask for a sharp tip
  or a chamfer thinner than one minimum wall; the Component Worker is told to
  blunt free edges and to repair the named feature.
- **Materialized instruction bytes changed** for new runs: the `cad`,
  `print-details` and `make-round` fingerprints and both Make role agents.
  Frozen runs keep the bytes they materialized.
