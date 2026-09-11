# Shared skill provenance

## Early publication-size accounting (2026-09-11)

Mixed-material guidance now explains the existing 95 MiB per-file, 512 MiB
sealed-tree and 50 MiB stored-ZIP carrier limits before final independent
review. The current carrier preserves every declared public path and adds
root STEP and hero aliases, so public bytes plus those two asset sizes are a
necessary lower bound with metadata/header headroom. This advisory accounting
neither builds a host pack nor certifies acceptance. No limit, format, identity,
privacy, engineering or lifecycle gate changed. Frozen runs receive the text
through the ordinary explicit tool refresh.

## Stateless renderer tessellation extraction (2026-09-11)

Both renderers now extract arrays directly from the same native triangulations
using indexed triangle access and transformed native points. This removes OCP
array-iterator overhead and temporary build123d Vector wrappers. Meshing calls,
tolerances, face order, orientation, placement, vertex offsets, colors and PNG
output remain unchanged. There is no additional cache, sampling, omitted face,
geometry substitution or changed timeout. Missing native triangulation still
raises the original failure instead of returning partial geometry.

Tests compare exact arrays and serialized PNG bytes against the installed
Shape.tessellate implementation on curves, nested transforms, repeated and
independent topology, reversed faces, alpha and imported STEP. Further tests
preserve native failures and source identity. Synthetic timing measurements
show lower extraction cost; they are not a measured Waterloo speedup. Frozen
runs receive the helper and renderer changes only through normal tool refresh.

## Geometry instance bounds for mixed assemblies (2026-09-11)

The mixed-material validator separates repeated geometry from manufacturing
definitions: geometry lists allow 4,096 items and the optional hierarchy allows
8,192 total nodes. Components, stock, consumables, tools, assembly steps, public
assets and other lists retain their 512-item bound. Existing JSON/file byte
bounds, hierarchy depth, uniqueness, complete coverage, quantity, source hashes
and private/public ownership checks remain intact. All limits apply together.

Synthetic tests cover large scenes with a small BOM, the exact geometry and
hierarchy boundaries, unchanged nongeometry bounds and malformed coverage.
No product CAD is executed by this validator. Frozen runs require the ordinary
explicit tool refresh to receive the corrected limits.

## Printed units with colored display regions (2026-09-11)

The mixed-material manifest's optional physical-unit grouping now also supports
`3d-print` components. Each grouped printed definition binds exactly one
explicit printable `part_<role>.step.py` and its generated sibling STEP through
its own private file hashes and `production_part` paths. Quantity counts exact
subassembly IDs; their descendant leaves still require unique complete coverage.
Purchased-unit behavior, source ownership, print selection and public projection
remain intact. Other fabrication processes retain the original leaf-count rule.

This makes CAD's existing disjoint color-region representation compatible with
the internal BOM. Paint is a consumable and need not add tiny coating solids.
The structural validator neither executes CAD nor proves region equivalence;
native Make retains geometry, interference, nozzle and visual verification.
Regression fixtures cannot execute their synthetic CAD and cover repetition,
unsafe or stale bindings, extra sources, wrong declarations, ownership, hierarchy
and privacy. Frozen products need an explicit normal host tool refresh to use
the new optional binding; source changes do not alter a running product.

## Review-render phase diagnostics (2026-09-11)

`render_review` reports flushed CLI-only phase starts and completions on stderr
for source loading/building, tessellation, and each view's raster/save. Completed
tessellation includes occurrence, vertex and triangle counts. Existing Make
timeout logs retain the last started phase, while failed phases propagate their
original exception without a false completion. Imported library calls stay quiet;
stdout paths, exact PNG bytes, geometry, tolerances and timeouts are unchanged.
Regression coverage exercises real timeout capture and each failure boundary.
The active Waterloo render completed before this change and retains its frozen
tool bytes; no restart or refresh is needed solely for diagnostics.

## Compatible signature-review verification (2026-09-11)

`verify_project` now consumes the schema-8 review already required by ADR 0063
and Make's finalizer. Its exact field set includes `print_gate_sha256s`; cited
thickness and overhang reports must be bounded regular in-project files whose
bytes match the reviewed digests and contain their passing result. Empty
bindings retain the existing no-claim case. Canonical JSON, image identity,
review findings and the final source-built print gates remain required.

This repairs an incompatible schema-7 verifier that could not consume any
current valid Make review. It does not change printable-source selection,
nozzle, measurements, thresholds, review allowance or the final gate sweep.
Regression fixtures exercise the same bytes against both validators and reject
stale/missing reports, changed settings, malformed identities, unsafe paths and
changed images. Existing frozen runs require an explicit host tool refresh.

## Exact assembly placement and complete print reports (2026-09-11)

Both renderers share `render_assembly.py` to flatten colored occurrences using
the same OCCT placement operation as before. Fresh detached shape wrappers keep
each leaf's complete topology, native location, orientation and effective
appearance without recursively copying Python assembly parents and siblings.
No tessellation tolerance, triangle selection, raster behavior, detail or tool
timeout changes. Synthetic regression checks compare exact triangle/color
arrays and product/review PNG pixels, including nested transforms, bare
compounds, inherited alpha, repeated leaves and source immutability.

The thickness and overhang tools now include their already computed stdout
`RESULT` verdict in the Markdown report too. Measurements, check statuses,
thresholds and exit codes are unchanged. This supplies the actual result text
that the existing signature-review contract requires in the exact cited report
bytes. Source updates do not change frozen runs; an explicit normal host tool
refresh is required before a stopped run uses these corrections.

## Workshop mixed-materials skill (2026-09-10)

`mixed-materials` is implemented locally by Workshop, not vendored from the CAD
repository. Its exact tree is bound in `LOCK.json`; the new entry has no upstream
source commit. The standard-library tool validates internal manufacturing
references and public file selection without running CAD. Its schema and
standalone CLI are materialized into new runs alongside the skill.

The local `make-round` adaptation uses CAD's existing printable-source discovery
for its print subset, retains building and visually inspecting nonprinted parts,
and includes source hashes in print-result reuse. An all-nonprinted project keeps
a geometry-only final verification and makes no print-ready claim. See ADR 0064.
The local Make-round tool card documents that subset explicitly. CAD's
step-generation reference distinguishes Spark's real Markdown verification
report from older host-owned JSON evidence; it no longer asks Spark agents to
invent a second verification artifact. These are instruction corrections;
frozen running products keep their materialized text until an explicit refresh.

## Motion progress diagnostics (2026-09-10)

