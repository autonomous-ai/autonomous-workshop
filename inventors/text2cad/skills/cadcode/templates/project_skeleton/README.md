# `<project_name>`

A CADCode project. Structure:

```
spec.md             design intent (read this first)
params.py           ALL dimensions + manufacturing constants
validation.py       runtime constraints (printability, fit)
main.py             entrypoint — runs validation, builds assembly,
                    assigns `result` for the runner
parts/              one file per physical part
features/           reusable feature functions (USB cutouts, vents, ...)
assemblies/         positioning + union of parts
exports/            (gitignored) generated STL/STEP/PNG
```

## Run

```bash
python ~/.claude/skills/cadcode/scripts/cad path/to/this/project/
```

The runner detects `main.py`, adds the project root to `sys.path`,
and exports artifacts next to the project unless you pass `--out-dir`.

## Editing rules (AI agents read this)

- **Dimensions go in `params.py` only.** Do not hardcode numbers inside
  geometry functions.
- **Each new physical feature is its own function.** Compose via the
  feature pipeline pattern, not a single fluent chain.
- **Parts don't know about each other.** Each part is built in its own
  local frame; positioning happens in `assemblies/`.
- **Keep names intent-aligned**: `add_left_usb_c_cutout`, `make_snap_fit_lid`.
  Not `thing1`, `helper2`.
- **Prefer simple primitives + booleans**: `box`, `cylinder`, `extrude`,
  `cut`, `union`, `hole`, `fillet`, `chamfer`, `mirror`, `array`.
  Avoid complex lofts/splines unless required.
