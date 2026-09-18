# Gears

Search `$step-parts` first, on the governing numbers (module, tooth count,
bore). A catalog gear at the right module beats a hand-authored one; a recorded
miss (manta_ray: m1 spur gears exist for 10/12/16/20/24/30/36/40/48/60/80
teeth, not 13/17/39/44) is what licenses authoring one.

## Spur gear numbers

| quantity | formula | note |
|---|---|---|
| pitch diameter | `d = m z` | the circle the mesh rolls on |
| tip diameter | `da = m (z + 2 ha)` | `ha` = 1.0 full depth, 0.8 stub |
| root diameter | `df = m (z - 2 × 1.25)` | dedendum 1.25 m |
| circular pitch | `p = π m` | tooth + gap along the pitch circle |
| centre distance | `a = m (z1 + z2) / 2` | internal gear: `m (z2 - z1) / 2` |
| ratio | `i = z_driven / z_driver` | output turns `i` times slower |
| rack travel per pinion turn | `π m z` | |
| bevel pitch cone (90°) | `δ1 = atan(z1 / z2)`, `δ2 = 90° - δ1` | mitre pair: 45° / 45° |

**Centre distance is derived, never typed.** manta_ray audits it as a datum
pair: `hypot(axis1 - axis2) == m (z1 + z2) / 2` within 0.2 mm. Place the
second shaft from the formula, then assert the placed distance.

## Printed tooth choices

- **Module ≥ 0.8 for FDM, 1.0 is the comfortable floor.** Below it the tooth
  tip is a few extrusion widths and prints as a blob.
- **Pressure angle**: 20° is standard; 14.5° with stub teeth (0.8 m addendum)
  gives thicker tips on small pinions (trotter's worm pair).
- **Undercut limit** for generated involutes: `z_min = 2 ha / sin²(α)` →
  17 teeth at 20°, 32 at 14.5° (full depth). A printed tooth is not generated,
  so this is a warning line: below it go stub, thin the tip, or add teeth —
  and check the tip width is ≥ 2 extrusion widths.
- **Backlash**: 0.2–0.3 mm per gear on a 0.4 nozzle (trotter measured 0.30:
  clear over a full tooth). Apply it by thinning each tooth at the pitch
  circle, never by pushing the centres apart — that shortens contact.
- **Face width** 6–10 m; wider only helps if the shafts are stiff.
- Knife edges at the tooth ends print badly: ramp the teeth in at the faces.

## Body under the teeth

The bore or keyed socket must leave a solid ring under the root circle:

```python
wall = (M * (Z - 2.5) - BORE_ACROSS_CORNERS) / 2
assert wall >= 1.2, f"m{M} z{Z}: {wall:.2f} mm of body under the teeth"
```

trotter-src's m1 z8 pinion had a 5.5 mm root circle and a 6.2 mm socket: the
teeth hung on a 0.4 mm skin and every gate passed it. If the assert fails,
add teeth, raise the module, or put the pinion on a hub.

## Mesh phasing

Two gears modelled at rest must put a tooth of one into a gap of the other on
the line of centres, or they overlap at rest and `interfere` fails. Rotate
one gear by `180° / z` from tooth-on-line to gap-on-line; with an odd tooth
count the tooth that sits on the line is not opposite another tooth. Record
the phase as a parameter and, in the kinematics, drive the second gear by
`-θ × z1 / z2` from that phase.

## Worm and crossed-helical pairs

- wheel pitch radius `r2 = z2 mn / (2 cos β2)`
- worm pitch radius `r1` is free (choose for strength and lead)
- centre distance `a = r1 + r2`; ratio `i = z2 / starts`
- worm lead angle `λ = 90° - β2` for a 90° shaft angle

trotter: `mn = 1`, 4 starts, `r1 = 4.0`, 12-tooth wheel at 30° →
`r2 = 6.93`, `a = 10.93`, 3:1. A single-start worm with a small lead angle
(below ~6°) **self-locks**: the wheel cannot back-drive it. That is right for a
lift or a winch, wrong for a toy the child is meant to roll backwards.

Which way the worm turns for a given wheel direction is a sign that is easy to
get wrong on paper; trotter measured it by sweeping the mesh both ways
(`output/trotter/measure/gear_sweep.py`) and recorded the sign as `[measured]`.

## Trains and ratio budget

- One spur stage up to ~1:6 in print; beyond that compound (two gears on one
  shaft) rather than a tiny pinion.
- The pinion is the weak member: it sees the most tooth engagements.
- Idlers change direction, not ratio.
- Belt or band pulleys replace gears for long centres; they slip, which is a
  feature for a toy with a hand crank.

## Measuring a mesh

Two numbers make a mesh claim honest, both measured on the built solids:

1. **One tooth pitch swept at fine steps** — worst overlap stays ≤ the
   threshold. Step size must be a fraction of a tooth (trotter: 0.35 mm),
   declared as `maxStepMm`, or the sweep steps over the collision.
2. **Free play** — rotate one gear against the other held still until
   contact, both directions (trotter: +1.75 / -1.5°). Zero play means it
   will bind when printed; large play means lost motion.

A full-cycle sweep at coarse steps is a bulk-clearance check, not a mesh
check — say which one each condition is in its description.
