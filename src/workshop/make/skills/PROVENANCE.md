# Shared skill provenance

## Resync to upstream `b67636e`: build123d libraries that downgrade the toolchain (2026-10-01)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `b67636e092a68f94335d0a76ee004b59784dad66` (2026-10-01), resynced from
  `db26c4e`. That is one upstream commit touching the same single file,
  `wiki/pages/modeling/element-libraries.md`. The merge is the same three-way
  merge as before. The Workshop copy was byte-identical to the `db26c4e` base,
  so it takes upstream's bytes unchanged. No other tree moved; their locks move
  to the new commit only, and `make-round` is unchanged.
- **What upstream brought.** A new section, "Other build123d libraries",
  makes a dry run the rule before any install
  (`pip install --dry-run --report`). The reason is that pip does not fail
  when a library cannot accept the environment: it backtracks to an old
  release that pins an old build123d. The section gives a verdict for
  `gflabel`, `gfthings`, `gridfinity_build123d`, `bd-vslot` and `capistry`,
  and the `cq-gridfinity` row now points to it. The page's aliases gain the
  new names.

Upstream measured its verdicts in its own venv, which runs Python 3.14 with
`bd_warehouse` 0.3.0. Workshop pins the same `bd_warehouse` range
(`>=0.3,<0.4`) and `build123d==0.11.1`, but declares
`requires-python = ">=3.11"`. Its development venv here is 3.11.12. Each
verdict was resolved against that venv with `uv pip install --dry-run`, read
against PyPI metadata on 2026-10-01:

- `gfthings` downgrades the toolchain here too, but for a different reason.
  It installs 0.8.3, which takes `build123d` from 0.11.1 to 0.10.0 and
  `cadquery-ocp` from 7.9.3 to 7.8.1. Its current 0.9.0 requires Python 3.12
  and pins `build123d<0.11`, so it would downgrade on any interpreter.
- `gflabel` 0.2.0 declares `requires-python <3.13,>=3.10` and
  `build123d>=0.8.0`. On 3.11 or 3.12 it installs cleanly with no change to
  build123d. Upstream's fallback only happens from 3.13 upward.
- `capistry` 0.2.0 requires Python 3.13 or later. On 3.11 it fails to resolve
  rather than installing, so "installs cleanly" holds only from 3.13.
- `gridfinity_build123d` is not on PyPI at all, so it is git-only. Upstream's
  reason for avoiding it (it pins `bd_warehouse` to a git commit) is not
  something a dry run from PyPI can show.
- The `bd-vslot` verdict does not depend on the interpreter.

The page is left as upstream wrote it, not adapted locally. Where a verdict
differs here, the difference is harmless: either a library the page warns
against turns out to install cleanly, or a library it clears fails to resolve.
In neither case does the page lead to a toolchain downgrade. The dry-run rule
it leads with is what shows the right answer on any interpreter. The page's
"The venv runs Python 3.14" describes upstream's venv, which the wiki
`SKILL.md` note on machines and fixtures already covers in spirit. Making the
verdicts depend on the interpreter belongs upstream.

Verified here: `verify_skill_locks` matches eight trees, `wiki --self-check`
passes and `wiki lint` reports 193 pages with 0 errors. `search gflabel`,
`search capistry` and `search bd-vslot` each rank the new section first.

Consequences for existing runs:

- **Materialized instruction bytes changed.** The `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed; resume
  fails closed on the materialized-instruction-hash mismatch.
  `workshop resume --refresh-tools` rewrites the skills a run already carries.
- No gate reads the wiki, and no script changed.

## Resync to upstream `db26c4e`: four more CadQuery libraries ruled out (2026-10-01)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `db26c4e38748d1affe67da62ab97a0c4943069b1` (2026-10-01), resynced from
  `7e03fc2`. That is one upstream commit touching one file. The merge is the
  same three-way merge as before: the base is the locked `7e03fc2` bytes, one
  side is the Workshop tree and the other is upstream `HEAD`. Only `wiki`
  moved. Its `modeling/element-libraries.md` was byte-identical to the
  `7e03fc2` base here, so it takes upstream's bytes unchanged. `cad`,
  `design-reference`, `electromechanical-integration`, `image-to-cad`,
  `product-design` and `step-parts` did not change, and their locks move to
  the new commit only. `make-round` is unchanged. Adoption is unchanged too:
  `toy-archive` and the reverse-engineering pair stay out.
- **What upstream brought.** The table "CadQuery libraries that do not apply"
  gains three rows and corrects a fourth. `cq-gridfinity` needs `cadquery` and
  `cqkit`, so author Gridfinity bins in build123d from the published profile
  (42 mm pitch, 7 mm height unit). `argus-diff` needs `cadquery`; the idea
  worth keeping is to match bodies by a fingerprint of volume, area, centre of
  mass, bbox and principal moments. `dl4to4ocp` pins `torch==1.12` and
  produces a voxel field with no parametric source. `cq-kit` was listed as
  missing from PyPI, which was wrong: it is published as `cqkit`. It now has
  its own row, which says it is CadQuery-only and that build123d's selectors
  already cover it. The page's aliases gain the new names, so
  `search gridfinity` and `search argus-diff` both rank this section first.

Merge: the page carries no Workshop-local lines, so nothing needed merging.
The `argus-diff` row names two tools. `interfere` resolves to the `cad`
skill's `scripts/inspect interfere`. `step_verify` is a script in upstream's
`step-to-source`, which Workshop does not adopt. The row still holds without
it, because it only explains why not to install a package and `interfere`
already covers clashes. The wiki `SKILL.md` note on `step-to-source`
mentions only `reverse-engineering/` pages, and this row is not on one. It
is left as upstream wrote it, not adapted locally.

Verified here: `verify_skill_locks` matches eight trees, `wiki --self-check`
passes and `wiki lint` reports 193 pages with 0 errors.

Consequences for existing runs:

- **Materialized instruction bytes changed.** The `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed; resume
  fails closed on the materialized-instruction-hash mismatch.
  `workshop resume --refresh-tools` rewrites the skills a run already carries.
- No gate reads the wiki, and no script changed.

## Resync to upstream `7e03fc2`: the joint catalogue, segmented axles, phrase-aware wiki search (2026-10-01)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `7e03fc2269ffbeb9f423cab348a3c699cbd69bde` (2026-10-01), resynced from
  `b149710` — 4 upstream commits touching 41 files. Same three-way merge as
  before: base the locked `b149710` bytes, one side the Workshop tree, the
  other upstream `HEAD`. Only `wiki` moved upstream; `cad`,
  `design-reference`, `electromechanical-integration`, `image-to-cad`,
  `product-design` and `step-parts` came out byte-identical, and their locks
  move to the new commit only. `make-round` is unchanged. Adoption is
  unchanged too: `toy-archive` (changed upstream in this range) and the
  reverse-engineering pair stay out.
- **What upstream brought.** Twelve researched pages cover joints the
  catalogue only named or did not have: `mechanisms/ball-and-socket-joints`,
  `posable-figure-joints`, `rod-ends-and-clevises`, `hinge-types`,
  `shaft-hub-connections`, `rolling-contact-joints`, `swivels-and-turntables`,
  `telescoping-tubes-and-locks`, `scissor-and-pantograph-linkages` and
  `bayonet-and-twist-locks`, `fasteners/push-pins-and-clip-fasteners`, and
  `printing/interlocking-joinery-for-prints`. A thirteenth,
  `mechanisms/joint-variant-index`, maps every variant to its section, and
  `joints.md` names the kinematic pair before the form. `shaft-couplings`
  gains CV and printed universal joints, `clutches-and-freewheels` dog and jaw
  clutches, and `flexures-and-living-hinges` six more flexure forms.
  `shafts-and-bearings` and `fdm-joining-split-prints` gain the segmented
  axle: an axle longer than the bed splits at the pivots it carries, each
  pivot pin printed lying on a D-flat that keys a D-socket, the flat cut where
  the curve leaves at about 50° because a shallower one fails `check_overhang`
  along the whole pin, and the sag computed with the section varying along
  the span. Back-links are wired across 20 pages; 193 pages.
- **Search.** `scripts/wiki` no longer lets a synonym member typed inside a
  longer typed member call its own group, and keeps stop words out of concept
  tokens: "split pin" had ranked parting lines first, "claw coupling"
  grippers, and "knuckle joint" hinges. `synonyms.txt` gains the new
  vocabulary. Upstream reports 4 of 76 sample queries changing their top page,
  each to the right one; the new self-check fixtures fail on the old code.

