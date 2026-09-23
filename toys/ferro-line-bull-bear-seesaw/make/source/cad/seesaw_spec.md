# Bull Bear Seesaw specification

Original interpretation of user text; no reference image was supplied.
All lengths are mm. X follows the beam, Y points rearward and Z points up.
The viewer looks toward +Y. All profile coordinates in seesaw_lib.py are
[assumed] authored dimensions. User constraints are [observed] from WISH.json;
all fit equations and pose transforms are [inferred] from those dimensions.

## Requirements

A fixed stand and central pivot support an approximately 200 mm [observed] desk seesaw.
A forward-facing charging bull occupies the left end and a bear the right.
Both faces are neutral at level. At 15–20 degrees bull-up only the bull's
smile appears; bear-up only the bear's blue tears appear. All changes use the
tilt relative to the fixed stand. Parts assemble by hand with printed pins
and keys, without glue, bought springs, motors, batteries or electronics.

## Dimension ledger

| Feature | Value | Basis |
|---|---|---|
| beam span/depth | 188 / 10 | assumed desk envelope |
| animal centres | X=-60,+60 | assumed balanced layout |
| animal outer extent | X=-102..98 (200 total) | inferred from silhouettes |
| base | 110 x 70 x 6 | assumed stable footprint, physical stability unverified |
| pivot | world Z=58, X=0 | assumed |
| fixed driver peg | Z=108, diameter8 | assumed |
| endpoint tilt | ±18 degrees | assumed within observed15–20 degree requirement |
| displacement | 50 sin(theta), maximum15.45085 | inferred rigid transform |
| axle pin | diameter8, bore8.8 | assumed0.4 radial clearance |
| animal mounting pin | diameter9, bore9.8 | assumed0.4 radial clearance |
| slider thickness | 3 | assumed FDM section |
| slider front/rear | Y=-9.6/-6.6 | inferred0.4 gaps to skin and backing |
| guide slot width | 8.8 | inferred from8mm peg |
| slot centreline | local Z=46.7..50.3 | inferred covers50cos(theta) |
| pin cross-slot / key | 2.8 / 2.4 | inferred0.2 side clearance |
| rear cover posts | bull8-square at X=-87/-33,Z55; bear6.4-square at X35/85,Z62; sockets0.8 larger | assumed0.4 side clearance |
| nozzle | 0.4 | observed |
| stand/beam stop | contact at±18 degrees | inferred planar line equation |

## Construction and colours

One Tier2 library supplies one printable entry per unique part. Curved profiles
are extruded along Y; animals are hollow-backed relief figures with rounded
heads, horns or round ears, legs and broad beam-seating feet. Their facial
windows expose separate colours. The common shuttle's vertical slot follows
the stand peg; its opposite mask margins produce mutually exclusive expressions.
Rear covers retain the slider axially. A separate black plate backs the bear's
eyes and nose, while the blue cover backs only the tears.

Bull body: cocoa_brown. Common carrier and muzzle: beige. Bear and tear mask: dark_brown.
Mouth backing: dark_brown. Eye plate:black. Tear backing:misty_blue.
Stand, beam, base and separate pins/keys:gray. Values are direct sRGB channels.

## Verification boundary

Component rounds inspect geometry, wall thickness, overhangs and shaded views.
Assembly checks must retain separate occurrences and inspect interference.
Exact-state stills describe the intended expressions and mechanical positions.
Motion sweeps, animations and independent motion review are disabled.
No physical fit, operation, durability or print readiness claim is made.

Final face revision: bull horns spanX=-102..4, Z54..74, Y=-14..-10.
Beige muzzle front ellipse34x22; rear36x24; centre(-49,39). FrontY=-14..-13.2,
taper expands1 mm per side byY=-11.6; rear cap endsY=-10.4. Seat0.4 radial clearance.
StopsX=-64..-61/-37..-34,Z43..46 extend rear toY=-6.6; cover gap0.4.
Bear eye centresZ56.7; rounded eye-connected tearsZ47.1..54.9. Moving maskZ26..55.5.
Black fixed plateX39..59,Z44.8..61.8,Y=-12.4..-10.4 with rear key aboveZ57.2.
Bear face pocket opens upward, preserving1.2mm front skin; running mask clearance0.8.
Bear blue cover bossesR6.4 at ear centres; holes7.2-square. Bull holes8.8-square.
All are assumed design values; printed-fit and physical function remain unverified.
