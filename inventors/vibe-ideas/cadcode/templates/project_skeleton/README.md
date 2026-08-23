# `<project_name>`

A CADCode project. Structure:

```
cad_project.json    stable CREATE → EDIT/REMIX identity
spec.md             design intent (read this first)
params.py           ALL dimensions + manufacturing constants
validation.py       runtime constraints (printability, fit)
main.py             entrypoint — runs validation, builds assembly,
                    returns shape + warnings from `gen_step()`
parts/              one file per physical part
features/           reusable feature functions (USB cutouts, vents, ...)
assemblies/         positioning + named `cq.Assembly` hierarchy
```

## Run

```bash
python ~/.claude/skills/cadcode/scripts/cad path/to/this/project/
```

The runner detects `main.py`, adds the project root to `sys.path`, and exports
artifacts inside the project unless you pass `--out-dir`. A multi-part build
keeps separately printable parts as stable, named assembly children so later
EDIT/REMIX turns can target them without reconstructing intent.

After copying this template, change `cad_project.json.artifactStem` to the
project directory's stable semantic name. Keep `model.parts` in exactly the
same order and with exactly the same IDs as the named `cq.Assembly` children;
when a physical part is intentionally added or removed, update both together.
The build reads that stem directly and rejects a conflicting `--stem`.

A release run is green only when the final JSON has `ok: true`,
`is_solid: true`, positive volume, and zero non-`info` warnings. Any source
edit after that build invalidates the candidate and requires another run.

## Editing rules (AI agents read this)

- **Dimensions go in `params.py` only.** Do not hardcode numbers inside
  geometry functions.
- **Each new physical feature is its own function.** Compose via the
  feature pipeline pattern, not a single fluent chain.
- **Parts don't know about each other.** Each part is built in its own local
  frame; positioning and stable child names happen in `assemblies/`. Do not
  union separately printable or removable parts.
- **Manifest IDs are an editing API.** Preserve `artifactStem`, part IDs, their
  source bindings, and order across normal edits.
- **Keep names intent-aligned**: `add_left_usb_c_cutout`, `make_snap_fit_lid`.
  Not `thing1`, `helper2`.
- **Prefer simple primitives + booleans**: `box`, `cylinder`, `extrude`,
  `cut`, `union`, `hole`, `fillet`, `chamfer`, `mirror`, `array`.
  Avoid complex lofts/splines unless required.