Merge: upstream changed only the `description` front matter of `wiki`'s
`SKILL.md`, and Workshop's lines there (the `workshop skills path` command and
the consult-only block) sit below it, so the merge was clean. Nothing needed
adapting. The new pages cite `skills/cad/scripts/cadfits.py` (`slot_for`,
`peg_for`, `mating_clearance`, `print_in_place_gap`), `cadprint.min_wall` and
`shell_wall`, and `stdpart sizes` for `SetScrew`, `LockCollar`,
`ExternalSnapRing`, `ShaftKey` and `ORing`. Every one resolves against the
Workshop trees, and the existing `SKILL.md` note already reads a
`skills/<name>/` path as the sibling Make skill.

`toy-archive`'s change (`6d989fb`: `publish` refuses a black-on-white
likeness mask as the Factory cover, because an image-derived `verify_project`
writes its own `snap/iso.png`) is not taken; that publish wraps a host-only
effect. Workshop's Factory handoff also uses the sealed `snap/iso.png` as the
cover, but the Make proposal binds that file to the signature review's
`iso_sha256`, so a mask written over the reviewed render fails the proposal
instead of reaching Factory.

Verified here: `verify_skill_locks` matches eight trees; `wiki --self-check`
passes, including upstream's four new phrase and stop-word fixtures; and
`wiki lint` reports 193 pages, 0 errors.

Consequences for existing runs:

