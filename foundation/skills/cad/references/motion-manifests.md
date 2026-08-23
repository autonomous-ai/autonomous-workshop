# Motion manifests

Schema and usage for `scripts/check_motion`. Load this when a project
has parts that insert, slide, hinge, latch, or have to stay put.

## What it is for

`validate` says the solid is sound. `interfere` says nothing overlaps once
assembled. Neither says the parts can be *brought* to that pose, and neither
says a connector actually holds. A motion manifest checks both claims.

## Running it

```bash
python skills/cad/scripts/check_motion <project-dir> --manifest <file.json>
python skills/cad/scripts/check_motion <project-dir> --manifest - < m.json
python skills/cad/scripts/check_motion <project-dir> --manifest m.json --list-parts
```

A manifest belongs at `<project-dir>/measure/motion.json` next to the other
verification artifacts. Exit 0 when every condition holds, 1 on any failure and
on any condition that could not run — a manifest naming a part that does not
exist is a broken check, not a clear path. `--allow-inconclusive` relaxes that
for the genuinely unmeasurable, and still prints what it skipped.

## Part names are placed instances

Parts come from the combined `<name>.step.py`, in **assembly pose**. This is
deliberate: a `part_*.step.py` returns *print* pose, which is the wrong frame
for asking whether two things collide on the way together.

Every labelled node is addressable, including sub-assemblies — a Compound's
solids reach its descendants, so `fuselage_nose` moves as one body rather than
as 60 windows. Where a label repeats, use its dotted path; `--list-parts` marks
which ones need it.

## Schema

```json
{
  "assembly": "<name>.step.py",
  "conditions": [
    {
      "id": "insert-withdraws",
      "check": "linear_motion_collision",
      "expect": "clear",
      "description": "why this motion has to be possible",
      "inputs": {
        "moving_part": "insert",
        "obstacle_parts": ["receiver"],
        "translation": [0, 0, -40],
        "steps": 14,
        "allow_seated_contact": true
      },
      "thresholds": { "maxOverlapMm3": 0.001 }
    }
  ]
}
```

`assembly` is optional when the project has exactly one combined entry.

| check | inputs |
|---|---|
| `linear_motion_collision` | `moving_part`, `obstacle_parts`, `translation`, `steps` |
| `rotation_motion_collision` | `moving_part`, `obstacle_parts`, `axis_point`, `axis_direction`, `start_deg`, `end_deg`, `steps` |
| `clear_path_proxy` | `start`, `end`, `radius`, `obstacle_parts` |
| `assembly_sequence` | `steps`: a list of the above, run in order |

Every motion check takes `allow_seated_contact` and every check takes
`thresholds.maxOverlapMm3` (default 0.001 — contact is not collision).

### `expect` is half the value

`"expect": "clear"` (default) is a motion that must be possible.
`"expect": "blocked"` is a **capture** — a dovetail that has to retain its
tenon, a pin that must not back out, a lid that must not lift.

Without the second form the gate can only ask whether parts come apart, never
whether they stay together, and a connector modelled as a plain boss in a plain
pocket reads as a clean pass. Write both directions for every joint: the one it
assembles along, and the one it must not.

### `allow_seated_contact`

Set it on any part that starts installed. An insert legitimately touches what it
is installed in, so step 0 measures the design intent rather than the path —
that is `interfere`'s job. With the flag set, the sweep starts at step 1.

## Choosing the direction

A wrong direction reads as a blocked path, so derive the vector from the
assembly geometry and intended motion before reporting a failure. Test the
assembly direction and the capture direction separately.

## What it still does not answer

Thread engagement, snap-fit compliance, elastic deformation, living hinges,
friction retention, and press-fit force. A rigid-body sweep cannot reach them.
Record them as open items rather than implying the gate covered them.
