# Shared skill provenance

## `cad`, `design-reference`, `electromechanical-integration`, `image-to-cad`, and `step-parts`

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `9e75609bb53bf880429353e57201995a4c0482e6` (2026-09-07), resynced from
  `1e56c145586fa9be230443612c1d9d47c957e4f8` (2026-09-03).
- The reviewed snapshot includes the complete upstream trees for all five
  skills. `cad` includes the vendored `cadgen` 0.4.19 source, bought-part mount
  tooling, run-cost guidance, and the strengthened image-derived verification
  runner. The image workflow includes clipped-reference rejection, reference
  silhouette preparation, and stored-camera replay for lower-cost iteration.
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

The deterministic `mesh_support.py` helper measures exact section boundaries,
deduplicates coincident oriented crossings, and finds real support separation.
It tests X/Y and the direction toward the nearest boundary point, allowing
rotated slots without an arbitrary angular grid. Bounded batches limit temporary
intersection matrices. Voxels only describe air gaps in reports; they no longer
select which surfaces can fail. Existing angle, layer, bridge-length, sample
budget and minimum-region-area limits remain. Frozen materialized runs retain
their prior bytes.

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
