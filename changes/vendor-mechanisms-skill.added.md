- Vendor and lock the upstream `mechanisms` skill from
  `autonomous-ai/autonomous-product-to-cad` `cf81f51`: a reference-only
  knowledge base for joints and working mechanisms (fits and joint forms,
  gears, linkages, cams and intermittent drives, energy sources, automaton
  layouts, how to verify a mechanism, and a catalogue of mechanism faults),
  with each feasibility condition written as an `assert` to copy into a
  parameter block. It has no script and no gate. It joins
  `PRODUCT_RUN_DOMAIN_SKILLS`, so it is materialized into every product run,
  its name is reserved against Inventor extension collisions, and the Make
  instructions point at it for anything that turns, slides, swings, indexes or
  latches. The other vendored trees stay pinned at `facbc58`.
- **Materialized instruction bytes changed**: one more skill is materialized
  and the product-run Make reference names it, so a run parked before this
  change must be restarted rather than resumed.
