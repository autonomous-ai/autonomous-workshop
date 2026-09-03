# Motion manifests

Schema and usage for `scripts/check_motion`. Load this when a project
has parts that insert, slide, hinge, latch, or have to stay put.

## What it is for

`validate` says the solid is sound. `interfere` says nothing overlaps once
assembled. Neither says the parts can be *brought* to that pose, and neither
says a connector actually holds. A motion manifest checks both claims.

## Running it

```bash
python "$CAD_SKILL_ROOT/scripts/check_motion" <project-dir> --manifest <file.json>
python "$CAD_SKILL_ROOT/scripts/check_motion" <project-dir> --manifest - < m.json
python "$CAD_SKILL_ROOT/scripts/check_motion" <project-dir> --manifest m.json --list-parts
```

A manifest belongs at `<project-dir>/measure/motion.json` next to the other
verification artifacts. Exit 0 when every condition holds, 1 on any failure and
on any condition that could not run — a manifest naming a part that does not
exist is a broken check, not a clear path. `--allow-inconclusive` relaxes that
for the genuinely unmeasurable, and still prints what it skipped.

Run `python "$CAD_SKILL_ROOT/scripts/check_motion" --self-check` after changing
this gate. Its regression fixture includes a shaft apparently held by a gate
which can itself leave; that manifest must fail until the gate and its key both
have proofs leading to the fixed frame.

Final `verify_project` reads the project's README and spec for documented
assembly procedures. An assembly-scoped `insert`, `seat`, `press`, `slide`,
`screw`, `snap`, `thread`, `lock`, or similar mating action requires this
manifest; merely omitting the file cannot turn a claimed path into a skipped
gate. Part count alone is deliberately not the trigger, because a print plate
or set of independent variants may carry several printable entries and no
assembly claim.

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
| `coupled_motion_collision` | `movers`, `steps`, optional `obstacle_parts` |
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

## Retention must close at a fixed root

A blocked sweep freezes every obstacle. That can produce a false proof: a shaft
looks retained by a journal gate even when the gate itself is free to fall or
walk out. Never use a removable obstacle as a retainer without proving why that
obstacle stays installed under gravity, vibration, and the driven load.

For every multi-part retention chain, add a top-level `retention` declaration:

```json
{
  "retention": {
    "fixed_parts": ["frame"],
    "proofs": [
      {
        "part": "camshaft",
        "condition": "camshaft-retained-by-gates",
        "supports": ["journal_gate:0", "journal_gate:1"]
      },
      {
        "part": "journal_gate:0",
        "condition": "left-gate-retained-by-key",
        "supports": ["gate_key:0"]
      },
      {
        "part": "gate_key:0",
        "condition": "left-key-gravity-seat",
        "supports": ["frame"]
      }
    ]
  }
}
```

Each proof must name a passing condition whose `expect` is `blocked` and whose
`moving_part` is the proof's `part`. `supports` must be obstacles of that
condition; omit it only when every `obstacle_parts` entry is load-bearing. Each
support must either have its own proof or be named in `fixed_parts`. The audit
fails on a missing proof or a dependency cycle.

`fixed_parts` means a genuine assembly root, such as the frame or housing. Do
not put a loose cap, gate, key, screw, magnet, or other conveniently stationary
test obstacle there merely to make the graph pass. If rigid-body motion cannot
prove its retention — threads, a press fit, magnetic force, elastic snap —
record that physical limitation explicitly rather than calling the part fixed.

This declaration is mandatory when a retention claim depends on a removable
part. A stop cut directly into the monolithic frame needs only the blocked
condition; a gate, clip, collar, key, pin, screw, or nested catch needs the
complete dependency chain.

## A machine moves more than one part — `coupled_motion_collision`

The first two checks move ONE part and hold everything else still. For a
mechanism that is the wrong question and it fails in the flattering direction:
hold the follower still and the drive's working stroke reads as a collision, so
the natural repair is to write a smaller sweep that avoids the engagement
entirely — and then every gate passes a machine that has never been through its
own cycle.

`coupled_motion_collision` takes a pose per mover per sample:

```json
{
  "id": "one-full-cycle",
  "check": "coupled_motion_collision",
  "expect": "clear",
  "inputs": {
    "steps": 120,
    "movers": [
      {"part": "driver",
       "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
                    "start_deg": 0, "end_deg": -360}},
      {"part": "follower", "driven": true,
       "rotation": {"axis_point": [50, 0, 0], "axis_direction": [0, 0, 1],
                    "angles_deg": ["...", "steps + 1 absolute angles"]}}
    ],
    "obstacle_parts": ["frame"]
  }
}
```