`cad/scripts/check_motion --json` emits flushed, bounded progress on stderr
while preserving its final stdout result document. Assembly loading and each
condition have start/completion diagnostics; sweep and drive phases report
their current sample at most once per 30 seconds within a phase, with at most
32 sample updates per condition. Scoped progress restores the parent across
assembly-sequence and retention checks. Imported tool functions remain quiet
unless diagnostics are explicitly enabled.

The existing Make runner retains these stderr bytes on timeout, so a
900-second failure can identify active work instead of leaving an empty log.
Progress never supplies gate evidence, changes a threshold or verdict, retries
geometry, or changes the final JSON schema. Regression coverage includes real
subprocess timeout capture, unchanged completed results, nested conditions,
throttling and bounds. No live pilot files or frozen tools are changed.

## Exact placed material reuse (2026-09-11)

`check_motion` reuses successful grouped-material normalization within one
immutable outer condition. A bounded 32-entry LRU avoids fusing a fixed
multipart obstacle again for each sample or a mover again for each obstacle.
Every cache hit requires identical OCCT topology, location and orientation via
`IsEqual`; independent TopoDS key values preserve the original placement.
Unlike the validity cache, material reuse never removes or changes a placement.
Pose-sensitive Boolean failures still run at every new pose and errors are not
cached. Nested conditions share the bounded scope, discarded on return or error.

Collision operations, samples, consistency checks, thresholds, results and exit
behavior are unchanged. Synthetic regressions compare complete results and
sampled pairs against uncached normalization, including first collision and
overlapping-child material volume; they also cover identity collisions, key
mutation, failure, scope cleanup and eviction. This is an implementation cost
reduction, not new physical evidence or a repair for invalid geometry. Frozen
tools and live products are not changed by the source update.

## Complete-product authored colors (2026-09-10)

Workshop's `cad/scripts/render_product` now descends to leaf occurrences with
accumulated parent placements, matching the existing `render_review` convention.
It preserves leaf or inherited STEP colors, converting linear RGB to PNG sRGB,
and uses the existing base/accent palette only for uncolored triangles. Color
rows remain aligned during presentation poses and triangle sampling. Product,
viewpoint and exact-state sheets carry the same authored appearance.

Exact-state difference checks retain their geometry-based appearance comparison:
recoloring otherwise unchanged geometry cannot pass as a new operating state.
Regression coverage includes nested transforms, source immutability, real STEP
round trips, color inheritance/encoding, uncolored fallback, malformed color
arrays and CLI hero/motion/state output. This fixes presentation; it adds no
host renderer, geometry format, texture model or material qualification. Frozen
runs retain their existing materialized renderer bytes.

## Complete-product schematic transparency (2026-09-10)

Workshop's `cad/scripts/render_product` retains authored or inherited alpha in
an aligned RGBA scene array. Existing RGB callers remain supported and opaque
renders retain their existing pixels. Partial alpha uses source-over blending
in the existing far-to-near triangle order; zero-alpha faces contribute no
fill, outline or shadow, and transparent faces receive no opaque outline.
The alpha-only raster path uses pixel centres and half-open shared edges in
bounded row strips, preventing a coplanar triangulation seam from blending
twice while preserving separate transparent layers.
Geometry and STEP bytes are unchanged, including exact full-model framing.

A synthetic clear-sheet/solid audit demonstrated that normal cadgen STEP
export/import retained alpha while the previous product rasterizer discarded
it. Regression tests cover real STEP front/behind placement, reversed child
order, inherited alpha, zero-alpha disappearance, opaque RGB compatibility,
sampling/pose/state alignment and invalid alpha. This is schematic transparency,
not refraction, reflection or physical transmission evidence. Mean triangle
depth remains approximate for crossing surfaces. No runtime dependency or host
renderer was added; frozen pilots keep their original tool bytes.

## Per-pixel opaque depth for product views (2026-09-10)

Two valid, nonintersecting STEP plates separated by 0.5 mm reproduced a severe
Product painter-order error in only 24 triangles: the lower plate covered
almost half of the nearer plate's top. `render_product` now adapts the bounded
orthographic barycentric depth interpolation already used by `render_review`.
It completes an opaque depth buffer, then clips transparent fragments against
that buffer without letting transparency write depth. Shared edges use the
existing half-open coverage rule so one translucent surface blends once.

Camera, placement, palette, shading, shadow, silhouette outline, exact STEP
inputs and geometry/review gates remain unchanged. Pixel-centre coverage can
differ from the former inclusive polygon fill. Transparent-to-transparent
source-over order is still based on triangle mean depth and is approximate,
including some nonintersecting overlapping surfaces; this is not an optical
simulation. No dependencies or host rendering path were added.

Regression coverage includes real STEP round trips, separated stacked plates,
triangle order and subdivision, front/rear transparent clipping, interpolated
fragment depth, no transparent depth writes, coplanar seams, zero-alpha
disappearance, RGB/RGBA compatibility and complete large-scene coverage. The
private diagnostic fixture and rendered comparisons remain outside Git.
Frozen running products retain their materialized tool until explicitly refreshed.

## `cad`, `design-reference`, `electromechanical-integration`, `image-to-cad`, and `step-parts`

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `facbc582ceee2b73e655711afa112e9bf10d7592` (2026-09-10), resynced from
  `673a9fa595d3ddfda89ed9a34a8bceabb49bc0db` (2026-09-10),
  `39a63f73617d70a45473c984b46926c9d29bb9bd` (2026-09-10),
  `ec25343ea240c520074b66eee7b28e76bd91ee49` (2026-09-09) and
  `9e75609bb53bf880429353e57201995a4c0482e6` (2026-09-07).
- The third 2026-09-10 resync takes upstream's `cad/filament-palette` branch,
  which gives colour a source of truth. `cad/scripts/cadfilament.py` is new: the
  Bambu Lab PLA Lite palette (13 names with the hex published at
  3dfilamentprofiles.com, read 2026-09-10) and `filament(name, alpha)`, which
  converts through `cadgen.color.srgb` so the channels reach the renderer
  linear. A printed part takes a filament name; `cadgen.srgb()` keeps the
  colours that are deliberately not filament — a purchased component, a
  reference surface, a see-through datum. An unknown name raises with the whole
  list rather than resolving to the nearest colour, for the reason `cadfits`
  derives the second half of a mate instead of asserting it. Four reference
  files move with it: `cad/references/build123d-modeling.md` (**Colour** is
  three rules now and carries the table), `cad/references/parameters.md` (a
  `cadfilament` section beside `cadfits`), `cad/references/organic-lofts.md`
  (the per-region example rounds sampled hex to stock rather than passing raw
  `Color()` channels, which broke the linear-RGB rule two sections above it) and
  `image-to-cad/references/build123d-operations.md` (a spec names a filament per
  leaf, never a hex of its own).
