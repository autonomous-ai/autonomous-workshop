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

With `--json`, stdout contains only the completed result document. Flushed
stderr progress identifies assembly loading, the active condition, sweep or
drive-evidence phase, and sampled step. Sample updates are throttled to one
per 30 seconds within a phase and capped at 32 per condition; phase changes
may report earlier. Condition start and completion remain visible. These
messages help locate long-running work in a preserved timeout log. They are
diagnostics only: incomplete output or a timeout cannot establish a passing
condition or replace the final JSON evidence.

A manifest belongs at `<project-dir>/measure/motion.json` next to the other
verification artifacts. Exit 0 when every condition holds, 1 on any failure and
on any condition that could not run — a manifest naming a part that does not
exist is a broken check, not a clear path. `--allow-inconclusive` relaxes that
for the genuinely unmeasurable, and still prints what it skipped.

A Boolean failure, missing solid, invalid result or nonfinite measurement is
**inconclusive**, not a clear path or a retention proof. The checker measures
material unions for grouped parts, so overlapping children are counted once,
and compares intersection volume with the volume implied by the union within
a band of at least 0.000001 mm3 that scales with the operand volumes (0.00001
of their sum), because the kernel integrates volume to a relative precision.
When the union disagrees or is unavailable, both differences must confirm the
intersection instead; failing that, every formulation must still give the same
verdict against the condition's collision threshold. A mismatch still makes
the condition inconclusive. These
operations share the same CAD kernel; agreement does not certify arbitrary
geometry or the motion between samples. The default exit status remains
nonzero for inconclusive conditions.

Within one condition, successful material unions may be reused only for the
same exact topology, location and orientation. The cache holds at most 32 placed
shapes and never reuses an error or substitutes another pose's union. This
reduces repeated work without changing the declared samples or proof rules.

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

The audit repeats the named linear or rotation escape sweep for **each
connected material solid**, using only the declared supports. A collision of
one member cannot retain another disconnected member. Members may meet their
supports at different samples. Overlapping primitives are normalized as
material; an enclosed cavity with several shells is still one solid.

`memberEvidence` records each member's bounds, volume, sampled result and
blocking obstacle. The original translation or rotation, thresholds, sample
count and seated-contact policy remain in force. Unavailable geometry or an
inconsistent Boolean is inconclusive. A proxy path cannot stand in for a
material member's escape sweep.

A plain blocked condition still answers whether the prescribed rigid group
hits an obstacle. Add a `retention` declaration when claiming that every
member of a disconnected group is held, including when its supports are fixed.
Passing this audit establishes only the declared sampled escape constraints;
it does not establish arbitrary-direction restraint, fastening, load capacity,
friction or physical operation. Existing runs retain their frozen tool bytes.

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

Each mover takes a `rotation`, a `translation`, or both — rotation first.
Rotation uses its `axis_point` and `axis_direction` with scalar `start_deg` and
`end_deg`, or an `angles_deg` table. Translation uses a `vector` in millimetres
with scalar `start` and `end` multipliers (defaults 0 and 1), or an `offsets_mm`
table. For example, this mover starts 80 mm behind its assembly pose and ends
at that pose:

```json
{"part": "shuttle",
 "translation": {"vector": [80, 0, 0], "start": -1, "end": 0}}
```

At each sample the offset is `vector * (start + (end - start) * i / steps)`.
`start` and `end` are numbers, not `[x, y, z]` points; omitting `vector` while
supplying start/end points is invalid. For a two-step motion, the equivalent
explicit translation is `{"offsets_mm": [[-80, 0, 0], [-40, 0, 0], [0, 0, 0]]}`.
Both table forms must contain exactly `steps + 1` absolute angles or offsets
relative to the original assembly pose, not incremental per-step changes.

Use the table for anything whose motion is not uniform: a Geneva wheel, a cam
follower, a crank slider, a four-bar coupler. The project already solved that
kinematics to place the geometry, so the table is that solution written down,
not a second guess at it. Every mover is tested against every other mover and
against the obstacles at every sample.

### The table proposes motion; contact evidence has a narrower scope

Mark each output mover with `"driven": true`. Movers without that flag are
the declared inputs. Select each assembly occurrence only once among movers:
repeating a name, using two aliases for the same node, or selecting both a
group and its descendant is inconclusive. Distinct assembly occurrences remain
independent selections even when they use the same part design.

The gate requires every output to be reachable from an
input through directed contact edges. For each edge from a parent to an output,
the exact same pair needs both:

- A collision above `maxOverlapMm3` when the output is frozen at sample 0 and
  the parent follows its declared poses.
- Surface contact in at least one checked **nominal** pose, with both parts at
  their declared positions. The numerical distance tolerance is 0.000001 mm;
  it is not a configurable operating clearance.

Static obstacles cannot supply drive edges. Outputs touching each other in an
island disconnected from every input fail. Two parts moving together across a
constant gap also fail, even if freezing one makes the other run into it.
Every declared output needs its own path; one reached follower is insufficient.

The result separates `clear`, the sampled collision answer, from
`driveContactEvidencePassed`. Required contact evidence that is missing fails
the condition even with `"expect": "blocked"`. `driveEvidence` records the
declared inputs, directed edges, frozen and nominal witness samples, and
unreached outputs. The result does not expose a `transmits` claim.

**Passing proves only necessary sampled geometric evidence.** A single nominal
contact can satisfy an edge; it does not prove sustained engagement, the
prescribed ratio or phase, force transmission, friction, or physical operation.
Clearance is checked at the declared samples, not at every intervening pose.
Construction and mechanism-specific verification must establish those remaining
requirements; an animation or this report alone cannot establish a working toy.

**Start the cycle away from the ends of the driven part's travel.** Freezing a
follower at its maximum excursion may prevent any parent from intersecting it,
even in a working mechanism. Choose a phase where the intended drive can reach
each frozen follower. With `allow_seated_contact`, sample 0 is omitted from
both nominal collision and nominal contact witnesses.

These output semantics apply to newly materialized tools. Existing runs retain
their frozen tool bytes.

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