Each mover takes a `rotation`, a `translation`, or both — rotation first. Either
one may be a `start`/`end` pair, which interpolates, or an explicit table
(`angles_deg`, `offsets_mm`) holding exactly `steps + 1` absolute values
measured from the assembly pose. Use the table for anything whose motion is not
uniform: a Geneva wheel, a cam follower, a crank slider, a four-bar coupler. The
project already solved that kinematics to place the geometry, so the table is
that solution written down, not a second guess at it. Every mover is tested
against every other mover and against the obstacles at every sample.

### The table is a claim, and `driven` is what tests it

A pose table that quietly describes two parts drifting past each other with a
gap between them will sweep perfectly clear. Mark the output side
`"driven": true` and the gate runs the sweep again **once per driven part**,
with that one part frozen at sample 0 and only contacts involving it counted.
Each one must be reached: if the drive completes its stroke without ever
touching it, that part is not being driven, and the condition fails with that
finding rather than a clearance.

Per part, rather than "something collided", because a machine with three
followers on one cam passes the weaker form while driving only one of them.

Together the passes say what a running machine has to satisfy — the parts clear
each other through the whole cycle, and every output is actually in contact with
the drive somewhere in it.

**Start the cycle away from the ends of the driven part's travel.** The frozen
pass asks "if this part stood still, would the drive run into it?", and for a
follower parked at the top of its stroke the honest answer is no — the drive
only ever falls away from it, and the contact that matters is a support, not a
push. A cycle that starts there reports the part as undriven however sound the
mechanism is. Park the assembly mid-stroke; with several outputs, pick a phase
where none of them is at an extreme.

### Name the frame, or the cycle never met it

`obstacle_parts` is optional here and required everywhere else, and the part it
quietly leaves out is the one a mechanism is guaranteed to run into. Six
machines into this repo, four of them had cycle sweeps that tested their movers
only against each other: every one passed, and one of the four was grinding its
lever 0.4 mm into a post through most of its swing.

So a `coupled_motion_collision` whose `inputs` has no `obstacle_parts` key at
all is **inconclusive**, and says which top-level parts it left out:

    ??  index-cycle-runs [coupled_motion_collision] coupled_motion_collision
        left base, pin_driver, pin_wheel out of the sweep entirely: they are
        neither movers nor obstacles, so this cycle was never tested against
        them.

Writing `"obstacle_parts": []` clears it. That is the point: absence is
unexamined, an explicit empty list is a decision on the record. Movers named by
a dotted path cover their top-level ancestor, so a sub-assembly does not have to
be listed twice.

### Sampling has to follow the motion, not the input

Sample count is not a cosmetic setting. A mechanism's output rate is rarely its
input rate — an intermittent drive can turn its output several times faster than
its input at mid-stroke — so a table sampled uniformly in the *driver* angle is
finest where nothing happens and coarsest where the parts actually pass. Choose
`steps` from the fastest part of the output motion, not from the input's.

**A sweep is blind to anything smaller than its own step.** Sample a gear mesh
every third of a tooth and a tooth passing clean through another reads as a
clear path; the gate has stepped over the collision. Every check therefore
reports the furthest any point of a moving part travels between consecutive
samples, as `step N mm` in its detail line, and a condition may declare the size
it has to be able to see:

```json
"thresholds": { "maxOverlapMm3": 0.001, "maxStepMm": 0.35 }
```

When the measured step exceeds that, the condition is **inconclusive** — a check
that did not run, not a path that was found clear — and `check_motion` exits
non-zero on it like any other inconclusive result.

Pick the declared size from the smallest thing the sweep must not miss: a
fraction of a tooth for a mesh, less than a post's diameter for a part swinging
past a post. Writing it down also records *what the condition is for*: a full
turn declared at one tooth is honest about being a bulk-clearance sweep with the
mesh checked separately, and reads as such to whoever comes next.

## Choosing the direction

A wrong direction reads as a blocked path, so derive the vector from the
assembly geometry and intended motion before reporting a failure. Test the
assembly direction and the capture direction separately.

## What it still does not answer

Thread engagement, snap-fit compliance, elastic deformation, living hinges,
friction retention, and press-fit force. A rigid-body sweep cannot reach them.
Record them as open items rather than implying the gate covered them.
