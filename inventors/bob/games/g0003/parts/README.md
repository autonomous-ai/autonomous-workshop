# CLEARANCE (g0003) — CAD project

Contract: `../brief.md`. Deviations: `../cad/DEVIATIONS.md`. Print/assembly:
`../cad/BUILD_NOTES.md`.

## Layout

| file | what it is |
|---|---|
| `clearance_lib.py` | all geometry + every algebraic parameter check, run at import |
| `threads.py` | single-start 60° ISO-form thread pair (screw and nut from one major ⌀) |
| `clearance.step.py` | the combined assembly, mid-travel pose — the entry that gets reviewed |
| `part_<part_id>.step.py` | one entry per printed part, bed datum at Z = 0 |
| `measure/check_fit.py` | **the project fit/print audit** (see below) |
| `render_assembly.py` | offscreen colour render → `renders/` |
| `part_colors.json` | `{part_id: "#hex"}` |

## The fit/print audit

`measure/check_fit.py` is this project's local **fit/print audit** — the half of
the mandated checks that needs project knowledge and that no generic gate can
make:

- every brief §3 coupled pair, as assertions in `clearance_lib._check_params()`
  (fits, datum stack, both hard stops, thread engagement over the whole travel,
  detent preload, hood clearances);
- the §3.3 margin guarantee, re-proved at three different measured `H_top`
  values — the claim is that `H_top` cancels, so one value would not prove it;
- bill ↔ parts: one `part_<part_id>.step.py` per printed `part_id`, no more;
- print envelope per part against the brief's 251 mm bed, plus the 45° yaw
  arithmetic for the two parts that do not fit a 220 mm bed axis-aligned.

Every mate derives its second half from `cadfits.py`; no clearance is typed
twice.

## Rebuild

```bash
export BOB_CAD_PY=.../bob/.venv-cad/bin/python
S=../../../skills/cad/scripts
$BOB_CAD_PY $S/gen part_yoke.step.py --write        # one part
$BOB_CAD_PY $S/gen clearance.step.py --write        # the assembly
$BOB_CAD_PY $S/export clearance.step --stl assembled.stl
$BOB_CAD_PY $S/check_fit . --bed 251 251
$BOB_CAD_PY $S/check_mesh part_yoke.stl --bed 251x251x251
$BOB_CAD_PY $S/inspect interfere clearance.step
$BOB_CAD_PY measure/check_fit.py
$BOB_CAD_PY render_assembly.py --views
```

`golden_stub` is not a product part — it is the brief's physics-question rig
(§"the wound"): print it with `column_screw` and `detent_leaf` and run tests 1–3
before committing to the other 40 parts.
