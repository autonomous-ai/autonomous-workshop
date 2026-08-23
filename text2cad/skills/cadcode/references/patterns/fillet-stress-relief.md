# fillet-stress-relief

**Trigger:** load when the user reports a part broke at a corner, asks
about "making it stronger", asks for fillets, mentions stress
concentration, fatigue, or cracking under load.

## Why this exists (the mechanics)

A sharp internal corner concentrates stress: the tighter the radius, the
sharper the stress riser, climbing toward infinity for a perfect knife
edge. The intuition is all you need — smaller radius means a worse stress
peak, and the first bit of radius buys the most relief, with diminishing
returns past r ≈ 0.5 × feature_width. Don't treat this as a calculator;
the point is qualitative. On a brittle FDM part, going from a near-sharp
corner to a modest fillet often means the difference between snapping on
first use and surviving hundreds of load cycles.

## Where fillets matter most (high priority)

1. **Junction of a cantilever to its mount** — boss/clip root. This is
   where every snap-fit, hook, or lever fails first.
2. **L-shaped intersections** where load runs around the corner —
   bracket inside corner, gusset roots.
3. **Holes near edges** — bone-shape relief or just a generous fillet
   around the hole rim, especially on the loaded side.
4. **Where a thin rib meets a thicker panel** — see `rib-stiffener.md`.
5. **Wherever a thread or hole runs out** of a feature — the run-out is
   a crack starter and almost always the failure point under repeated
   tightening.

## Where fillets are wasteful

- Top edges of external faces — purely cosmetic, no strength gain.
- Inside corners of pockets that never see load (e.g. decorative cavities,
  cable channels).
- Every-edge `.edges().fillet(1)` — blows part complexity, slows export,
  fragile to selector breakage on small geometry changes, and often
  triggers OCCT failures on tiny chamfer-adjacent edges.

## Applying the fillets

See `cadquery-modeling.md` for safe filleting (fillet last, always filter
the edge set, r ≤ wall/2). This doc only covers *where* the fillets go;
that doc covers *how* to land them without crashing OCCT.

## Sizing rule

Size the fillet relative to the feature, not from a lookup. For a
high-stress corner where two features meet (h = thinner feature thickness
at that junction):

    r ≈ 0.25–0.5 × h

The lower end already buys most of the relief; past `r ≈ 0.5 × h` returns
diminish quickly (the same diminishing-returns rule from the mechanics
above). Going larger mostly costs material and print time without
meaningfully easing the stress riser. Worked example: a 2 mm-thick wall at
a loaded corner wants `r ≈ 0.5–1.0 mm`. Cap at `r ≤ wall/2` regardless, so
the fillet never eats through the wall.

## Pitfalls

(For the CadQuery failure modes — over-large radius, unfiltered
`.edges()`, filleting after a cut — see `cadquery-modeling.md`. These are
the *mechanical* pitfalls.)

- **Sharp corners are not always wrong** — convex (outward) corners
  barely concentrate stress. Save fillet operations for concave
  (internal) corners where tension actually builds.
- **Print orientation matters**: a filleted internal corner can require
  support. If the fillet is at the root of an overhang, leave it sharp
  on the bottom side or add a 45-degree chamfer instead — chamfers
  print self-supporting and recover most of the stress-relief benefit.
- **Filleted edge across layer lines is still weak**: FDM parts crack
  along the layer interface regardless of fillet. Reorient the part so
  the load runs along filaments, not across them, before tuning radii.
- **Reread your part name**: corner cracks BEHIND the load face are the
  usual failure — the fillet must be on the LOADED (tension) side. A
  fillet on the compression face wastes material and does nothing.
