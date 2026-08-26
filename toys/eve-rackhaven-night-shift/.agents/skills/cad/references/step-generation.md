# STEP generation

Read this file when generating or regenerating STEP/STP artifacts from build123d Python source, or when working with imported STEP/STP files.

## Tools

The launchers live in the CAD skill directory:

```bash
python "$CAD_SKILL_ROOT/scripts/gen" targets... [flags]     # build render GLB/topology packages from gen_step() sources
python "$CAD_SKILL_ROOT/scripts/export" target [flags]      # write STL/3MF/GLB mesh files (see supported-exports.md)
python "$CAD_SKILL_ROOT/scripts/verify_project" project ... # sequential quick/final project workflow
```

`scripts/gen` accepts gen_step() Python generator sources only. Use explicit target paths only; target paths resolve from the command cwd unless absolute. Do not rely on directory-wide generation.

Building a generator writes its hidden render package (GLB/topology artifacts) beside the source; it writes no `.step` file by default. Write the `.step` file in the same generation run with `scripts/gen <name>.step.py --write` — bare `--write` writes each target's sibling `<name>.step`; an explicit path requires exactly one target and resolves from the command cwd. This is the only way to write a `.step` file; `scripts/export` writes mesh formats only. Do not put output paths in the `gen_step()` return value; the CLI flags own output paths.

## Quick iteration versus final generation

Do not pay the full project pipeline after every cosmetic or proportion edit.

- **Quick iteration:** build the combined entry only, omit `--write`, optionally
  use a coarser preview-only `--mesh-tolerance 0.1`, and render one diagnostic
  view. Run only the measurements or relationship checks affected by the edit.
- **Final generation:** pass the combined entry and every affected part entry
  to one multi-target `scripts/gen ... --write` call, restore the default mesh
  tolerance, then run the complete validation/export workflow.

The combined entry is sufficient for visual iteration because it builds every
placed part. The separate part entries remain mandatory final outputs and are
the source for print-orientation checks.

```bash
# Fast visual loop
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/gen" <project-dir>/<name>.step.py \
  --mesh-tolerance 0.1

# Final generation: one daemon request, explicit targets
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/gen" \
  <project-dir>/<name>.step.py \
  <project-dir>/part_base.step.py \
  <project-dir>/part_body.step.py \
  <project-dir>/part_lid.step.py \
  --write --json
```

The warm daemon is single-request-at-a-time. Multiple concurrent warm clients
do not make OCP parallel; they queue behind one another and make timeout/session
handling worse. Batch targets inside one command instead.

For a Tier 2 project, use the runner when its generic gates match the task:

```bash
# Combined assembly only, coarse preview mesh, one ISO review
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --quick --fresh

# Complete sequential gate; also refresh GLB/STLs and validate each STL
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --exports

# Image-derived final: add every usable reference viewpoint
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --fresh --exports \
  --image-derived \
  --likeness-ref hero=ref/hero.png \
  --likeness-ref side=ref/side.png
```

`verify_project` runs `check_layout`, one final multi-target generation,
`check_fit`, the local `measure/check_{fit,spec,landmarks}.py` hooks that exist,
`check_mount` and `check_motion` when their manifests exist, then one batched
refs/validate/interfere pass. With `--exports`, it exports each printable STL,
runs `check_mesh` first, then `check_thickness`, and writes each thickness
report under `measure/`.

`--image-derived` is an explicit completion mode rather than an inferred one.
It requires exactly one `*_spec.md`, both `measure/check_spec.py` and
`measure/check_landmarks.py`, and at least one `--likeness-ref LABEL=PATH`.
Before the expensive validation batch it writes clean front/right/top/iso
views, searches the camera for every reference, compares the source with the
fresh STEP, and runs the 0.90 likeness gate. Read
`image-derived-verification.md` before writing the two local audits.

Every non-quick run persists the command, result, and elapsed time for each
phase to `measure/verification-pipeline.md`, including failed runs. Use
`--report` to choose another path inside the project or `--no-report` only when
the caller already captures an equivalent record.

It stops at the first failed phase and verifies that inspect emitted exactly
one successful response per request. It is the generic project baseline, not a
replacement for spec-specific `measure`, `align`, `frame`, or `diff` requests;
run those separately for every claimed dimension or relationship. Use
`--dry-run` to review its exact plan without modifying artifacts.
By default it prints elapsed time for every phase and one concise line per
inspect response; pass `--verbose` only when the complete successful inspect
JSON is needed. `--bed` overrides the first `--bed WxDxH` declaration in the
project README/spec, which otherwise overrides the 220 x 220 x 220 default.
Pass `--strict-fit` when a project's advisory disconnected-body and local-audit
notes are also meant to fail the run; legitimate print plates may leave it off.
Pass `--skip-thickness` only for an explicit mesh-only delivery; doing so makes
the resulting artifacts ineligible for a print-ready claim.

