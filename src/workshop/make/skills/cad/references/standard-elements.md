# Standard elements — `bd_warehouse` and `py_gearworks`

A screw, a nut, a washer, a deep-groove ball bearing, a snap ring, an o-ring, a
shaft key and an involute spur gear all have one thing in common: **nobody in
this repository is entitled to invent their dimensions.** They are published —
ISO 4762, ISO 4032, ISO 7089, ISO 3601, DIN 471/472, DIN 6885-1, and the metric
boundary-dimension tables every bearing supplier builds to — and a number typed
from memory into a generator is a number no gate can check.

`bd_warehouse` ships those tables and builds the element from them in
build123d; `py_gearworks` generates the gear geometry `bd_warehouse` does not.
`requirements.txt` installs both, so they are always present and always
reachable: unlike a network catalog, an empty answer from them is a **real
miss** rather than an inconclusive one.

## Which of the three sources owns a part

Step 4 of `SKILL.md` stops you before authoring a standard element. It has
three possible answers and they are not interchangeable:

| the part is | source | how it enters the project | gate |
|---|---|---|---|
| a **vendor's** product — servo, gearmotor, board, connector, a specific SKU | `$step-parts` | its STEP under `<project>/ref/`, seat via `cadmount` | `check_mount`, with the file's `sha256` |
| a **standard's** element — fastener, bearing, ring, o-ring, key, gear | `bd_warehouse` | build123d source, no file | the ordinary geometry gates |
| **neither** | your own geometry | source, with the miss recorded in the brief | the ordinary geometry gates |

The split is about where the dimensions live, not about whether you buy the
part. You buy a ball bearing, but its bore, OD and width **are** its published
boundary dimensions, so a seat derived from the table fits every conforming
bearing and a vendor file adds nothing to it. You also buy an SG90, and nothing but that vendor's own
file says where its mounting ears are.

Two consequences worth stating plainly:

- A `bd_warehouse` element is **not a foreign STEP**. It is generated from
  source like everything else, so it needs no `ref/` file, no mount row and no
  checksum, and `check_mount`'s provenance rules do not apply to it. That is
  the cheapest correct answer available for a standard part.
- It is still not the part in your hand. The table is the standard's, and a
  supplier who deviates from the standard deviates from this model too.

## Ask before you author

`scripts/stdpart` reads the installed libraries, so its answer cannot go stale:

```bash
python "$CAD_SKILL_ROOT/scripts/stdpart"                          # every family, one line each
python "$CAD_SKILL_ROOT/scripts/stdpart" find M3                  # who carries an M3 size
python "$CAD_SKILL_ROOT/scripts/stdpart" find bearing
python "$CAD_SKILL_ROOT/scripts/stdpart" sizes SocketHeadCapScrew --standard iso4762
python "$CAD_SKILL_ROOT/scripts/stdpart" --self-check
```

`find` matches a whole `-`-separated field of a size designation, so `M3` does
not drag in `M30`, and falls back to a substring when nothing matches exactly.
An empty result is the licence to author the geometry yourself — record it in
the brief's component table exactly as a catalog miss is recorded.

What is there, in one line: every common metric screw head and nut form,
four washer standards plus lock washers, heat-set inserts in five vendors'
tables, five bearing families, external and internal snap rings, ISO 3601
o-rings, DIN 6885-1 parallel keys, ISO metric / Acme / trapezoidal / bottle
threads, roller-chain sprockets, ASME pipe and flanges, the OpenBuilds V-slot
extrusion range with its wheels and stepper motors — and, from `py_gearworks`,
spur, helical, herringbone, bevel, cycloid, internal-ring and rack gears plus
planetary sets.

## The mate derives from the element

This is the reason to reach for it rather than for a diameter you remember.
`references/parameters.md` forbids sizing both halves of a mate independently;
these classes make the female half a function of the male object:

| you have | you cut | with |
|---|---|---|
| a screw or nut | its clearance hole, counterbore and countersink | `ClearanceHole(fastener, fit=...)` |
| a screw | the hole you tap into | `TapHole(fastener, material=...)` |
| a screw | a modelled or simple threaded hole | `ThreadedHole(fastener, ...)` |
| a `HeatSetNut` | the insert pocket | `InsertHole(fastener, manufacturing_compensation=...)` |
| a bearing | its press-fit bore | `PressFitHole(bearing, interference=..., fit=...)` |
| a snap ring | its groove | `RetainingRingGroove(ring)` |
| a `ShaftKey` | the shaft slot or the hub slot | `Keyway(key, keyway_type="shaft"\|"hub")` |

```python
from build123d import *
from bd_warehouse.fastener import ClearanceHole, SocketHeadCapScrew

screw = SocketHeadCapScrew("M3-0.5", 16, mode=Mode.PRIVATE)   # see rule 1

with BuildPart() as bracket:
    Box(PLATE_L, PLATE_W, PLATE_T)
    with Locations(*MOUNT_HOLES):
        ClearanceHole(screw, fit="Normal", counter_sunk=False)
```

The element then tells you where it goes, so the assembly does not retype a
coordinate either:

- **`fastener.hole_locations`** accumulates every location a hole was cut at,
  in the order they were cut — that list places the screws in the combined
  entry.
- **Joints.** A screw carries `joints["a"]` at its **under-head bearing face**
  (its body runs in −Z from there); a nut, a washer and a bearing carry `"a"`
  and `"b"` at their two faces. Connect them the way
  `references/positioning.md` connects any other joint, instead of composing a
  `Location` by hand.
