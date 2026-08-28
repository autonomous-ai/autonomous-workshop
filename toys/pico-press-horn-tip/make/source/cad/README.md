# Horn Tip CAD project

One-piece crescent desk rocker. Print the combined `assembled` entry on one
flat cheek; no supports, fasteners, or purchased parts.

Printer bed declaration used by fit/mesh gates: `--bed 220x220x220`

## Envelope (print coordinates, mm)

- Silhouette in XY, thickness along +Z
- Outer rocking radius 42, inner radius 30, half-angle 50 degrees
- Thickness 18, round horns of radius 6
- Expected bbox about 67 x 25 x 18
- Rest pose in use: cylindrical outer belly on the desk, horns up

## Files

- `assembled.step.py` — sole printable generator (`PRINTABLE = True`)
- `assembled.step` / `assembled.stl` — derived STEP and mesh
- `measure/` — spec audit, fit/print audit, and verification record

## Rebuild

From this CAD project directory:

```text
python "$CAD_SKILL_ROOT/scripts/verify_project" . --fresh --exports --strict-fit
```
