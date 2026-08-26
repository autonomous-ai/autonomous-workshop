- Add Concept as a mandatory sixth run stage between Invent and Make
  (`Wish -> Match -> Invent -> Concept -> Make <-> Playtest -> Release ->
  Deliver`), gated by `concept.sealed-v1` and binding `NativeMade` to a
  required `concept_sha256`. Workshop now needs a second credential, at
  `$WORKSHOP_HOME/credentials/concept-images.env`, for the Concept
  image-drawing provider; a run without it parks at Concept with a concrete
  need instead of failing outright. ABO is rewritten as a declarative,
  schema-v7 Inventor bundle, replacing its Python capabilities.
- **Materialized instruction bytes changed**: the `autonomous-workshop`
  workflow skill gained `references/concept.md` and an edited `SKILL.md`, and
  every existing Inventor's `<id>-inventor/SKILL.md` gained a Concept
  stage-contribution bullet. Any run parked mid-flight before this change
  must be restarted rather than resumed — resume fails closed on the
  materialized-instruction-hash mismatch by design; this is expected and
  correct, not a bug.
