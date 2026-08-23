# Skill provenance

## cad + step-parts — shared from Workshop (vendored 2026-08-22)
- Canonical location: `../../../workshop/skills/{cad,step-parts}`; the paths in this
  folder are compatibility symlinks so Bob's existing build loop keeps working.
- Via: peterat617/text-to-3d @ f18aebe (the product lead's CAD toolchain —
  it built "Arrows Across The River", live on the Factory 08-21)
- Upstream: earthtojake/text-to-cad, cadgen 0.4.19, commit 16e90db, MIT
  (© 2026 Thompson Labs LLC — LICENSE in each skill dir)
- What Bob uses: build123d STEP-first authoring (`gen`), `check_mesh`
  (topology/envelope diagnostics per STL), `check_fit` (component-envelope and
  adjacency diagnostics),
  `verify_project`, `with_budget` (the 30-min run ledger), `cadfits`
  (derive the second half of a mate).
- Runtime: needs Python >= 3.10 + `pip install cadgen==0.4.19` in a venv
  (`.venv-cad`); the harness stays stdlib-3.9 — only the BUILD stage and
  the mesh half of the build gate shell into the venv, and both degrade
  honestly when it is absent (warning recorded, never a silent pass).
- Release caveat: these tools are not a printability certificate. They do not
  replace strict topology, slicer-backed DFM, calibrated fits, fail-closed
  motion/interference, or physical evidence. Workshop Stamps must bind those
  results before unattended release.
- Update discipline: bump the canonical Workshop snapshot from Peter's repo, never
  by hand edits; record the new commit in `workshop/skills/PROVENANCE.md`.
