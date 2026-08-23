# heat-set-insert-pocket

**Trigger:** load when the user asks for heat-set inserts, brass inserts,
threaded inserts, McMaster/Ruthex/Voron inserts, or any "screw that goes
into plastic many times without stripping".

## Why this exists (the mechanics)

A knurled brass insert heated with a soldering iron (~240 C for PLA — see
Pitfalls for the per-material range) locally melts
the plastic around its knurls; the plastic reflows into the knurl pattern
and solidifies, locking the insert mechanically and giving you real
machine-threaded engagement in a 3D-printed part. Pull-out strength is
roughly 5-10x a self-tap into PLA, and you can re-torque a screw hundreds
of times without stripping. The pocket is a plain cylinder slightly deeper
than the insert (so it can sit flush) with a small wider relief at the rim
to catch displaced plastic. Critically, the pocket diameter is the insert's
*body* diameter (between the knurls), NOT the maximum knurl OD — the
knurls themselves must bite into solid plastic.

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper cuts the
body-diameter pocket plus the rim relief (the wider, shallow counterbore that
catches the plastic the iron pushes upward) in one call:

```python
from cadlib.mounting import add_heat_set_pocket

part = add_heat_set_pocket(
    part,
    positions=[(0, 0)],       # pocket centres in the open_face plane
    insert_size="M3",         # key into HEATSET_TABLE
    bottom_clearance=1.5,     # extra depth past the insert length (typ 1-2 mm)
    open_face=">Z",           # face the iron enters from
)
```

Insert dimensions (`pocket_d` body Ø, `insert_len`, plus the `relief_d` ×
`relief_h` rim relief) are owned by `cadlib/tables.py::HEATSET_TABLE` and keyed
by `insert_size`; the helper reads them for you. `Read` that file if you need the
raw numbers — don't transcribe them. The helper raises `ValueError` for an
unknown `insert_size`.

The rim relief that older notes called "mandatory" is **now cut by the
helper** — you no longer have to add it yourself. It pulls `relief_d` /
`relief_h` straight from the table, so displaced plastic has somewhere to go
and screw heads sit flat.

## Boss sizing around the pocket

The rule is `boss OD = pocket_d + 2 x wall`, with `wall >= 2.5 mm` (>= 3 mm for
PLA — bare 2 mm walls split in practice on PLA). Pull `pocket_d` from the helper
rather than hand-listing it: an M3 insert (pocket_d ~4 mm) lands at
`OD >= 4 + 5 = 9 mm`.

Less wall and the boss splits when the iron pushes the insert in (the
softened plastic has nowhere to go and pressure cracks the cold ring around
it). For bosses near a part edge, add wall on the thin side or chamfer
the corner so the crack path is longer.

## Pitfalls

- Pocket Ø ≠ knurl Ø. The pocket is the insert *body* diameter (between the
  knurls); the knurls must bite INTO solid plastic. Use the max-knurl Ø by
  mistake and the insert won't go in straight, ends up tilted, threads cock
  relative to the screw axis. (The table's `pocket_d` is already the body Ø.)
- Pocket Ø too loose: insert spins under torque, no thread engagement,
  whole part is scrap.
- Pocket too shallow: insert sits proud of the surface, the mating lid
  won't close flat and clamps on the brass instead of the plastic.
- Wall too thin around the boss: boss splits visibly when the insert is
  pressed in — usually a vertical crack along a layer line.
- Top face print quality matters: the insert seats on the top layer, and
  if it's rough or stringy the insert tilts. Use 5+ top layers and turn
  on ironing if your slicer supports it.
- Iron temperature by material: typical starting temps are 220-240 C for PLA,
  260-280 C for PETG, 300-320 C for ABS / PC — verify against the
  filament/insert datasheet rather than treating these as authoritative. Too
  high and you melt a halo around the insert so it sinks too deep or droops
  sideways. ABS / PC actually hold heat-sets better — the higher glass
  transition gives a stronger reflowed bond.
- Don't put a heat-set insert in TPU or other flexible filament — there
  is no rigid plastic for the knurls to bite into, the insert just sinks
  and wallows.
- Insert installed crooked: don't try to correct it once cold. Reheat
  with the iron on top of the insert, let it sink, re-seat with a flat
  surface (back of a caliper) pressing straight down.
- Don't put pockets on a face that prints against the build plate unless
  you flip the part — set `open_face` so the open end of the pocket is on a
  top face for the iron to reach it cleanly.