- Nothing in the toolchain enforces the palette: it is a table a generator
  imports, not a gate. Geometry is untouched, and the STEP still carries linear
  RGB, which is what `workshop.make.cad.step_color` reads back and Release
  publishes. Workshop adopted the branch in full, with the two path adaptations
  it already applies to `cadfits` — the self-check line names
  `"$CAD_SKILL_ROOT/scripts/cadfilament.py"`, and the import note records that
  `verify_project` also supplies its materialized scripts directory when it
  launches local audits. Verified here: the self-check passes 16/16 in the
  Workshop environment, round-tripping all 13 colours back to their published
  hex.
- The second 2026-09-10 resync takes upstream's
  `cad/restore-print-gates-on-source` branch and its ordering follow-up, which
  **reverse the gate half of the removal below while keeping the export half
  reverted.** The two were removed together only because `check_mesh`,
  `check_overhang` and `check_thickness` each took an STL positional argument,
  so deleting the exporter left them with no subject. That coupling was an
  implementation detail: a mesh gate needs a mesh, not an artifact, and OCP
  tessellates the B-rep on demand. Upstream restores the three gates,
  `meshlib.py`, `cadprint.py` and `repair_mesh`, adds `printlib.py` (printable-
  entry discovery and tessellation at 0.02 mm deviation, measured within 0.03%
  of exact volume), and gives `verify_project` a `--print-gates` sweep with
  `--nozzle`, `--overhang-angle` and `--skip-thickness`. Each gate now takes one
  printable `*.step.py` entry. `repair_mesh` repairs in memory to name the
  defect class and the source fix; it writes nothing. STEP remains the only
  thing the toolchain writes, and no mesh file is read or written anywhere.
  The follow-up moves the sweep back to last in `_final`, after the
  image-derived render and likeness, where it ran before the removal.
- What upstream does **not** restore, and Workshop does not either: the old
  source-vs-artifact pair that caught a stale export. With no artifact there is
  nothing to go stale.
- Workshop adopted the restoration in full. Its consequences are recorded in
  ADR 0063: the host CAD gate has two tiers again, chosen by two agreeing
  hash-bound declarations — `full-with-thickness` with
  `final_pipeline.print_ready_claim: true`, or
  `digitally-verified-not-print-ready` with `false` — and the host reruns the
  verifier in the tier that pair names, so a claim the sealed project cannot
  reproduce is refused rather than downgraded. The full tier's command carries
  `--print-gates --nozzle 0.4`, never `--skip-thickness`, because skipping the
  wall gate forfeits the claim. Make, Playtest and Release require print-ready
  evidence again exactly where they did before ADR 0062. `make-round` gates every
  part that builds and reports wall and overhang verdicts beside the build
  verdict, reusing a passing pair only when both gates passed and the tool logs
  still hash to what was recorded. The signature review binds the reports that
  back its claim (schema 7 -> 8, `print_gate_sha256s`), and new runs freeze
  `deep-economics-v15`, which routes a failed print gate into a targeted repair
  the way v13 did before v14 dropped it.
- Workshop's verifier adaptation accepts that same schema-v8 review before its
  final geometry work and checks that `print_gate_sha256s` is a report-to-digest
  mapping. This keeps the vendored verifier's pre-geometry review guard aligned
  with the run-local Make finalizer; schema 7 remains historical evidence only.
- The **legacy full-tier replay path stays retired**. It would rerun a
  `final-fresh-exports-strict-fit` verifier, and `--exports` is still gone; the
  restored tier is a different command, so a pre-tier receipt cannot be replayed
  into it. `legacy_full_tier_compatibility` remains permanently false.
- Per-part gate reports are sealed evidence again, not volatile output. Both
  `measure/overhang-<role>.md` and `measure/thickness-<role>.md` embed the
  argument vector they were run with, so the host compares them exactly apart
  from the two path arguments' directory prefix; every measurement, option,
  check, region and line of prose stays byte-exact, and an unknown report format
  fails closed. This is stricter than the pre-ADR-0062 arrangement, which
  allowlisted the thickness reports as fully volatile.
- The 2026-09-10 resync takes upstream's `cad/drop-assembly-glb-export` branch,
  which is a single coherent capability removal: **STEP becomes the only
  format the toolchain writes.** Upstream deletes `scripts/export` (the whole
  CLI), `meshlib.py`, `cadprint.py`, `repair_mesh`, the `check_mesh`,
  `check_thickness` and `check_overhang` gates, cadgen's `_internal/stl.py`
  and `_internal/threemf.py`, `verify_project`'s `--exports` mode, and the
  `supported-exports.md`, `repair-loop.md` and `print-optimisation.md`
  references. `cad/SKILL.md` now states that a request for an STL, a 3MF, a
  GLB or any sliced mesh has no workflow, and that an output must never be
  called print-ready. Every non-deletion hunk in the four upstream commits is
  prose or validation following from that removal; there is no independent
  fix to take. `design-reference`, `electromechanical-integration` and
  `step-parts` are byte-identical to the previous snapshot, and `cadgen` stays
  at 0.4.19.
- Workshop adopted the removal in full rather than forking the mesh half, so
  this is a breaking product change and not a routine resync. Its consequences
  are recorded in ADR 0062: `render_product` and `motion_presentation.py`
  tessellate the exact STEP in memory instead of reading an STL; the
  Workshop-local `--print-preflight` mode and its
  `measure/print-preflight.md` record are gone, taking
  `print_preflight_sha256` out of the signature review (schema 6 -> 7);
  `make-round` reports a build verdict per part instead of a wall verdict; the
  host CAD gate collapses to the single
  `digitally-verified-not-print-ready` tier, retires the legacy full-tier
  replay path, and can no longer substantiate a print-ready claim at any
  stage; sealed products carry `parts/<name>.step` rather than
  `parts/<name>.stl` and no `assembled.stl`; and the Factory handoff ships
  exchange solids. Nothing in the toolchain measures a wall, a mesh or an
  overhang any more, so no Workshop stage may call a product printable.
