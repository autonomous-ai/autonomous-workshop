- **Two STEP-only leftovers still told a run to produce a mesh.** ADR 0062
  removed the mesh export but not every contract that named one.
  `make/schemas/cad-project.schema.json` still listed `stl_path` in each
  part's `required` set under `additionalProperties: false`, so the published
  CAD project contract mandated a per-part STL that the toolchain can no
  longer write; the field is gone and the document bumps to schema version 2
  (`$id` `cad-project-v2.json`). Nothing validates against this schema — it is
  discovered by `workshop schemas list` only — so no artifact changes shape.
- `.agents/product-run/.agents/skills/autonomous-workshop/references/make-playtest.md`
  kept six STL instructions: "actual STEP/STL", "assembled STEP/STL outputs",
  "root-level assembled STEP/STL files", "stable exported STEP/STL/GLB files",
  "exact STL poses", and `render_product` "on an exact verified STL". `SKILL.md`
  no longer routes to this reference, but every file under the product-run
  skill root is materialized into a run, so a native agent could still read it
  and go looking for `scripts/export`, which the vendored skill no longer
  ships. All six now say STEP.
- Three stale mentions in live code now name the format the host actually
  handles: `stage_proposal.py`'s cache-pruning docstring said "stable
  exported STEP/STL/GLB", Factory's occurrence guard raised "STEP path is
  unsafe" as "STL path is unsafe" while checking a `.step` suffix, and
  `fe_parts.key_parts` described its `part_meshes` as "sealed production STL
  bytes" when they are in-memory tessellations of sealed STEP. Behaviour is
  unchanged; one `ContractError` message differs.
- Deliberately unchanged: the `deep-economics-v1..v13` references and the
  v5-v9 proof prompts in `workflow/native_run.py` keep their `--stl` text
  because ADR 0062 froze them for runs already bound to those profiles, and
  the throwaway binary-STL staging bytes that `release/renders.py` and the
  Factory part keying hand to three.js are in-memory tessellations of sealed
  STEP, not a deliverable.
- **Materialized instruction bytes changed**: the `autonomous-workshop`
  fingerprint is new. Frozen runs keep their materialized reference; a parked
  run picks the corrected text up through `workshop resume --refresh-tools`.