- **Materialized instruction bytes changed.** The `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed; resume
  fails closed on the materialized-instruction-hash mismatch.
  `workshop resume --refresh-tools` rewrites the skills a run already carries.
- No gate reads the wiki, and `scripts/wiki` is the only script that changed.
  A query whose top page moved now names the joint it asked for.

## Resync to upstream `b149710`: per-piece likeness, bought parts in 6h, print unions (2026-09-30)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `b149710749317fca5ae359f40fb17a362525b1de` (2026-09-30), resynced from
  `bd1dcdc` — 11 upstream commits touching 42 files. Same three-way merge as
  before: base the locked `bd1dcdc` bytes, one side the Workshop tree, the
  other upstream `HEAD`. `design-reference`, `electromechanical-integration`
  and `step-parts` came out byte-identical; their locks move to the new commit
  only. `make-round` is unchanged. Adoption is unchanged too: `toy-archive`
  (changed upstream in this range) and the reverse-engineering pair stay out.
- **What upstream brought.** `cad`: `verify_project --likeness-entry
  LABEL=ENTRY` scores a reference that shows one piece of a set against that
  piece's entry, rendered into its own `snap/<entry>/`; `printlib` builds an
  entry's optional `gen_print_union()` for `check_mesh`, `check_overhang`,
  `check_thickness` and `repair_mesh`, so a multi-colour plate's shared faces
  stop reading as non-manifold; `check_spec_format` gains
  `missing-not-printed`; `check_spec_numbers` pairs names and values across
  table cells and reads each module once; `check_motion` resolves a
  project-relative `--manifest`; `stdpart` folds punctuation in queries
  (`o-ring` finds `ORing`); `render_review` lights both sides of a face; and
  the references gain staged paths as one coupled condition, pose tables from
  the project's own kinematic solution, and the cost of a coupled cycle.
  `image-to-cad`: spec section **6h, "Not 3D printed"** — every bought part,
  fastener and consumable, with quantity and order name — in the template,
  the decomposition step and the handoff table; `measure_image` measures a
  vertical-gradient backdrop (a CAD viewer's default) row by row;
  `render_views`' source-vs-STEP drift check keeps every body instead of the
  largest blob; `ref_silhouette --json` serialises numpy values.
  `product-design`: sketch the side view in 2D first, review the figure alone
  and close, and treat "ugly" as a request for craft. `wiki`: two new pages
  (`mechanisms/push-to-turn-indexer`, `modeling/carved-figures-on-split-prints`)
  and additions to twenty others; 180 pages.

Merge decisions where both sides had changed the same lines:

- `check_motion`: upstream rewrote `overlap_volume` to sum leaf-solid pairs,
  because the Common of a group whose members share faces came back empty, and
  let a thrown Boolean propagate as inconclusive. Workshop's `overlap_volume`
  (the 2026-09-08 to 09-10 consistency entries below) already fuses each
  operand's solids before the Common and raises on an unusable Boolean, so it
  is kept. Upstream's fixture 7 (a face-sharing inlaid mover pushed into a wall)
  and `resolve_manifest` are adopted; the fixture passes against Workshop's
  measurement (50 mm3 at step 3).
- `render_review`: upstream replaced its painter's sort with a per-triangle
  depth buffer and flips a normal that faces away. Workshop's batched per-pixel
  rasteriser is kept and the flip is ported into it, ahead of `shade_faces`.
  Upstream's two fixtures (tiles over a covered plate, a square with mixed
  windings) pass against it. The raster-equivalence test's reference renderer
  lights both sides too; its opposite-winding case now asserts one shade, since
  the two windings no longer shade differently.
- `verify_project`: upstream's `_final` call site collides with Workshop's
  restructured final call behind the ADR 0070 verdict reuse; `likeness_entries`
  is threaded into Workshop's. The reuse closure already hashes the raw argv,
  so a changed `--likeness-entry` never reuses a verdict.
- `measure_image.py`: both sides added a mask path — Workshop's CIELAB
  pale-subject admission, upstream's gradient backdrop. Both are kept with
  their fixtures; the gradient path returns before the single-colour path the
  pale admission extends.
- `motion-manifests.md`: upstream's two subsections close the coupled-motion
  section, ahead of Workshop's section on sampling cost and the deadline.

Workshop adaptations of the new text:

- **A print union must be the plate's own material.** The print gates, and
  the host's print-ready rerun of `verify_project --print-gates` (ADR 0063),
  would otherwise measure whatever `gen_print_union()` returns in place of the
  plate `gen_step()` exports, so a region left out or a wall thickened would
  pass for an object nobody ships. `printlib.check_print_union` refuses a
  union whose volume differs from the regions' summed volume by more than
  1e-5 of it (or 0.001 mm3), or whose bounding box sits more than 0.01 mm off
  theirs. Volume and box rather than a Boolean difference: two integrations
  cost nothing beside the gates they guard. Two self-check fixtures (inlay
  left out; block moved 1 mm) pin it, and `print-optimisation.md` says so.
- **`make_round` does not forward `--likeness-entry`.** Its `--full` scores
  the Wish's sealed references at assembly scope and each Component's own
  image through `--component` rounds (ADR 0074), so `make-round` is
  unchanged. A Manager running `verify_project` directly can pass the flag.
- No path adaptation was needed: the new command lines already use
  `$CAD_SKILL_ROOT`, and new prose uses the `wiki show` form each `SKILL.md`
  resolves.

Verified here: `verify_skill_locks` matches eight trees; the self-checks of
every changed script pass — `check_motion`, `check_spec_format`,
`check_spec_numbers`, `printlib`, `render_review`, `stdpart`,
`verify_project`, `measure_image`, `ref_silhouette` and `render_views` — and
`wiki lint` reports 180 pages, 0 errors.

Consequences for existing runs:

- **Materialized instruction bytes changed.** Four fingerprints move (`cad`,
  `image-to-cad`, `product-design`, `wiki`). A run parked before this change
  must be restarted rather than resumed; resume fails closed on the
  materialized-instruction-hash mismatch. `workshop resume --refresh-tools`
  rewrites the skills a run already carries.
- **A spec with a section 6 now needs a 6h.** `verify_project` runs
  `check_spec_format` in every mode whenever a `*_spec.md` exists, so a
  refreshed parked run or a `workshop fix` of an older archive whose spec
  predates 6h fails preflight until it gains the subsection — one line when
  everything is printed and nothing is glued. The finding names the fix.
- Review renders change pixels only where a face's winding points away from
  the camera; no gate reads them. `render_review`'s bytes changed, so its
  tessellation cache, keyed on them, misses once per project.

## Resync to upstream `bd1dcdc`: the wiki replaces `mechanisms`, `product-design` joins (2026-09-29)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `bd1dcdc0426e562d3e09bdc3d61cf0868b9f26fa` (2026-09-29), resynced from
  `facbc58` for `cad`, `design-reference`, `electromechanical-integration`,
  `image-to-cad` and `step-parts`, and from `cf81f51` for `mechanisms` — 95
  upstream commits. It was a three-way merge: base the locked upstream bytes,
  one side the Workshop tree, the other upstream `HEAD`. `step-parts` came out
  byte-identical; its lock moves to the new commit only. `cadgen` stays at
  0.4.19.
- **`mechanisms` is retired; `wiki` replaces it.** Upstream moved the design
  knowledge out of the skills (`79241b6`) into `skills/wiki`: 178 pages under
  `mechanisms/`, `modeling/`, `printing/`, `structures/`, `materials/`,
  `fasteners/`, `electronics/`, `standards/`, `image-reading/`,
  `product-design/` and `reverse-engineering/`, searched by a stdlib-only
  `scripts/wiki` (BM25 over sections, synonym expansion, `lint`). The eight
  `mechanisms` pages are wiki pages now, and the resynced `cad`,
  `image-to-cad` and `electromechanical-integration` references point into
  roughly forty of them for knowledge they used to carry themselves.
- **New skills, materialized into every product run:** `wiki` and
  `product-design` (an industrial-design pass for a prose request: survey,
  direction, concept selection, sizing and recorded review rounds, ending in
  the same `<name>_spec.md` `image-to-cad` writes).
- **Not adopted:** upstream's `toy-archive`, whose `publish` wraps a Factory
  effect only the host may perform, and its reverse-engineering pair,
  `step-to-source` (recover or re-author build123d source from a STEP with no
  generator) and `stl-to-step` (convert a supplied mesh into a reference STEP).
  A Wish supplies reference images, not meshes or STEPs to rebuild, so neither
  has input in a run. The wiki's `reverse-engineering/` pages still cite them;
  the wiki's `SKILL.md` says they are not Workshop skills, and
  `product-design`'s says a supplied STL or STEP still does not fire it.
- **What else upstream brought.** `cad`: `scripts/stdpart` and
  `references/standard-elements.md`, standard fasteners, bearings, keys and
  gears built by `bd_warehouse` and `py_gearworks` with the mating feature
  derived from the element; `scripts/cadcache.py`, a content-hashed parallel
  build cache; a `CARRIES = "ref/x.step"` declaration that exempts a carrier
  entry's own body from the mount audit; `check_overhang` stops calling a cap
  on a stem a bridge and scores a mirror image as the same overhang;
  `cadmount.load` takes a named solid from a multi-solid catalog STEP;
  Bambu Lab PLA Matte (25 colours) joins the palette, which retires the bare
  `"PLA"` shorthand because two PLA stocks are now loaded; the STEP writer
  drops pcurves when every face is planar (`626d798`); and a step 13 that
  writes back what an edit taught. `image-to-cad`: a declared camera per
  reference and a handedness check (`c1c3886`), one hole-scoring rule, a ruler
  in every view, the pose settled at the resolution the gate scores, the
  search's own score recorded and held, and a render that survives a face OCCT
  will not triangulate.
- **The camera is required, as upstream has it.** `verify_project
  --image-derived` refuses a `--likeness-ref` without `@AZ,EL[,TOL]`, because
  a pose search over every azimuth scores a model built the wrong way round
  like the right one. `render_views` without `--camera` still searches freely
  and says it is mirror-blind. Workshop adopted the refusal, and taught
  `make_round` to carry a camera on `--ref LABEL=PATH@AZ,EL[,TOL]`, on a
  `LABEL=ref/x@AZ,EL` ledger line and in the build spec's new camera column.
  It passes the camera to `render_views --camera` and forwards it on `--full`.
  A `--ref` that copies a sealed Wish image lends that image its camera, since
  the Wish seals pixels, not where they were taken from. A replay that
  `render_views` refuses because its stored pose lies outside the declared
  window is re-searched inside it rather than failing every later round. The
  product-run `make.md` and the `make-round` tool card say to declare a camera
  from the first round.

Merge decisions where both sides had changed the same lines:

- `render_review`: upstream `a6747ce` walks nested assemblies so each solid
  keeps its colour and placement. Workshop's placed-leaf walk already did that
  and carries the ADR 0068 tessellation cache and the angular deflection, so
  Workshop's hunk is kept and upstream's nested fixture is adopted beside it;
  it passes against the Workshop implementation.
- `verify_project`: both sides' additions are kept — Contract Mode likeness
  (ADR 0074) and `CARRIES`. The camera refusal runs before the Contract Mode
  checks, `_final` takes both `skip_gen` and `likeness_cameras`, and the
  cameras are forwarded through Workshop's restructured final call.
- `render_views.py`: upstream's match record plus Workshop's `worst_bands`.
- `cadfilament.py`, `build123d-modeling.md`, `parameters.md`,
  `organic-lofts.md`, `build123d-operations.md`: upstream's three-stock text,
  with Workshop's two `$CAD_SKILL_ROOT` path adaptations re-applied. The PETG
  Basic table Workshop added on 2026-09-15 is byte-identical to upstream's.
- `likeness-gate.md`: upstream's condensed text, keeping Workshop's ADR 0074
  wording — below 0.90 the Workshop Manager accepts with a reason the run
  reports, rather than upstream's "the user's decision: stop and ask".
- `cad/SKILL.md`: Workshop's tool listing with `stdpart` added, Workshop's
  step 13 kept, and upstream's write-back step renumbered 14.

Workshop adaptations of the new text:

- **Paths.** Runnable command lines use the `$<NAME>_SKILL_ROOT` form the
  earlier resyncs used, and `wiki search` becomes
  `python "$(workshop skills path)/wiki/scripts/wiki" search`. Prose pointers
  such as `skills/wiki/pages/printing/fit-derivation.md` stay upstream's
  bytes. One note in each `SKILL.md` resolves `skills/<name>/...` under
  `$(workshop skills path)`. No script in `wiki` or `product-design` changed.
- **Write-back.** Upstream now ends every edit by writing what it taught into
  `skills/wiki`. A product run's skills are read-only (`0400`) and hash-bound
  into its input manifest, so the wiki is consult-only there. The `cad` step 14
  and the wiki's own `SKILL.md` send a new rule to the final response instead.
  The Make lessons loop still carries gate failures into the design vault, and
  a Workshop builder writes durable rules back here or upstream.
- **`product-design`** fires only while the design is open: a prose Wish with
  no sealed concept, Design Contract or reference image. It works inside the
  Inventor's `TASTE.md` and treats the Wish's words as the user's. Its review
  rounds spend Make's frozen round and review allowance and never replace the
  blind signature review. Its spec lives in the run's CAD project, and it adds
  no `--fresh`.

Host changes the new trees force:

- **Run input caps.** A run now materializes about 460 inputs and 4.2 MiB
  (about 300 and 3 MiB before). That crossed `MAX_AGENT_INPUT_BYTES` (4 MiB)
  and left about 55 files under `MAX_AGENT_INPUT_FILES` (512) for Wish
  references and an imported correction tree. The caps rise to 6 MiB and 768
  files, restoring the headroom they had. The agent-run test that materializes
  the complete installed inventory now holds it at least 1 MiB and 200 files
  under both caps, so the next growth fails there by name instead of in every
  end-to-end run.
- **Host colour vocabulary.** `workshop.make.cad.filament_names` repeats the
  palette's names for the occurrence-name gate and gains the 24 PLA Matte
  names that are new (43 colours across 51 spools). Longest-first matching now
  reads `arm_dark_blue` as `dark_blue`, the spool it names, not `blue`.

Dependencies: `bd-warehouse>=0.3,<0.4` and `py-gearworks>=0.0.23,<0.1` join
Workshop's own dependencies, exactly as `cad/requirements.txt` pins them, so
`tools/verify_skill_locks.py` still finds every CAD requirement pinned
identically. `uv.lock` resolves `bd-warehouse` 0.3.0 and `py-gearworks` 0.0.24
without moving `build123d` 0.11.1 or `cadquery-ocp`. Both are Apache-2.0. The
lock keeps its revision-3 format; only those two packages and the root entry
changed.

Verified here: every tree's self-check passes — `verify_project` (camera and
`CARRIES` fixtures included), `render_review` (upstream's nested fixture
against Workshop's walk), `render_views`, `check_likeness`, `measure_image`,
`check_overhang`, `meshlib`, `printlib`, `repair_mesh`, `cadfits`,
`cadmount`, `cadfilament` (all 51 colours round-trip), `cadcache`, `stdpart`,
`check_power`, `download_step_part`, `make_round`, and `wiki lint` (178
pages, 0 errors).

Consequences for existing runs:

- **Materialized instruction bytes changed.** Every upstream fingerprint moves
  except `step-parts`, `make-round`'s moves with its camera plumbing, two
  trees are added and one is dropped, and the product-run `make.md` and
  `make-playtest.md` change. A run parked before this
  change must be restarted rather than resumed; resume fails closed on the
  materialized-instruction-hash mismatch.
- `workshop resume --refresh-tools` rewrites only the skills a run already
  carries. A parked run gains the resynced trees and, for a token-budget run,
  the new `make.md`. It never gains the two new trees and keeps its own
  `mechanisms`. The resynced `cad` reaches the wiki through
  `$(workshop skills path)`, which is the installed package. An
  image-derived final in such a run now needs a camera per reference, and the
  verifier's refusal names the fix.
- An all-planar part now writes different STEP bytes (`626d798`). A
  `workshop fix` correction whose source archive was made before this change
  therefore re-measures such a part instead of carrying it, even when its
  geometry did not move. That costs work, never correctness.
## Vendored cadgen installed into the Workshop venv (2026-09-26)

A Workshop-local change to the vendored `cad` tree, not an upstream resync.
`cad/scripts/packages/cadgen` has declared version 0.4.19 since it was
vendored, the same number as the unrelated `earthtojake/text-to-cad` release on
PyPI that the root `cadgen==0.4.19` pin installed. The two are different code:
the PyPI wheel lacks `cadgen.inspection_runtime` (added here in 6716bf26) and
carries modules this copy never had. A process that imported `cadgen` before
putting the vendored path first got the PyPI copy, and a later
`cadgen.inspection_runtime` import could not be found. The #65 Correction Run
lost an assembled-round render to it: `render_review` put the path first only
after the entry it was rendering had imported `cadgen`.

Two changes:

- The root `pyproject.toml` installs this tree through `[tool.uv.sources]`
  (editable), so the uv venv holds the vendored code under the same pin. A plain
  pip install of the Workshop wheel still resolves the pinned PyPI release.
- `render_review.build_shape` puts the vendored path first before it runs the
  entry, as `gen`, `snap_frames` and the other skill entry points already do.

The vendored `pyproject.toml` now builds with `uv_build` instead of setuptools.
setuptools writes `src/cadgen.egg-info/` and `build/` into the source tree,
which here is a fingerprinted skill: they would drift this `LOCK.json`
fingerprint on every synced checkout and be copied into every run. It also
drops the `readme = "README.md"` line, since no README was ever vendored, and
the setuptools package-data for `.mjs` files that do not exist here. **The `cad`
fingerprint changed**: a frozen run keeps its materialized skills, and a parked
one picks the fix up through `workshop resume --refresh-tools`.

## Pin build123d and cadquery-ocp for cadgen (2026-09-25)

A Workshop-local change to the vendored `cad` tree, not an upstream resync.
`cadgen/pyproject.toml` declared `build123d` and `cadquery-ocp` with no
version, so two installs of the same `cadgen==0.4.19` could resolve
different OCCT builds. #60's parallel-boolean experiment
(`docs/PARALLEL_BOOLEAN_EXPERIMENT.md`, Finding 3) found a fresh resolve can
land on a pair that does not work together at all -- `cadquery-ocp` 8.0.1
drops `OCP.TDF.TDF_LabelSequence`, which `cadgen`'s STEP scene loader needs,
while the newest `cadquery-ocp` release old enough to keep it is too old for
newer `build123d`'s `OCP.collections` use -- and is the simplest explanation
for two Carry Forward builds hashing a part differently under no geometry
change.

`cadgen/pyproject.toml`, the CAD skill's `requirements.txt` and the root
`pyproject.toml` now all pin `build123d==0.11.1` and
`cadquery-ocp==7.9.3.1.1` -- the pair `uv.lock` already resolved and the one
`docs/PARALLEL_BOOLEAN_EXPERIMENT.md`'s own experiment ran against. This
follows the existing `Pillow>=10,<13` precedent: `tools/verify_skill_locks.py`
requires the Workshop to pin every CAD skill requirement exactly as the skill
declares it, so the root dependency list carries the same two specifiers.
This changes the `cad` fingerprint only; no script, gate or geometry
algorithm changed.

## Vendored cadgen installed into the Workshop venv (2026-09-26)

A Workshop-local change to the vendored `cad` tree, not an upstream resync.
`cad/scripts/packages/cadgen` has declared version 0.4.19 since it was
vendored, the same number as the unrelated `earthtojake/text-to-cad` release on
PyPI that the root `cadgen==0.4.19` pin installed. The two are different code:
the PyPI wheel lacks `cadgen.inspection_runtime` (added here in 6716bf26) and
carries modules this copy never had. A process that imported `cadgen` before
putting the vendored path first got the PyPI copy, and a later
`cadgen.inspection_runtime` import could not be found. The #65 Correction Run
lost an assembled-round render to it: `render_review` put the path first only
after the entry it was rendering had imported `cadgen`.

Two changes:

- The root `pyproject.toml` installs this tree through `[tool.uv.sources]`
  (editable), so the uv venv holds the vendored code under the same pin. A plain
  pip install of the Workshop wheel still resolves the pinned PyPI release.
- `render_review.build_shape` puts the vendored path first before it runs the
  entry, as `gen`, `snap_frames` and the other skill entry points already do.

The vendored `pyproject.toml` now builds with `uv_build` instead of setuptools.
setuptools writes `src/cadgen.egg-info/` and `build/` into the source tree,
which here is a fingerprinted skill: they would drift this `LOCK.json`
fingerprint on every synced checkout and be copied into every run. It also
drops the `readme = "README.md"` line, since no README was ever vendored, and
the setuptools package-data for `.mjs` files that do not exist here. **The `cad`
fingerprint changed**: a frozen run keeps its materialized skills, and a parked
one picks the fix up through `workshop resume --refresh-tools`.

## Pin build123d and cadquery-ocp for cadgen (2026-09-25)

A Workshop-local change to the vendored `cad` tree, not an upstream resync.
`cadgen/pyproject.toml` declared `build123d` and `cadquery-ocp` with no
version, so two installs of the same `cadgen==0.4.19` could resolve
different OCCT builds. #60's parallel-boolean experiment
(`docs/PARALLEL_BOOLEAN_EXPERIMENT.md`, Finding 3) found a fresh resolve can
land on a pair that does not work together at all -- `cadquery-ocp` 8.0.1
drops `OCP.TDF.TDF_LabelSequence`, which `cadgen`'s STEP scene loader needs,
while the newest `cadquery-ocp` release old enough to keep it is too old for
newer `build123d`'s `OCP.collections` use -- and is the simplest explanation
for two Carry Forward builds hashing a part differently under no geometry
change.

`cadgen/pyproject.toml`, the CAD skill's `requirements.txt` and the root
`pyproject.toml` now all pin `build123d==0.11.1` and
`cadquery-ocp==7.9.3.1.1` -- the pair `uv.lock` already resolved and the one
`docs/PARALLEL_BOOLEAN_EXPERIMENT.md`'s own experiment ran against. This
follows the existing `Pillow>=10,<13` precedent: `tools/verify_skill_locks.py`
requires the Workshop to pin every CAD skill requirement exactly as the skill
declares it, so the root dependency list carries the same two specifiers.
This changes the `cad` fingerprint only; no script, gate or geometry
algorithm changed.

## Corrections carry unchanged parts forward by default (2026-09-21)

A Workshop-local change to the vendored `cad` and `make-round` trees, not an
upstream resync. Both SKILL.md files carry the same block: a `workshop fix`
run establishes its changed-part set by building and exporting every part and
hashing each against the source archive's `make/made.json` `product_manifest`,
and a part whose STEP comes out byte-identical keeps that archive's isolated
component round and its two per-part print-gate reports instead of
reproducing them. Nothing about the assembly is ever carried.

This is a default, not a permission the skills grant themselves. The host
already enforced the precondition: `make_round --require-component-passes`
rebuilds every part and refuses assembly review for any whose digest no longer
matches its recorded component pass, so a part that moved cannot be carried
even by a run that tried. What the block changes is the reading of ADR 0063
for a correction, which imports a product tree whose component histories
already pass.

The choice is frozen at run creation in the run-root `MAKE-OPTIONS.json` as
`carry_unchanged` under `schema_version: 2`, read by
`motion_policy.carry_unchanged()`. Schema 1 is unchanged and means "carry
nothing", so `workshop wish`, `workshop start` and `workshop fix --full` write
the exact pre-policy bytes and no existing checkpoint hash moves. A run created
before the policy existed has no schema-2 document, so it keeps its original
behaviour even after the legacy resume path refreshes its `cad` and
`make-round` copies from source -- the block conditions on the document, not
on the tool version. The corrections created while the policy was opt-in wrote
the field as `quick_fix`; both names read as the same choice, and a document
carrying both is refused rather than guessed. `motion_policy.quick_fix` stays
as an alias so a tool frozen into such a run still resolves.

Measured on the first run to use it (the Antisol Jove mirror, 2026-09-21):
20 of 24 printed parts were byte-identical and carried, saving 717 seconds of
component-round work read from the source archive's own `make_round` logs.
The remaining four were re-measured because their bytes moved, although the
movement was one `NEXT_ASSEMBLY_USAGE_OCCURRENCE` line and no geometry. See
ADR 0069 for the decision and its limits.

This changes the `cad` and `make-round` fingerprints.

## PETG Basic stock in the filament palette (2026-09-15)

A Workshop-local addition to the vendored `cad` and `image-to-cad` trees, not an
upstream resync: `cad/scripts/cadfilament.py` now holds two stocks instead of
one. Bambu Lab PLA Lite keeps its 13 colours and stays the default; Bambu Lab
PETG Basic adds 13 more -- `black` 30105, `white` 30106, `gray` 30107,
`misty blue` 30108, `red` 30201, `orange` 30302, `yellow` 30402,
`dark beige` 30403, `green` 30502, `pine green` 30503, `reflex blue` 30603,
`navy blue` 30604, `dark brown` 30800 -- with the sRGB hex from Bambu Lab's own
published "Filament Hex Code Table - PETG Basic", read 2026-09-15. `filament()`
and `filament_hex()` gain a keyword-only `material`; `MATERIALS` and
`DEFAULT_MATERIAL` join `FILAMENTS` in `__all__`, and `FILAMENTS` still names
the PLA Lite table so existing generators import unchanged.

Seven names sit in both tables and five of them are a different hex in each
(`black` and `orange` are the same colour in both stocks), so a colour name
alone no longer identifies a spool. `material` defaults to PLA Lite -- what
every colour authored before PETG was stocked already meant -- and a PETG-only
name asked for as PLA raises with the stock that carries it instead of resolving
to the nearest PLA colour, keeping the module's rule that a near-miss which
still builds is the failure worth preventing. An unstocked material raises the
same way.

Four reference files move with it: `cad/references/build123d-modeling.md`
(**Colour** carries both tables and the stock rule),
`cad/references/parameters.md`, `cad/references/organic-lofts.md` (a region
rounds to its own part's stock) and
`image-to-cad/references/build123d-operations.md` (a build spec names a stock
per part, not only a colour). The product-run Make reference is untouched here:
it still authors a leaf colour as sRGB channels on `Color(r, g, b)` rather than
through the palette, so it has no stock keyword to gain until that guidance is
reconciled with the `cad` skill's.

No gate reads the palette; it is a table a generator imports. Geometry, the
sealed STEP's linear RGB, `workshop.make.cad.step_color` and the print gates are
untouched, and a PETG part's print-in-place joints still take their looser gap
from `cadfits.print_in_place_gap(..., material="PETG")`, which already knew the
filament. The palette self-check passes 33/33 here, round-tripping all 26
colours to their published hex, and `tests/make/test_filament_palette.py` holds
the same contract plus the PETG codes. **Materialized instruction bytes
changed**: the `cad` and `image-to-cad` fingerprints in `LOCK.json` are new, so
a frozen run keeps its materialized skills and a parked one picks PETG up
through `workshop resume --refresh-tools`. Nothing here establishes that a PETG
part was printed.

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
  On 2026-09-14 the thickness and overhang Markdown writers again include
  their exact stdout `RESULT:` verdict. The refreshed upstream reports had
  omitted this summary while Workshop's frozen finalizer still required it.
  Passing and failing measured fixtures exercise the writer-to-finalizer
  contract; no measurements, thresholds or exit codes change.
  Geometry, measurement, inspection, validation, export, and `cadgen`
  algorithms are otherwise the reviewed upstream bytes.
- Adapted locally on 2026-09-21 so `render_review` rasterises whole batches of
  triangles instead of one at a time. A whole-set review frame carries over a
  million triangles, most of them smaller than a pixel, and the per-face pass
  cost a flat ~50 us each: about two hours of one measured correction run was
  software rasterisation. Face normals, flat shading and bounding boxes are now
  one array call each, and faces are drawn in batches padded to a power-of-two
  box. The depth test keeps its hysteresis exactly -- each pixel's candidates
  are applied in draw order, one layer at a time -- so which of two
  near-coincident faces is kept does not change. A differential test draws
  every scene twice, through the renderer and through the per-face pass it
  replaced, and requires identical pixels; on 1.44 M triangles at 900 px the
  frame falls from 83 s to 2.2 s with identical output. `tessellate_occurrences`
  also accepts the angular deflection (`--angular-tolerance`), which build123d
  defaults to 0.1 rad; runs that render curved form previously had to
  reimplement the routine to pass it. No view, colour, framing or verdict
  changes.
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
- Adapted locally on 2026-09-13 so the long motion tools count themselves down
  on stderr. `check_motion` names the assembly it is building, each condition
  as it starts, and reports `k/N, elapsed, ~left` through every sweep and
  through drive-evidence sampling; `motion_states.py` does the same per posed
  sample and per rendered animation frame. A multi-hour sweep was previously
  indistinguishable from a hang. Progress is stderr only, throttled
  (`WORKSHOP_PROGRESS_INTERVAL`, default 10s) and disabled by
  `WORKSHOP_PROGRESS=0`; stdout, geometry, hashes, verdicts and exit statuses
  are unchanged.
- Adapted locally on 2026-09-13 so a motion sweep is bounded. `check_motion`
  projects the sampled Boolean/distance operations a manifest asks for before
  the first sweep and accepts `--deadline SECONDS`
  (`WORKSHOP_MOTION_DEADLINE_SECONDS`); a condition that runs out of budget
  stops at the sample it reached and reports `inconclusive` with
  `deadlineStopped`, which fails the run even under `--allow-inconclusive`.
  `verify_project` passes a 900s default so an over-declared manifest cannot
  consume the whole verification. `motion_presentation.py` takes the same
  `--deadline` for its posing and rendering halves, which share one clock and
  write nothing unless both finish. Unbounded runs remain the default for
  direct invocations, and no geometry, threshold or verdict changed.

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

## Harness verdict projection (2026-09-14)

Workshop is also installed as a domain-specific harness of Autonomous Harness
(`harness.json` at the repository root; `harness/` holds the agent-facing
`AGENTS.md`, the workspace template, the toolchain scripts and the vendored 3D
viewer). Harness reads one file for its pane header, `.harness/verdict.json`,
so `cad/scripts/verify_project` gained `_write_harness_verdict`: at the end of
a quick or final run, and on a refused preflight, it projects the pipeline
record onto that file — `ready` only for a passing final run, one finding per
failing, skipped, noted or accepted-failing row, the combined entry's STEP as
the artifact. It runs only when `HARNESS_WORKSPACE` is set, which Harness sets
on the engine it launches and nothing else does, so Workshop's own product runs
write no extra file; it never raises. Upstream does not carry it; re-apply on
the next resync. `tests/make/test_harness_verdict.py` covers it.

## `mechanisms` (2026-09-18)

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `cf81f5113ffdb261e39f71166fe4aeae56509413` (2026-09-18), the commit that
  added the tree. It is pinned on its own and does not move the other five
  upstream trees off `facbc58`; the 36 upstream commits between the two
  revisions are not taken here.
- Reference only: `SKILL.md` plus eight `references/` pages on joints, gears,
  linkages, cams and intermittent drives, energy sources, automaton layouts,
  mechanism verification and a failure catalogue. It has no script, no gate
  and no dependency, and upstream changed no other skill in the same commit.
  Every tool and field it names — `cadfits.slot_for`/`peg_for`/
  `mating_clearance`/`print_in_place_gap`, `cadmount`, `check_motion`, and
  the manifest's `driven`, `obstacle_parts`, `retention`, `maxStepMm`,
  `maxOverlapMm3` and `assembly_sequence` — is present in the reviewed `cad`
  tree at `facbc58`.
- Local path adaptations, prose only. Upstream's bare
  `skills/cad/references/motion-manifests.md` (three places) and
  `skills/cad/scripts/cadfits.py` do not resolve in the materialized
  `.agents/skills` layout, so they read "the CAD skill's `references/...`" /
  "the CAD skill's `scripts/...`", the wording the product-run references
  already use. The failure catalogue's "this repository" names the upstream
  repository, and `SKILL.md` gains one paragraph saying `output/trotter`,
  `output/manta_ray` and `trotter-src` are upstream machines that are not
  materialized in a run, so an agent does not go looking for those paths.
  Lines were reflowed where a rewrite lengthened them; no rule, number or
  formula changed. Only `SKILL.md`, `joints.md`, `verification.md` and
  `failure-catalog.md` differ from upstream; `gears.md`, `linkages.md`,
  `cams-intermittent.md`, `energy-drive.md` and `automata-patterns.md` are
  byte-identical.
- No standalone license file in the pinned tree, like `design-reference`,
  `electromechanical-integration` and `image-to-cad`; this ledger does not
  infer an MIT grant for it.
- Motion checks remain opt-in (`MAKE-OPTIONS.json` `check_motion`, 2026-09-14).
  The design pages apply to any moving product; `verification.md` describes
  evidence only a `check_motion: true` run produces.

## `print-details`

Added 2026-10-01 (issue #79). Host-owned, not vendored: authored in this
repository and recorded in `LOCK.json` under this repository's URL, like
`make-round`. A one-file build123d library of printable decorative detail for
Component Workers -- rivets, round bosses, low domes, raised bands and rims,
half-round pipe ribs, inset panels with an optional lancet arch, windows and
grille slits. Each limit it enforces names the `wiki` page it comes from
(`printing/fdm-minimum-feature-sizes.md`,
`printing/wall-thickness-and-hollowing.md`,
`printing/overhangs-and-print-orientation.md`); the library reads those
numbers, it does not change the pages. Its `--self-check` runs the vendored
`cad` tree's own `check_thickness` and `check_overhang`, unchanged, on every
feature at its minimum and default sizes. It does not modify the vendored
`cad` or `wiki` trees, so a resync does not touch it, and it could be offered
upstream later. The Manager copies it into a CAD project as
`features/print_details.py` so the sealed project stays self-contained.

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

Spark component-first extension (2026-09-10, ADR 0063): `--component` gives
each `part_<role>.step.py` an isolated round history and visual packet;
`--require-component-passes` freshly builds every part and prevents assembly
review until all current component STEP bytes have passing isolated evidence.
The native Manager still supplies the visual judgment. Forge and Quest keep
their prior whole-product round sequence.

Sealed-reference extension (2026-09-24, ADR 0072): an assembly round now
scores every reference the Wish sealed under `wish-references/`, read from
`WISH.json` rather than from a ledger the Manager writes. A sealed reference
is skipped only when a current, passing component round already scored it at
or above the floor. A sealed reference that is missing or no longer matches
its hash, or a `WISH.json` that cannot be read, fails the round rather than
scoring nothing. The ledger parser also reads the Likeness handoff table row
of image-to-cad's build spec template. `ad-astra-antisol-v01` sealed eight
references, and its rounds scored none of them. The reviewed `cad` and
`image-to-cad` tools, and every threshold, are unchanged.

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

## Optional motion verification (2026-09-14)

Workshop adds `motion_policy.py` and opt-in motion handling to `verify_project`
and `make_round`, plus corresponding CAD and image-to-CAD guidance. New runs
freeze `MAKE-OPTIONS.json`; disabled checks and animation review remain
explicitly unverified. The underlying motion checker is unchanged.

Operator resume also defaults to false. Make-round's final verification uses
the current host-selected motion option instead of a previous round's option.

## Geometry inspection duplicate work and progress (2026-09-15)

A prolonged geometry-inspection delay was reported, but the affected model,
frozen tool tree and live process were unavailable. Source inspection found
two independently reproducible defects in the current tools:

- `validity._is_self_intersecting` constructed `BRepAlgoAPI_Check(shape, True,
  True)` and then called `Perform()` again. The shape-taking constructor
  already performs the complete check, as confirmed by
  [OpenCascade 7.9.3 source](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/BRepAlgoAPI/BRepAlgoAPI_Check.cxx).
  The redundant second call is removed; the same flags and result decoding
  remain. Topology, closure, signed-volume and self-intersection findings retain
  their existing semantics.
- `verify_project` captured inspection stderr until the entire batch exited.
  It now inherits stderr, matching the other verifier commands. Each batch
  request announces its id/command before work, then exit code and duration.
  `WORKSHOP_PROGRESS=0` suppresses these lines; JSONL and report verdicts retain
  their existing contract. This identifies the active request, not progress
  inside a single kernel call. No deadline or skipped gate is introduced.

Regression coverage includes live parent/child progress before completion,
quiet/loud JSONL equality, malformed/missing/failed batch results, kernel
exceptions, and real sound, overlapping, inverted and open geometry.
Isolated paired measurements on two archived parts (Cratercade access frame
and Tidal Crown white knight) confirm matching self-intersection verdicts with
roughly half the time in this one subcheck across three paired trials per part.
An exploratory timing set ran alongside regression tests; both parts were then
measured again after those tests completed, retaining all attempted trials in
private local evidence. These are subcheck measurements, not full-product runs
or evidence that the reported delay is resolved. Repeated occurrence validation,
pairwise interference cost and the affected machine remain unverified causes.
Existing materialized runs retain their frozen tools until a host tool refresh;
this source patch does not modify or resume any live run.

### Existing-run adoption

An operator's plain `resume` now adopts this correction once for an unfinished
run carrying CAD tools, including runs that already carry motion options.
The host recognizes a versioned marker in the hash-bound inspection reference,
refreshes the complete carried CAD skill from the installed source, and rebinds
the original native session before recording completion. Later resumes retain
that materialized tree. The native agent cannot modify its own tools. Other
domain skills, lifecycle instructions, review allowances, budget usage and
accepted product artifacts remain intact; ADR 0066's existing motion-option
migration still applies independently.

Regression tests use real immutable-input materialization and the actual saved
session rebind with deterministic native launchers. They cover plain CLI
resume, saved product/review/budget preservation, interrupted rebind and
completion recovery, changed motion choice on retry, idempotency, missing
installed correction, input tampering, pending Make refinalization and
read-only/terminal behavior. These are host contract tests, not a new native
Wish or the affected operator's session. See ADR 0067 for the migration boundary.

### Complete archived assembly replay

The full exported Cratercade assembly was replayed with the real `inspect batch`
CLI against baseline `78eb7203` and the corrected inspection code at `bfd07e96`.
The unchanged 35,213,424-byte STEP has SHA-256
`c7f89595204dcc2e1f8cbc52d61612ca189b456cebd9eeac3fbf7f42f017aa78`,
matching its public archive manifest. It loads as 542 occurrences and 181
geometry prototypes. The archived render was also checked against its manifest.

Both corrected trials and the completed baseline returned identical JSON
results: 542 occurrences with zero validity failures; 146,611 potential pairs,
1,838 exact intersection tests, 144,773 bounding-box rejections, zero truncated
pairs and zero clashes at the unchanged 1 mm³ tolerance. Self-intersection was
enabled, with no pair limit.

| Attempt | Baseline | Corrected | Conditions |
|---|---:|---:|---|
| 1 | Stopped at 600.03 s; no verdict | Passed in 408.78 s | Overlapped regression tests; corrected trial also overlapped the diagnostic below |
| 2 | Passed in 742.44 s | Passed in 401.34 s | Sequential runs, no regression tests or other geometry jobs alongside them |

The clean pair was about 46% faster on this assembly. The experiment's second
pair allowed 1,200 seconds per batch; no production timeout was introduced.
Environment: macOS arm64, Python 3.11.13, build123d 0.11.1 and cadquery-ocp
7.9.3.1.1. A separate instrumented diagnostic was deliberately stopped at 90
seconds after 223 occurrences completed; 43 nut checks consumed 72.73 of the
84.32 seconds spent inside those checks. It is a partial profile, not a gate
pass or a clean timing comparison. All attempted runs and raw outputs were
retained in private local evidence.

This establishes gate parity and reduced inspection time on an archived complex
model. It is one completed clean comparison plus an earlier corrected replay,
not broad reliability evidence. No new native Wish was launched, no geometry
was changed, and print/motion gates were not rerun. The affected Wish, frozen
tools and live process remain unavailable; the reported delay remains open.

## Local correction: cancellable geometry and unverified disclosure (2026-09-16)

CAD inspection now runs in a disposable worker with parent-enforced deadlines,
per-measurement progress, failure retention, atomic exact-input checkpoints,
one source build per adjacent request group and a bounding-box sweep for
collision candidates. Validity reuses rigid copies; intersection keys retain
world placement. Native operations preserve input geometry. Warm daemon
heartbeats no longer renew a request deadline, and an independent watchdog
bounds native code that holds the GIL. Make-round and final verification reap
owned child process groups and label timed-out analysis UNVERIFIED.

The explicit continuation policy is documented in ADR 0068. It changes the
handoff grade, not the truth of measurements: incomplete checks are sealed into
final geometry notes, README and public limitations, with no print-ready claim.
Measured failures and artifact/identity failures still block. Plain resume
adopts CAD, Make-round and the finalizer once under a recorded v2 correction;
existing session identity and consumed effort are preserved. This changes the
`cad` and `make-round` fingerprints. Raw model replay artifacts remain private.

Validation on the same archived 542-occurrence, 181-prototype assembly retained
byte-for-byte JSON verdict parity with the prior passing replay: validity had
zero failures, and interference tested all 1,838 bounding-box candidates out of
146,611 possible pairs, with zero clashes. The initial corrected run took
115.66 seconds; a fresh worker reusing completed measurements took 9.76 seconds.
A separate forced 12-second interruption retained 96 completed validity
measurements and returned UNVERIFIED. Resuming completed both checks with the
same verdicts; the subsequent repeat took 9.70 seconds. This is one complex
model replay, not a new native Wish or validation of the reported machine.
An earlier development run exposed native shape mutation causing cache misses;
copying validity inputs and non-destructive Boolean operations corrected it.

## Local change: the likeness gate leaves the Workshop pipeline (2026-09-29)

A Workshop-local change to the vendored `cad` and `image-to-cad` trees and to
Workshop's own `make-round`, not an upstream resync (ADR 0076). It supersedes
the likeness parts of the resync notes above: `verify_project` no longer runs
`check_likeness` and refuses `--likeness-ref`, `--likeness-min`,
`--likeness-accept-mismatch`, `--likeness-accept-regression` and
`--search-fov`; its `render_views` step keeps only the orthogonal renders and
the source-vs-STEP drift check. In Contract Mode it requires a current
component round that passed its checks and an independent review for every
sealed `geometry:<id>` image, and writes `component-acceptance.json` in place
of `likeness-acceptance.json`. `make_round` no longer calls `render_views
--match`; it composes each reference beside a `render_review` view at the
reference's declared camera and records a reviewer's judgement with
`--record-review`. `cad/SKILL.md` and its references drop the likeness
invocations, and `image-to-cad/SKILL.md` gains one note at Step 8 saying the
gate is not used inside Workshop. `render_views.py`, `check_likeness.py` and
`likeness-gate.md` keep their upstream bytes. This changes the `cad`,
`image-to-cad` and `make-round` fingerprints.

## Local change: make-round waits at a 300000 ms yield (2026-09-29)

A Workshop-local change to Workshop's own `make-round`, not an upstream resync
(ADR 0077). The Rules section now starts `make_round` and continues it with an
empty `write_stdin` poll at `yield_time_ms: 300000` instead of 30000. Codex
0.158.0 accepts an empty-poll yield from 5000 to 300000 ms and returns as soon
as the process exits, so the longer yield only removes re-sent polling
requests. This changes the `make-round` fingerprint.

## Local change: a component packet binds only its own and shared files (2026-09-30)

A Workshop-local change to Workshop's own `make_round` (ADR 0077). Component
Workers repair Components in parallel, and `--record-review` refused a review
as stale whenever any source or STEP in the project had changed since the
packet, including another Component's. A component round's visual packet now
binds its own `part_<id>.step.py` and STEP and every shared file, but no
longer another Component's own source or STEP. A shared helper edit still
stales every pending component packet, and the assembly packet still binds
everything. This changes the `make-round` fingerprint.

## Local change: component rounds record a worker nonce (2026-09-30)

A Workshop-local change to Workshop's own `make-round` (ADR 0080). `make_round`
accepts a hidden `--worker-nonce <32 hex>` on a component build round only and
records it as `worker_nonce` in that round's `summary.json`; any other use is a
usage error. The Workshop guard hook passes the nonce to a
`component-worker`'s call; the host refuses a component round whose nonce it
did not issue. The Rules section says who runs which call. This changes the
`make-round` fingerprint.

## Local change: the b149710 resync keeps the likeness gate out (2026-09-30)

Merging `main`'s resync to upstream `b149710` into `rein/remove-likeness`
kept every non-likeness upstream change and left out the upstream likeness
additions to the vendored `cad` tree: `verify_project --likeness-entry`
(scoring a part-only reference against its part entry), its camera-window and
routing self-checks, and the matching prose in `cad/SKILL.md` and
`references/image-derived-verification.md`. The likeness gate stays out of
the Workshop pipeline (ADR 0076). `render_views.py`, `check_likeness.py` and
`likeness-gate.md` keep their upstream `b149710` bytes. This changes the
`cad` fingerprint.

## Local change: Shape Rounds follow Component Reviews (2026-10-01)

A Workshop-local change to Workshop's own `make-round` (ADR 0081). One pure
`round_policy` decides admission, Shape Round counting and the lock of a
component round: a passing round must be reviewed before the Component's
geometry may change (a refused round exits 2, writes no round and puts back
the STEP it overwrote); a Shape Round is the first geometry change after a
disagreeing review; an agreeing review or a Component Acceptance locks the
Component until a Shared Helper it imports changes or the Manager records an
assembly unlock with the new root-only `--record-unlock`; a rerun of the
reviewed B-rep carries the review forward. A component packet binds only the
Component's own files and the Shared Helpers it imports, and a component round
that fails its checks is not rendered. This changes the `make-round`
fingerprint.

## Local change: a Component Review names its bound reviewer (2026-10-01)

A Workshop-local change to Workshop's own `make-round` (issue #77, extending
ADR 0081). When the Workshop host sets `WORKSHOP_REVIEWER_RUNTIME` (Claude
Code), `--record-review` requires `reviewer` to be the reviewer's native agent
id, binds a Component's first reviewer id in its component state and refuses
a review naming another id. Without it a review keeps the free-text reviewer
name. `SKILL.md` describes the fixed review request and the worker reading
the recorded review itself. This changes the `make-round` fingerprint.

## Local change: Interfaces between Components (2026-10-01)

A Workshop-local change (ADR 0082, issue #78) to Workshop's own `make-round`
and to the vendored `cad` tree. `make_round --shared-helpers` builds the
Manager's samples under `samples/` and runs `check_thickness` and
`check_overhang` on them, freezing the Shared Helpers by hash on a pass; under
a sealed contract with an Interfaces section a component round refuses to
start before that freeze and reports a frozen helper it imports that changed,
with the Components that import it. A new `make-round/scripts/check_envelope`
checks a separable Interface's Keep-out Envelope on a Component's B-rep in its
own round, and `make_round --interface <id>` runs `check_motion`'s
`coupled_motion_collision` on one Coupled Interface's locked Components,
unlocking the contract's yielding Component on failure.
`--require-component-passes` also needs a current passing check of every
Coupled Interface. In `cad`, `verify_project`'s Contract Mode component gate
applies the same Coupled Interface rule through `make_round` and writes the
Interfaces, each with its proof, into `component-acceptance.json`. Upstream
`check_motion` keeps its `b149710` bytes. This changes the `cad` and
`make-round` fingerprints.

## Local change: Shared Helper rules checked at the freeze (2026-10-01)

A Workshop-local change (ADR 0082) to Workshop's own `make-round`.
`make_round --shared-helpers` now checks the Shared Helper rules on every
helper a Component or sample imports before it builds a sample: each
module-level design value cites an existing page of the run's wiki with
`# wiki: <slug>` and appears in an `assert`; a function or class named for a
standard element needs `bd_warehouse` or `py_gearworks`; no helper names an
involute. The installed `features/print_details.py` is exempt only byte for
byte. A failure builds and freezes nothing. This changes the `make-round`
fingerprint.

