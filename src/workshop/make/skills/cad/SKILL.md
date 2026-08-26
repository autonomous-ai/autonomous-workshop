---
name: cad
description: Create, modify, inspect, and validate STEP-first parametric CAD parts and assemblies. Use for natural-language CAD specs, reference images, 2D technical drawings, STEP/STP generation or direct inspection, Python CAD source, source-level joints, selector references, geometry facts, measurements, mating deltas, and secondary STL/3MF/native GLB outputs from CAD geometry.
---

# CAD generation, inspection, and validation

Provenance: maintained in [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad).
Use the installed local skill files as the runtime source of truth; the
repository link is only for provenance and release review.

## Purpose

Create or modify parametric CAD models from natural-language requirements, generate validated STEP/STP artifacts, inspect geometry references, and return checked outputs. Treat STEP as the primary CAD artifact. Treat STL, 3MF, and native GLB as secondary export workflows that branch from a STEP-first process. For assemblies, prefer `cadgen.assembly.AssemblyHelper` with source-level build123d joints, named mating datums, and native labels when the parts have functional assembly relationships.

There are two ways into the STEP workflow: generate from build123d Python source (the default when designing from scratch or modifying a generated model), or import an existing STEP/STP file directly (when no generator exists or the user explicitly targets the STEP file). Both produce the same inspectable artifacts.

## Use this skill when

Use this skill when the user asks for CAD files, STEP/STP files, build123d source, selector refs such as `#o1.2.f1`, mechanical parts, assemblies, enclosures, brackets, fixtures, holes, counterbores, countersinks, slots, pockets, bosses, standoffs, ribs, fillets, chamfers, shells, source-level joints, mating, or measurements. Also use it when the user supplies reference images or 2D technical drawings of a part to reproduce or take design intent from.

Also use it when the user asks for STL, 3MF, or native GLB output from CAD geometry. Keep those workflows secondary and load `supported-exports.md` for details. For 2D DXF drawings, use the `$dxf` skill; when a DXF projects from a 3D part, this skill owns the STEP geometry and `$dxf` owns the drawing.

Do not use this skill for render-only concept art, CAM toolpaths, engineering certification, FEA conclusions, architectural BIM, or freehand illustration unless the user also needs CAD geometry.

## Default assumptions

Use these defaults unless the user specifies otherwise. These are first-pass modeling defaults, not manufacturability, tolerance, or certification claims:

- Units: millimeters.
- Origin: per the part-type defaults in `references/positioning.md`; center of the main part or assembly when nothing better applies.
- Base plane: XY.
- Up/extrusion axis: positive Z.
- Output geometry: closed, positive-volume solids unless the user requests surfaces or construction geometry.
- STEP structure: one valid solid, a compound of solids, or a labeled assembly compound.
- Assembly structure: fixed root part, part-local frames, named mating datums, `AssemblyHelper` relationships backed by build123d joints where applicable, explicit generated placements, and verbose native labels.
- Small plastic enclosure wall: 2.0-3.0 mm when unspecified.
- Cosmetic fillet: 1.0-3.0 mm when safe for local geometry.
- M3/M4/M5 normal clearance holes: 3.4/4.5/5.5 mm unless another standard is requested.

Ask one focused clarification question only when missing information makes the model impossible, fit-critical, safety-critical, or compliance-bound. Otherwise proceed with explicit assumptions. Ask only about preferences that change the geometry — what the object is for, the device it has to fit, a style the user cares about. Decide every engineering choice silently from the defaults and references above: wall thickness, clearance, fillet radius, fastener and joint type, print orientation. Those are never questions.

## Tools and paths

Resolve the materialized CAD skill once instead of assuming a repository
checkout layout:

```bash
CAD_SKILL_ROOT="$(workshop skills path)/cad"
python "$CAD_SKILL_ROOT/scripts/gen" ...             # render GLB/topology packages from gen_step() Python sources
python "$CAD_SKILL_ROOT/scripts/export" ...          # STL/3MF/GLB mesh files from Python sources or imported STEP
python "$CAD_SKILL_ROOT/scripts/inspect" ...         # refs, measure, align, frame, diff
python "$CAD_SKILL_ROOT/scripts/artifact" ...        # debug one on-demand render-package build (imported STEP)
python "$CAD_SKILL_ROOT/scripts/verify_project" ...  # sequential quick/final project pipeline
```

