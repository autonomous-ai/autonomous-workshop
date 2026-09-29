# Deciding the conversion without asking

A conversion raises three decisions: what unit each mesh is in, which backend
to spend on it, and whether a mesh with holes can be converted at all. Nothing
after conversion is decided here. How the STEP becomes source, whether the set
is assembled, and when the references are deleted all belong to
`$step-to-source`'s `references/deciding-without-asking.md`.

The rule is **measure, decide, declare**. For two of the three, the user's
answer is worse than the file's: they are recalling what some other program
did, and the file records what it actually did. The one genuine question is at
the end of *Backend*. It is a question because going ahead would write
something unusable, not merely something assumed.

```bash
python "$STL_TO_STEP_SKILL_ROOT/scripts/convert_plan" mesh/*.stl --project output/thing
```

`convert_plan` applies these rules to the meshes and prints the conversion
commands and the assumptions to declare. It writes nothing, and it refuses a
STEP input. Its last command hands the converted STEPs to `$step-to-source`'s
`source_plan`.

## Units - measured, from the size the file claims to be

Read the max bounding-box dimension as mm, in, cm, m, ft in that order and
take the first reading that lands in **10 mm - 5000 mm**. Under 1 mm the
rescale is `measured`; between 1 mm and 10 mm keep mm and stamp it `assumed`
with the other reading named; let a set of parts settle a single ambiguous
file; with nothing plausible, convert as mm and declare the bounding box. The
reasoning behind each rule:
`wiki show mesh-to-step-conversion#units-read-from-the-size-the-file-claims-to-be`.

`--units` scales the solid **and** the volume it is verified against, so a
declared unit is checked rather than trusted.

## Backend - fidelity first, on what is installed

`2step` is the only backend that repairs a mesh and the only one that restores
complete primitives as analytic surfaces, so it wins whenever it is present.
When it is absent:

- **closed mesh** - convert on `stltostp` or the built-in `sew`, and declare
  that every face came back a facet and no analytic surface was attempted.
  This is not worth 7.6 GB of someone's disk spent without being asked.
- **mesh with holes or non-manifold edges** - this is the real question. No
  other backend repairs, so converting writes a shell with no inside
  (`wiki show mesh-to-step-conversion`). Stop and ask for either the install
  or a closed export, and say which two options they are.

## What to declare, every time

The handover says which of these were decided rather than given:

- the unit, when anything was rescaled, and whether it was `measured` or `assumed`;
- the backend, any fallback and why the preferred one failed, and
  `analytic surfaces none` when nothing was restored;
- the crossing-pair and self-intersection counts, when they are not zero.
  `validate` will reject the solid, every boolean against it will fail, and
  the fix is upstream;
- a mesh reported "not closed" only because of non-manifold edges (0 boundary
  edges), which converts to closed solids on a non-repairing backend.