## Local change: Interfaces between instances of one Unique Geometry (2026-10-01)

A Workshop-local change (ADR 0082, amended by #80) to Workshop's own
`make-round` and `cad/scripts/verify_project`. An Interface may name one
instance of a Unique Geometry, `<id>#<n>`. `make_round --interface` builds the
instance's Component once and places each referenced instance as its own
child labelled `<id>#<n>`, through `assembly_pose(shape, pose, instance)` and,
when it takes one, `gen_step(instance=n)`; it refuses a Component file whose
`assembly_pose` takes no `instance`. Locking, staleness and the unlock act on
the Component. `check_envelope --instance n` checks one instance against its
side of a Keep-out Envelope, and a component round runs one check per named
instance. The final verifier judges an instance on its Component's identity.
Upstream `check_motion` keeps its `b149710` bytes. This changes the `cad` and
`make-round` fingerprints.

## Local change: compare in the Display Pose at the Reference Camera (2026-10-02)

A Workshop-local change (ADR 0083, issue #81) to Workshop's own
`make-round`. Under a schema 3 Design Contract every sealed reference carries
its Reference Camera. A component round renders `compare-NN.png` from a
generated entry that returns the Component's `assembly_pose(shape, None)`
(the first instance when its `gen_step` and `assembly_pose` take one) at that
camera, under `visual/display-pose/`, while `front`, `top` and `iso` stay in
the print stance; an assembly round shows its sealed assembly reference from
its camera. A schema 3 component round of a file with no `assembly_pose` is
refused before anything is built. `--record-review` accepts a
`camera_mismatch` answer that names the reference and the landmarks each side
shows: it leaves the round policy awaiting review, spends no Shape Round,
writes `camera-mismatch.json` instead of `review.json`, and puts the need in
the summary. A camera the host amended in the run-root
`CONTRACT-AMENDMENTS.json` replaces the sealed one. Schema 1 and 2 contracts
keep the declared-camera-else-front comparison. This changes the
`make-round` fingerprint.

## Local change: print gates name the failing feature; blunt free edges (2026-10-02)

A Workshop-local change (issue #82) to the vendored `cad` tree and to
Workshop's own `print-details` and `make-round`. In `cad`, `printlib.py` gains
`entry_shape`, `printed_mesh` and the feature lookup the two gates share:
`check_thickness` and `check_overhang` now build the entry once, keep its
B-rep, and for each region they print name the nearest feature print-details
tagged in `PRINT_DETAIL_TAGS` (within 1 mm), else the nearest B-rep face, with
how far a failing region is past its limit. Failing regions are listed first.
An open tessellation is decided by the B-rep: an invalid solid fails with its
bad faces listed; a valid one is re-tessellated once at a quarter of the
deviation and half the angle, and measured if that closes it; one that stays
open exits 4 with `RESULT: UNMEASURABLE MESH`. Thresholds, the classifiers and
every self-check verdict are unchanged; `check_mesh` is unchanged. The
`check_overhang` self-check now passes per-sample slopes through `cluster`.

`print-details` tags every feature it makes with the caller's file and line,
and adds `bore` (teardrop), `blunt_tip` and `rib_end`, each in its
self-check. `make_round` records each gate's failing feature keys
(`defects`), a part's `repeated_defects` against its previous round and the
round's `repeated_print_defects`, and the gates' exit 4 as an `UNMEASURABLE`
verdict that fails `checks_ok` without counting as a print failure. This
changes the `cad`, `print-details` and `make-round` fingerprints.

## Local change: `check_mesh` reads the same mesh as the measuring gates (2026-10-02)

A Workshop-local follow-up to issue #82 in the vendored `cad` tree. The change
above left `check_mesh` on `entry_mesh` at the default deviation, so a valid
solid whose seam closed only at the finer retry passed `check_thickness` and
`check_overhang` in its component rounds and then failed `check_mesh`, which
`verify_project` runs first, at final verification. `check_mesh` now takes its
mesh from `printlib.printed_mesh` too: an invalid B-rep fails with its bad
faces listed, a mesh the finer retry closed is checked on that mesh (its
watertight line says so), and one that stays open exits 4 with
`RESULT: UNMEASURABLE MESH`. Every other `check_mesh` check and threshold is
unchanged, and `verify_project` still treats any nonzero exit as a failed mesh
gate. This changes the `cad` fingerprint.

## Local change: Interface text and Reference Conflicts (2026-10-02)

A Workshop-local change (ADR 0084, issue #83) to Workshop's own `make-round`
and `cad/scripts/verify_project`. Under a schema 4 Design Contract a component
round writes the Component's own contract, its geometry row, its requirement
rows and the `text` of every Interface naming it (`<id>` or `<id>#<n>`), into
`visual-packet.json` (bound by the packet hash) and `summary.json`, and its
contract-row hash covers those Interfaces. `--record-review` accepts
`reference_conflicts` beside `differences`, each naming a reference the round
compared, what it shows and what the contract requires; they may stand beside
an agreement, are kept out of `review.json` (in `reference-conflicts.json` and
the summary), carry with the review, and a disagreeing review with only
conflicts is refused. The final verifier notes each conflict and writes them
to `component-acceptance.json` as `reference_conflicts`. Schema 3 contracts
keep their cameras and Display Pose comparison under schema 4. Schema 1 to 3
packets carry no `contract`. This changes the `cad` and `make-round`
fingerprints.

## Local change: every Detail Refusal of a build at once, with a passing value (2026-10-02)

A Workshop-local change (issue #86) to the vendored `cad` tree and to
Workshop's own `print-details` and `make-round`. Every `PrintLimitError`
of `print-details` now carries `passing`, what would pass at that spot: the
limit for a size below it, the largest `d` or `width` the surface there
takes and the least height that clears it (both re-measured, not
estimated), the spacing that leaves the minimum gap between copies, or the
kind of spot when no size fits. While `WORKSHOP_PRINT_DETAILS_BUILD` is set
a refused feature returns its host unchanged and records its Detail Refusal
in `DETAIL_REFUSALS`; `refusal_error()` turns them into one
`DetailRefusals`, one `detail-refusal {json}` line each. Outside a build
every refusal still raises at once; `limits()` is unchanged, and the
self-check adds a collected three-refusal build. In `cad`, cadgen's
generator runner and `printlib.build_entry` set the variable while the
entry loads and runs, then raise the collected refusals, after any error
that stopped the build. `make_round` parses the lines into the part's
`build.detail_refusals`, prints a `refuse` line for each, records each
part's refusal keys in its state and reports a detail refused at the same
line in the previous round under `repeated_detail_refusals`, apart from
`repeated_print_defects`. This changes the `cad`, `print-details` and
`make-round` fingerprints.

## Local change: Blocked Reports a Component Worker records and the Manager clears (2026-10-03)

A Workshop-local change (issue #88) to Workshop's own `make-round`.
`make_round --component part_<id>.step.py --report-blocked BLOCKED.json`
records a Component Worker's Blocked Report in the CAD project's
`measure/blocked-reports.jsonl`: the Component, its latest round and the
contract rows it names, each checked verbatim (whitespace aside) against the
sealed Design Contract, bound to the run by the sha256 of `WISH.json`. The
Workshop Manager answers it with `--clear-blocked ANSWER.json`: a decision, a
decision waiting on another Component, or a need that quotes every row. A
waiting report stays open until that Component's next round whose checks
pass; that round's summary carries `wakes_blocked`, and `--blocked-reports`
marks the report woken. While any report is open or waiting an assembly
round and `--full` refuse to run. Nothing is built for a report or an answer.
This changes the `make-round` fingerprint.

## Local change: in-run Contract Amendments a fresh Contract Reviewer confirms (2026-10-03)

A Workshop-local change (issue #90, ADR 0085) to Workshop's own `make-round`.
`make_round --propose-amendment PROPOSAL.json` records the Workshop
Manager's Contract Amendment in the CAD project's
`measure/contract-amendments.jsonl`: two or more contract rows that cannot
both hold, verbatim, and the whole requirement or Interface texts it
replaces, bound to the sha256 of `WISH.json` and to the canonical-JSON hash
of the contract it amends. It writes a packet holding every sealed
reference by path and sha256 for a fresh `contract-reviewer`.
`--record-amendment-review REVIEW.json` records that reviewer's verdict; the
amendment applies only when the rows contradict, the change is the
smallest, and no reference shows it. Rounds then read the amended rows: the
rows a component round delivers, the rows a Blocked Report quotes, and the
contract-rows hash its review binds, so a locked Component whose rows
changed unlocks. `--clear-blocked {"report", "amendment"}` clears a Blocked
Report with an applied amendment that names it. While an amendment awaits
review an assembly round and `--full` refuse to run;
`--contract-amendments` lists them. Nothing is built for a proposal or a
review. This changes the `make-round` fingerprint.

## Local change: a motion state has no fixed byte limit (2026-10-03)

A Workshop-local change (issue #93, ADR 0060 amendment) to Workshop's own
`cad/scripts/motion_presentation.py`. `generate` no longer refuses a posed
state whose canonical encoding exceeds 20 MiB. That cap was the on-disk
`state-*.stl` artifact limit; since ADR 0062 the state is tessellated in
memory and bound only by hash, validation never checked its size, and it
fired after posing and rendering had finished, so it bounded neither memory
nor time. It did force a detailed toy to change locked, contract-required
rivets. Validation still rebuilds every state at the same fixed tessellation
and refuses one whose hash differs. `references/motion-presentation.md`
says not to simplify geometry for the animation. This changes the `cad`
fingerprint; materialized runs keep their copied bytes.
