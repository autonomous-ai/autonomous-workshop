---
title: Print time and material estimation, and spiral vase mode
tags: [print-time, filament, mass, cost, volumetric-flow, infill, perimeter, estimate, vase-mode, spiralize]
aliases: [filament usage, filament weight, grams of filament, spool length, meters per kg, print cost, print duration, max volumetric speed, mvs, flow rate, spiral vase, vase mode, spiralize outer contour, single wall print]
sources:
  - https://help.prusa3d.com/article/max-volumetric-speed_127176
  - https://help.prusa3d.com/article/layers-and-perimeters_1748
  - https://github.com/prusa3d/PrusaSlicer/issues/9474 (machine limits change the time estimate)
  - https://vorpal.se/posts/2025/jun/23/3d-printing-with-unconventional-vase-mode/
  - https://www.3dsourced.com/rigid-ink/how-many-meters-of-filament-on-a-spool-calculator/ (1.75 mm PLA ≈ 335 m/kg; via search excerpt)
  - skills/cad/scripts/cadprint.py
related: [perimeters-infill-and-strength, filament-properties, fdm-layer-height-and-nozzle, wall-thickness-and-hollowing, fdm-multi-material-design, overhangs-and-print-orientation]
updated: 2026-09-23
---

# Print time and material estimation, and spiral vase mode

The slicer is the authority on grams and hours, but a design decision —
hollow or not, one part or four, a 0.4 or 0.6 nozzle, a vase-mode shell —
needs the order of magnitude **from the CAD volume**, before slicing. This
page gives the bounds and the formulas, and says which geometry qualifies for
spiral vase mode, the one setting that changes both numbers by an order of
magnitude.

## Mass from the model: the shell plus a fraction of the core

A sliced part is not solid. It is a skin of perimeters and top/bottom layers
at full density around a core filled at the infill fraction `f`:

```text
V_skin ≈ A_side · t_wall + A_flat · t_flat
         t_wall = N_perim · line_width     (≈ 0.86 mm for 2 × 0.45, lines overlap)
         t_flat = N_top · layer_h on up-facing area, N_bottom · layer_h on down-facing
V_fill ≈ f · (V − V_skin)
m      ≈ ρ · (V_skin + V_fill) + m_support + m_brim + m_purge
```

`A_side` and `A_flat` are the model's near-vertical and near-horizontal
surface areas; `V` is the solid volume (build123d `shape.volume`,
`face.area`). Two bounds need no area split at all:

```text
ρ · f · V   ≤   m_part   ≤   ρ · V
```

