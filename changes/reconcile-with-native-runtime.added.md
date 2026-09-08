- Complete the native-runtime reconciliation: ABO is a declarative Inventor
  bundle (now manifest schema v8) instead of Python capabilities, and every
  Inventor's `<id>-inventor/SKILL.md` and the `autonomous-workshop` workflow
  skill were rewritten for the native session. The separate Concept stage
  that landed with this work (commit 187ac3b3) was bypassed the next day
  (commit ba513aba) and never entered a current route; concept work belongs to
  Invent (Forge and Quest) or to Spark Make, sealed as Invented JSON with no
  concept renders and no second image-provider credential.
- **Materialized instruction bytes changed**: runs parked mid-flight before
  this change must be restarted rather than resumed; resume fails closed on
  the materialized-instruction-hash mismatch by design.