If the host supplies the materialized skill directory directly, use that exact
directory for `CAD_SKILL_ROOT`. Run these commands from the project that owns
the artifacts so target paths resolve inside the product workspace.

**A run is expensive.** The measured cost of every command, and which to run per round versus once at the end, are in `references/run-cost.md` — read it before planning a run, because `inspect validate` and `inspect interfere` are more than half the cost between them and belong at the end, once.

Use the active project Python interpreter; treat `python` in examples as an
interpreter placeholder. Use
`python "$CAD_SKILL_ROOT/scripts/<tool>" --help` for the complete current
command interface; reference docs show recommended workflows, not every flag.

**Bootstrap before the first run, not after the first failure.** `requirements.txt` pins `cadgen`, which needs **Python ≥ 3.10** — a macOS system `python3` is often 3.9 and will fail at import, so create a project venv on a modern interpreter rather than pip-installing into the system one, then `python -m pip install -r <skill-dir>/requirements.txt`. That one line is enough for every script here: `numpy` and `scipy` arrive with `build123d`, and `shapely` — which `repair_mesh` needs — with `cadgen` itself. Check that up front; discovering it mid-workflow costs a full build round.

**Streams.** stdout carries the result; stderr carries progress, timing, and failures. Every tool answers on stdout — `gen` prints `<outcome> <package path>` per target — so `2>/dev/null` leaves something parseable and `>/dev/null` leaves a readable log. JSON on stdout is always compact; pipe through `jq .` to read it. The two never interleave, so `2>/dev/null` leaves a clean parseable result and `>/dev/null` leaves a readable log. For machine-readable output: `gen` and `export` take `--json`; `inspect` already emits JSON and takes `--format text` for prose. `--verbose` adds stage timing (and full tracebacks) on stderr. Output volume does not grow with model size — a 600-occurrence assembly logs the same dozen lines a single part does.

**Failures** print the exception and the frames *in your own generator*, not the runtime's:

```text
[scripts/gen] FAILED: ValueError: bad radius
[scripts/gen]   <project-dir>/<name>.step.py:9 in gen_step
[scripts/gen]       return _profile(radius)
[scripts/gen] re-run with --verbose for the full traceback
```

**A build waits for a concurrent build of the same model** rather than racing it, and says so on stderr (`waiting for another run to finish building ...`), repeating while it waits. Pass `--lock-timeout SECONDS` to give up instead and report `{"ok":true,"contended":true}`. With `--json`, each target's `outcome` is `built`, `current`, `skipped-peer` (the peer finished and its package is current), or `contended` (the peer is still building and this run declined to wait).

**Do not launch warm CAD CLIs concurrently.** The daemon shared by one
materialized CAD skill tree handles requests strictly sequentially, so parallel
clients only queue invisibly and can outlive the orchestration call that
launched them. Give all affected targets to one multi-target `scripts/gen`
call, and use `scripts/inspect batch` for several inspection requests.
`inspect batch` reads JSONL from stdin and therefore runs as one cold process
even when `CADGEN_WARM=1`; it still pays the heavy import only once.

Target paths resolve from the command's current working directory, not from the skill directory. Run commands from the workspace that owns the artifacts and pass cwd-relative target paths so project CAD files never resolve accidentally under the skill directory. Keep a STEP output and its Python generator in the same directory with the same basename unless the user explicitly requests otherwise.

CAD references are `#...` selector tokens local to a target, for example `#o1.2` or `#o1.2.f1`. Pass the STEP/CAD file as a separate target argument when using CAD CLIs.

## Required workflow

Scale depth to the task: a simple part needs a short brief and few spec-driven checks; assemblies and fit-critical work need full positioning and alignment validation.

