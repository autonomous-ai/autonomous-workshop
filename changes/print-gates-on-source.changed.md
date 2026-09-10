- Resynced the vendored CAD skills to `autonomous-product-to-cad` `673a9fa`
  and adopted the restoration in full: **the print gates are back, fed from
  source instead of an exported mesh.** `check_mesh`, `check_overhang`,
  `check_thickness`, `meshlib`, `cadprint` and `repair_mesh` return, each
  taking one printable `*.step.py` entry; new `printlib.py` tessellates the
  B-rep in the gate at 0.02 mm deviation and `verify_project` regains a
  `--print-gates` sweep with `--nozzle`, `--overhang-angle` and
  `--skip-thickness`, running last after the image-derived render and
  likeness. No mesh file is read or written anywhere: ADR 0062's export half
  stands and STEP remains the only geometry Workshop writes, seals or ships.
  The host CAD gate has two claim-bound tiers again — root product status
  `full-with-thickness` with `print_ready_claim: true`, or
  `digitally-verified-not-print-ready` with `false` — and reruns the verifier
  in the tier that pair names, so a half-declared or unreproducible claim is
  refused rather than downgraded; the full tier's command carries
  `--print-gates --nozzle 0.4` and never `--skip-thickness`. Make, Playtest
  and Release require print-ready evidence exactly where they did before ADR
  0062. `make-round` gates every part that builds and reports wall and overhang
  verdicts beside the build verdict, reusing a passing pair only when both
  gates passed and their tool logs still hash true. The signature review binds
  its supporting reports through `print_gate_sha256s` (schema 7 -> 8), and the
  per-part `measure/thickness-<role>.md` and `measure/overhang-<role>.md`
  reports are sealed evidence compared exactly apart from their directory
  prefix. The legacy `--exports` full-tier replay path stays retired. Frozen
  runs keep their materialized skills and `deep-economics-v1..v14`; new runs
  freeze `deep-economics-v15`. See ADR 0063.
