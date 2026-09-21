# Nothing on Neptune stands proud of its globe

Neptune's globe is a sphere of radius 10.945 mm centred 13.945 mm above
the disc's bed face. Every marking on it is a flush colour inlay:
`parts/world.py` SPLITS the ball rather than adding to it, so a
marking body's outer face is the ball's own sphere. Below is the
greatest distance any point of each body reaches from that centre,
measured on the exact solids at a 0.002 mm chord tolerance.

One body is expected to reach past the sphere and does: the `globe`
body is the ball PLUS the seat cone it stands on, which springs from
latitude -42.0 and spreads outward at 12.0 degrees from vertical down
to the disc face. That collar is original geometry, shared by all
sixteen worlds, untouched by this revision, and it is what stops a
sphere resting tangentially on a flat disc from leaving an
unsupported cap underneath it. It is listed and excluded from the
verdict; the verdict is about the MARKINGS.

| army | body | filament | furthest point from globe centre mm | globe radius mm | proud by mm | |
|---|---|---|---:|---:|---:|---|
| Sol | `globe` | `blue` | 12.324588 | 10.945000 | +1.379588 | the seat cone, by design |
| Sol | `spot` | `dark_gray` | 10.945000 | 10.945000 | +0.000000 | flush |
| Sol | `streaks` | `white` | 10.945000 | 10.945000 | +0.000000 | flush |
| Anti-Sol | `globe` | `blue` | 12.324588 | 10.945000 | +1.379588 | the seat cone, by design |
| Anti-Sol | `spot` | `dark_gray` | 10.945000 | 10.945000 | +0.000000 | flush |
| Anti-Sol | `streaks` | `white` | 10.945000 | 10.945000 | +0.000000 | flush |

The greatest any MARKING reaches past the globe's own surface is
**+0.000000 mm** -- the two markings touch the sphere exactly and
neither crosses it.

Nothing is proud of the sphere, on either army, to within a
millionth of a millimetre. The globe's outer surface is an exact
sphere and the markings are parts of it, so **nothing protrudes and
no marking adds a downward-facing surface** -- there is no new
surface at all, only a different filament through the outer
1.20 mm of the same ball.

## The dark spot is not a faceted polygon either

The spot is walked at 40 even bearings about its own centre. The
furthest any of its 40 chords falls inside the true ellipse is
**0.1597 degrees of arc, 0.0305 mm** -- 8 per cent of one nozzle
width, on a marking 5.35 mm across. There is no facet on this ring
that a printer could lay down, let alone one an eye could find.

Looked at directly rather than argued about: the same frame the
reader read, magnified four times about the spot, shows a
continuous smooth ellipse whose only stepping is the single-pixel
staircase that `render_review` puts on EVERY boundary in the
image, the white wisps included, because it does not antialias.
At 1:1 on a Ø21.89 mm globe the spot is about 130 pixels across, so
that staircase is one pixel in forty of its width -- which is what
a reader is describing as a corner.

## Why a reader sees otherwise

Reported blind, from the rendered frames: the markings "are solid
raised lenses that break the ball's silhouette", with "thin
overhanging slivers" and "unsupported knife-edged lips over the
puck". The measurement above says the geometry does not do that, so
what the reader is seeing is the renderer. A marking that reaches
the limb IS on the silhouette -- it is the sphere there -- and
`render_review` shades flat, with no shadow and no ground plane, so
a near-white body against the pale background at the outline has no
cue that says it is coplanar with the blue beside it rather than in
front of it. The same flat shading is why several markings read
mid-grey on one side of the ball and pure white on the other. That
limitation is recorded for the whole set rather than for this world,
and it is a property of the review renderer, not of the solid the
shop receives.
