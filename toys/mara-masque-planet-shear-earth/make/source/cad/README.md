# Planet Shear — matter rank-4 piece, CAD project

A stylised Earth on a flat cylindrical disc: the rank-4 matter piece of Planet
Shear, a Dou Shou Qi set reskinned as matter and antimatter celestial bodies.

**Bed:** 220x220x220 mm. **Nozzle:** 0.4 mm. **One printed part.**

Assembled size 34.00 x 34.45 x 25.08 mm, 9.76 cm3 of solid.

## Files

| Path | What it is |
|---|---|
| `planet_shear_earth_spec.md` | the build spec: dimension ledger, provenance of every number |
| `planet_shear_lib.py` | all parameters and the part builders |
| `planet_shear_geo.py` | relief solids on a sphere, and the printable wall lean |
| `planet_shear_atlas.py` | stylised lon/lat outlines for land, dryland and ice |
| `part_piece.step.py` | the one printed body, disc face on the bed — the print-gate target |
| `planet_shear_earth.step.py` | combined entry: the same body split into coloured occurrences |
| `ref/hero.png` | the sealed reference image, copied in from the Wish |
| `measure/` | gate reports, round history, and the two local audits |
| `snap/` | the canonical render family and the signature review |

The six colour occurrences are regions of the single printed body, not separate
prints. Their volumes sum to the printed part exactly, and
`measure/check_landmarks.py` asserts that.

## Rebuild

```sh
python .agents/skills/cad/scripts/gen part_piece.step.py planet_shear_earth.step.py --write
python .agents/skills/cad/scripts/verify_project . --strict-fit --print-gates \
    --image-derived --unpowered --likeness-ref hero=ref/hero.png
```

Run both from the workspace root with the paths prefixed by this directory.

## Print table

| Part | Qty | Envelope (mm) | Orientation | Supports |
|---|---|---|---|---|
| `part_piece` | 1 | 34.00 x 34.45 x 25.08 | disc face on the bed | none |

Printability is geometric only: `check_mesh`, `check_overhang` and
`check_thickness` at a 0.4 mm nozzle. Nothing here has been printed, and motion
is unverified because this run's `MAKE-OPTIONS.json` sets `check_motion` false.
