# CAD tool contracts

This is the whole interface Make needs from the materialized CAD skill. Read it
instead of opening a tool's source. `verify_project` is 2,288 lines and its
`--help` prints only the first line of its module docstring, so reading the
source to rediscover a mode, a report path, or an ordering rule costs many
requests and returns what is written here.

Every command below runs under `"$WORKSHOP_PYTHON"` from the run root, with
`.agents/skills/cad/scripts/<tool>` as the script path and a path inside the
product root as the project. Replace bracketed names from `STAGE.json`.

## Writing geometry

`gen <entry.step.py> [more.step.py ...] --write` is the **only** way to write a
`.step`. Without `--write` it builds the render package and no CAD file. With no
path after `--write` each target writes its sibling `<name>.step`; an explicit
path requires exactly one target. `--force` rebuilds when artifacts already
match the source closure. `--json` prints one result line per target on stdout
and keeps progress on stderr. `--lock-timeout SECONDS` gives up when another
run holds the same model's generation lock and reports
`{"ok":true,"contended":true}` instead of building; the default, `0`, waits for
the peer, so a `gen` that appears hung may be waiting on a lock rather than
computing.

`export <entry.step | entry.step.py> --stl [OUTPUT]` writes mesh formats only:
`--stl`, `--3mf`, `--glb`. Each defaults to the sibling `<name>.<ext>`. It never
writes a `.step`. Export from the fresh STEP, not from source, so the mesh and
the CAD file cannot disagree.

Both accept `--mesh-tolerance` and `--mesh-angular-tolerance`.

## Rendering

`render_product <entry.stl> -o <out.png>` renders one view. It has no per-flag
help text, so this is its interface:

- `--view iso|front|right|top` (default `iso`), `--size N` (default 900),
  `--pose-degrees D`.
- `--base`, `--accent`, `--background` take `#rrggbb`.
- `--motion-sheet <out.png>` with `--motion-angles=a,b,c` (default
  `-12,0,12`) and `--motion-view` (default `front`) rotates **one unchanged
  mesh**. It is viewpoint evidence and can never prove a state change.
- `--state-sheet <out.png>` with repeated `--state-stl <file>` renders distinct
  exact-state meshes at one fixed `--state-view` (default `front`).
  `--min-state-difference` (default 2.0) refuses a sheet whose states are not
  actually different. This is the only still-image way to show a promised state
  transition.

## verify_project modes

The modes are mutually exclusive and each writes STEP. Combining a final-mode
flag with `--quick` is an argument error, not a warning: `--exports`,
`--strict-fit`, `--strict-mount`, `--skip-thickness`, `--powered`,
`--unpowered`, `--image-derived` and `--likeness-ref` are all final-mode only,
and `--print-preflight` and `--quick` are mutually exclusive.

| Mode | Flag | Writes | Runs |
| --- | --- | --- | --- |
| plan | `--dry-run` | nothing | prints the sequential plan |
| quick | `--quick` | combined entry's `.step` + render package | no gates |
| preflight | `--print-preflight` | one `.step` and `.stl` per printable, `measure/print-preflight.md` | strict bed fit, mesh, wall thickness at a fixed 0.4 mm nozzle |
| final | *(default)* | combined + per-part `.step`, `measure/verification-pipeline.md` | layout, provenance, generation, print fit, local audits, bought-part mounts, powered/motion when declared, refs + validate per entry, assembly interference |
| final + exports | `--exports` | also assembly GLB and one STL per printable | plus mesh and printable wall thickness on the exported meshes |

`--print-preflight` is the one cheap gate allowed before visual review.
Lowering `--nozzle` below the standard profile is refused rather than turned
into a local pass; `--skip-thickness` means the output cannot be called
print-ready.

## What final mode refuses before it does any geometry work

Final mode is bound to work that must already exist. It refuses, cheaply, when:

- `measure/print-preflight.md` is missing, or is not a passing
  `print-preflight` record — it must start with `# Verification pipeline
  record`, contain ``- Mode: `print-preflight` `` and `- Result: **PASS**
  (exit 0)`;
- `snap/SIGNATURE-REVIEW.json` is missing, is over 64 KiB, is not canonical
  JSON (sorted keys, `,`/`:` separators, no NaN), is not schema 6, or its field
  set does not match the schema exactly;
- the review's `print_preflight_sha256` is not the hash of that passing
  preflight report — a review written against an earlier preflight is refused,
  so regenerating the preflight means rewriting the review that cites it;
- `motion_presentation.validate` rejects the review's presentation claims;
- an **image-derived** final run has not classified power: pass `--powered`,
  which requires `measure/power.json`, or `--unpowered` when there is no
  functional electrical load. The two are mutually exclusive, `--unpowered` is
  refused when a `measure/power.json` already exists, and `--unpowered` is an
  argument error outside `--image-derived`.

A refusal still writes a `refused` row into the pipeline record, so a cheap
failure is auditable rather than absent.

## Declarations final mode reads

- `measure/motion.json` — the motion manifest, or `--motion-manifest <path>`.
  A documented assembly procedure requires one; the gate names the missing file
  rather than skipping silently. `check_motion --list-parts` names the parts it
  can pose, and `check_motion --json` emits machine-readable results.
- `measure/power.json` — required by `--powered`.
- `measure/mounts.json` — required whenever the project carries a component
  STEP under `ref/`. A fetched part with no declared mount is a seat no gate
  has measured.
- `*_spec.md` — whenever one exists, `check_spec_numbers` runs in **every**
  mode and holds a backticked number attributed to a named parameter to that
  parameter's actual value.

## Reading the report

`measure/verification-pipeline.md` (override with `--report`, suppress with
`--no-report`) records one row per gate. A conditional gate that did not run is
written as `skipped`, because a gate missing from the record is
indistinguishable from one that passed. Read the rows rather than only the
exit code.

`--verbose` prints complete successful `inspect` JSON; without it, successful
responses are summarized. `--self-check` runs the built-in fixtures and exits
without touching a project.

## Cost rules that Make must follow

- Run only the narrow checks an edit affected. Once the baseline is plausible,
  run `--print-preflight` **without** `--fresh`.
- Do not delete `__cadgen__` or pass `--fresh` inside the product sandbox. The
  trusted host owns the isolated fresh rebuild.
- Run the integrated final verifier **once**. It is a gate, not an iteration
  loop, and it is deliberately expensive.
- These runs are long: `--print-preflight` takes 6.5 s to 46 s, a final run 25 s
  to 75 s on a simple product and 580 s to 690 s on a complex one. Both reports
  record `- Elapsed:` and per-gate seconds, so read the previous one to know
  what the next will cost.
