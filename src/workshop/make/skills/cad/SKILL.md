---
name: cad
description: Create, modify, inspect, and validate STEP-first parametric CAD parts and assemblies. Use for natural-language CAD specs, reference images, 2D technical drawings, STEP/STP generation or direct inspection, Python CAD source, source-level joints, selector references, geometry facts, measurements, mating deltas, and on-request native GLB viewing exports from CAD geometry. Do not use during a host-identified Workshop v8/v9 early-proof turn; use the host's exact proof commands and load this broad skill only after the proof marker.
---

# CAD generation, inspection, and validation

Provenance: maintained in [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad).
Use the installed local skill files as the runtime source of truth; the
repository link is only for provenance and release review.

## Purpose

Create or modify parametric CAD models from natural-language requirements, generate validated STEP/STP artifacts, inspect geometry references, and return checked outputs. STEP is the only format this skill writes. There is no mesh export of any kind — no STL, no 3MF, no GLB deliverable. Printability is gated separately by `verify_project --print-gates`, which tessellates each printable entry in the gate and writes nothing; call an output print-ready only when that run passed. For assemblies, prefer `cadgen.assembly.AssemblyHelper` with source-level build123d joints, named mating datums, and native labels when the parts have functional assembly relationships.

There are two ways into the STEP workflow: generate from build123d Python source (the default when designing from scratch or modifying a generated model), or import an existing STEP/STP file directly (when no generator exists or the user explicitly targets the STEP file). Both produce the same inspectable artifacts.

## Use this skill when

Use this skill when the user asks for CAD files, STEP/STP files, build123d source, selector refs such as `#o1.2.f1`, mechanical parts, assemblies, enclosures, brackets, fixtures, holes, counterbores, countersinks, slots, pockets, bosses, standoffs, ribs, fillets, chamfers, shells, source-level joints, mating, or measurements. Also use it when the user supplies reference images or 2D technical drawings of a part to reproduce or take design intent from.

A request for an STL, a 3MF, a GLB, or any sliced/printable mesh has no workflow here — say that STEP is the deliverable, rather than improvising an export. If what the user actually wants to know is whether it prints, run `verify_project --print-gates`: that answers the question without producing a mesh. The only mesh this toolchain builds is the `__cadgen__/` render package that `inspect` and the viewer rebuild on demand, and it is not a deliverable. For 2D DXF drawings, use the `$dxf` skill **when it is installed**; when a DXF projects from a 3D part, this skill owns the STEP geometry and `$dxf` owns the drawing. `$dxf` is a separate sibling skill and does not travel with this one, so check for it before promising a drawing.

Do not use this skill for render-only concept art, CAM toolpaths, engineering certification, FEA conclusions, architectural BIM, or freehand illustration unless the user also needs CAD geometry.

## Copying assembly subsets for handoff