## Generated vs imported STEP

These two terms classify a STEP file by what its source is, and they drive every workflow decision in this skill:

- A **generated STEP file** has a Python generator script as its source — a `.step.py` (a `.py` that defines `gen_step()`). The STEP and its GLB/topology artifacts are *derived* from that script, so the script is what you edit and regenerate; the `.step` is an output.
- An **imported STEP file** is its own source: a STEP/STP authored or downloaded elsewhere, not derived from any generator script. There is nothing upstream to regenerate — the STEP file itself is the source of truth.

When a generated STEP file's `gen_step()` builds on another STEP file, that other file is a **dependency** of the generator (ordinary code-dependency terms apply: the parent depends on the child). How you wire a dependency in depends on whether the child is generated or imported — see "Child dependencies" in `positioning.md`.

## Entry generators are named `<name>.step.py`

An entry defines **exactly one `gen_step()` at module scope**, takes no
arguments, and returns the shape — a build123d object, an assembly compound, or
the envelope dict described below. Everything else in the file is a helper it
calls. Output paths are owned by the CLI flags and never appear in the return
value, and the generated `.step`, `.stl`, `.3mf`, `.glb` and render sidecars are
outputs: edit the generator and rebuild, never the artifact.

A **STEP entry generator** — a Python script that defines `gen_step()` and is meant to be built, inspected, or exported on its own — is named `<name>.step.py`. That filename is the marker the build tools scan for. Ordinary **helper / library modules** (shared geometry functions, `*_parts/` packages, `*_common.py`, anything imported by other generators but not built on its own) stay `<name>.py` and are NOT treated as entries even if they define `gen_step` — the tools scan for `.step.py`, not every Python file. So: if a `.py` script is a buildable model on its own, name it `<name>.step.py`; if it only exists to be imported by other generators, leave it `<name>.py`.

- A `<name>.step.py` entry produces the logical STEP `<name>.step` (the filename minus the trailing `.py`); its render package lives at `<dir>/__cadgen__/models/<name>.step.py/`. Build/inspect it by passing the `.step.py` path to the CLI, exactly like any generator source.
- **A `.step.py` file cannot be imported by name.** `import foo` does not find `foo.step.py`, and `import foo.step` makes Python look for a `foo` package (a `foo/` directory) — neither exists. Load an entry generator by PATH (`importlib.util.spec_from_file_location`), which is how the CLI and assembly composition already load generators. If generators must share constants/functions, put the shared code in a plain `<name>.py` helper they both import, or path-load the entry. When a generated assembly composes a generated child (see "Child dependencies" in `positioning.md`), it path-loads the child `.step.py` and calls its `gen_step()` — it never `import`s it by name.

  **`sys.path` does not survive into `gen_step()`.** The CLI restores `sys.path`
  after loading your generator module, so a path inserted at import time is gone
  by the time `gen_step()` runs — an import attempted inside the function fails
  with a bare `No module named ...` that points at the module rather than at the
  path. Import sibling helper modules at module top level and only *call* them
  inside `gen_step()`.

  Minimal path-load (cache it with `functools.lru_cache` if a child is composed many times):

  ```python
  import importlib.util
  from pathlib import Path

  def load_entry(step_py_path):
      path = Path(step_py_path)
      spec = importlib.util.spec_from_file_location(path.stem, path)  # path.stem == "<name>.step"
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      return module

  child = load_entry("<project-dir>/<name>.step.py")
  child_shape = child.gen_step()   # compose this into the parent's gen_step()
  ```

## Generated Python source

This is the default path when designing from scratch or modifying a generated model. Generated build123d sources define:

```python
def gen_step():
    ...
    return step_ready_shape_or_labeled_compound
```

Generated Python targets infer their kind from the source metadata and `gen_step()` return value; pass the source path directly:

```bash
python "$CAD_SKILL_ROOT/scripts/gen" path/to/part.step.py
python "$CAD_SKILL_ROOT/scripts/gen" path/to/a.step.py path/to/b.step.py
python "$CAD_SKILL_ROOT/scripts/gen" path/to/assembly.step.py
```

Passing a generated assembly's exported `.step` to a tool treats it as imported native STEP and loses source-level assembly composition; work with the `.py` assembly source. For generated build123d assemblies, prefer `cadgen.assembly.AssemblyHelper` in the Python source so native labels, named mate frames, and source-level relationships are preserved before STEP export (see `positioning.md`).

