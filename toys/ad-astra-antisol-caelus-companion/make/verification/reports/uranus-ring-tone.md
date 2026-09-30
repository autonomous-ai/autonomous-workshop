# Uranus's ring tone against `cyan`

The ring prints in `white` #FFFEF7 from this revision, by owner decision.
It printed in `cyan` #00FFFF in the edition before, which was the globe's
own colour. The geometry underneath did not move: this is one body
changing spools. What that costs or buys in contrast is measured here
rather than argued.

One Uranus Sol piece is built once and rendered twice at one camera
with only the ring repainted between the two renders. The pixels that
differ are the ring's own pixels under identical geometry and light.
Luma is Rec. 709 on 0..255.

| | `white` | `cyan` | separation |
|---|---|---|---|
| sealed hex | `#FFFEF7` | `#00FFFF` | 52.9 |
| as rendered | - | - | 53.6 |

## Measured on the piece, frame by frame

| frame | camera | ring pixels | measured separation | reading |
|---|---|---|---|---|
| hero | az -55.0, el 22.0 | 22520 | **38.7** | present without shouting |
| sheet | az -45.0, el 35.3 | 24025 | **39.3** | present without shouting |
| world hero | az -55.0, el 22.0 | 22520 | **38.7** | present without shouting |

## What the number says

Across the three frames the white hoop separates from the cyan globe
by **38.7 to 39.3** of 255 greyscale levels.
For scale, this set has already committed to 9.4 as its narrowest
visible separation, on Saturn's bands, and rejected 21.8 on Mercury
as vanishing on a small ball. The ring is far above both: it is the
loudest single boundary on any globe in the set.

That is the whole of what this measurement can say. Whether a bright
hoop on a bare saturated ball READS as a seam is a question about
recognition, not about contrast, and it is answered by the blind
review in `snap/SIGNATURE-REVIEW.json`, not here. The number belongs
beside that answer, which is why it is measured.
