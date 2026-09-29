# Carrying: a scaffold, never the finish

A carrier entry imports a reference and returns it:

```python
from pathlib import Path

from build123d import import_step

PRINTABLE = False
CARRIES = "ref/<name>.step"


def gen_step():
    shape = import_step(str(Path(__file__).resolve().parent / "ref" / "<name>.step"))
    shape.label = "<name>"
    return shape
```

It builds, `gen --write` re-emits the object, and every gate can run on it. That
makes it useful **while the work is in progress**: something to review, place
roughly, or interference-check while each part is re-authored. It is not where
the route ends. The route ends with source that needs no references, and a
carrier dies with its reference. `release_refs` refuses to delete anything
while a carrier exists, reporting both its `CARRIES` line and its
`import_step` call.

`CARRIES` exists so that `verify_project` does not mistake the carried STEP
for a purchased component awaiting a `measure/mounts.json` row. It must be a
literal path, or a list of literal paths, under `ref/`.

## Splitting a multi-body reference

A reference with several solids carries the structure the file kept: how many
bodies, which repeat, where each sits. One `import_step()` throws that away
(`wiki show authoring-from-a-reference#a-multi-body-reference-already-carries-structure`).

```bash
python "$STEP_TO_SOURCE_SKILL_ROOT/scripts/carrier_project" <project>/ref/<name>.step \
                                                     --name <name> --dry-run
```

`--dry-run` lists the groups and writes nothing, which is often all the
re-authoring stage needs: the body count, which bodies repeat, and each one's
volume. Without it, the script writes `<name>_lib.py`, one
`part_<role>.step.py` per group, and a combined entry. Bodies are grouped by
**volume and face count, never by bounding box**, because a repeated body laid
along a curve arrives rotated. Roles are measured, not identified (`body_n`,
`links_n`), and each group re-checks its members' volumes, so a replaced
reference fails loudly. Degenerate solids are reported and left out.
Why volume and face count and not the box: a repeated body laid along a curve
arrives rotated.

Replace groups with authored parts one at a time. When the last group is
authored and the carrier library is gone, the project can release its
references.

## What a carried project cannot pass

`validate` (self-intersecting mesh solids), `interfere` (overlapping shells
inside one file), a small file (every facet is a B-rep face), and
`release_refs`. Measurements and reasons:
`wiki show authoring-from-a-reference#what-a-carried-mesh-conversion-cannot-pass`.
