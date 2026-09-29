---
name: step-to-source
description: Turn STEP references into build123d source that needs no references - a supplied STEP with no generator, or one $stl-to-step converted from an STL. Plans the route from the files, recovers prismatic solids or re-authors refused ones as named parameters held to frozen measurements, releases (deletes) the reference STLs and STEPs once the source passes, and assembles the parts into one model with the right part in the right place. Also reads exact facts out of a B-rep (bore diameters and positions, chamfer angles, fillet radii, stepped bores, wall spacing). Use when asked to reverse, decompile, re-parameterise or "make parametric" a STEP, to delete the STL/ref STEP while keeping the source, or to put a kit that arrived as separate parts or print plates back together.
---

# STEP to source

## Purpose

Take a STEP with no generator and end with source that builds the same object
without it: parts as named parameters, an assembly that places them, and the
reference files deleted. Measure the distance from source to reference at
every step, so each claim is checked rather than assumed.

This is not a decompile. A B-rep stores surfaces, not history. Nothing in it
records that a face came from an extrude, that a bore was a shaft plus a
clearance, that two parts are a mirrored pair, or what any dimension was
called. The geometry survives; the design intent is authored again.

## The route

```text
STL ──$stl-to-step──> ref/<name>.step ─┐
                    supplied STEP ─────┤
                                       ▼
                    1. plan           source_plan: exit per solid, placement verdict
                    2. build source   recover | re-author  ->  params.py, parts/, validation.py
                    3. spec + release <name>_spec.md, then release_refs deletes ref STLs/STEPs
                    4. assemble       assemblies/ from parts/: right part, right place
```

An STL is converted first, and `$stl-to-step` does nothing else. From the
converted STEP on, a converted mesh and a supplied STEP take the same four
stages. Run from the repository root. `python` means `.venv/bin/python`.

**Inside Workshop** there is no repository root. Resolve the skill trees
instead, and run from the project directory:

```bash
STEP_TO_SOURCE_SKILL_ROOT="$(workshop skills path)/step-to-source"
CAD_SKILL_ROOT="$(workshop skills path)/cad"
```

A `skills/<name>/...` path in these pages, or in a command `source_plan`
prints, names a sibling Make skill under `"$(workshop skills path)/<name>/"`.
In a product run, `release_refs --delete` may remove only a reference the run
itself converted or copied into its project; a sealed Wish reference and every
other host-materialized input stays exactly where the host put it.

## Use this skill when

- a STEP arrived without source and has to be modified, parameterised or
  rebuilt;
- the user wants the supplied STLs or reference STEPs **deleted** and the
  source to keep exporting;
- several parts arrived as separate files, or as print plates, and have to
  become one specific assembled model;
- the exact geometry of a STEP is needed as numbers.

Do not use it when a generator exists: edit that generator, because recovering
from its output throws away every name and relationship. Do not use it on a
purchased component that only has to be seated: that stays under
`<project>/ref/` with a `cadmount` seat and a `measure/mounts.json` row, is
never re-authored, and survives stage 3.

## 1. Plan

```bash
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/source_plan" <project>/ref/*.step --project <project>
```

For each solid the plan runs the recovery in memory and reports an exit:
`recover`, `recover_refit`, `re-author`, or `several_bodies` (keep each body
separate and labelled). For the set, it gives a placement verdict:
`assembled`, `recentred`, or `print_plates`. It prints the commands for every
stage and the assumptions to declare. It writes nothing. The rules, and what
to declare instead of asking, are in `references/deciding-without-asking.md`.

## 2. Build source

Every part ends in the same state: a builder in `parts/<role>.py` that reads
no file, its dimensions named in `params.py` with provenance, mating datums
recorded as parameters, and its measured volume, bbox and section areas frozen
into `validation.py`. There are two roads to that state.

### Recover: a stack of prisms

```bash
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/step_probe"   ref/part.step --summary
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/step_recover" ref/part.step -o part_body.step.py
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/step_verify"  ref/part.step part_body.step.py
```