Use two execution phases. During **quick iteration**, build only the entry
needed to review the current edit (normally the combined assembly), and rerun
only checks whose relationships changed. During **final verification**, rebuild
every affected entry together, write the STEP files, run every mandatory gate,
and export requested meshes. Quick iteration never substitutes for the final
gate.

1. **Classify the task.** New part, new assembly, source modification, direct STEP/STP inspection, reference selection, measurement/alignment check, or secondary output request.
2. **Load only the needed references.** Use the triggers below instead of reading the whole reference set.
3. **Write a natural-language CAD brief.** Extract dimensions, units, coordinate convention, feature intent, output paths, assumptions, and validation targets from all provided inputs — prose, reference images, technical drawings. Use `references/cad-brief.md`.
4. **Check purchasable components — by name AND by form.** Two triggers, and the second is the one that gets missed. **By name:** the brief calls out an off-the-shelf actuator, servo, motor, electronics board, or connector. **By form:** you are about to author procedural geometry for a standard mechanical element — a gear, bearing, bolt, screw, nut, washer, rivet, pin, spring, bushing, o-ring, circlip, chain, belt, pulley, coupling, hinge, caster, magnet, or threaded insert. A form trigger fires even when nothing names the part, which is exactly why writing your own `spur_gear()` or `hex_bolt()` helper must stop and search `$step-parts` first. Search on the governing numbers (module and tooth count, bore and OD, thread and length), not on prose. If the API was reachable and returned nothing, that is a **recorded miss**: write it into the brief's component table and into the final response, then use a documented envelope. An unreachable API is inconclusive — retry with network permission rather than calling it a miss.
5. **Plan before coding.** Decide the printed-part count first — default to one, and split only against the test in `references/project-structure.md` — then define parameters, intent labels, source paths, expected bounding boxes, and any mating/positioning datums before editing. **The printed-part count does not decide the file count.** "One printed part" is an answer about geometry; step 6 asks a separate question about layout, and a single-piece display model still gets split across files once it crosses the thresholds there.
6. **Edit source, not generated artifacts.** Author build123d Python with `gen_step()`, naming a buildable entry generator `<name>.step.py` (helper/library modules stay `<name>.py`; see `references/step-generation.md`). A model with separately printable parts, 3+ named parts, or more than ~120 lines of geometry gets a project directory rather than one file — `references/project-structure.md` carries the layout, the filename rules, and the editing discipline. **A split project always carries both halves: one combined `<name>.step.py` that places every part, and one `part_<role>.step.py` per part. Neither substitutes for the other** — the combined entry is what gets reviewed and exported, the part entries are what get opened and edited. Run `scripts/check_layout <project-dir>` before `scripts/gen`; it is static, costs milliseconds, and exits non-zero naming the file to split. **Once part entries exist, the layout in `references/project-structure.md` is mandatory rather than advisory**, and `check_layout` enforces the tier too: a project with `part_*` entries whose importable modules pass ~400 code lines is Tier 3 (`params.py` + `parts/` + `features/` + `assemblies/`), not a bigger `_lib.py`. Outgrowing Tier 2 is invisible to every other gate — a 700-line library builds, validates, and passes interference, motion and mesh exactly like a healthy one. When a Python generator exists, run `scripts/gen` on the generator, never on its exported STEP. Imported STEP/STP files (no generator) need no build step: `scripts/inspect` and `scripts/export` read them directly.
7. **Generate explicit targets.** Run `scripts/gen` on explicit generator targets only; do not run directory-wide generation. Pass all affected targets to one invocation instead of starting one process per entry. Add `--write` when the user needs the `.step` file itself, and use `scripts/export` when they need STL/3MF/GLB mesh files. For secondary geometry-only exports after a successful `--write`, prefer the fresh STEP target so export does not invoke the Python builders again.
8. **Validate geometrically.** Run `scripts/inspect refs <step-or-cad-target> --facts --planes --positioning` as the baseline, then verify the dimensions and relationships the user's spec calls out with targeted `measure`, `align`, `frame`, or `diff` checks. Put several independent requests through one `scripts/inspect batch` process; do not parallelize warm `inspect` calls. Run `scripts/inspect validate <step-or-cad-target>` for geometry soundness: `refs --facts` reports counts and bounds, and its `ok` field covers ref resolution only — an open shell and an inverted solid both pass it. For an assembly, also run `scripts/inspect interfere <step-or-cad-target>`: nothing else in the toolchain answers whether two parts occupy the same space, and no render can establish the *absence* of a clash — least of all one hidden inside the assembly.
9. **Reconcile image-derived work.** When the project came from an image/spec, every source repair that changes a parameter, landmark, part count, or construction family must be reconciled back into the approved `*_spec.md`. Give every landmark a local geometry target, render the orthogonal set plus every usable reference viewpoint, compare source against STEP, and run the likeness gate. `references/image-derived-verification.md` defines the two local audits and the integrated `verify_project --image-derived` command.
10. **Repair and rerun.** If a check fails, change the smallest responsible source section, regenerate, and rerun the failed validation.