A small or thin part sits near the upper bound (it is almost all skin); a
large chunky part sits near `ρ · (f · V + A · t_wall)`. That is why hollowing
a model saves far less filament than the volume it removes
([[wall-thickness-and-hollowing#hollowing-is-worth-less-than-the-volume-it-removes]];
`cadprint.savings()` returns both numbers). Wall and infill choices for
strength are [[perimeters-infill-and-strength]].

Add what the part does not contain: support (often a large share on an
overhang-heavy part — orient it away, [[overhangs-and-print-orientation]]),
brim, and for multi-material the purge per tool change, which can exceed the
part ([[fdm-multi-material-design]]).

## Density, length and cost

Use the density of the filament that will be printed
([[filament-properties#printed-specimen-properties-one-supplier-one-test-method]]).
Suppliers disagree: one PLA sheet gives 1.17 g/cm³, while 1.24 is the common
figure and `cadprint.PLA_DENSITY`. The spread is ±3 %, below the error in
the infill estimate.

Length per mass follows from the filament cross-section:

```text
A_fil = π d² / 4           1.75 mm → 2.405 mm²   2.85 mm → 6.379 mm²
g per metre = A_fil · 1000 · ρ / 1000   (mm², g/cm³ → g/m)
metres per kg = 1000 / (g per metre)
```

| filament | ρ g/cm³ | g/m at 1.75 | m/kg at 1.75 |
|---|---|---|---|
| PLA | 1.24 | 2.98 | ≈ 335 |
| PLA (low-density sheet) | 1.17 | 2.81 | ≈ 355 |
| PETG | 1.25 | 3.01 | ≈ 333 |
| ABS | 1.12 | 2.69 | ≈ 371 |

Cost is `m · price_per_kg / 1000`, with `m` including support, brim and
purge.

## Time: flow-bound, then everything else

A hotend can melt only so much plastic per second — the **maximum
volumetric speed** (MVS, mm³/s). The slicer caps each move so
`speed ≤ MVS / (line_width · layer_h)` (Prusa; it uses a stadium
cross-section, slightly less than `w · h`). Prusa's knowledge base lists
typical ranges: PLA 12–20, PETG 8–15, ABS/ASA 10–16, PC 6–10, PA 8–12,
TPU 2–5 mm³/s; standard all-metal hotends 8–12, high-flow hotends 25–40 mm³/s.

That gives a hard **lower bound** on print time:

```text
t_min = V_extruded / MVS                     V_extruded = m / ρ
```

Worked: 40 cm³ of PLA at 12 mm³/s → t_min = 40 000 / 12 s ≈ 56 min. The real
time is longer, often several times longer, because:

- **perimeters print slowly on purpose** — an outer wall at 0.45 × 0.2 mm and
  25 mm/s is 2.25 mm³/s, far below MVS, and on a thin-walled part perimeters
  are most of the volume;
- **small layers are slowed** to a minimum layer time for cooling, so a tall
  thin part is time-bound by layer count `H / layer_h`, not volume;
- **acceleration and corners**: the head rarely reaches the set speed on short
  moves; the estimate is only as good as the machine limits configured in the
  slicer — PrusaSlicer's estimate can double when a single acceleration limit
  changes (PrusaSlicer issue 9474);
- **travel, retraction, tool changes**, and per-layer Z moves.

Rules of thumb that fall out of this:

- Halving layer height doubles the layer count. Moves limited by their set
  speed (perimeters) take twice as long; moves limited by MVS (fast infill)
  can run twice as fast on the halved cross-section and barely change
  ([[fdm-layer-height-and-nozzle#what-the-nozzle-changes]]).
- A 0.6 nozzle shortens speed-limited moves (a wall needs fewer, wider lines
  at the same speed); moves already at MVS gain nothing unless the hotend
  melts more, and a layer-time-bound part gains little.
- Many copies on one plate share the per-layer overhead; a single small part
  wastes it.

Report the estimate as a range, `t_min … k · t_min`, and let the slicer's
figure replace it once sliced.

## Spiral vase mode: what it is

Vase mode (PrusaSlicer "Spiral vase", Cura "Spiralize outer contour") prints
the part's **outline as one continuous helix**, rising Z steadily instead of
stepping, with no layer seam. The slicer forces one perimeter, 0 % infill,
no top solid layers and no support; only the bottom layers remain solid.
Only one object per job (Prusa; sequential printing works around it).

Model it as the **solid** outside shape: the slicer produces the wall. A
model that is already a shell gives inner and outer contours and fails
(Prusa).

## Which geometry qualifies

- **One island per layer**: every horizontal section is a single closed
  outline. Two posts, a handle loop or a hole through the side makes a
  second contour the spiral cannot visit.
- **No top**: the part is open at the top, or its top is only the rim.
- **Self-supporting overhangs**: a one-line wall has no inner line to lean
  on, so overhangs must stay within the normal limit, with margin
  ([[overhangs-and-print-orientation]]) and there is no bridging.
- **No internal geometry**: shelves, ribs and internal walls are ignored
  unless connected to the outline. A near-zero-width slit from the outline
  into the part (≈0.0001 mm, with the slicer's gap-closing radius set to 0)
  makes the spiral trace in and back out, giving a double-wall internal rib
  (vorpal.se).

## Strength limits of a single wall

- The wall is **one extrusion width**. It can be widened (Prusa's example
  0.45 → 0.6 mm on a 0.4 nozzle) with a bigger nozzle or wider line, but it
  cannot be reinforced with extra perimeters.
- Loads across the layers of a one-line wall peel it apart; treat a vase-mode
  part as cosmetic or as a light container, not a structural part
  ([[layer-anisotropy]]).
- Prusa gives the wider line as the way to a stronger or watertight
  container; a default-width single wall is not a seal until tested.
- Material and time: `m ≈ ρ · (A_side · w + A_bottom · t_bottom)`, and time
  is dominated by path length at wall speed — typically a fraction of a
  normal print of the same outline.

## Checks

```python
m_hi = RHO * V_solid / 1000                        # g, V in mm³
m_lo = RHO * INFILL * V_solid / 1000
assert m_lo <= m_est <= m_hi, "mass estimate outside the solid/infill bounds"
t_min_h = (m_est / RHO * 1000) / MVS / 3600
assert t_budget_h >= t_min_h, f"budget below the flow-bound minimum {t_min_h:.1f} h"
if VASE_MODE:
    assert all(len(sec.wires()) == 1 for sec in horizontal_sections), "vase mode needs one outline per layer"
    assert not has_top_face and max_overhang_deg <= OVERHANG_MAX, "vase mode: no top, no bridges"
```
