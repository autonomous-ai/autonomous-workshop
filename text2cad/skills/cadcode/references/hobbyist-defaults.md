# Sourcing dimensions + FDM best-practice defaults

Two parts:

1. **How to source a dimension** — where each number in your model comes from,
   and how to get real-world product specs right.
2. **Generic FDM best-practice values** — the print rules of thumb, stated as
   formulas. These are this skill's calibrated defaults; use them directly.

---

## Part 1 — How to source a dimension

Every number sorts into one of three buckets. Pick the right one; never invent a
spec.

### Real-world dimensions of a named product → web-search

Specific phones, motors, doorbells/cameras, mount standards (VESA, ARCA, GoPro,
1/4-20, GridFinity), connector collars, or a bearing/part you don't recognize:
**web-search the manufacturer or catalog spec**, then:

- **State it as an assumption the user can correct** (e.g. "Assuming iPhone 16 ≈
  147 × 72 × 8 mm — correct me if your model differs").
- **Round for printing** to 0.5 mm; add **4–6 mm** to each dimension if a phone
  case must fit.
- Pull the dimension that actually drives the fit (a cradle cares about
  *depth*; a bearing seat cares about *OD*; a captive-cable opening cares about
  the *connector collar Ø×len*, not the cable jacket).

Do **not** recall these from memory — they drift by model, region, and revision,
and a confident wrong number is the classic failure. If a search can't pin a
specific device, say so and **ask the user** for the dimension rather than guess.

### Hardware a cadlib helper already covers → pass a named size

Screws, nuts, bearings, magnets, and heat-set inserts have dimensions baked into
`cadlib/tables.py`; the helpers (`add_screw_post`, `add_nut_trap`,
`add_bearing_seat`, `add_magnet_pocket`, `add_heat_set_pocket`) read them from a
named size. Pass `bearing="608"` / `screw_size="M3"` and let the helper supply
the geometry — don't transcribe the numbers into your model. For an open-ended
fit a helper takes a raw dimension (e.g. `cable_diameter=…`); that's where a
web-searched value goes.

### Generic print physics → use the rules in Part 2

Tolerances, wall thickness, fits, boss sizing — these are formulas, not lookups.

---

## Part 2 — Generic FDM best-practice values

Assumes a 0.4 mm nozzle on an XY-calibrated printer (PLA/PETG). State the rule;
quote a number only as a worked example.

### Fits & tolerances (per side, added to the hole)

| Fit | Slop | Use |
|---|---|---|
| Press-fit | `+0.2 mm` | tight, stays put, hand-press |
| Hand-assembly / slip | `+0.4 mm` | slides/seats freely by hand |
| Snap / interference | `0.3–0.5 mm` | plastic creep accommodates it |

`cadlib.fits` (`mating_clearance`, `slot_for`, `peg_for`) encodes these — prefer
it for mating parts so one fit class drives both halves.

### Holes for fasteners

- Clearance hole `= nominal + 0.3–0.4 mm` (M3 → 3.4 mm, M4 → 4.5 mm, M5 → 5.5 mm).
- Self-tap into plastic `= major-thread Ø − 0.3 mm`.
- Counterbore Ø `= cap-head Ø + 0.5 mm` (rounded to 0.5 mm).

For the actual screw/nut/insert geometry, prefer the cadlib helper (Part 1) over
hand-cut holes.

### Walls

- Minimum/structural wall `= N × nozzle width`. At 0.4 mm: 1.2 mm decorative
  (3 perimeters), **2.0 mm enclosure** (stiff, no flex), **2.8 mm + ribs**
  load-bearing. See `references/patterns/wall-thickness-rules.md` for the `h³`
  rationale and why a rib beats a thicker wall.

### Press-fit / bearing / magnet pockets

- Bearing seat `= bearing OD − 0.05 mm` (interference press fit). The
  `add_bearing_seat` helper applies this from `BEARING_TABLE`.
- **Slicer XY compensation:** a calibrated printer lands within ±0.05 mm; stock
  i3-class printers run +0.10 to +0.15 mm oversized. If press fits come out
  tight, set the slicer's XY compensation / horizontal expansion to ≈ −0.10 mm.
- **Elephant's foot:** the first 2–3 layers squish wider. For any press-fit,
  bearing, or magnet pocket whose open face is on the build plate, add a
  `~0.4 × 45°` chamfer on that bottom edge so the wider layers don't crush the fit.

### Sanity-scale check

Consumer/handheld objects cluster in roughly **20–200 mm**. If a dimension lands
far outside the part's obvious human scale (a "phone stand" coming out 8 mm tall,
a "vase" 2 m wide), suspect a **unit mistake or a radius-vs-diameter swap**
before trusting the geometry. (cadpy's hard sanity bound is 200 × 200 mm.)
