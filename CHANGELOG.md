# Changelog

Notable user-visible, contributor-visible, compatibility, schema, skill, state,
and security changes are recorded here. This project follows the structure of
Keep a Changelog and uses semantic versioning for released distributions.

## Unreleased

### Added

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
