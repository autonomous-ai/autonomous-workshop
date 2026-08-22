# Skill provenance

## cad + step-parts — vendored 2026-08-22
- Via: peterat617/text-to-3d @ f18aebe (the product lead's CAD toolchain —
  it built "Arrows Across The River", live on the Factory 08-21)
- Upstream: earthtojake/text-to-cad, cadgen 0.4.19, commit 16e90db, MIT
  (© 2026 Thompson Labs LLC — LICENSE in each skill dir)
- What Bob uses: build123d STEP-first authoring (`gen`), `check_mesh`
  (watertight/bed/overhang per STL), `check_fit` (bed packing),
  `verify_project`, `with_budget` (the 30-min run ledger), `cadfits`
  (derive the second half of a mate).
- Runtime: needs Python >= 3.10 + `pip install cadgen==0.4.19` in a venv
  (`.venv-cad`); the harness stays stdlib-3.9 — only the BUILD stage and
  the mesh half of the build gate shell into the venv, and both degrade
  honestly when it is absent (warning recorded, never a silent pass).
- Update discipline: bump by re-vendoring from Peter's repo, never by hand
  edits; record the new commit here.
