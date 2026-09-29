# Deciding the route without asking

Once there is a STEP, whether supplied or converted from an STL by
`$stl-to-step`, a few decisions remain: how each solid becomes source, whether
bodies stay separate, whether the set is already assembled, and when the
references can go. The rule is **measure, decide, declare**. For each of
these, the file's answer is better than the user's: they are recalling what
some other program did, and the file records what it actually did.

```bash
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/source_plan" <project>/ref/*.step --project <project>
```

`source_plan` applies the rules below and prints the commands and the
assumptions to declare. It writes nothing. The conversion's own decisions
(unit, backend, holes) belong to `$stl-to-step`.

## How each solid becomes source - measured, by running the recovery

`step_recover` decides by refusing, so `source_plan` runs the recovery in
memory rather than predicting it:

| what the reference holds | exit | then |
|---|---|---|
| one solid the recovery decomposes | `recover` | name the literals, restore relationships (`what-survives.md`) |
| one solid refused sharp, whose torus faces loft | `recover_refit` | recover to measure, re-apply `fillet()` with the probed radius |
| one solid refused outright | `re-author` | measure and author it (`re-authoring.md`) |
| several solids | `several_bodies` | keep each body separate and labelled; recover or re-author each |

Surface kinds alone do not predict a refusal, so the plan runs the tool; for a
mechanical part converted from a mesh, expect `re-author`. Refused does not
mean hard (`wiki show brep-vs-source#what-a-refusal-is-telling-you`).

Carrying is never an exit here. It is a scaffold while parts are authored
(`carrying.md`), because the route ends with the references deleted.

## Whether the set is assembled - measured, from the bounding boxes

| boxes | verdict | pose from |
|---|---|---|
| each at its own offset, at different heights | `assembled` | the files: record offsets as named placements before release |
| two or more at, or centred on, the origin | `recentred` | datums and mates |
| every one standing on Z = 0 | `print_plates` (`assumed`) | the designer's photos or manual, then datums |

Overlap decides nothing, and the `assembled` verdict can be wrong for a folder
of per-part exports whose origins sit off their bounding boxes. How to read and
refute each verdict: `wiki show kit-assembly-poses#where-a-pose-can-come-from`.
Look for the designer's source before asking the user how the parts go
together (`assembling.md`).

## When the references can go - checked, not judged

When the user asks for the STLs or reference STEPs to be deleted, or when the
source is finished, the answer is `release_refs`:

- nothing in the source reads a reference (no carrier, no `import_step` of an
  undeclared file);
- `validation.py` exists, reads no file, and passes;
- `<name>_spec.md` exists, its quoted parameters match `params.py`, and its
  dimensions are tagged;
- every entry's `.step` was written after the newest source.

If any check fails, the answer is the blocker list, not a deletion. Photos,
manuals and declared purchased parts under `ref/` are kept.

## Names - from the evidence, not guessed

Name a part after the supplied file name, the designer's part list or the
user's words. When two supplied files share a name, they are two roles
(`front_gear_a`, `front_gear_b`). `carrier_project`'s measured group names
(`body_n`, `links_n`) are placeholders, to be replaced once the part is known.
A wrong guess in a filename outlives every comment.

## What to declare, every time

Declare these in the handover and in `<name>_spec.md`, which is written
before release (`templates/source_spec.md`).

- the exit taken for each part, and, for a recovered part, that its literals
  were named;
- per re-authored part, the volume and section-IoU figures reached against its
  reference;
- the placement verdict and where the pose came from;
- what `release_refs` deleted, and what it kept;
- anything not modelled (a motor the kit does not contain) and every designed
  tight fit `interfere` reports.