- Rebasing the removal onto Workshop's later mesh work retired that work with
  its subject. The pre-review assembly screening of 2026-09-08 lived inside
  `--print-preflight` and goes with it; final verification still runs the same
  validity and 1.0 mm3 interference checks, only later. The `check_overhang`
  preceding-layer/bridge-span fix and its `mesh_support.py` helper measured a
  mesh that is no longer built. `motion_presentation.py` keeps the declared-pose
  constructor and byte reconciliation of ADR 0060, but its states are
  tessellated in memory and bound by hash instead of written as
  `measure/motion-states/state-*.stl`, which the sealed manifest would now
  reject. `make_round` keeps the strict `check_motion` reader, per-reference
  pose files and one-piece entry handling; the wall-evidence reuse it gained
  has no wall left to reuse.
- The reviewed snapshot includes the complete upstream trees for all five
  skills. `cad` includes the vendored `cadgen` 0.4.19 source, bought-part mount
  tooling, run-cost guidance, and the strengthened image-derived verification
  runner. The image workflow includes clipped-reference rejection, reference
  silhouette preparation, and stored-camera replay for lower-cost iteration.
- The 2026-09-09 resync takes upstream's compact-agent-loop and structured
  diagnostic work. The `cad` and `image-to-cad` instructions shed repeated
  context while retaining their gates; powered-only build-spec sections move
  into `build_spec_powered.md`; image measurement and likeness tools emit
  compact JSON; and `step-parts` returns a smaller ranked catalog payload.
  `cad/scripts/check_spec_format` is new and rejects untagged dimensions,
  unfilled template markers, scaffold project names, missing powered sections,
  one-direction motion claims, and a discounted likeness floor before geometry
  work begins. `verify_project` now aggregates independent cheap-preflight and
  per-printable export failures, records dependent skips explicitly, and
  hardens its report diagnostics. The three-way resync preserves Workshop's
  materialized-skill command paths, v8/v9 proof deferral, print-preflight and
  signature presentation path, restricted-run cache ownership, exact-state
  motion evidence, deterministic STEP headers, and alpha/tinted-subject image
  masks. `design-reference`, `electromechanical-integration`, the vendored
  `cadgen` 0.4.19 source, and both requirements files are unchanged from the
  previous snapshot.
- The 2026-09-07 resync takes upstream's single-commit fix that makes every
  verified run leave a `.step` behind. `cad`'s `verify_project` now passes
  `--write` unconditionally in quick mode, which previously built the combined
  entry, wrote the render package and wrote no CAD file at all, so a
  preview-only project was indistinguishable from one whose STEP write had
  failed. A new `--self-check` fixture holds `--write` in the planned quick-mode
  `gen` command, and `SKILL.md` step 7 plus the `--quick` help stop reading as
  permission to skip the write. `design-reference`,
  `electromechanical-integration`, `image-to-cad` and `step-parts` are
  byte-identical to the previous snapshot; `cadgen` stays at 0.4.19 and both
  `requirements.txt` files are unchanged. The upstream delta was three-way
  merged so Workshop's local `--print-preflight` mode, materialized-skill-root
  command shapes, and `SKILL.md` step 6 single-combined-entry rule survive
  intact; the only local reconciliation is the new "every mode writes STEP"
  runner note, which also names `--print-preflight` because this copy has that
  third mode and it already generates with `--write`.
- The 2026-09-03 resync takes upstream's build-direction and resolution work.
  `cad` gains two gates: `check_overhang`, which is the only thing in the
  toolchain that knows which way is up and splits down-facing surface into
  spannable bridges and failing overhangs, and `check_spec_numbers`, which
  holds a backticked constant quoted in a `*_spec.md` to the value its module
  actually defines. `verify_project` runs the spec gate in every mode wherever
  a `*_spec.md` exists and the overhang gate over every exported printable.
  `check_motion` grows a coupled sweep that poses every mover from the
  project's own kinematics, re-runs once per driven part, requires
  `obstacle_parts` rather than silently omitting the frame, reports its own
  step so a sweep too coarse to see a collision is inconclusive, and validates
  a declared `retention` chain to a genuine fixed root. `check_thickness`
  classifies each sub-minimum region as a wall, a taper or a spot by the width
  of the band rather than by its thinnest point, confirms material entry with
  two consecutive occupied samples, and omits a one-pitch band beside genuine
  mesh creases. `render_review` is new and renders shaded PNGs without a
  browser, which is what an exposed mechanism needs and a silhouette cannot
  give; `image-to-cad`'s `render_views.py` gains the matching `--shaded`
  output. `references/print-optimisation.md` carries the closed form that
  solves a repeated feature's count from the web it leaves.
  `design-reference`, `electromechanical-integration` and `step-parts` are
  byte-identical to the previous snapshot; `cadgen` stays at 0.4.19.
- The CAD skill's `requirements.txt` now declares `Pillow>=10,<13` beside the
  `cadgen` pin, because `render_review` draws with it. Workshop's own
  `pillow` dependency is tightened to the same range, and
  `tools/verify_skill_locks.py` no longer requires the skill to depend on
  `cadgen` alone: every requirement it declares must be pinned identically by
  the Workshop that installs it.
- The 2026-08-28 resync takes upstream's research-first turn.
  `design-reference` stops shipping an offline client: `scripts/design_refs.py`,
  `scripts/catalog_build.py`, `data/sources.json`,
  `references/catalog-schema.md` and `tests/test_design_refs.py` are removed,
  and the skill is now Internet research guidance whose used, rejected, missed
  and unavailable results are cited by URL, revision and license in build-spec
  section 6d. `verify_project` drops its `design_refs verify` gate and the
  `ref/external/` carve-out, so every STEP under `ref/` is bought or foreign
  geometry the mount preflight must see; `check_power` drops the same carve-out
  from `_outside_ref`, its manifest errors, and its self-check. `image-to-cad`
  reorders Step 5 into decompose, research, then select, and adds build-spec
  section 6g — the frozen per-domain design selection that `cad` implements
  without reopening candidate choice. `electromechanical-integration` gains
  `references/component-selection.md` for that research. `step-parts` is
  byte-identical to the previous snapshot; `cadgen` stays at 0.4.19 and both
  `requirements.txt` files are unchanged.
- The 2026-08-27 resync took upstream's hardened gates: `verify_project` grows
  its own `--self-check` fixture suite over the refusals that decide whether a
  gate runs at all, plus an explicit `--powered`/`--unpowered` classification
  that `--image-derived` final runs must now declare; `check_thickness` steps
  only the rays still in flight and reports every thin region rather than the
  thinnest point; `check_fit`, `check_layout`, `check_mount` and `check_motion`
  close gaps that let an inconclusive result pass as a skip. The image workflow
  gains a likeness-gate history with audited acceptance for a stalled loop, and
  splits its oversized `SKILL.md` into `references/likeness-gate.md`,
  `references/high-likeness-organic.md` and `references/repeated-scene.md`.
  `cadgen` stays at 0.4.19 and both `requirements.txt` files are unchanged.
