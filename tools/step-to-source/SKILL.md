---
name: step-to-source
description: Recover editable CadQuery or build123d source from a STEP/STP file, and measure exactly how far the recovery is from the original. Use when handed a STEP without its generator, when asked to reverse-engineer, decompile, or "get the Python back" from a CAD file, or when a mesh (STL/3MF) has been converted to STEP and needs re-authoring. Not for STL or 3MF directly -- a mesh carries no analytic geometry to recover.
---

# STEP to source

Recover a parametric Python program from a B-rep solid, and say plainly how
much of the original survived.

## What is actually recoverable

A STEP file stores the finished solid, not the program that built it. There is
no feature tree, no variable names, no sketch constraints, no boolean history.
What it does store is exact analytic geometry -- each face is a plane,
cylinder, cone, sphere, torus, or spline with its own parameters -- so
dimensions come back to full precision while intent does not.

Two different numbers follow from that, and conflating them is the usual way
these tasks go wrong:

| Question | Answer |
|---|---|
| Does the rebuilt solid match the original? | Measurable, often >99.99% |
| Does the source look like the source that made it? | No. Names, relations, and feature order are gone |
| Can one edit propagate like it did before? | No. Every relation is now a literal |

Tell the user the second and third answers up front. A recovered file that
prints identical parts is still not a parametric model, and someone who
believes otherwise will edit one number and get a broken part.

## Workflow

### 1. Measure before promising anything

```bash
python scripts/step_probe.py part.step --summary     # human read
python scripts/step_probe.py part.step               # full JSON fact sheet
```

The summary answers the only question that matters at this stage: is this
shape exactly rebuildable, or only approximable? It reports face kinds, the
analytic fraction, bores with their diameters and axes, chamfer angles, fillet
radii, arc slots, mirror-seam half-cylinders, and whether a single extrusion
direction exists.

Quote the analytic fraction to the user before doing any work. A part that is
100% planes and cylinders will come back exactly; one with spline faces will
not, and saying so early avoids a promise you cannot keep.

### 2. Emit source

```bash
python scripts/step_emit.py part.step --dialect build123d -o part.py
python scripts/step_emit.py part.step --dialect cadquery  -o part.py
```

`step_emit.py` uses **slab decomposition**: when every face is parallel or
perpendicular to one direction, the solid is a stack of prisms, so sectioning
between consecutive cap planes gives each slab's exact cross-section.
Extruding those and fusing reproduces the solid rather than approximating it.

It refuses when that is not true -- a cone tapers along the axis, a torus
curves along it, and extruding a constant section would silently drop those
features. **Do not reach for `--force` to get past a refusal.** The refusal
names the blocking surface kinds; `step_probe.py` already reports the chamfer
angle or fillet radius involved, so the honest move is to emit the slab body
and add `chamfer()` / `fillet()` by hand, then verify.

### 3. Verify -- never skip this

```bash
python scripts/step_verify.py original.step rebuilt.step
```

Run the emitted source to produce a STEP, then compare. The metric is the
symmetric difference -- material in one solid and not the other, both ways --
because equal volumes can hide two compensating errors. The report also
compares face kinds, which is what catches a dropped chamfer even when the
volume error is a rounding artifact.

Booleans in OpenCASCADE go degenerate when two solids share many coincident
faces, which is exactly what a good recovery looks like. The verifier escalates
its fuzzy tolerance only as far as needed and prints which value it used, so
the precision floor of every number is visible; if booleans fail at every
tolerance it falls back to point sampling and reports a confidence interval
rather than a falsely exact figure.

## Measured results

Across the 18 printable parts of `toys/axel-rake-heritage-horizon` (606 faces:
88.1% plane, 9.6% cylinder, 1.0% cone, 1.3% freeform):

- **6 parts emitted**, every one verified at **99.9978%–100%** with identical
  face counts and kinds, in both dialects.
- **12 parts refused** -- 11 with no single extrusion direction, 1 (the wheel)
  because its 45° chamfer rides on cone faces.

Recovered dimensions were checked against the original generator's constants
and matched exactly: bore Ø3.5 against `slot_for(3.0, 0.25)`, arch radii
30.2/33.2 against `ARCH_INNER`/`ARCH_OUTER`, axle centres against
`AXLE_X = (-70, 70)` and `AXLE_Z = 27`.

Read that honestly when quoting it: **a third of parts came back exact, and
none of them came back parametric.**

## Inputs this skill does not accept

STL and 3MF are triangle meshes. They carry no planes, cylinders, or radii to
recover -- only facets -- so there is nothing for `step_probe.py` to read. A
mesh must first be converted to a B-rep (FreeCAD `Part > Shape from mesh`,
Fusion `Mesh > BRep`), and the result is a faceted solid whose "cylinders" are
hundreds of tiny planes. This skill will report that faithfully: a very low
analytic fraction and no prismatic axis. That is the correct answer, not a
failure -- tell the user the mesh has to be re-modelled, not recovered.

## Reporting back

State the verified match percentage, whether face kinds matched, and which
features were dropped. Then state what was not recovered: parameter names,
derived relations, fit and tolerance intent, boolean decomposition, feature
order, module structure, and mirror relationships. The user is deciding
whether to build on this file or re-model from scratch, and only the second
list tells them which.
