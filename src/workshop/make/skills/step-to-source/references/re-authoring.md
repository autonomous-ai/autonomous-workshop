# Re-authoring a part as parametric source

The build stage for every part `step_recover` refuses, and for every part
whose shape must change. The result is source with **no file inputs**: each
part builds from named parameters, and `validation.py` holds it to numbers
measured from the reference and frozen as literals. That is what lets the
references be released afterwards (`SKILL.md`, stage 3).

A recovered part joins the same state by the other road: name its literals,
restore its relationships and re-verify (`what-survives.md`). Either way, the
project ends with the same layout and the same frozen checks.

## Layout

This is Tier 3 from `$cad`'s `references/project-structure.md`. A kit of
several parts passes the 400-line library threshold quickly:

```text
params.py            one block per part; every value has its provenance comment
parts/<role>.py      build() -> the part in its own frame; reads no file
assemblies/<name>.py placement and labels only (assembling.md)
validation.py        MEASURED = {role: volume, bbox, {cut: area}} as literals
<name>.step.py       combined entry
part_<role>.step.py  one per part
```

Give each part the frame its reference arrived in, keep separate bodies
separate and labelled, and record mating datums as parameters as soon as they
are measured. Why each matters:
`wiki show authoring-from-a-reference#frames-bodies-and-datums`.

## Authoring

One parameter per measured quantity with its reading beside it; build the way
it was designed, never a loft between slices; correct plan-view chamfers for
offset growth; search the catalog before authoring a standard element; derive
mates with `cadfits`. The rules and the reasons:
`skills/wiki/pages/reverse-engineering/authoring-from-a-reference.md`
(`wiki show authoring-from-a-reference#build-it-the-way-it-was-designed`).

Measure with `measuring.md`: which source to prefer for each number, the
instruments, and the ones that lied.

## Holding the source to the reference

While the reference exists, compare every part after every edit round:
`step_verify` against an exact STEP, and per-cut section IoU against a faceted
one (`measuring.md`).

The agreement to expect against a mesh (straight-edged vs turned parts, and
why a turned part comes out slightly over its mesh):
`wiki show mesh-measurement#what-agreement-to-expect-against-a-mesh`. Record
the numbers actually reached, not aspirational ones.

## Freezing the checks

Before the references are released, copy what each reference measured into
`validation.py` as literals: volume, bbox, and section areas at the cuts used
above. `validation.py` rebuilds each part and asserts against those values
within the tolerances actually reached, and exits non-zero on any miss. After
release it is the only evidence that the source still matches the object, so
it reads no file. `release_refs` runs it and refuses to delete anything if it
fails.

Then write `<name>_spec.md` from `templates/source_spec.md`. Quote each part's
key parameters by name (`` `MB_WALL` 2.0 mm `[observed]` ``), with the
measurement beside them and the figures reached against the reference.
`release_refs` also refuses to delete while the spec is missing, quotes a
parameter that no longer matches `params.py`, or carries an untagged
dimension.