Do not use `copy.copy()` or `deepcopy()` on already-parented build123d
components to collect STEP handoff groups. Their copy implementation can clone
and retain the whole parent assembly for every selected child. Use
`cadgen.assembly.copy_subtree()` for a geometry-only snapshot of the selected
subtree; read the local-coordinate and metadata contract in
`references/positioning.md` before grouping those snapshots. This does not
replace production-part definitions, required exports, verification or seals.

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
python "$CAD_SKILL_ROOT/scripts/inspect" ...         # refs, measure, align, frame, diff
python "$CAD_SKILL_ROOT/scripts/artifact" ...        # debug one on-demand render-package build (imported STEP)
python "$CAD_SKILL_ROOT/scripts/render_review" ...   # browser-free shaded PNGs for appearance review
python "$CAD_SKILL_ROOT/scripts/verify_project" ...  # sequential quick/final project pipeline
python "$CAD_SKILL_ROOT/scripts/render_product" ...  # shaded RGB product PNG from an exact STEP state
```

If the host supplies the materialized skill directory directly, use that exact
directory for `CAD_SKILL_ROOT`. Run these commands from the project that owns
the artifacts so target paths resolve inside the product workspace.

**Workshop v8/v9 proof deferral.** When the immutable Make packet and host prompt
identify a frozen v8 or v9 proof turn, this broad skill is deliberately not
applicable yet. The host supplies the exact `gen`, `export`, and
`render_product` command shapes. Follow that narrow interface without loading
this file, `run-cost.md`, progressive references, or `--help` output. Load this
skill after the checkpoint-bound proof-ready marker exists and use the full
workflow for final Make. Deferral does not waive final CAD checks or permit
guessing an interface the host did not supply.

`python "$CAD_SKILL_ROOT/scripts/verify_project" --self-check` runs the runner's own validation
fixtures — the refusals that decide whether a gate is required at all — in a
temporary paper project, with no geometry and no daemon. Run it after touching
that file: a guard that stops firing does not fail, it just stops appearing.
The final runner collects failures from every independent cheap preflight gate
before it stops, and `--print-gates` collects mesh/overhang/thickness failures
across every printable target. Read the complete failing report and repair the
whole batch before rerunning; dependent checks remain explicitly skipped when a
prerequisite failed.

**A run is expensive.** Outside the Workshop v8/v9 proof deferral, the measured
cost of every command, and which to run per round versus once at the end, are
in `references/run-cost.md` — read it before planning a run, because `inspect
validate` and `inspect interfere` are more than half the cost between them and
belong at the end, once.

Use the active project Python interpreter; treat `python` in examples as an
interpreter placeholder. Use
`python "$CAD_SKILL_ROOT/scripts/<tool>" --help` for the complete current
command interface except during the Workshop v8/v9 proof deferral; reference
docs show recommended workflows, not every flag.

**Bootstrap before the first run, not after the first failure.** `requirements.txt` pins `cadgen`, whose own metadata declares `requires-python = ">=3.11"` — a macOS system `python3` is often older and pip will refuse to resolve it, so create a project venv on a modern interpreter rather than pip-installing into the system one, then `python -m pip install -r <skill-dir>/requirements.txt`. That one line is enough for every script here: `numpy` and `scipy` arrive with `build123d`, and `shapely` — which `repair_mesh` needs — with `cadgen` itself. Check that up front; discovering it mid-workflow costs a full build round.

**Streams.** stdout carries the result; stderr carries progress, timing, and failures, and the two never interleave. Every tool answers on stdout — `gen` prints `<outcome> <package path>` per target — so `2>/dev/null` leaves a parseable result and `>/dev/null` a readable log. JSON on stdout is always compact; pipe through `jq .` to read it. For machine-readable output: `gen` and `export` take `--json`; `inspect` already emits JSON and takes `--format text` for prose. `--verbose` adds stage timing (and full tracebacks) on stderr. Output volume does not grow with model size — a 600-occurrence assembly logs the same dozen lines a single part does.

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
every affected entry together, write the STEP files, and run every mandatory
gate — including `--print-gates` whenever the work will be printed or called
printable. Quick iteration never substitutes for the final gate.

1. **Classify the task.** New part, new assembly, source modification, direct STEP/STP inspection, reference selection, measurement/alignment check, or secondary output request.
2. **Load only the needed references.** Use the triggers below instead of reading the whole reference set. Each one you load is re-sent on every later round.
3. **Write a natural-language CAD brief.** Extract dimensions, units, coordinate convention, feature intent, output paths, assumptions, and validation targets from every input — prose, reference images, technical drawings. Use `references/cad-brief.md`. For an image-derived build spec, **section 6g is the design contract**: implement the exterior, mechanical, electrical, lighting and bought-device selections it already made. Do not reopen the candidate search or invent a different mechanism, topology or MPN during CAD. If an active domain is missing or incomplete, return it to the analysis phase rather than hiding the gap behind a generic stand-in.
4. **Check purchasable components — by name AND by form.** **By name:** the brief calls out an off-the-shelf actuator, servo, motor, LED/lamp/module, board, or connector. **By form:** you are about to author procedural geometry for a gear, bearing, bolt, screw, nut, washer, rivet, pin, spring, bushing, o-ring, circlip, chain, belt, pulley, coupling, hinge, caster, magnet, or threaded insert. The form trigger fires even when nothing names the part — which is exactly why writing your own `spur_gear()` or `hex_bolt()` must stop and search `$step-parts` first. Search on the governing numbers (module and tooth count, bore and OD, thread and length), not on prose, and rank the script's compact `items`. A reachable API returning nothing is a **recorded miss**: write it into the brief's component table and the final response, then use a documented envelope. An unreachable API is inconclusive — retry with network permission rather than calling it a miss.
5. **Trigger `$electromechanical-integration` for any functional electrical load, including lighting, before the enclosure or assembly layout is fixed.** Its pre-CAD phase does the research and hands this skill the component/mount/route/interface contract. This phase materializes the selected STEP/envelopes and assembly labels, then writes schema 3 `<project>/measure/power.json` with `mounts.json` and any `motion.json`; only then can their gates run. GitHub supplies construction patterns, never component ratings or fit dimensions.
6. **Plan before coding.** Decide the printed-part count first — default to one, split only against the test in `references/project-structure.md` — then define parameters, intent labels, source paths, expected bounding boxes, and mating/positioning datums before editing. **The printed-part count does not decide the file count:** "one printed part" answers a question about geometry, and step 7 asks a separate question about layout. A single-piece display model still gets split across files once it crosses the thresholds there.
7. **Edit source, not generated artifacts.** Author build123d Python with `gen_step()`, naming a buildable entry `<name>.step.py` (helpers stay `<name>.py`; see `references/step-generation.md`). A model with separately printable parts, 3+ named parts, or more than ~120 lines of geometry gets a project directory — `references/project-structure.md` carries the layout, filename rules and editing discipline. **A project has exactly one non-part combined `<name>.step.py` entry. A split project also has one `part_<role>.step.py` per part. Neither substitutes for the other.** The isolated host verifier infers that sole non-part entry; presentation, state, signature and other auxiliary generators must be ordinary `<name>.py` helpers called by the combined entry, not additional `*.step.py` entries. The combined entry is what gets reviewed, and the part entries are what get edited. Mark a logical review entry `PRINTABLE = False`; mark a split one-piece model's combined entry `True`. Legacy `part_*` entries and a Tier 1 combined entry stay printable by default. Run `scripts/check_layout <project-dir>` before `scripts/gen`: it is static, costs milliseconds, and exits non-zero naming the file to split. **Once part entries exist, the documented layout is mandatory rather than advisory**; a project whose importable modules exceed the Tier 3 threshold needs `params.py`, `parts/`, `features/` and `assemblies/`, not a larger `_lib.py`. Run `scripts/gen` on the generator, never on its exported STEP; imported STEP/STP files need no build step, as `inspect` reads them directly.
8. **Generate explicit targets.** Apply the source edit and run `scripts/gen` in the **same model round**; never open a round whose only job is to generate. Name explicit generator targets — no directory-wide generation — and pass all affected targets to one invocation rather than one process per entry. **Always pass `--write`** on the run that ends an edit cycle: `gen --write` is the only command that writes a deliverable at all, and a project whose newest artifact is a render package is indistinguishable from one whose STEP write failed.
9. **Validate geometrically.** During quick iteration run `scripts/inspect refs <target> --facts --planes --positioning` plus the targeted `measure`/`align`/`frame`/`diff` checks the current edit changed — in the same round as the `gen`. Put independent requests through one `scripts/inspect batch`; do not parallelize warm `inspect` calls. Defer `inspect validate` and `inspect interfere` until the shape has stopped changing (`references/run-cost.md` owns that timing). `refs --facts` reports counts and bounds, and its `ok` covers ref resolution only — an open shell and an inverted solid both pass it. Do not start `scripts/verify_project` until a standalone `interfere` is clean.
10. **Reconcile image-derived work.** Every source repair that changes a parameter, landmark, part count or construction family is reconciled back into the approved `*_spec.md`. Give every landmark a local geometry target, render the orthogonal set plus every usable reference viewpoint, compare source against STEP, and run the likeness gate. `references/image-derived-verification.md` defines the two local audits and the integrated command.
11. **Review appearance with the instrument that can see it.** A silhouette suffices for an exterior-outline comparison and can hide every interior part of an exposed mechanism beneath a larger base. When the claim depends on interior openings, overlapping parts, occurrence colours or relative visual mass, use the CAD viewer when available, otherwise `scripts/render_review <source> --view front --view top --view iso -o <project>/snap/review` and inspect the shaded PNGs. Visual evidence only; it never replaces a geometry gate.
12. **Repair and rerun.** If a check fails, change the smallest responsible source section, regenerate, and rerun the failed validation **in the same model round**.
13. **Render before the expensive final gate.** Once exact draft geometry is
    plausible, generate every declared entry with `--write` so each carries a
    fresh `.step`. Run `verify_project --print-gates --nozzle <mm>` here rather
    than at the end: at roughly 7-12 s per part per gate it is cheap beside
    `validate` and `interfere`, and a wall or overhang defect found now costs
    one source edit instead of a repair cycle after review. Until that run has
    passed, printability is unverified — say so rather than calling the result
    printable. Then use `scripts/render_product
    <assembled-or-primary.step> -o <project>/snap/iso.png` and inspect the PNG
    at full size; it tessellates the exact STEP in memory and writes no mesh.
    When the promise changes product geometry or state, write two to five
    exact-state STEPs and add `--state-sheet
    <project>/snap/signature.png --state-source <state-0.step> --state-source
    <state-1.step> ...`; the fixed-camera sheet rejects visually
    indistinguishable states. Use `--motion-sheet` only for viewpoint evidence
    of one unchanged shape. Rotating the camera or object cannot prove a
    mechanism state transition. Choose product-appropriate `--base`, `--accent`
    and `--background` colours. This presentation evidence never replaces a
    geometry gate. For a static product, use the motion sheet as exact views
    that expose its anti-generic detail. For a coupled operating mechanism,
    follow `references/motion-presentation.md`: use exact-state animation for
    the motion read and mechanical checks for kinematics. The calling workflow
    owns independent semantic review, its repair budget and the decision to
    invoke the integrated final verifier; this skill owns the CAD and render
    evidence it consumes. In Workshop, follow the current Make reference for
    that review. Keep binary likeness silhouettes under a named evidence path,
    never at `snap/iso.png`. In a restricted product run, do not manually
    delete `__cadgen__` or add `--fresh` to iterative preflight: the trusted
    host owns the authoritative isolated fresh rebuild. Before detailed parts,
    reject a blockout that is a blob attached to a board, a flat plaque,
    floating presentation pieces, or a silhouette that needs copy to explain
    it.

## Handoff

CAD soundness stays deterministic: `scripts/inspect` (refs, validate,
interfere, measure, align, frame, diff) plus the project gates (`check_layout`,
`check_fit`, `check_mesh`, `check_motion`, `check_mount`, `check_thickness`,
`check_spec_numbers`, `check_spec_format`) and
`$electromechanical-integration`'s `check_power` for powered products.
For image-derived projects, `verify_project --image-derived` additionally uses
the sibling `image-to-cad` renderer and likeness gate; those visual checks do
not substitute for any geometry gate. Report the checks that actually ran and
their results; a claim needs the check that produced it, never an unaudited
visual impression.

Autonomous Workshop materializes the sibling `image-to-cad` and
`design-reference` skills beside this tree. Use `image-to-cad` for a direct
reference-image reconstruction and its required likeness evidence.

## Non-negotiables

**Artifacts and source**

- STEP is the only validated CAD deliverable. The GLB/topology render package and render sidecars are derived internal artifacts under `__cadgen__/`, never handed over.
- Keep presentation and measurement imagery distinct. `snap/iso.png` and
  `snap/signature.png` are visually inspected, chromatic product views made
  from exact CAD state; a black/white likeness silhouette is diagnostic
  evidence and cannot replace them.
- Use named parameters, closed solids, verbose native build123d labels, and source-controlled geometry intent.
- Every entry generator defines exactly one `gen_step()` at module scope and returns the shape; output paths belong to the CLI flags, never to the return value.
- Author assembly positioning in source. `references/positioning.md` is authoritative for `AssemblyHelper`, joints, `Location` transforms, and alignment validation.
- Do not use `git status`, `git diff`, or file-size churn as CAD comparison for exported artifacts. Compare source changes, `inspect` summaries, or topology output; path-limited git status is for bookkeeping only.
- Outside a restricted Workshop product run, delete the project's `__cadgen__/` after editing a shared `*_lib.py`, before the next build. `gen` does not notice a sibling library changed and `--force` does not repair it: you get `built` on stdout and the **previous** geometry in the `.step`. Inside a restricted Workshop product run, never manually delete that protected cache; regenerate every affected target explicitly with `scripts/gen <targets...> --write --force`, use non-`--fresh` iterative preflight, and let the trusted host perform the authoritative isolated fresh rebuild. Explicit regeneration is not proof that the shared-library cache defect is repaired; inspect the changed geometry and let the fresh rebuild establish freshness. A protected empty cache directory is harmless and must not be reported as a blocker. See "Shared-library cache defect" in `references/step-generation.md`.
- Do not size the two halves of a mate independently. Derive the second from the first with `scripts/cadfits.py` (`peg_for(bore, "slip")`, `slot_for(pin, 0.15)`). A pair typed by hand in two files cannot be audited afterwards — the only available check restates the arithmetic and reduces to `True`. No gate catches a mate that drifted. See `references/parameters.md`.
- Do not type a bought part's dimensions into a generator. Fetch its STEP with `$step-parts` into `<project-dir>/ref/` and derive the cavity with `scripts/cadmount.py` (`seat_for`, `bolt_cutter`). Never grow the component with `offset(solid, +clearance)`: on the step.parts SG90 that silently drops the output hub and returns a solid 2.9 mm **shorter** than its input, and the bracket cut from it validates. See `references/bought-parts.md`.

**Gates that must pass before a claim**

Each of these blocks a specific claim, and each exists because no *other* gate
in the toolchain catches what it catches.

- **`check_layout` — before "done".** Rename scaffold directories (`project_name`, `object_name`) before the first build. A generator over the step 7 layout thresholds with no `part_*.step.py` beside it is unfinished work, and `oversized-library` is over the line whether or not the model is otherwise perfect: once a project has part entries it owes the full layout. Migrating a tier is a pure move — fingerprint every entry's volume, solid count and bbox from source before and after, and diff.
- **`validate` and `interfere` — before "sound".** A finding (`invalidTopology`, `openShell`, `nonPositiveVolume`, `noSolid`, `selfIntersecting`) that is not an intended surface model, a reported clash, a part floating free, or a feature unjustified against the brief each block completion. No render can establish the *absence* of a clash. An `{"ok":false}` naming no finding is usually not this model: `cadgen` scans the whole worktree, so one stale `*.py` with a pre-migration `gen_step()` envelope takes `validate` and `refs` down for every model at once — check that before editing geometry.
- **`check_fit` — before "fits the bed".** It checks the four things nothing else covers: the part sits on the bed (`min(Z) == 0`), its footprint fits, it has positive volume, and the generator runs. A part still in assembly coordinates passes `validate` and `interfere` and cannot be printed. It reports but does not fail on disconnected bodies and a missing per-project audit; `--strict` promotes both.
- **`check_motion` — before "assemblable".** `validate` and `interfere` answer whether parts are sound and whether they overlap once assembled, never whether they can be brought together or whether a connector holds. Final `verify_project` refuses to skip motion when the README/spec documents an insertion, seating, pressing, sliding, screwing, snapping, threading or locking action; part count alone does not trigger it. Write **both** directions of every joint — the one it assembles along, and the one it must not, via `"expect": "blocked"`; a dovetail only checked for coming apart passes as a plain pocket. **A blocked sweep freezes its obstacles, so it is not proof when a removable obstacle is itself free:** declare the complete `retention` chain, and every removable support needs its own passing blocked condition until the graph reaches a genuine fixed frame/housing root. Never mark a loose gate, cap, key, pin, screw, magnet or catch as fixed to close the audit. Give each separately installed rigid part with constrained access its actual insertion path — final-pose rotation does not prove the camshaft can enter the frame. See `references/motion-manifests.md`.
- **`check_mount` — before "it can hold the part".** Deriving a seat with `cadmount` is not proof the model has one: the generator may never have subtracted it, cut it in the wrong place, or eaten it with a later feature — and `validate`, `interfere`, `check_fit` and `check_motion` pass all three. The gate places the component's own STEP at a declared pose and measures the built solids for clash, clearance, and whether a screw reaches each hole from either side. Keep every bought/foreign STEP under `ref/` and declare it in `measure/mounts.json` with the checksum from its catalog row; final `verify_project` rejects a supplier file hidden elsewhere, then requires every STEP under `ref/` to have a mount row whose `sha256` matches. A derived envelope cannot replace the supplier source. `"bolts": false` is the escape hatch for a strapped or glued component. See `references/bought-parts.md`.
- **`check_mesh` — on every printable entry, beside `check_fit`.** It builds the entry from source and tessellates it, then answers what the slicer will see: watertight, manifold, winding, one shell, positive volume, bed. `check_fit` measures the same solid's B-rep, so the two are cheap and expensive halves of one question rather than a staleness pair — nothing is exported here to go stale. A non-manifold edge fails: the subject is one printed part, so an edge four faces share is a defect however normal it is between two bodies (`--assembly` demotes it for a combined entry). `scripts/repair_mesh` writes nothing; it repairs in memory to name which defect class you have, and the fix goes in the generator. See `references/repair-loop.md`.
- **`check_thickness` — before "print-ready".** `<project>/part_<role>.step.py --nozzle 0.4` fails a wall under two extruded lines, which a slicer drops or prints as two perimeters with a gap while the STEP stays perfect. Hollow in the source with `scripts/cadprint.py`, never a bare `offset(solid, -wall)`: that shrinks the solid rather than shelling it, and every gate passes the undersized result. See `references/print-optimisation.md`.
- **`assert len(shape.solids()) == 1` — for a multi-segment organic body.** `validate` and `interfere` both pass a body whose tail is a separate solid resting against it: a loft's end cap is a plane normal to its own tangent, so a segment starting where the previous one "ended" starts outside it. The assert is the only thing that catches it. See `references/organic-lofts.md`.

**Powered products**

- Every functional motor, servo, solenoid, LED, lamp, beacon, strip or illuminated control invokes `$electromechanical-integration`, which owns the search record, the complete source → protection → switching → load → return path per independently rated branch, and the ratings evidence. A motor or light is a load, never an energy source.
- This skill owns the geometry: real holder, hatch, channel, retention and strain-relief geometry, a `measure/mounts.json` row per seat, a routed wire clearance envelope rather than a centerline, validation-only STEP envelopes for the parts that stay out of the render, and a modelled inlet or lead for an external source. When the brief says the product is self-contained or portable and must run, spin, move or emit light, do not discard its battery, switch or wiring as an unapproved "outside CAD scope" assumption.
- **No geometry gate can prove electrical compatibility.** Write schema 3 `measure/power.json`, run `python "$(workshop skills path)/electromechanical-integration/scripts/check_power" <project-dir>`, and pass `--powered` to final `verify_project`; an absent or failing manifest blocks the powered claim. For a removable lamp, only a `passed` coupon made with the exact hardware and final material/process/orientation permits a physical-fit claim — `planned` is reported physically unverified and `failed` blocks delivery.

**Image-derived work**

- Do not declare image-derived CAD complete while its spec and source disagree, a defining landmark lacks a local geometry target, a reference viewpoint is omitted, source-vs-STEP comparison finds drift, or any likeness pair is below 0.90 without the user explicitly accepting that measured **failing** result. Run `scripts/verify_project <project> --image-derived --likeness-ref LABEL=PATH` with every usable reference and classify power explicitly (`--powered` / `--unpowered`).
- The mode requires `measure/check_spec.py` and `measure/check_landmarks.py` because a generic gate cannot infer project-specific claims, and the runner never lowers the 0.90 floor. `references/image-derived-verification.md` owns both audits, the accept-mismatch path and the three-non-improving-rounds stall rule.

**Reporting**

- Keep local fit audits algebraic where a generic gate already builds geometry: assert shared base dimensions, clearance application and connector naming locally, and let `check_fit` and `validate` own the solid/body checks. Rebuilding every shape in both places is slower without adding a distinct claim.
- Never call a model sound, printable, or fit-correct from reading the source. The claim needs the check that actually ran.
- Never call an exposed mechanism visually reviewed from silhouettes alone when a larger occurrence hides its interior layout. Use the CAD viewer or `scripts/render_review` and inspect the shaded output; keep silhouettes for outline/likeness claims. Exposed mechanisms are legitimate design choices rather than automatic defects; judge their finish against the actual Wish and preserve physical uncertainty explicitly.
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
- `references/motion-presentation.md` — construct and reconcile operating animations from the same declared poses used by `check_motion`; load for coupled mechanisms.
- `references/motion-manifests.md` — motion-manifest schema, the `expect: blocked` capture form, assembly sequences, and what a rigid-body sweep cannot answer.
- `references/motion-presentation.md` — exact-state animation and review evidence for coupled mechanisms; load when motion must be understood visually.
- `references/positioning.md` — part-local datums and origins, assembly transforms, build123d joints, CLI alignment validation, and positioning reports.
- `references/parameters.md` — parameterizing a STEP model: source parameters, naming, defaults and bounds, deriving the second half of a mate with `scripts/cadfits.py`, and how a parameter change is confirmed.
- `references/bought-parts.md` — seating an off-the-shelf component: fetching its STEP, deriving the cavity and the screw pattern from that file with `scripts/cadmount.py`, why offsetting an imported solid silently loses features, and what a derived seat still cannot answer. **Load whenever the model has to hold a motor, servo, LED module, bearing, board or any purchased part.**
- `references/repair-loop.md` — diagnosis and repair procedures, including the source fixes for the mesh defects `check_mesh` fails on.
- `references/print-optimisation.md` — wall thickness, hollowing, and why `offset(solid, -wall)` shrinks rather than shells.
- `references/run-cost.md` — the measured cost of every command, which checks to run per round versus once at the end, why agent-loop tokens scale with round count rather than `gen` seconds, the two incompatible `--bed` flag forms, and why a stale generator anywhere in the worktree breaks `validate` for every model.

Final responses should include generated files, validation actually run, assumptions, and caveats. Use `references/inspection-and-validation.md` for report structure.