## Handoff

CAD soundness stays deterministic: `scripts/inspect` (refs, validate,
interfere, measure, align, frame, diff) plus the project gates (`check_layout`,
`check_fit`, `check_mesh`, `check_motion`, `check_mount`, `check_thickness`).
For image-derived projects, `verify_project --image-derived` additionally uses
the sibling `image-to-cad` renderer and likeness gate; those visual checks do
not substitute for any geometry gate. Report the checks that actually ran and
their results; a claim needs the check that produced it, never an unaudited
visual impression.

Autonomous Workshop materializes the sibling `image-to-cad` and
`design-reference` skills beside this tree. Use `image-to-cad` for a direct
reference-image reconstruction and its required likeness evidence.

## Non-negotiables

- Keep STEP as the primary validated CAD artifact. Generated STEP/STP, STL, 3MF, GLB/topology outputs, and render sidecars are derived artifacts; STL/3MF are secondary unless the user explicitly says otherwise.
- Use named parameters, closed solids, verbose native build123d labels, and source-controlled geometry intent.
- Author assembly positioning in source. `references/positioning.md` is authoritative for `AssemblyHelper`, build123d joints, explicit `Location` transforms, and alignment validation.
- Do not use `git status`, `git diff`, or file-size churn as CAD comparison for large exported STEP/STP, GLB/topology, STL, or 3MF artifacts. Compare source changes, `scripts/inspect` summaries, or generated topology output instead; use path-limited git status only for bookkeeping.
- Every entry generator defines exactly one `gen_step()` at module scope, and returns the shape; output paths belong to the CLI flags, never to the return value.
- Do not declare image-derived CAD complete while its spec and source disagree, a defining landmark lacks a local geometry target, a reference viewpoint is omitted, source-vs-STEP comparison finds drift, or any likeness pair is below 0.90. Run `scripts/verify_project <project> --image-derived --likeness-ref LABEL=PATH` with every usable reference. The mode requires `measure/check_spec.py` and `measure/check_landmarks.py` precisely because a generic gate cannot infer those project-specific claims. See `references/image-derived-verification.md`.
- Do not declare the work done while any of these stands: a `validate` finding (`invalidTopology`, `openShell`, `nonPositiveVolume`, `noSolid`, `selfIntersecting`) that is not an intended surface model, a clash reported by `interfere`, a part floating free of the assembly it belongs to, or a feature you cannot justify against the brief. Repair the source and rerun the check that failed. An `{"ok":false}` that names no finding is usually not this model: `cadgen` resolves even an explicitly named target by scanning the whole worktree for generators, so one stale `*.py` with a pre-migration `gen_step()` envelope takes `validate` and `refs` down for every model at once. Check for that before editing geometry — `references/run-cost.md`.
- Do not declare the work done while `scripts/check_layout` exits non-zero on the project. A generator over the step 6 thresholds with no `part_*.step.py` beside it is unfinished work, not a style preference — no geometry check catches it, which is exactly why it is listed here. The same applies to `oversized-library`: **once a project has part entries it owes the full layout**, and a library that has passed the Tier 3 threshold is over the line whether or not the model is otherwise perfect. Migrating up a tier is a pure move, so prove it is one — fingerprint every entry's volume, solid count and bbox from source before and after, and diff.
- Do not declare a part printable while `scripts/check_fit` exits non-zero on the project. It builds every `part_*.step.py` and checks the four things no other check covers: the part sits on the bed (`min(Z) == 0`), its footprint fits, it has positive volume, and the generator runs. A part still in assembly coordinates passes `validate` and `interfere` and cannot be printed. The gate reports, but does not fail on, disconnected bodies and a missing per-project audit; those two need a human to read the README, and `--strict` promotes them. `scripts/check_fit` reads the source; run `scripts/check_mesh <part>.stl` on every exported STL beside it, which reads the artifact the slicer gets -- watertight, manifold, winding, one shell, positive volume, bed. They answer different questions, and when they disagree the export is stale. A non-manifold edge fails there: the subject is one printed part, so an edge four faces share is a defect however normal it is between two bodies (`--assembly` demotes it for a combined STL). `scripts/repair_mesh` fixes slivers, holes and non-manifold vertices in the artifact, but it does not close the loop -- the next `export` writes the broken mesh again, so repair the source and say in the README when a shipped STL is repaired rather than generated. See `references/repair-loop.md`.
- Do not declare an assembly assemblable from `validate` and `interfere`. They answer whether the parts are sound and whether they overlap once assembled, never whether they can be brought together, and never whether a connector holds. Where parts insert, slide, hinge, or latch, declare the motions in a manifest and run `scripts/check_motion <project> --manifest <file>`. Write both directions of every joint — the one it assembles along, and the one it must not, via `"expect": "blocked"`. A dovetail that is only checked for coming apart passes as a plain pocket. See `references/motion-manifests.md`.
- Do not declare a part print-ready without measuring what it costs to print. `scripts/check_thickness <part>.stl --nozzle 0.4` fails a wall under two extruded lines -- which a slicer drops or prints as two perimeters with a gap, while the STEP stays perfect -- and reports the material a shell would remove. Hollow in the source with `scripts/cadprint.py`, never with a bare `offset(solid, -wall)`: that shrinks the solid rather than shelling it, and every gate passes the undersized result. See `references/print-optimisation.md`.
- Do not declare a multi-segment organic body finished without asserting its **solid count in the source**. `validate` and `interfere` both pass a body whose tail is a separate solid resting against it — a loft's end cap is a plane normal to its own tangent, so a segment that starts where the previous one "ended" starts outside it. `assert len(shape.solids()) == 1` is the only thing that catches it. See `references/organic-lofts.md`.
- Delete the project's `__cadgen__/` after editing a shared `*_lib.py`, before the next build. `scripts/gen` does not notice that a sibling library module changed and `--force` does not repair it: you get `built` on stdout and the **previous** geometry in the `.step`. This is expensive because `validate` and `interfere` agree with each other about an artifact that no longer matches its source. The image-derived runner now adds a three-view source-vs-STEP comparison, but silhouettes can miss an internal change; clearing the cache remains mandatory rather than relying on that partial detector. See "Shared-library cache defect" in `references/step-generation.md`.
- Do not size the two halves of a mate independently. Derive the second from the first with `scripts/cadfits.py` — `peg_for(bore, "slip")`, `slot_for(pin, 0.15)` — so the clearance is applied once, in one place. A pair written by hand as `hole = PIN_D + 2 * PIN_CLEAR` with the pin in another file cannot be audited afterwards: the only check available restates the arithmetic and reduces to `True`, so it passes whatever the geometry does. This is structural, not a preference — no gate in the toolchain catches a mate that was typed twice and drifted. See `references/parameters.md`, "Derive The Second Half Of A Mate".
- Do not declare a model able to hold a bought part while `scripts/check_mount` exits non-zero on the project. Deriving a seat with `cadmount` is not proof the model has one: the generator may never have subtracted it, may have cut it in the wrong place, or may have added a feature later that ate half of it, and `validate`, `interfere`, `check_fit`, `check_motion` and `check_mesh` pass all three. The gate places the component's own STEP into the combined entry at a declared pose and measures the built solids — clash, clearance, and whether a screw can reach each hole of the component's own mounting pattern from either side. Declare the mounts in `measure/mounts.json`; `"bolts": false` is the escape hatch for a strapped or glued component. See `references/bought-parts.md`.
- Do not type a bought part's dimensions into a generator. A servo, gearmotor, bearing or board owns its dimensions in a datasheet rather than in the repository, so a pocket sized by hand cannot be audited by anything — every gate here passes a bracket whose seat is 2 mm too shallow for the motor it was drawn for. Fetch the component's STEP with the `step-parts` skill into `<project-dir>/ref/`, and derive the cavity from it with `scripts/cadmount.py` — `seat_for(part, "slip")`, `bolt_cutter(part, depth=...)`. Never grow the component with `offset(solid, +clearance)` to make that envelope: on the step.parts SG90 that silently drops the output hub and returns a solid 2.9 mm **shorter** than its input, and the bracket cut from it validates. See `references/bought-parts.md`.
- Keep local fit audits algebraic where a generic gate already builds geometry: assert shared base dimensions, clearance application, and connector naming locally; let `check_fit`, `validate`, and `check_mesh` own solid/body/mesh checks. Rebuilding all shapes in both places is slower without adding a distinct claim.
- Never call a model sound, printable, or fit-correct from reading the source. The claim needs the check that actually ran.
- Report only checks that actually ran or are directly supported by tool output.