- `electromechanical-integration` was added to the locked tree in the same
  2026-08-27 resync that introduced it upstream. It carries the powered-system
  research and specification workflow, `references/power-manifest.md`'s
  schema 3 declaration, `references/lighting-discovery.md`, and the
  `check_power` gate that the reviewed `cad`, `design-reference`, and
  `image-to-cad` bytes already name as `$electromechanical-integration`.
  `verify_project` resolves that gate as a sibling materialized tree, so the
  cross-skill reference now lands on a present skill rather than a missing
  one. The gate still runs only for a project that declares
  `measure/power.json`; a project without one records a skip.
- Adapted locally on 2026-08-26 only for Workshop's materialized
  `.agents/skills` layout: command examples resolve each package-owned skill
  through `workshop skills path`; the image renderer prints the absolute
  materialized likeness-checker path; the design-reference cache is rooted in
  the writable invocation workspace rather than the immutable skill tree; its
  HTTP user agent uses the renamed repository identity; CAD warm-daemon
  identity and staleness are rooted in the materialized CAD skill tree, with a
  compact portable byte-bounded socket path inside the private temp root; and
  the CAD skill documents the now-present sibling image workflow and no longer
  points at the removed repository-authored `product-to-cad` skill.
  Re-applied on 2026-08-27 to the command examples that resync introduced: the
  `meshlib.py` self-check, and the `step-parts` download, `verify_project` and
  `check_motion` calls the image workflow now makes. `image-to-cad/SKILL.md`
  declares the sibling `cad` and `step-parts` roots it resolves alongside the
  ones it already had; the two cross-skill calls that the previous snapshot
  left unadapted are corrected with them. `electromechanical-integration`
  resolves its own `check_power` through `workshop skills path` and points
  at the materialized CAD runner rather than a checkout path, and the CAD
  skill's own `check_power` pointer is resolved the same way.
  The 2026-08-28 resync retires the adaptations whose files upstream deleted —
  the design-reference cache root, its HTTP user agent, its client and test
  command examples, and the `catalog-schema.md` whitespace normalization — and
  drops the now-unused `DESIGN_REFERENCE_SKILL_ROOT` declaration from
  `image-to-cad/SKILL.md`. One trailing blank line in `generation_runner.py` is
  still normalized for repository whitespace checks.
  Re-applied on 2026-09-03 to the command examples that resync introduced: the
  `check_overhang` docstring and `references/print-optimisation.md` examples,
  and the `check_motion --self-check` example in
  `references/motion-manifests.md`. The CAD skill's tool listing resolves the
  new `render_review` through `workshop skills path` alongside the others, and
  keeps upstream's new appearance-review step ahead of the Workshop's own
  render-before-the-final-gate step, which is renumbered rather than replaced.
  Geometry, measurement, inspection, validation, export, and `cadgen`
  algorithms are otherwise the reviewed upstream bytes.
- Adapted locally on 2026-08-27 in the canonical `cadgen` STEP writer to apply
  the STEP header only after Open CASCADE transfer and to set its `FILE_NAME`
  timestamp to the fixed ISO-8601 value `1970-01-01T00:00:00`. This preserves
  the intended model name and originating-system metadata while making fresh,
  equivalent exports byte-identical. A real build123d solid round-trip test
  covers both reproducibility and valid geometry.
- Adapted locally on 2026-08-30 so Workshop's integrated final CAD pipeline
  requires the canonical hash-bound blind signature review before it spends a
  complete verification pass. Quick iteration remains available. The final
  pipeline records the exact schema and review hash; the shared workflow and
  CAD guidance limit the native critic to two rounds and require separate
  agreement on the Wish's subjects, action, and spatial or causal relationship.
- Adapted locally on 2026-08-31 so a frozen Workshop deep-v5 Make proof turn
  follows host-supplied exact `gen`, `export`, and `render_product` commands
  before optional CAD references or help discovery. The exception ends at the
  proof-turn marker and does not change any final CAD gate.
- Adapted locally again on 2026-08-31 after the first deep-v5 production proof
  exposed that `scripts/gen` is a Python package directory rather than a shell
  executable. Deep-v6 instructions require the exact Workshop interpreter for
  every CAD entry point and explicitly require one module-scope `gen_step()`;
  final CAD behavior remains unchanged.
- Adapted locally again on 2026-08-31 after the deep-v6 production proof
  generated valid CAD and renders but exhausted its turn before blind review.
  Deep-v7 defers this broad skill until the proof marker because the host
  supplies the complete narrow interface; final CAD behavior remains unchanged.
- Adapted locally again on 2026-08-31 after the deep-v7 production proof spent
  both bounded turns on preparatory agent cycles without source. Deep-v8 keeps
  broad-skill deferral while batching stable reads and reserving independent
  blind critique for the mandatory final review; final CAD behavior is unchanged.
- Adapted locally on 2026-09-10 so a declared retention proof repeats its
  linear or rotational escape sweep for each normalized connected material
  solid against the declared supports. Aggregate group collision no longer
  certifies retention of a disconnected escaping member. Bounds, volumes and
  per-member outcomes remain in the JSON evidence; the original sweep limits
  and numerical consistency checks remain unchanged. Regression controls cover
  connected unions, cavity shells, independently retained members, placed
  assemblies, seated-contact policy and measurement failures. This is sampled
  directional evidence, not a physical joint or load-bearing certification.
- `cad` and `step-parts` include MIT licenses, copyright 2026 Thompson Labs
  LLC. The embedded cadgen source also includes its MIT license.
- `design-reference`, `electromechanical-integration`, and `image-to-cad` do
  not contain standalone license files in the pinned upstream snapshot. They
  were migrated at the repository owner's direction; this ledger does not
  infer an MIT grant for those three trees. `design-reference` no longer
  bundles or downloads a dataset; the sources it directs research at keep their
  own licenses, recorded per result in the build spec.
- Update by importing and reviewing a new pinned upstream tree, running CAD
  characterization fixtures, and updating this ledger plus [`LOCK.json`](LOCK.json).
  CI verifies the exact canonical tree fingerprints. Never edit a vendored skill
  silently.

These scripts are diagnostics. Several current checks can pass empty or
inconclusive geometry, degrade boolean errors, or omit slicer/physical evidence.
Do not use their exit status alone as a Workshop release receipt.

