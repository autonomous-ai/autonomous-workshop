# ADR 0088: Catch mesh validity, interference and insertion before assembly

- Status: Accepted; implemented and deterministically tested, with the
  interference step also run against real build123d parts; not yet
  validated by a live run
- Date: 2026-10-07
- Issue: #108
- Amends: ADR 0082 decision 5 (what a Coupled Interface check runs) and ADR
  0063's component-round gate list (`check_mesh` joins `check_thickness` and
  `check_overhang`)
- Relates to: ADR 0081 (unlocks), ADR 0082 decision 4 (Keep-out Envelopes,
  unchanged)

## Context

In Broken God attempt 18 three print-readiness failures surfaced only at
assembly rounds or final verification, each costing an assembly round (about
an hour plus repairs): a staff that could not be inserted into its fist
(r0008), an arm that interfered with the wing (r0010) and non-manifold edges
on two parts (r0012). Each belonged to one Component or one Interface.

## Decision

1. **Mesh validity in every round.** `make_round` runs `check_mesh` on every
   part it builds, beside `check_thickness` and `check_overhang`, against the
   project's declared `--bed` or the final verifier's default. It reads the
   round's kept B-rep like the other gates. A failure (an invalid solid, open
   or non-manifold edges, flipped winding, the bed) fails the round's checks
   like a print gate, so a component round is not rendered. `check_mesh`
   now names each non-manifold edge (`[edge ]` rows, up to eight), and the
   round keeps them as `print.<role>.mesh.edges`, the repair input. A
   recorded print pass without a mesh verdict is measured again. The Shared
   Helper samples keep their two gates.
2. **Interference and insertion in the Coupled Interface check.**
   `make_round --interface <id>` places the Interface's locked Components as
   before and runs, in order: `inspect interfere` on the generated entry
   (a clash stops the check before any motion sweep), then one
   `check_motion` run of the pose-table condition together with the
   insertion paths: every `linear_motion_collision`,
   `rotation_motion_collision`, `clear_path_proxy` or `assembly_sequence`
   in `measure/motion.json` whose parts are all this Interface's Components,
   named by their Interface references. A path that names any other part
   stays for assembly. The summary records `interference` and `insertion`.
   A clash, a collision or a blocked insertion path unlocks the yielding
   Component exactly as a motion failure did, with the clash list and the
   interference log's hash, or the failing conditions and the motion log's
   hash, as its evidence.
3. **Separable Interfaces are unchanged.** Each side's component round
   already checks interference and the insertion path against the Keep-out
   Envelope, one shape per declared pose (ADR 0082 decision 4).
4. **The last word stays where it was.** Assembly rounds and final
   verification still run `check_mesh`, assembly interference and the whole
   motion manifest; they should now rarely be the first to fail.

## Consequences

- A non-manifold part costs one component round, not an assembly round, and
  its worker sees where the edge is.
- A Coupled Interface check costs one `inspect interfere` more; its motion
  sweep runs only on placed Components that do not already clash.
- An insertion path joins an interface check only when the Manager names its
  parts by Interface reference in `measure/motion.json`; one that names an
  assembly label instead is checked only at assembly.

## Compatibility

Runs created before this change keep their materialized `make_round`,
`check_mesh` and instructions, including on resume. A contract without
Interfaces gains only the mesh gate.
