# Changelog

Notable user-visible, contributor-visible, compatibility, schema, skill, state,
and security changes are recorded here. This project follows the structure of
Keep a Changelog and uses semantic versioning for released distributions.

## Unreleased

### Fixed

- Two STEP-only leftovers no longer ask a run for a mesh. The published
  CAD project contract (`make/schemas/cad-project.schema.json`) required
  `stl_path` on every part under `additionalProperties: false`, mandating
  an export the toolchain removed in ADR 0062; the field is gone and the
  document is schema version 2 (`$id` `cad-project-v2.json`). Nothing
  validates against it, so no artifact changes shape. The orphaned
  `references/make-playtest.md`, still materialized into every run even
  though `SKILL.md` no longer routes to it, kept six STL instructions
  including `render_product` "on an exact verified STL"; all six say STEP.
  The frozen `deep-economics-v1..v13` references, the v5-v9 proof prompts,
  and the in-memory tessellation three.js and Factory part keying consume
  are unchanged. See ADR 0062.
- Daydream no longer universally rejects classic games, faithful reskins, or
  theme-led reinterpretations. Each Inventor's `TASTE.md` now defines the kind
  of originality it owns, while the existing catalog and notebook checks still
  reject repeats of prior Workshop work.
- The full CAD-gate tier's command names the overhang angle beside the nozzle
  (`--print-gates --nozzle 0.4 --overhang-angle 45`), so the receipt records
  both thresholds the print-ready claim was measured against instead of
  inheriting `verify_project`'s own default for one of them. Report bytes are
  unchanged. See ADR 0063.
- A failed CAD gate no longer banks the wrong anti-pattern in the shared game
  vault. The host's finding embeds the tier, and the full tier is spelled
  `full-with-thickness`, so the keyword classifier filed every full-tier
  rejection under `underbuilt-shell`; classification now reads the verifier's
  own tail (`classify_text`) while the banked finding keeps the tier. A print
  gate's `RESULT:` line outranks the keyword sweep, and the host CAD-gate codes
  that never refused the geometry — `cad-not-print-ready`,
  `sealed-product-changed`, `verifier-timeout`, `verifier-output-limit` — are
  protocol slips that teach the vault nothing.
- `NativeCadGateEvidence`'s field defaults paired the full tier with the lower
  tier's verifier mode, a combination no policy accepts; the default is now the
  tier that claims nothing.

### Added

- Codex products accept `--max-tokens` (default 10,000,000), persisted across
  stages, native children and resumes; `resume --max-tokens N` changes the
  total cap without resetting usage. Normal time/turn limits are superseded
  for marked runs, with engineering and publication gates unchanged.
- `workshop start`, `daydream`, and `wish` now expose `--agent`, `--model`,
  and model `--effort`; new runs freeze those choices in `MANAGER.json`.
  Codex accepts Astra and Sol aliases, while Claude Code accepts the Opus 5
  alias.
- The host CAD gate compares declared STEP files by their entity graph
  (`workshop.make.step_canonical`) instead of by bytes: Open CASCADE emits
  presentation-style entities in pointer order, so a faithful fresh re-export
  of a coloured assembly differed byte-for-byte on every run and every Make
  proposal was rejected as `declared-cad-output-changed`. Geometry, colour,
  wiring, header, and mode changes still fail closed.
- `workshop wish --max-rounds N` freezes the Invent-Make-Playtest round
  budget (1-100, default 4) for a run; the Make-Playtest reference now names
  the two host CAD gate preflight facts (one combined entry, vendored
  helpers) that otherwise cost a Make session each.
- Machine-readable component ownership, CODEOWNERS, maintainer governance,
  security and conduct policies, support guidance, and architecture decisions
  for the component-oriented Workshop layout.
- Complete contract tests on Python 3.11 and 3.14, plus installed-wheel
  acceptance and byte-identical source-distribution rebuild verification on
  Python 3.14.
- Locked, subtractive top-groove geometry for printable box parts, including
  bounded failure diagnostics when Make cannot reach its release target.

### Changed

- New Codex runs default to Astra at medium effort. Explicit model selections
  and the exact model frozen into existing runs are unchanged.
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

