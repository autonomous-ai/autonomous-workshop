- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `7e03fc2`. Only the wiki moved upstream. It gains twelve researched joint
  pages (ball-and-socket and posable-figure joints, rod ends and clevises,
  hinge types, shaft-hub connections, rolling-contact joints, swivels and
  turntables, telescoping tubes, scissor linkages, bayonets, push-in clips and
  pins, interlocking joinery) and a joint-variant index that maps each variant
  to its section. It also covers segmenting an axle longer than the bed at its
  pivots, with each pin printed lying on a D-flat deep enough to pass
  `check_overhang`; the wiki now has 193 pages.
- **Wiki search reads a typed phrase as one term.** If a synonym member is
  typed inside a longer member, only the longer member's group is called, and
  stop words stay out of concept tokens. "split pin" no longer ranks parting
  lines first.
- **Materialized instruction bytes changed**: the `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed.
