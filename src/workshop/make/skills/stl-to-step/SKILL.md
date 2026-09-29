---
name: stl-to-step
description: Convert an STL the user supplied into a verified STEP solid, and nothing else. Use when someone hands over an STL (or several) and the work needs a STEP; when asked to "turn this STL into a STEP/CAD file"; or to judge whether a supplied mesh is closed enough to convert. It decides unit and backend from the files, converts, and verifies volume, box and self-intersection. Its output is a faceted reference STEP under ref/, never source; everything after that - source, deleting the references, assembly - is $step-to-source.
---

# STL to STEP

## Purpose

Turn a triangle mesh into a valid STEP solid, and measure the result against
the mesh so the conversion is a checked fact rather than a file that appeared.
That is the whole job. The converted STEP is a reference for
`$step-to-source`, which builds source from it, deletes it, and assembles.

A mesh and a B-rep are not two encodings of the same thing. An STL holds
triangles and nothing else: no radius, no axis, no plane, no units. Every curve
in the original was replaced by flat facets before the file was written, and no
converter reads them back. So what this does is change the container - the
triangles become faces of a closed solid - plus, on one backend, a bounded
attempt to recognise a few complete primitives and restore them.

That is worth doing. A solid can be measured, cut, mounted against, checked for
interference and gated for printing; a mesh can do none of those things in this
toolchain. What it does not produce is source, a parametric model, or the exact
geometry the mesh threw away.

"Can be gated for printing" is not "must be". An STL input is not a print
request: `$step-to-source` closes the rebuild without `--print-gates` unless the
user asks for a printability check (its section 5).

## Use this skill when

- the user has only an STL, or a set of them, and the work needs STEP
- someone asks whether their STL can become CAD, and how much of it survives
- a supplied mesh must be checked for holes, crossings or units before anything
  is built from it

Do not use it when a STEP already exists: go straight to `$step-to-source`.

**Inside Workshop** there is no repository root: resolve
`STL_TO_STEP_SKILL_ROOT="$(workshop skills path)/stl-to-step"`, and read a
`skills/<name>/...` path in these pages, or in a command `convert_plan` prints,
under `"$(workshop skills path)/<name>/"`. A product run has no user to approve
an install, so it never runs `stl_to_step --install`: it converts with the
built-in `sew` backend or a backend the host already provides, and reports a
mesh that needs a missing backend as blocked rather than downloading one.

## The route, and where this skill stops

```text
STL ──stl_to_step──> ref/<name>.step    this skill: convert and verify
                     └─> $step-to-source: plan, build source, release refs, assemble
```

When the input is an STL, **the conversion is the first command**: nothing
else in this toolchain reads a mesh. The converted file in `ref/` is not
handed over. It is a reference, and `$step-to-source` builds source from it,
then deletes it (together with the STL) once the source no longer needs it.
This skill makes no decision about source, carrying, assembly or deletion.

**Decide the conversion from the files rather than from the user.**

```bash
python "$STL_TO_STEP_SKILL_ROOT/scripts/convert_plan" mesh/*.stl --project output/thing
```

It reads the meshes and decides unit and backend for each one, and whether
anything is blocked. Then it prints the conversion commands, the assumptions to
declare, and, last, the `$step-to-source` `source_plan` command for the
converted STEPs. It writes nothing. The rules are in
`references/deciding-without-asking.md`.

### Several meshes

Every script here takes **one STL, one call**. Several meshes means a shell
loop:

```bash
for f in base post cap; do
  python "$STL_TO_STEP_SKILL_ROOT/scripts/mesh_probe"  mesh/$f.stl --summary
  python "$STL_TO_STEP_SKILL_ROOT/scripts/stl_to_step" mesh/$f.stl -o <project>/ref/$f.step
done
```

A mesh that fails, times out or comes back self-intersecting fails alone, so
read every file's report, not only the loop's exit code. A set is converted
when every file passed. `--units` is per file: a set mixing exports from two
programs can need different values. Two slicer exports named
`obj_<n>_<name>.stl` can share a `<name>` with different bytes, so name the
converted files apart (`<name>_a`, `<name>_b`) rather than letting one
overwrite the other. **Keep every file where the conversion put it**, the STL
under `mesh/` and the STEP under `ref/`: whether the set is assembled, and
where each part goes, is read from those coordinates by `$step-to-source`.

## Three commands

Run from the repository root; `python` means `.venv/bin/python`. None of them
touches the CAD daemon, so `CADGEN_WARM` does not apply.