- Rename the public lifecycle selector from `--effort` to `--workflow` and
  the native runtime selector from `--manager` to `--agent`; JSON run receipts
  now report `workflow`, `agent`, `model`, and model `effort`.
- Rename the distribution to `autonomous-workshop`, the Python package to
  `workshop`, and the internal command application to the sibling `cli`
  package.
- Organize source, contracts, tests, schemas, and Make skills by the Workshop
  components they belong to.
- Make component package roots the canonical Python APIs, keep the root import
  surface as a behavior-free 0.x facade, and enforce an acyclic module-load
  graph plus one-way provider boundaries in architecture tests.
- Move durable receipt and publication contracts, including their byte-identical
  schemas, from Integrations to Runtime; external adapters now implement ports
  declared by Make, Release, Deliver, and Runtime.
- Compose default workers only in `workshop.bootstrap`; bundled and generated
  inventor profiles call that application boundary explicitly.
- Materialize an installed inventor catalog into a content-addressed,
  user-writable Workshop home before a Wish creates durable state.

### Removed

- Remove the legacy `inventor_workshop`, `inventor_core`, and
  `inventor_foundation` Python namespaces and the duplicate command alias.
- Remove the unused Workshop 0.2 `workshop.workflow.creation` forwarding
  module; Make's public API is owned by `workshop.make`.

### Fixed

- Make CAD review resolves visibility at each pixel, preventing rear surfaces
  from painting over nearer parts when whole-triangle depth ordering is wrong.
- Make motion checks intersect the actual solids of nested assemblies and
  include every ancestor placement when resolving a named part. Grouped
  mechanisms no longer appear collision-free merely because the assembly
  container has no own topology or a child was checked in its local frame.
- Make CAD support checks use the preceding layer's material and actual bridge
  spans. This catches cantilevers and thin ledges, preserves short rotated
  bridges and supported collars, and keeps decisions stable when equivalent STL
  triangle records or cyclic vertex orders change.
- Make final and print-preflight verification refuse a project whose README or
  spec names a `<name>.step.py` entry that does not exist, so a delivered file
  map or rebuild command cannot cite a removed entry and fail on first use.
- Make motion checks judge Boolean volume agreement within a band that scales
  with the operand volumes instead of a fixed 0.000001 mm3, arbitrate a
  disagreeing or unavailable union with both differences, and otherwise accept
  a pose only when every formulation agrees on the collision verdict, so
  accepted parts of thousands of mm3 and interpenetrating thin shells are no
  longer reported inconclusive; split verdicts still fail closed.
- Make motion drive-evidence checks place each mover once per sample and run
  the nominal contact query on the faces that can realize a contact, so a
  published product's coupled cycle no longer takes minutes per condition;
  witnesses, thresholds and fail-closed behaviour are unchanged.

- Allow generated inventor commands to parse run options and positional Wish
  text in either order.
- Preserve an Inventor's ordered two-shore token rules, token order, and
  per-token sweep marks through Make and the pinned 1,000-game Playtest instead
  of silently reducing the design to generic shared-supply take-away.
- Reject invented-game simulator contracts that the pinned Playtest cannot
  replay before they reach Make, and keep Make's reward gate scoped to concept
  fidelity and verified geometry rather than future Playtest evidence.
- Run long-form structured Invent and Make creators at bounded low reasoning
  and allow their actions up to twenty minutes while retaining the Workshop's
  sixty-minute outer worker bound.

## Change fragments

Each pull request with a user-visible, contributor-visible, operational, or
compatibility effect adds one file under `changes/`. See
[`changes/README.md`](changes/README.md) for naming and content. Release
preparation groups those fragments under `Added`, `Changed`, `Deprecated`,
`Removed`, `Fixed`, or `Security`, then removes the consumed files.

Documentation typo fixes, tests with no behavior change, and mechanical changes
may select `No changelog required` in the pull request template.

Release entries must distinguish:

- Python API compatibility from durable-data compatibility;
- a historical reader from a newly produced format;
- offline capability from live provider or physical readiness;
- package-resource moves from intentional skill or schema byte changes.
