# Blindcap: Duel — CAD handoff

All dimensions are millimetres. The exact two-player kit is 2 tiles, 12
stools, 6 crowns, 6 owner-marked probes, and 2 personal troughs: 28 pieces.

## Production geometry

- Loam tile: nominal 132 × 132 × 28; 144 × 144 × 30 overall including
  dovetails and socket collars. Print two.
- Stool: 34 × 34 × 49. Each player receives 2 Deadhead, 2 Bracket, 1
  Inkcap, and 1 Hollow. P1/P2 cap bites are real cuts and all eight public
  stool families have distinct owner geometry. A 12mm conical support grows
  from the 12mm neck to the full cap, while a D-profile 4mm shoulder continues
  the shank key without an unsupported rear crescent. The canonical upright
  raw STL slices without floating-region/cantilever warnings; gills overlap
  the neck by 0.5mm.
- Crown: 24 × 24 × 6, with 0.8 diametral clearance on the 16mm boss.
- Probe: 34 long with a 4mm-across-flats hex shaft, 6.8mm channel, blunt
  0.9mm-radius tip, and one/two 1.6mm through-holes for owner identity.
- Keyed reader: 21.4mm D-shank in a 21.8mm D-bore. Shank/bore flats are
  y=-6.0/-6.2, giving 0.2 radial and 0.2 keyed-face nominal clearance.
  The 28mm collar retains 3.1mm radial material around the bore.
- A/B paths are strictly parallel and never cross. Both run southwest inward
  / northeast outward at 70° from vertical. Mouth centres are
  A=(6.363961,15.273506) and B=(15.273506,6.363961), 12.6 apart. The paths
  are 31mm blind channels with 16mm sloped head-withdrawal relief. One raised
  2mm dot identifies A; two identify B.
- The shank retains 5.8mm between channels and 1.0mm at the thinnest outer
  wall. The two 11.8mm knurled heads retain a 0.8mm same-socket gap.
- Trough: 154 × 150 × 40, with six 3mm-deep cradles and three 5mm-deep
  crown pockets; the pockets retain a 1mm floor. Both bed axes are ≤160mm.

## Reference poses and exact reader evidence

- Seated stool origin: z=8. Seated crown origin: z=54.
- Blocked onset is symmetric for A/B: 27.632812 proud is clear and
  27.625 proud has positive solid overlap. The reference high pose is their
  midpoint, 27.628906 proud.
- The admitted hard stop is 3.0 proud. 3.1 clears; 2.9 collides with the tile
  by 3.683604mm³ for both paths.
- All four species truth-table rows pass exact solid intersections. Every P1/P2
  combination of simultaneous A+B admitted probes has 0mm³ overlap.
- A full extraction sweep from each legal low/high state to 34mm proud for
  both blocked paths and all four admitted paths has 0mm³ maximum overlap
  against tile and matching stool.
- The four-neighbour sweep checks both paths from 3mm proud through complete
  extraction against every adjacent stool and admitted A/B pin; maximum
  overlap is 0mm³.
- Conservative alignment proof combines the full 0.2mm radial translation,
  1.303593° D-key rotation, and 1.145763° bore tilt in 64 poses per admitted
  route. All four routes remain at 0mm³ overlap. The analytic worst-case axis
  error is 0.789304mm against 1.090599mm radial probe-channel clearance, a
  0.301295mm digital margin.

## Validation and remaining risk

Every unique manufacturing B-rep must export valid, and every individual STL
must be watertight, consistently wound, and a single connected body. The
assembled STL/STEP is a viewer scene, not a one-piece manufacturing mesh.
`motion.json` declares six exact placed-pin occurrences and withdraws each from
its actual staged pose to 34mm proud. Admitted pins use vector
[20.598354,20.598354,10.602624] in 31 steps; high pins use
[4.233356,4.233356,2.179042] in 7 steps.

Harvest is an explicit two-step motion: record the four probe metrics, then
fully withdraw every pin to 34mm proud before lifting any stool. Inverted
cap-down reveal pieces fit within the 44mm socket pitch (34mm cap), stand on a
flat 16mm boss, and a removed crown can rest on the upward 21.4mm shank tip.

Physical fit is **not verified**. The 0.2mm radial/flat keyed fit is a nominal
digital allowance below a generic drop-fit recommendation and may bind on an
uncalibrated printer. Print the socket/stool/probe and dovetail coupons on the
production printer before making any fit claim. The player-facing trough panel
remains flat (approximately 140 × 26 usable) for a separate scoring insert.