```bash
python "$STL_TO_STEP_SKILL_ROOT/scripts/convert_plan"     part.stl --project <project>
python "$STL_TO_STEP_SKILL_ROOT/scripts/mesh_probe"       part.stl --summary
python "$STL_TO_STEP_SKILL_ROOT/scripts/stl_to_step"      part.stl -o <project>/ref/part.step
```

The first takes the whole set at once, mesh or STEP, and decides the route. The
other two each take exactly one file. A set of meshes is one `convert_plan`
call and a loop over the other two (*Several meshes* above).

**Probe first.** A conversion fails for reasons that are visible in the mesh
beforehand, and the decisive one is not triangle count: every edge of a closed
mesh is shared by exactly two triangles. One unshared edge is a hole, and a mesh
with holes sews into a shell with no inside - it cannot be cut, mounted against
or measured for volume. `mesh_probe` counts those edges, and prints the bounding
box, because an STL carries no units and a part that arrives 25.4x too small is
the most common surprise here. The reading decides the unit on a stated rule
(`references/deciding-without-asking.md`), and `--units` scales the solid and
the volume it is verified against, so a declared unit is checked rather than
trusted.

It also counts **crossing triangle pairs**, which is the defect the edge counts
cannot see and the one that survives the conversion. A mesh can be closed and
manifold and still have surfaces cutting through one another; every backend
sews that into a solid with the right volume and the right box, and
`BRepCheck_Analyzer` calls it valid, because that check does not look for
self-intersection. The kernel's BOP check does, and so does this repository's
`validate` gate - after a conversion and a pipeline round. Read the number
before spending either.

**Then convert.** `stl_to_step` tries the backends in order and keeps the first
output that passes verification: a solid exists, the kernel calls it valid, its
volume matches the mesh's own volume within tolerance, and the bounding box
agrees. A backend that exits cleanly and writes an unusable STEP counts as
failed, which is why the check runs inside the chain rather than after it.

The conversion that wins is then counted for self-intersection with the same
BOP check `validate` uses, and the count is printed on its own line. Read that
line, not the word beside the solid count: `well-formed` there is
`BRepCheck_Analyzer`, which never looks for faces passing through one another.
A conversion can be well-formed, hold the volume to the digit, and still be
rejected by `validate` - that is the same gap `mesh_probe` warns about above,
measured this time on the solid rather than the mesh.

It is reported, not failed on, and the asymmetry is deliberate: the defect is
usually inherited from the mesh, where no backend choice removes it, so failing
would walk the whole chain to reach the same answer and then write nothing. A
faceted reference that reproduces the object is worth keeping with the defect
recorded; calling it valid is not. Booleans, fillets and offsets against the
counted bodies should be expected to fail, so say so when handing one over.

The count has a budget (`--self-intersection-budget`, 120 s; roughly 20 s for
100 solids over 49k faces). When it runs out it says how many it did not reach
rather than reporting a partial count as the whole, and `0` skips the check -
which forfeits the answer rather than passing it.

Every attempt is reported, and `skipped` (never installed) is distinguished
from `failed` (ran, did not work), because those need different fixes.

## The backends