## Imported STEP/STP files

An imported STEP/STP file (downloaded or authored elsewhere, no generator) needs no build command. Its render artifacts are generated on demand from the STEP file itself by `scripts/inspect`, and its part/assembly kind is inferred from embedded metadata or the STEP product hierarchy.

To produce STL/3MF/native GLB files from an imported STEP, pass it directly to `scripts/export`; read `supported-exports.md`.

After a generated target has been rebuilt with `--write`, use its fresh sibling
STEP as the input for STL/3MF and geometry-only GLB exports. Passing the
`.step.py` source to `scripts/export` invokes its builders again. Use the source
target only when the export needs source-only scene metadata that the STEP did
not retain. Omit an explicit output path when the desired result is the normal
sibling file; relative explicit export paths are easier to misplace than the
default.

To debug or pre-run the on-demand render-package build itself, `scripts/artifact` runs exactly one build for an imported STEP/STP file (or a generator source) and prints the result payload:

```bash
python "$CAD_SKILL_ROOT/scripts/artifact" path/to/imported.step [--kind part|assembly] [--force]
```

## Optional-module generators and the artifact cache

A generator that imports several part modules and SKIPS the ones that do not
exist yet is a useful pattern for parallel work — the assembly stays renderable
while individual parts are still being written. It has one sharp edge.

The artifact's source-closure hash is computed from the modules the generator
ACTUALLY IMPORTED at build time. Modules that did not exist during the first
build were never in the closure, so their later appearance cannot change the
hash. The cache is self-consistent and permanently stale: tools that resolve
artifacts on demand keep serving the old package, with no error and no warning,
long after the new modules land.

Run `scripts/gen` on the entry explicitly after adding a part module, rather than
relying on implicit resolution by `inspect`.

### Shared-library cache defect in this repository

The local Tier 2 layout has a known cache defect: editing a sibling
`*_lib.py` does not reliably invalidate existing `__cadgen__` packages, and
`--force` does not repair that stale package. After any shared-library edit,
delete that project's cache once before the next build:

```bash
find <project-dir>/__cadgen__ -depth -delete
```

Then use the quick combined-only loop while refining and one multi-target final
generation when the source is stable. Do not repeatedly delete the cache
between commands that all correspond to the same source revision.

## Render packages

Every `scripts/gen` run writes a hidden adjacent GLB/topology package as its
build output, and `--write` derives the `.step` from it. Nothing else reads it:
`inspect` and `export` build the shape from source in memory. Imported STEP/STP
files get the same package on demand, per the previous section.

## After generation

- Confirm the process succeeded and the STEP file exists and is non-empty.
- Run the baseline inspection and any spec-driven checks per `inspection-and-validation.md`:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" refs path/to/model.step --facts --planes --positioning
```

## Warm daemon (opt-in)

Every `scripts/gen` / `scripts/export` / `scripts/artifact` / `scripts/inspect`
invocation pays a multi-second OCP/build123d import. Set
`CADGEN_WARM=1` to route these CLIs through a shared warm-process daemon
instead:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/gen" path/to/part.step.py
```

- The first warm call spawns the daemon (paying the import cost once) and each
  later call runs in the warm process, streaming the CLI's stdout/stderr and
  exit code back unchanged. Arguments, cwd resolution, and outputs match the
  cold CLIs; requests are handled sequentially.
- The daemon is **per materialized CAD skill tree**: the socket is
  `$TMPDIR/cadgen-daemon-<sha256(skill-root)[:12]>.sock` (falling back to
  `/tmp`), with a `.log` file beside it for daemon lifecycle and C-level OCP
  noise. Product runs using the same materialized skill share that sequential
  daemon. `CADGEN_DAEMON_SOCKET` overrides the socket path.
- **Staleness:** the daemon records a version token (max mtime over the CAD
  skill's `scripts/**/*.py`, including its bundled `cadgen` package) at
  startup. When a client's token differs — i.e. cadgen or the skill CLIs
  changed — the daemon exits and the client transparently respawns a fresh one,
  so edits to runtime code always take effect on the next call.
- **Idle exit:** the daemon exits after 10 minutes without a request
  (`CADGEN_DAEMON_IDLE_TIMEOUT` seconds overrides) and cleans up its socket.
- Without `CADGEN_WARM=1` nothing changes; on any daemon spawn or protocol
  problem the CLI silently falls back to the normal cold in-process run.

`scripts/inspect batch` and `worker` also read JSONL from stdin. Their launcher
therefore stays in the calling process rather than routing to the daemon; this
is intentional and still amortizes the OCP import across every request in the
batch.