- **A gear reports `pitch_radius`, `base_radius` and `root_radius`**, so the
  centre distance of a mesh is `g1.pitch_radius + g2.pitch_radius` — derived
  from the pair, which is what `skills/wiki/pages/mechanisms/gears.md` requires
  and what a typed centre distance can never be.

## Four rules that keep it inside this repository's gates

**1. `mode=Mode.PRIVATE` on every element you are not adding to the part.**
These classes are build123d `BasePartObject`s, so inside a `BuildPart` they
default to `Mode.ADD` and **fuse into the part being built** — a plate that
quietly grows a screw, still one solid, still valid, still printable. Nothing
downstream reports it. Build components outside the builder, or pass
`mode=Mode.PRIVATE`.

**2. Keep `simple=True`, which is the default on every fastener.** It builds
the body without modelling the thread. `simple=False` models it, and a modelled
thread breaks two mandatory gates at once, by construction rather than by
accident: the fastener becomes a compound of a `body` and a `thread` child that
**overlap on purpose** so the union takes. On a prismatic fixture — a plate, a
screw, a nut, a bearing and a gear — swapping the two fasteners to modelled
threads measured:

| | simple (default) | modelled threads |
|---|---|---|
| `gen` (warm, 2 entries) | 3.5 s | 18.8 s |
| `inspect validate` | 2.1 s, `ok` | 42.6 s, **`selfIntersecting`** on each thread |
| `inspect interfere` | 1.1 s, 0 clashes | 13.5 s, each fastener **clashes with its own thread** |
| written `.step` | 0.85 MB | 2.77 MB |

A thread you genuinely need on a printed part is a different move: build it
standalone and **fuse** it (`core + IsoThread(...)`), which validates as one
solid — and costs 35 s of `validate` for one M6×14 stud.

**3. One solid per printable entry; fuse or label everything else.** A raw
element is often many solids: a modelled-thread M3 cap screw is 34, a modelled
nut 7, an `IsoThread` 13, and a ball bearing 14 — a labelled compound of
`OuterRace`, `InnerRace` and one `Roller` per ball, which is correct and which
`check_mesh` will read as 14 separate shells if you return it from a
`PRINTABLE` entry. In an assembly they are fine (they validate, and the balls
sit tangent to the races without clashing), but they inflate the occurrence
count, and `interfere` pairs grow with its square.

**4. `bd_warehouse` fits are the standard's; FDM allowances are `cadfits`'.**
`ClearanceHole`'s `Close`/`Normal`/`Loose` are ISO 273 clearances for a
machined hole — for M3 they are 3.2/3.4/3.6 mm, which is where `SKILL.md`'s
default table comes from. They say nothing about a hole that is printed rather
than drilled, so prefer `Loose` when the hole comes off a nozzle, and keep
`scripts/cadfits.py` for every printed-to-printed mate. The two do not
overlap: `cadfits` owns tab/slot, peg/socket and print-in-place gaps;
`bd_warehouse` owns standard-element-to-part.

## Gears: two libraries, and which one

`bd_warehouse` builds a lone spur gear as a plain build123d object;
`py_gearworks` builds every other type and a meshed pair, taking angles in
radians and building through `gear.build_part()`. Two rules are enforced by
`stdpart --self-check`:

- **Thin the teeth in the constructor and omit `mesh_to`'s `backlash`.**
  `mesh_to(backlash=0.0)` is not the default: it closes the centres onto
  already-thinned teeth and the pair clashes in `interfere`.
- **`import py_gearworks as pgw`, never `*`**: its `IN` is a direction
  vector, build123d's is the inch.

The library comparison, the `mesh_to` example, the measured backlash table,
build cost and print-gate results per gear type are in
`skills/wiki/pages/modeling/element-libraries.md` (`wiki show element-libraries`);
module, backlash magnitude and body under the teeth are `wiki show gears`.

## Libraries that do not apply here

`cq-electronics`, `cq_gears`, `cq-kit`, `cadquery-plugins` and `cadquery`
itself are unreachable or pointless in this build123d toolchain (pinned
`cadquery-ocp` 7.9); why each one is out is
`wiki show element-libraries#cadquery-libraries-that-do-not-apply`. A
CadQuery-only part is a recorded miss plus a `$step-parts` search, not a
second kernel.

## What it does not answer

- **Whether the element prints.** It usually is not meant to — a bought screw
  is bought. When the element *is* the printed part, gate it like any other:
  an M6×1 ISO thread fails `check_thickness` at a 0.4 mm nozzle (32.6 % of its
  surface under the 0.8 mm minimum, thinnest 0.13 mm — the crest), and a bevel
  gear fails overhang and thickness printed axis-up, while spur and helical
  gears pass all three.
- **Whether the mesh runs.** `skills/wiki` (`wiki show gears`) owns module choice, backlash
  magnitude, undercut, the body under the teeth and the feasibility assert. A
  generated involute is not a printable tooth. Worm, hypoid and face gears are
  in neither library: `py_gearworks` lists them as unsupported, so a worm drive
  is a `$step-parts` search and then geometry you author.
- **Whether the fastener is right for the joint.** Length, grip, thread
  engagement, insert pull-out and preload are design decisions; the library
  builds whatever size you name.
- **Whether a supplier's part matches the standard.** Hobby-grade hardware
  deviates. When the fit is critical and a vendor file exists, that file plus
  `check_mount` is still the stronger claim.

Self-check — run it after upgrading either library, because it asserts the
behaviours above and fails when one of them changes:

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/stdpart" --self-check
