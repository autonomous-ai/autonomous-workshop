# Repair loop

Read this file when generation, export, inspection, positioning, or documentation validation fails.

## Loop

1. Read the failing command output.
2. Classify the failure.
3. Make the smallest responsible source or command change.
4. Rerun the failed command in the same model round as the source change.
5. Rerun any dependent validation checks.
6. Report remaining risk or deliberate deviations.

## Failure classes and fixes

Classify the failure first. What each class usually means and its source fix
lives in the wiki (`wiki search <words>`):

| failure | page |
|---|---|
| "Failed to create valid loft" / "Recovery failed", or a loft that succeeds with an absurd volume | `wiki show loft-pitfalls#diagnosing-failed-to-create-valid-loft` |
| a boolean against a large lofted surface never returns | `wiki show boolean-pitfalls#booleans-against-a-large-lofted-surface` |
| source import or syntax failure, invalid or missing geometry, wrong scale or bounding box, missing feature, selector fragility, positioning or joint mismatch | `wiki show modeling-failure-modes` |
| fillet or chamfer failure | `wiki show fillet-chamfer-pitfalls` |
| a valid-looking body that fails the next boolean, or an inverted solid | `wiki show kernel-validity` |

For a positioning or joint mismatch, inspect `refs --positioning`, then `frame`
and `align` on the relevant selectors, apply the smallest correction from
`positioning.md` (Source-level positioning corrections), regenerate the
assembly from the Python source and rerun the failed check.

### Where the gate and the repair agree about a mesh

`scripts/check_mesh` and `scripts/repair_mesh` share `scripts/meshlib.py`, and
they share it on purpose: a gate and its repair that each carried their own
idea of what a vertex is would disagree exactly where it matters — a weld
tolerance that closes a hole for one and leaves it open for the other reads as
a flaky check rather than as two definitions. Change the tolerance or the
umbrella walk there, never in one caller.

```bash
.venv/bin/python "$CAD_SKILL_ROOT/scripts/meshlib.py"       # self-check
```

### Mesh defects the generator produced

`check_mesh` fails on three things that no source-level check sees, because they
appear only in the tessellation. It builds the entry from source and tessellates
the B-rep itself, so there is no export step and no artifact -- and no way to
close the loop other than fixing the generator. `scripts/repair_mesh` writes
nothing; it repairs in memory to prove which defect class you have and what
closing it costs, and then names the source fix.

**A feature whose pitch equals its own size.** A 3x3 grid of 28 mm pockets on a
28 mm pitch leaves each pocket's corner touching its neighbour's at exactly one
point. The solid is valid, `validate` and `interfere` both pass, and the mesh
comes out with an edge four faces share -- two cones of material joined at a
line no slicer can walk across. Cutting the pockets in one combined operation
does not help; the tools do not overlap, so the result is the same.

```python
POCKET = PITCH - 0.1        # not PITCH
```

The same arithmetic reaches this by accident whenever a size and a spacing are
derived from one parameter without a gap term. Give the gap a name.

**A union of solids that only touch.** Two operands meeting on a coplanar face,
or at an edge, return two solids rather than one -- `references/organic-lofts.md`
covers the lofted form of this, where a segment starting at the previous
segment's last station starts *outside* it. In the mesh it shows up as open
edges along the seam, or as a second shell. Overlap the operands, and assert
what you expected:

```python
assert len(shape.solids()) == 1
```

`--nudge`-sized translations are not the fix. A 0.01 mm shift makes the boolean
intersect, but leaves a 0.01 mm feature in the geometry; overlap by something
the model can afford (roughly 1 mm for a through-cut, a whole station for a
loft) and let the union absorb it.

**Slivers, and the holes dropping them opens.** Tessellation emits triangles
with no altitude. They carry no geometry, so `check_mesh` drops them before
counting -- but a sliver stitching a T-junction was load-bearing, and dropping
it opens the three edges it held. That is why the gate reports the boundary
count both ways: if the two differ, the hole is the drop, and the fix is the
tessellation deviation rather than the shape. `printlib.MESH_DEVIATION` sets it
for every gate at once; a defect that survives a finer deviation is in the solid.

**To find out which of the three you have:**

```bash
python "$CAD_SKILL_ROOT/scripts/repair_mesh" <project>/part_<role>.step.py
```

It drops slivers, triangulates every planar hole rim (including a figure-8 rim,
which a fan or ear-clip fill cannot close), and splits each non-manifold vertex
into one vertex per umbrella, moved 2 microns into its own material. All of that
happens in memory and is discarded: what you keep is the before/after table, the
volume the repair moved, and the named source fix. `RESULT: clean` means a source
fix of that shape exists, not that anything is now fixed. Make it in the
generator, rebuild, and rerun `check_mesh`.

## Diff after repair

Use `diff` when the fix might have affected unrelated geometry:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" diff path/to/before.step path/to/after.step --planes
```

## Reporting failed repairs

If a check cannot be repaired in the current environment, report:

```text
- what failed
- what was tried
- which artifact is still usable
- which validation claims cannot be made
- what the next source-level correction should be
```