## Removed trees

The repository-authored `product-to-cad` skill was removed on 2026-08-26. The
Invent now owns the build spec, selected visual direction, and researched
physical facts it used to restate, and Make reaches CAD through the `cad`,
`image-to-cad`, `design-reference`, and `step-parts` skills directly.

Workshop's local CAD adaptation also adds fixed-camera exact-state signature
sheets. `render_product --state-sheet` accepts two to five state STLs and
rejects visually indistinguishable frames, while the older motion sheet remains
truthfully documented as viewpoint presentation of one unchanged mesh. This
closes the production gap where repeated camera angles were mistaken for
evidence of a toy's promised transformation.
# Local image-to-cad adaptations after the 2026-09-03 resync

- 2026-09-07 (ADR 0056): `measure_image.py` and `check_likeness.py` read a
  cut-out reference's silhouette from its alpha channel instead of the colour
  the encoder left under transparent pixels.
- 2026-09-08 (ADR 0059): `measure_image.py`'s mask, and through it the gate,
  admit a pale tinted subject on a white ground by CIELAB a*b* distance, so
  a cream print on a white sweep keeps its lit head and torso while neutral
  shadows and background-coloured apertures stay out; `likeness-gate.md`
  documents both. The lock records the adapted tree's digest under the
  upstream commit it was adapted from.

# Local motion-presentation extension (2026-09-07)

Workshop adds `cad/scripts/motion_presentation.py` and common-frame rendering
to bind exact-state animation to CAD source, motion conditions and independent
review. The final verifier validates this evidence for coupled mechanisms;
existing geometry, motion, retention, mesh and thickness gates are unchanged.
CAD skill instructions now distinguish presentation from physical validation
and judge exposed mechanisms against the actual Wish. See ADR 0047.

## Restricted-run cache instructions (2026-09-07)

Port the cache-guidance portion of `f35bbfc4`: distinguish ordinary local cache
cleanup from restricted Workshop runs, where the finalizer removes derived
files and the host owns the isolated fresh rebuild. Explicit `--force`
regeneration is not asserted to repair the shared-library cache defect; changed
geometry still needs inspection and authoritative fresh verification. Protected
empty cache directories are not deliverable bytes or blockers.

## Make and CAD ownership clarification (2026-09-07)

Selectively port the ownership guidance from `04f6c88b` and `63eeef74`. Make
owns the independent review procedure and visual repair budget; CAD owns
modeling, render evidence, and deterministic verification mechanics. Move the
duplicated review instructions to Make without changing verifier checks, review
schemas, frozen early-proof routing, or motion-review requirements. Concept
image reconstruction and the source branch's verifier simplification are not
part of this adaptation.

## `make-round`

Local extension (2026-09-09, ADR 0060): each round renders native inspection
views and accepts source/image/reference-bound Manager feedback with concrete
visual defects and repairs. Pending inspection cannot pass. The CAD final
verifier and run-local finalizer now allow the initial blind review plus three
repair-and-rereview cycles. Python performs no visual judgment or model calls.

- Host-owned, not vendored: authored in this repository (ADR 0057) and
  recorded in `LOCK.json` under this repository's URL so the reviewed-skill
  lock still covers every tree under `make/skills/`. It sequences the reviewed
  `cad` and `image-to-cad` tools without changing them; a resync of the
  upstream skills does not touch it.


## Local audit dependency transport (2026-09-08)

A preserved Make rejection and a current-code subprocess reproduction show that
`measure/check_fit.py` can lose the bundled `cadfits` import when final
verification launches it directly. `verify_project` now supplies its own
materialized scripts directory before the project and inherited Python paths,
matching generator access to the immutable helpers. This does not install a
package, change clearance values, skip an audit, or rewrite older frozen skills.
Subprocess regressions cover relocated skills, paths with spaces, project and
inherited dependencies, helper precedence, and invalid-fit failure propagation.
This is an import-transport correction, not evidence of general Make quality.

## Exact printable-body connectivity (2026-09-08)

A native Make draft exposed a false connection in `check_fit`: two frame solids
were separated by more than 2 mm, but overlapping bounding boxes caused the
checker to count one body. Bounding boxes now exclude distant pairs only;
remaining pairs require exact shape separation within the unchanged contact
tolerance before their groups merge. Touching compounds remain supported, and
failed or invalid distance queries become build errors. Deterministic geometry
regressions include a separate island inside a frame, touching and overlapping
solids, transitive contacts, tolerance boundaries, and query failures. This
improves one diagnostic; it does not establish mechanism function, print success,
or overall Make quality. Existing materialized skill bytes remain unchanged.

## Support screening before visual review (2026-09-08)

A preserved native draft passes the fresh print preflight while the existing
final overhang checker rejects its frame and rotor in their exported print
orientations. The early preflight now runs that same checker on every printable
at the standard 45 degree profile, before thickness and before visual review.
Review binding requires passing support checks for every part; a lowered angle,
missing part, or failed checker cannot supply that evidence. The final check
still reruns. This corrects when an existing manufacturing defect is reported;
it does not prove physical printing or general Make quality. Frozen runs retain
their materialized skills.

## Nested assembly review colors and placements (2026-09-08)

A transformed subassembly containing separately colored parts was tessellated
as one object by `render_review`, replacing leaf colors with a group or fallback
color. Review now traverses all leaf occurrences and composes their ancestor
placements before tessellation. Explicit leaf colors take precedence; uncolored
leaves retain an available group color. The original hierarchy stays untouched.
Regression coverage compares nested and flat assemblies, rendered pixels, STEP
round trips, repeated instances, inherited colors, and tessellation failures.
This corrects the CAD review renderer's existing color-preservation promise;
STL presentation and physical-product acceptance remain separate questions.
Existing materialized skill bytes remain frozen.

## Assembly screening before visual review (2026-09-08)

Printable-only preflight could pass a model whose combined assembly still had
part clashes, leaving the existing final interference check to reject it after
review. Preflight now generates the selected combined entry with the printables
and batches the existing assembly validity and interference checks first. The
1.0 mm3 contact threshold matches final verification; no gate is relaxed.
The review-bound report records the selected assembly and fixed checks only
after both succeed. Final verification rejects missing or mismatched early
assembly evidence and still reruns its own checks. Frozen runs keep their
materialized skills. This is earlier deterministic feedback, not proof of
native repair reliability, physical assembly or product acceptance.


## Support geometry and mesh-order invariance (2026-09-08)

