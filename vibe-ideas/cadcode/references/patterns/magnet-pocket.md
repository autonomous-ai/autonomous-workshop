# magnet-pocket

**Trigger:** load when the user asks for magnets, magnetic closure, magnetic
mount, snap-shut lid, sliding magnet, N42 / N52 disc magnet pocket, or any
"hold it together with magnets" feature.

## Why this exists (the mechanics)

Neodymium disc magnets ship in standard stock sizes given as D x T
(diameter x thickness). The printed pocket is either a slip fit
(clearance, magnet drops in cleanly and is held with a drop of CA glue) or
a press fit (slight interference, friction only). The top wall — the thin
layer of plastic between the magnet face and the outside of the part —
controls remaining hold force: thinner wall is stronger but more fragile.
POLARITY is set by which way you insert the magnet; the design must
dictate which face attracts so two mating parts come together right-side
up, never repel.

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper offsets the
workplane DOWN into the body by `top_wall` so the magnet sits below the
printed surface, then cuts the pocket at the right diameter for the fit:

```python
from cadlib.cutouts import add_magnet_pocket

part = add_magnet_pocket(
    part,
    positions=[(0, 0)],     # pocket centres in the open_face plane
    magnet_size="10x3",     # key into MAGNET_TABLE (D x T)
    fit_type="slip",        # "slip" (clearance, glue) | "press" (interference, friction)
    top_wall=0.4,           # plastic between magnet face and outside (typ 0.4–0.8)
    open_face=">Z",         # open face — must point up at print time (see pitfalls)
)
```

The helper reads magnet stock dimensions from
`cadlib/tables.py::MAGNET_TABLE` — pass `magnet_size=...` with a known key
and let it supply the geometry. It raises `ValueError` for an unknown
`magnet_size` or `fit_type`.

## Hold-force vs top-wall

The rule: each additional mm of plastic between the magnets roughly HALVES
the pull. For a lid closure, **0.4–0.8 mm** is the usable range — strong
enough to feel a snap, thin enough to bridge-print reliably on a 0.4 mm
nozzle (1–2 layers at 0.2 mm layer height).

Rough absolute figures for a 10x3 N52 pair in PLA — measured on one setup,
verify for yours; hold force is highly bridge-quality-dependent (a 0.4 mm
wall printed with poor bridging behaves like an 0.8 mm wall):

- 0.2 mm top wall: ~2.5–3.5 N pull
- 0.4 mm top wall: ~1.8–3.0 N pull
- 0.8 mm top wall: ~1.0–2.0 N pull
- 1.5 mm top wall: ~0.6–1.2 N pull

## Polarity protocol

When you have N pockets on each of two mating parts, the magnets must
attract in the assembled position. Strategies, in order of robustness:

1. **Single pair (simplest)**: only one magnet per part — any
   orientation works, the parts will rotate themselves into alignment.
2. **Multiple pairs**: number or colour-code each pocket. Insert all
   magnets in part A "north up", then all magnets in part B "north
   down". Mark north with a Sharpie dot before insertion.
3. **Anti-rotation 3-magnet pattern**: 3 magnets in a triangle on each
   part. If the user assembles flipped, two of the three pairs repel
   while one attracts — gives clear tactile feedback and physically
   prevents the wrong orientation from latching.
4. **Asymmetric layout**: place pockets at non-symmetric (x, y)
   positions so the parts only mechanically register one way; polarity
   then becomes secondary.

## Pitfalls

- **Forgot top_wall**: with `top_wall=0` the pocket cuts all the way to
  the surface, the magnet sits flush and pops out when bumped or jumps to
  nearby ferrous objects, ripping the pocket open. (The helper always
  offsets by `top_wall`, but `0.4` is the minimum that bridges reliably.)
- **top_wall too thin (<0.3 mm)**: single-layer bridge fails during
  print, pocket opens through to the outside.
- **top_wall too thick (>1.5 mm)**: hold force drops below useful;
  user complains the closure "doesn't really hold."
- **Wrong fit_type**: press fit on a brittle magnet (N52 is glass-hard
  and chips easily) can shatter a corner during insertion. Slip fit
  plus a drop of CA glue is foolproof.
- **Polarity reversed**: parts repel instead of attract. Always mark
  north with a Sharpie before insertion; verify by bringing two
  magnets together loose before gluing.
- **Magnets shatter if dropped on a hard floor** — order 20% spares.
- **Two magnets attract during printing**: if pockets are close
  together, don't insert any until the print is done — an already-seated
  magnet will rip the next one off the bed or jump up into the nozzle.
- **Steel screw near magnet pocket**: magnets grab the screw and hold
  the assembly crooked. Use brass or A2 stainless screws within ~10 mm
  of any pocket.
- **Heating the magnet >80 deg C demagnetises it permanently**: never
  try to "heat seat" magnets with a soldering iron the way you would
  brass inserts. Glue, don't melt.
- **Hole orientation**: pocket cut from `>Z` requires the open face to
  point up at print time too, otherwise the top_wall bridge has to
  print as an overhang and will sag.
- **Bridging trap on the top wall**: the 0.4–0.8 mm wall between the
  magnet and outside is a BRIDGE (~10 mm span for a D10 magnet pocket).
  Print orientation must align infill direction with the bridge OR
  include a small chamfered transition; otherwise the wall sags and
  pull-force drops 30–50%.