| Backend | What it gives | Cost |
|---|---|---|
| `2step` ([2STEP-Converter](https://github.com/yaneony/2STEP-Converter), MIT) | mesh repair, coplanar merging, and complete spheres/cylinders/cones and straight holes restored as **analytic surfaces** | ~7.6 GB, 5-15 min first run: it installs its own micromamba environment |
| `stltostp` ([slugdev/stltostp](https://github.com/slugdev/stltostp), BSD) | triangle-to-triangle with coplanar merging; no analytic surfaces | a few seconds: a C++ build, no dependencies |
| `sew` (built in) | the same class of output, in process, offline | nothing: it uses the OCP the CAD skill already requires |

Install with `python "$STL_TO_STEP_SKILL_ROOT/scripts/stl_to_step" --install <backend>`;
`--list-backends` says what is present. **Do not install `2step` on someone's
behalf** - 7.6 GB is their disk. Use it when it is already there, and when it
is not, convert a closed mesh on what is installed and declare that no analytic
surface was attempted. A mesh with holes is the exception and the one genuine
question on this route: no other backend repairs, so converting writes a shell
with no inside. Stop there and offer the two options - install `2step`, or go
back for a closed export.

Only `2step` restores analytic surfaces, and that is the whole reason it is
first in the chain: a bore that comes back as a real cylinder can be measured
with `step-to-source`'s `step_probe`, and a faceted one cannot. It is also the
only backend that repairs a mesh. When the model matters and the mesh is
imperfect, installing it is the right call; when the part is prismatic and the
mesh is clean, the other two produce the same merged faces it would.

Restoration needs a **complete** primitive to find, so an organic body gets
none of it - the report says `analytic surfaces none` and that is the correct
result, not a failed run. On one there it is still the backend to use, for the
repair and the merge: a mesh with non-manifold edges is one the other two sew
the defect straight through.

Checkouts live in `~/.cache/autonomous-cad/step-tools` (override with
`CAD_TOOL_CACHE`), deliberately outside the worktree: this repository's entry
resolver scans the whole tree, and a cloned converter full of `.py` files is
exactly the stale envelope that breaks unrelated validation.

## What the output is

A STEP holding one solid per closed body, with coplanar facets merged - a
tessellated cube arrives as twelve triangles and leaves as six faces. Its
surfaces are planes: `stl_to_step` prints `analytic surfaces none` when nothing
was restored, which is the normal result on two of the three backends and is
the line that stops the file being mistaken for real CAD.

Use it as a reference part: measure it, mount to it, cut against it, check
interference. Do not treat its faces as design surfaces, and do not fillet or
offset them expecting clean results.

Do not hand this file over either. The geometry is not wrong, but nothing has
gated it and no generator owns it. Hand it to `$step-to-source`, which builds
source from it and then releases it.

## Limits worth stating before promising anything

What a mesh cannot give back (curves, a solid from an open or crossing mesh,
units, assembly, faces exactly on the mesh) and why sewing cost explodes are
general knowledge: `wiki show mesh-to-step-conversion`. What that means for
this skill's commands:

- **STL is the only input.** The mesh is read before a backend is chosen, so a
  3MF, OBJ, AMF, PLY or glTF is refused by name whatever is installed - the
  `2step` backend does not take one either. Export it to STL and convert that.
- **Holes and crossings are fixed upstream.** Only `2step` repairs holes;
  `mesh_probe` counts crossing surfaces, and no backend setting removes one.
- **`--units` is a claim.** It scales the solid and the volume it is checked
  against; declare it, never present it as measured.
- **There is no batch mode.** A set is a loop; whether it is assembled is
  `$step-to-source`'s question.
- **Always pass `--timeout`** (default 900 s) and let it fail rather than
  reading a quiet process as progress. On a timeout, reduce the mesh (`2step`
  takes `--reduce`) or let `2step` convert it - it fits surfaces before it
  sews.
- **Keep the STL until the source is finished**: `2step`'s repair can leave
  faces proud of the mesh, and `$step-to-source` measures mating datums on it.
- **Repairs are reported, not hidden.** A STEP with no product structure, or a
  surface model rather than a solid, is repaired here and printed as a
  `repaired` line. If you see one, the backend's raw output was not usable.

## Self-checks

Each script builds its own fixtures and needs no network or project:

```bash
python "$STL_TO_STEP_SKILL_ROOT/scripts/convert_plan" --self-check
python "$STL_TO_STEP_SKILL_ROOT/scripts/mesh_probe"   --self-check
python "$STL_TO_STEP_SKILL_ROOT/scripts/stl_to_step"  --self-check
```

`convert_plan`'s fixtures hold the decision rules themselves: a 20 mm part
exported in inches reads as inches, a 4 mm one is rescaled but stamped assumed,
two meshes at the origin are the recentred case and two at their own offsets
are not, a holed mesh without `2step` is blocked rather than converted into a
shell, a STEP input is refused rather than planned, and a mesh plan ends by
handing the converted STEPs to `source_plan`.

The rest cover the invariants this skill rests on: a closed mesh converts to one
valid solid holding exactly the mesh's volume; a tessellated bore stays
faceted; two bodies stay two solids; a mesh with holes is refused rather than
written as a shell; a 3MF is refused as the wrong format rather than as a
broken STL; `--units` scales what is verified as well as what is written; and a
backend that fails - by erroring, or by cleanly writing the wrong solid - hands
over to the next one.

Two of them hold the line between the kernel's two notions of a good solid: a
body that passes through itself is counted as self-intersecting even though
`BRepCheck_Analyzer` calls the same body well-formed, and skipping the count
reports as unknown rather than as clean.

## References

- `references/deciding-without-asking.md` - unit, backend and the holed-mesh
  question, and what to declare instead of asking. Read it before putting a
  question about a conversion to the user.
- `references/backends.md` - installing and verifying each backend, what was
  measured here and what has not been run yet, the container repairs, and what
  to do when every backend refuses a file.
- Next: `$step-to-source`'s `SKILL.md`.