The support checker could turn the same STL geometry from failing to passing
when only its triangle records were reordered. Its single sampled-region
centroid could sit between supports while an outer cantilever remained
unsupported. A fused flat cap on one narrow stem reproduced that false bridge
classification independently of any product artifact.

The checker now uses equal-area subtriangle centroids with a corner-symmetric
sample set, canonicalizes oriented triangles before welding, and groups samples
by shared edges of the actual down-facing surfaces. Every non-bed down-facing
sample is checked against the preceding layer's mesh section. The angle and
layer height define a lateral allowance of `layer / tan(angle)`, so a thin step
can rest on the preceding layer without being mislabeled as a bridge. The same
geometric principle is used in [OrcaSlicer 2.4.2's angle-based support detection](https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.4.2/src/libslic3r/Support/SupportMaterial.cpp#L1434);
this is an independent implementation, not a slicer port.

The deterministic `mesh_support.py` helper measured exact section boundaries,
deduplicates coincident oriented crossings, and finds real support separation.
It tests X/Y and the direction toward the nearest boundary point, allowing
rotated slots without an arbitrary angular grid. Bounded batches limit temporary
intersection matrices. Voxels only describe air gaps in reports; they no longer
select which surfaces can fail. Existing angle, layer, bridge-length, sample
budget and minimum-region-area limits remain. Frozen materialized runs retain
their prior bytes. The 2026-09-10 STEP-only resync removed the gate and this
helper along with every other mesh measurement.

Area remains sampled, the bridge directions are a bounded search, and grouping
by a connected down-facing surface can combine unsupported subsets separated
by accepted samples. These checks do not establish slicer equivalence or physical
printability. Regression coverage includes thin ledges, rotated bridges and
cantilevers, disconnected small surfaces, sample symmetry, shared-edge crossings,
actual support separation and CLI/report agreement. Private native artifacts and
slicer comparisons stay outside this repository.


## Nested assembly motion geometry (2026-09-08)

A build123d assembly created with `Compound(children=...)` exposes the placed
solids through `solids()` but can have an empty wrapped topology for Boolean
intersection. Two coincident boxes reproduced a false clear result when one
was addressed as a group; the equivalent wrapped compound correctly reported
8 cubic millimetres of overlap. Named descendants also retained local poses
when an ancestor was translated or rotated.

`check_motion` now intersects compounds made from the actual placed solids on
both sides of a collision query. Its part index composes every ancestor
location, including the root, without mutating the source assembly. Linear,
rotational, coupled and proxy checks retain their existing thresholds and
manifest contracts. Regression coverage exercises grouped movers and
obstacles, equivalent wrapped geometry, nested placement aliases, clear paths,
and real translation/rotation collisions.

This correction makes declared motion evidence measure the intended geometry;
it cannot infer an omitted retention requirement, prove a continuous path from
samples, or establish physical snap performance. Frozen runs retain their
materialized tool version. Private diagnostic products remain outside Git.


## Per-pixel depth for CAD review (2026-09-08)

Sorting triangles by their mean depth painted parts of a rear surface over a
nearer one. A sloped quad behind a small square reproduced the occlusion error;
changing only the quad diagonal also changed the resulting image.

`render_review` now selects the nearest surface at each pixel using barycentric
depth interpolation for its orthographic projection. Small row batches bound
temporary arrays for large projected faces. Occurrence placements, materials,
lighting, camera and tessellation remain unchanged. Regression coverage includes
near and far surfaces, crossing planes, alternative triangulations, occurrence
order, triangle order and cyclic corner order.

This corrects image visibility, not geometry or physical behavior. Edge coverage
uses pixel centres and may differ from the previous polygon fill. Truly
coplanar overlapping materials have no unique geometric depth ordering. Frozen
runs retain their existing renderer and review artifacts; private diagnostic
models and rendered comparisons stay outside Git.


## Explicit STEP validity authority (2026-09-08)

`inspect validate model.step` could execute the neighboring `model.step.py`
instead of checking the requested file. An open-face STEP passed when a sibling
generator built a closed box, while the exact same STEP bytes failed without
that generator. A broken sibling generator could also prevent inspection of a
valid STEP.

Validity inspection now loads an existing STEP target directly. An explicitly
named Python generator remains source-driven, and logical entry aliases retain
their existing generator resolution. Regression coverage includes the
open-face false pass, a broken sibling source, changed STEP bytes, standalone
imports and source-only entries. This matches the existing distinction used by
topology loading and mesh export.

This fixes target selection for validity inspection. It does not repair STEP
exchange geometry, prove source/export equivalence, or change the verifier's
choice of source targets. Frozen runs keep their materialized implementation.
Private product artifacts and experimental construction methods remain outside
the repository.

- Workshop's 2026-09-09 motion-evidence correction adds `motion_states.py`,
  shares `check_motion` occurrence identities and poses with presentation,
  preserves occurrence colors at fixed framing, and replaces hash-only
  animation provenance with schema-v2 reconstruction. The older frozen tools
  are unchanged. ADR 0060 records the implementation and validation limits.


## Motion measurement consistency (2026-09-09)

`check_motion` could turn a Boolean exception or a nonfinite volume into a clear
path. A successful but empty intersection could also contradict the operands'
union. Separately, two coincident solid children counted twice and could change
a threshold-sensitive retention result.

The checker now requires finite nonnegative solid volumes, completed non-null
Boolean operations and valid result geometry. Each grouped operand is measured
as a material union. Intersection volume must agree with operand volumes minus
union volume within a fixed 0.000001 cubic millimetre consistency tolerance;
manifest collision thresholds are unchanged. Failed or inconsistent
measurements become inconclusive under the existing default nonzero exit rule.

A bounded cache avoids repeating ordinary validity checks for identical
complete topology and orientation during one immutable condition. Positive
unit-scale placements may change. Hash matches require exact topology identity;
new topology and evicted entries are validated. Nested sequences share the
condition scope, which is discarded on return or exception. The cache holds at
most 256 entries and Boolean operations preserve their input geometry.

Regression tests cover real overlap, contact and separation, duplicated or
overlapping groups, invalid and unavailable operations, nonfinite values,
clearance and retention expectations, default CLI failure, nested geometry,
rigid placement, orientation, hash collisions, scope cleanup and eviction.
Common and Fuse use the same kernel; their agreement is a consistency check,
not independent geometric certification or physical validation. Frozen runs
retain their materialized tools. Private replay artifacts remain outside Git.

## Current print-preflight result (2026-09-09)

The pre-review print gate validates only the newest pipeline record. Previously
it could borrow PASS, the required mode, assembly screening, or printable check
rows from preserved history even when the newest record failed or was incomplete.
Regression tests use the real report writer to retain older records and exercise
failure, omitted checks, and weaker print profiles. A complete newest PASS still
accepts older failed records; the signature review continues to bind the entire
report's hash. Final geometry checks and frozen materialized tools are unchanged.
This corrects report-history validation; it does not establish that a passing
preflight belongs to the current construction source bytes.

## Sampled contact evidence for driven parts (2026-09-10)

A frozen-output collision could be reported as transmission even when the
nominally moving parts remained separated. Mutually reaching outputs could
also pass without a path from an input, and static obstacles could provide the
only apparent drive contact.

Coupled motion now requires every declared driven output to be reachable from
an input through mover pairs with both a frozen-output collision and nominal
surface-contact witness. Static obstacles do not supply these edges. Repeated
names, aliases of the same occurrence, and overlapping group selections are
inconclusive. JSON separates the sampled collision result from the required
contact evidence and records each edge's witnesses; missing evidence fails
both clear and blocked expectations. The former ten-millimetre-gap positive
self-check is retained as a negative regression.

These are necessary sampled geometric conditions. They do not prove sustained
engagement, the declared ratio or phase, force transmission, or physical
operation. Numerical contact and Boolean consistency tolerances are unchanged.
Frozen runs keep their exact materialized tools. Private product evidence and
unqualified gear construction experiments remain outside Git.

## Documented entry references (2026-09-10)

A delivered project could pass every geometry gate while its README file map
and rebuild command named a `<name>.step.py` entry that no longer existed. The
documented rebuild command then failed on the reader's first step, although
the remaining entries generated valid solids. Nothing read the documentation
for existence, only for assembly-action claims.

`verify_project` now resolves every `<name>.step.py` reference in README.md
and `*_spec.md` by basename in the project root or by the written path, in
print-preflight and final modes, and refuses on the first missing one with its
file and line. Wildcards, placeholders, suffixed names and absent documents
are not references. `--quick` is unchanged. The refusal is recorded in the
pipeline report like other preflight refusals.

Contract tests cover existing, wildcard, placeholder, path-prefixed, spec and
fenced-command references, refusal before geometry work in both gated modes,
quick-mode passthrough and report recording. A text-only replay over forty
preserved and archived project READMEs found no false positive and the one
preserved defect. This checks documentation consistency only; it does not
establish that a documented command reproduces the delivered geometry.
Frozen runs keep their exact materialized tools.

## Drive-evidence cost on accepted products (2026-09-10)

The input-connected contact rule for driven parts made one published product's
motion check exceed fifteen minutes (369 s for a single 120-sample coupled
cycle; 133 s on the tree without the rule; 256 s for the whole manifest at
publication). A profile attributed 244 s to 1,094 whole-part minimum-distance
queries on mover pairs that collide when one is frozen but never touch in
their nominal poses, and 70 s to deep-copying the same placements once per
pair. Neither is part of what the rule measures.

Placements are now made once per mover and sample and shared by every pair
and both witnesses. The nominal contact query accepts a `within` tolerance:
faces whose bounding boxes lie farther than that (plus a millimetre-scale
margin for shape tolerance) from the other part cannot realize a closer
point, so the extrema query runs on the near faces only. The answer stays
exact whenever it is at most `within`, and otherwise only certifies that the
distance exceeds it, which is all the witness uses. Without `within` the
function is the exact whole-part distance it was.

Contract tests cover single placement per mover and sample, exact contact
through inner faces, far parts, a small gap inside overlapping bounding
boxes, nested material with a thin gap, and invalid tolerances. The rule's
witnesses, thresholds and fail-closed behaviour are unchanged; the cost is
measured privately on the same product before and after.

## Consistency band at kernel precision (2026-09-10)

The motion checker compared the direct intersection volume with
operands-minus-union under a fixed 0.000001 mm3 band. Kernel volume
integration is precise relative to the operand, not to an absolute cubic
micrometre. Replaying the published manifests of twelve host-accepted toys
under the integrated checker made five of them inconclusive (15 of 52
evaluable conditions on both the baseline and candidate tool trees, plus one
more on the candidate tree), and the same band left a preserved crank
source/export comparison inconclusive at a 3.8e-6 mm3 delta on 6,389 mm3.
A step-by-step probe over three of those toys (273 pair-steps) found the
union-inferred value drifting by up to 3.4e-6 of the operand volumes in
seated-contact poses of filleted and curved parts, while the direct
intersection and both Cut-based differences agreed within 1e-5 of the operand
volumes in every over-band pair; in three seated poses the union was invalid
where the intersection was valid.

The band is now max(0.000001 mm3, 0.00001 x the operand volumes), applied to
the group union and to the intersection/union agreement alike. When the union
fails or is invalid, the intersection is cross-checked against both
differences within the same band instead of failing closed; disagreement or a
failed difference remains inconclusive. Manifest collision thresholds,
validity requirements and the inconclusive-fails-closed rule are unchanged.

A second probe over interpenetrating thin shells of another accepted product
found every formulation disagreeing by tens of cubic millimetres, one
difference negative, while all of them exceeded the 0.001 mm3 collision
threshold at the deciding sample. A union that disagrees beyond band is
therefore arbitrated the same way as an unavailable one, and when the
differences disagree too the intersection is accepted only if every
available formulation gives the same threshold verdict for the condition
being judged; outside a condition, or with a split verdict, the pose stays
inconclusive.

Contract tests cover kernel-scale noise on large operands for clear and
blocked expectations, a ten-cubic-millimetre discrepancy, the absolute floor
on tiny operands, duplicated material, an intersection larger than an operand,
group-union noise versus excess, the difference fallback with agreeing and
disagreeing differences, a failed fallback, a lossy union arbitrated by real
differences, an empty intersection that arbitration does not rescue, a
unanimous blocked verdict, a split verdict, and the absence of a threshold. The sealed replay is repeated
at the corrected tree and recorded privately. Frozen runs keep their exact
materialized tools; this is measurement calibration, not a product-quality
claim, and it does not change the necessary-contact rule for driven parts.

## Earlier review-count compatibility correction (2026-09-09)

An earlier local correction allowed positive signature-review counts instead
of the former two-review allowance. Integration with the team's ADR 0060
superseded that change: Make's current four-review policy and verifier are
preserved unchanged, in accordance with the instruction to leave Make alone.
Workshop token budgeting removes host execution caps, not Make's internal
review allowance. The lock binds the integrated team skill bytes.
