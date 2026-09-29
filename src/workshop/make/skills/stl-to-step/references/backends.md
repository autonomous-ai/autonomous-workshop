# The three backends

Read this before installing anything, when a conversion falls through to a
backend you did not expect, or when every backend refuses a file. What each
kind of converter can and cannot do, why sewing cost is not linear in facets,
and why the check is volume are design knowledge:
`skills/wiki/pages/reverse-engineering/mesh-to-step-conversion.md`
(`wiki show mesh-to-step-conversion`).

## What each one is

### `2step` - github.com/yaneony/2STEP-Converter (MIT)

Python on OpenCASCADE, shipped with its own micromamba environment. The only
backend that repairs a mesh and restores complete primitives as analytic
surfaces, which is why it is first in the chain
(`wiki show mesh-to-step-conversion#what-each-kind-of-converter-can-and-cannot-do`).

The install is ~7.6 GB. Ask the user before spending it:

```bash
python "$STL_TO_STEP_SKILL_ROOT/scripts/stl_to_step" --install 2step
```

Its flags are read from its own `--help` at call time rather than assumed: the
CLI belongs to another project, and a flag it does not know turns a conversion
into an argparse error and a silent fall-through to a backend that repairs
nothing.

Three things about it are worth knowing before the first run:

- **It is driven from its own checkout**, because that is where its launcher
  expects to be, so every path handed to it is resolved absolute first. A
  relative one resolved under the tool cache and came back `File not found`.
- **It does not hand back the vertices it was given**, so both the volume and
  the bounding-box checks carry a percentage.
- **Read the `analytic surfaces` report line.** `none` is the expected result
  on anything freeform, not a failure.

### `stltostp` - github.com/slugdev/stltostp (BSD)

A small C++ tool with no dependencies; the install is a cmake build measured in
seconds. It merges edge-connected coplanar triangles into planar faces and
writes AP203/AP214. No analytic reconstruction, no mesh repair.

Its raw output has no product structure and an `OPEN_SHELL` rather than a
solid (`wiki show mesh-to-step-conversion`). This toolchain adds the minimal
AP214 wrapper and sews and promotes the faces, touching no coordinate, and
prints both repairs. If either line appears in a report, the backend's raw
file was not usable as delivered. It is still a legitimate conversion; the
geometry is its own.

### `sew` - built in

The same idea as `stltostp`, in process, on the OCP the CAD skill already
requires: each triangle becomes a face, the faces are sewn into shells, each
closed shell becomes a solid, and `ShapeUpgrade_UnifySameDomain` merges
coplanar faces. No network, no build, no install.

It exists for three reasons: it is the fallback when nothing else is installed,
it is what the self-checks run so they work offline, and it is the reference
the other backends are compared against. On a clean prismatic fixture it
produces the same merged face set `stltostp` does.

**It runs in a child process, and that is not incidental.** `--timeout` has to
mean the same thing here as on the two backends that shell out, and in process
it cannot: sewing is one C++ call that a Python signal handler cannot
interrupt. A child can be killed. `_stage` in
`meshstep.py` is that indirection, and it covers the promote-to-solid step too,
which sews the faces of whatever the winning backend wrote and was unbounded
for the same reason. Both report `timed out after Ns` and hand the chain on.

## The verification

Every backend's output is checked the same way, inside the chain, before it is
accepted: a solid exists, `BRepCheck_Analyzer` calls the shape valid, the
bounding box agrees, and the solid's volume matches the volume computed from
the triangles, within a printed percentage. `valid` here does not include
self-intersection; catch that from `mesh_probe`'s crossing count. Why:
`wiki show mesh-to-step-conversion#why-the-conversion-check-is-volume`.

## When every backend refuses

Work through these in order:

1. **`mesh_probe` says the mesh is not closed.** Nothing downstream can fix
   that. Either install `2step`, which repairs meshes, or go back to whoever
   exported it: a slicer or scanner export with holes is a bad export, not a
   hard problem.
2. **The mesh is closed and the volume check still fails.** Compare the
   bounding box in both reports. A large delta with a correct shape is a units
   problem - convert with `--units in` (or `cm`, `m`) and it will agree.
3. **`sew` reports `timed out after Ns`**, or runs long on a mesh above ~50k
   facets with large flat regions. The cost is driven by defects and coplanar
   area, not facet count
   (`wiki show mesh-to-step-conversion#sewing-cost-is-not-linear-in-facet-count`).
   Reduce the mesh (`2step` takes `--reduce`, and any mesh tool will do it), or
   use `2step`, which fits surfaces before sewing. Raise `--timeout` only when a
   smaller run has shown the trend is survivable.
4. **A scan, or an organic shape.** The conversion will succeed and give you a
   solid with tens of thousands of faces that every later gate crawls through.
   Convert a reduced copy for measurement, then re-author the part.
5. **Every backend accepted it and `validate` rejects the result.** Not a
   conversion failure: check `mesh_probe`'s crossing count. A mesh whose
   surfaces cross converts cleanly into a solid whose faces cross, and the
   defect belongs to whatever wrote the mesh.

## Cache and offline behaviour

Checkouts live in `~/.cache/autonomous-cad/step-tools`, overridable with
`CAD_TOOL_CACHE`, and never inside the worktree - the entry resolver scans the
whole tree, and a cloned converter full of `.py` files is exactly the stale
envelope that breaks unrelated validation.

With no network and nothing installed, `sew` still runs and the self-checks
still pass. That is deliberate: a skill whose tests need a download is a skill
that stops being testable on the day it matters.
