# Independent Luma Vale Make audit — sealed rotor contradiction

An independent native-agent review inspected the sealed Moonwake Garden
concept without editing it. The review found that four simultaneous Invent
requirements cannot all be represented by one conforming rotor:

1. The rotor diameter is 68.0 mm, so its outer radius is 34.0 mm.
2. The only optical opening is a 110-degree annular sector centered on local
   +Y, hence spanning local angles 35 to 145 degrees, with outer radius
   31.5 mm.
3. One registered detent notch is at local +75 degrees and has 0.55 mm radial
   depth.
4. The sealed minimum rotor outer web is 2.5 mm.

The +75-degree notch lies inside the sector span. Its root is therefore at
radius `34.0 - 0.55 = 33.45 mm`, leaving only
`33.45 - 31.5 = 1.95 mm` between notch root and optical opening. This misses
the 2.50 mm sealed minimum by 0.55 mm.

The other notch placements are not arbitrary: the fixed tooth at world -45
degrees aligns the local -45, +75, and +195-degree notches at rotor poses 0,
-120, and -240 degrees. Relocating a notch or tooth changes the sealed detent
geometry. Indenting the optical sector near +75 changes the sealed annular
sector. Reducing notch depth or the minimum web likewise changes sealed Invent
authority. This is therefore not an ordinary CAD repair.

Invent must explicitly reconcile these dimensions and then re-evaluate all
three indexed optical states. A viable revised concept may relocate the detent
system outside the optical window, locally reshape and re-authorize the window,
or change the notch/minimum dimensions, but Make cannot silently choose among
those concept-level tradeoffs.

The audit also noted secondary checks for the revised concept: measure the
rear-chamfer aperture ligament, perform exact 5/6/7 state booleans and a
one-degree sweep, evaluate ±20-degree rays and thumb-bay leakage, and keep all
snap, flexure, print, optical-brightness, and human-response claims physically
unverified until Playtest.