1. **Probe** reads the file's own surface parameters. Every number is the
   kernel's, not a fit. It says whether the part can be rebuilt and what
   would block it.
2. **Recover** writes the entry, runs it, compares it against the STEP, and
   stamps the measured difference into the file's docstring. It exits
   non-zero when the recovery misses, and keeps the file either way.
3. **Verify** runs the same comparison on demand, for any two shapes, each a
   STEP or a `<name>.step.py`.

A solid whose every wall is parallel to one direction is a stack of prisms, so
extruding its exact cross-sections reproduces it: **0.000000 %** symmetric
difference on planes and cylinders.

| In the STEP | Rebuilt as | Cost |
|---|---|---|
| planes, cylinders | extruded slabs | exact |
| cone: chamfer, countersink, draft | lofted slab, ruled | exact, because a cone is straight along its generatrices |
| torus: fillet, blend | refused (lofts only with `--loft-tapers`) | recover sharp, re-apply `fillet()` with the probed radius, verify to zero |
| sphere, bspline, freeform | nothing | refused: re-author |

A converted mesh is planes and nothing else, so what decides it is whether
those planes share an extrusion axis (`step_probe`'s `extrusion:` line). A
tessellated bore, boss or gear tooth leaves facets at every angle, so expect
refusal. On a 15-part kit, 1 of the 7 simplest parts recovered.

**A recovered entry is not finished.** Every dimension is a literal. Name the
ones that matter into `params.py`, restore relationships with `cadfits`,
re-apply chamfers and fillets as features, and run `step_verify` after each
edit. The procedure is in `references/what-survives.md`.

### Re-author: everything recovery refuses

Measure the reference (`references/measuring.md`), author the part the way it
was probably designed, compare it per cut while the reference exists, and
freeze the numbers reached. See `references/re-authoring.md` for the layout,
the frames, the authoring rules and the acceptance figures.

While parts are being authored, a carrier entry can stand in for one that is
not done yet. It is a scaffold, never the finish (`references/carrying.md`).

### Reading a verification

`step_verify` exits on the symmetric difference, the material in one solid and
not the other as a fraction of the original's volume. Volume agreement is
deliberately not the test, because a bore moved 3 mm changes no volume. Look
twice at a **PASS with differing surface kinds**, which means something was
approximated. **Failed booleans** are reported as a failure, never as a
number: both shapes must be valid first (`$cad`'s `inspect validate`). Against
a faceted reference that self-intersects, use per-cut IoU instead
(`references/measuring.md`).

## 3. Write the spec, then release the references

The source is finished when it no longer needs what it was measured from.
Before anything is deleted, write `<project>/<name>_spec.md` from
`templates/source_spec.md`. It holds the bill of materials, each part's key
parameters with how they were measured, the mating datums, the assembly pose
and its source, what is not modelled, and the verification figures reached.
After release, the spec and `validation.py` are the only record of what the
references were, so both are gated:

- every millimetre number carries `[observed]` (measured on a reference),
  `[inferred]` (derived) or `[assumed]` (chosen) (`check_spec_format`);
- every `` `PARAM` value `` quoted must equal `params.py`, and the spec must
  quote at least one (`check_spec_numbers --strict`);
- anything driven (motor, crank, linkage) needs section 8 with a feasibility
  `assert` and a motion table that has a blocked row for every clear one.

`verify_project` runs the same two gates on every later run, so the spec
cannot drift from the source.

```bash
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/release_refs" <project>             # dry run
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/release_refs" <project> --delete    # checks, then deletes
```

It deletes only when every check passes:

- nothing in the source reads a reference: no carrier, and no `import_step`
  of a file that is not a declared purchased part;
- `validation.py` exists and passes;
- `<name>_spec.md` exists and passes `check_spec_numbers --strict` and
  `check_spec_format`;
- every entry's `.step` was written after the newest source (`gen --write`
  first).

It deletes `ref/**/*.step` not declared in `measure/mounts.json`,
`ref/**/*.stl` and `mesh/**/*.stl`. Photos, manuals and declared purchased
parts under `ref/` stay. A blocker list is the answer to "can I delete the
STLs/STEPs yet".

## 4. Assemble

Build the assembly from `parts/` and nothing else, and prove two things:

- **right part:** every solid carries a role label, bodies are identified by
  label and never by position, and a bill of materials per variant is
  asserted exactly;
- **right place:** the pose comes from the files only when they are a real
  assembly. Otherwise it comes from the designer's photos or manual, then from
  datum pairs that are part parameters. Every placement has determinant +1,
  every other pair is audited, moving parts are solved rather than typed,
  keys and teeth are phased by scan, and `interfere`, `check_motion` and a
  render against the photos close it.

Asked whether a combined file is "assembled correctly", answer from the
placement verdict first. A `print_plates` or `recentred` combined entry is a kit
layout, not an assembly, and a clean `interfere` on it proves nothing. Say so,
say what assembling will cost, and find the designer's build photos before
asking the user how the parts go together.

`references/assembling.md` has the method and the numbers from a 15-part kit.

## 5. Close: run the gates the rebuild claims, not the print gates

A rebuild claims one thing: the source builds the same parts, in the right
place, as the references did. The closing run proves that and nothing more:

```bash
CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/verify_project" <project> \
  --assembly <name>.step.py --fresh
```

Do **not** add `--print-gates` on this route by default. `check_mesh`,
`check_overhang` and `check_thickness` measure whether geometry prints, not
whether it matches the reference, and they cost three tessellating runs per
printable entry (48 runs on a 16-part kit) after everything that proves the
rebuild has already passed. They measure the designer's geometry, which the
rebuild copied on purpose: a thin wall or an overhang they flag is the
original's, not a rebuild defect, and the fix would be a departure from the
reference. None of these makes it a print request:

- the input was an STL, or the kit arrived as print plates;
- the parts are marked `PRINTABLE = True` and sit on a Z=0 bed datum (that is
  layout and `check_fit`, not a printability claim);
- the designer's page is a printing site.

Add `--print-gates` only when the user asks for print-ready parts or a
printability check, or when the task changed printed geometry away from the
reference (new walls, new overhangs, rescaled parts). Without it, report
printability as unverified in the spec's section 6/7 and in the handoff, which
is what the repository rules require, and do not describe the result as
print-ready.

## References

- `templates/source_spec.md` - the spec for a model rebuilt from references,
  written before release and gated by `check_spec_numbers` and
  `check_spec_format`.

- `skills/wiki/pages/reverse-engineering/` - the knowledge behind every stage:
  `brep-vs-source`, `mesh-measurement`, `authoring-from-a-reference`,
  `kit-assembly-poses`, `kit-assembly-clash-diagnosis`,
  `mesh-to-step-conversion`, `cad-container-formats` (`wiki search <words>`).
- `references/deciding-without-asking.md` - the exit per solid, bodies,
  placement verdict, when references can go, names, and what to declare.
  Read it before asking the user anything on this route.
- `references/what-survives.md` - what a B-rep keeps and destroys, and how to
  re-parameterise a recovered entry.
- `references/measuring.md` - which source to measure each number on, the
  mesh and section instruments, the ones that lied, and source-vs-reference
  comparison.
- `references/re-authoring.md` - Tier 3 layout in per-part frames, separate
  labelled bodies, datums as parameters, authoring rules, acceptance figures,
  and freezing `validation.py`.
- `references/carrying.md` - the carrier entry and `carrier_project` as a
  scaffold while parts are authored, and why a carried project cannot finish.
- `references/assembling.md` - the right part and the right place: where the
  pose comes from, label-based identity and BOM, datums as parameters, det
  +1, datum-pair audit, solved linkages, scanned phases, and the proofs.

Every script runs its own fixtures with `--self-check` and needs no project.