## Progressive references

Load these files only when their trigger applies:

- `references/cad-brief.md` — converting prose, reference images, and technical drawings into a CAD brief.
- `references/build123d-modeling.md` — build123d modeling patterns, topology, selectors, features, labels.
- `references/organic-lofts.md` — freeform bodies: station tables, the loft frame that does not degenerate on a vertical spine, why consecutive segments must overlap rather than meet, the one-body assertion, section families, and per-region colour. **Load for any animal, figure, hull, or body whose section changes along a curved spine.**
- `references/step-generation.md` — STEP generation from Python source, direct STEP/STP imports, and post-generation steps.
- `references/project-structure.md` — how many printed parts a design should have, and how to split the model across files once it outgrows one: project layout, entry/library filename rules, import resolution, companion files, and the editing rules for parameters, features, parts, and assemblies.
- `references/inspection-and-validation.md` — validation sequence, selector refs, facts, planes, measurements, alignment, diff, frame, and validation reporting.
- `references/image-derived-verification.md` — spec/source reconciliation, landmark audits, source-vs-STEP renders, reference-pose matching, and the integrated final gate. **Load for every project built from photographs or illustrations.**
- `references/motion-manifests.md` — motion-manifest schema, the `expect: blocked` capture form, assembly sequences, and what a rigid-body sweep cannot answer.
- `references/positioning.md` — part-local datums and origins, assembly transforms, build123d joints, CLI alignment validation, and positioning reports.
- `references/parameters.md` — parameterizing a STEP model: source parameters, naming, defaults and bounds, deriving the second half of a mate with `scripts/cadfits.py`, and how a parameter change is confirmed.
- `references/bought-parts.md` — seating an off-the-shelf component: fetching its STEP, deriving the cavity and the screw pattern from that file with `scripts/cadmount.py`, why offsetting an imported solid loses features, and what a derived seat still cannot answer. **Load whenever the model has to hold a motor, servo, bearing, board or any purchased part.**
- `references/run-cost.md` — the measured cost of every command, which checks to run per round versus once at the end, the two incompatible `--bed` flag forms, and why a stale generator anywhere in the worktree breaks `validate` for every model.
- `references/supported-exports.md` — STL/3MF/native GLB mesh export workflows via `scripts/export`.
- `references/repair-loop.md` — diagnosis and repair procedures, including the source fixes for the mesh defects `check_mesh` fails on.
- `references/print-optimisation.md` — wall thickness, hollowing, and why `offset(solid, -wall)` shrinks rather than shells.

Final responses should include generated files, validation actually run, assumptions, and caveats. Use `references/inspection-and-validation.md` for report structure.
