# Neptune's tones, and whether the new cloud reads as bright

One piece built once, rendered twice per question at one camera,
with a single region repainted between the two renders and nothing
else altered. Every pixel that moves belongs to that region, under
identical geometry and identical light. Mean absolute Rec. 709 luma
difference over those pixels, on 0..255.

Both armies, because the lean is most of the story here: the two
markings in question are SOUTHERN, the Sol piece leans its north
pole toward the lens, and `render_review` lights from above.

## The Sol piece

| question | frame | pixels | mean luma apart | least | most |
|---|---|---:|---:|---:|---:|
| companion against the globe | `hero` | 329 | **51.6** | 51.5 | 51.7 |
| companion against the globe | `sheet` | 118 | **47.5** | 46.8 | 47.7 |
| companion against the globe | `spot` | 630 | **57.4** | 56.7 | 57.9 |
| companion against the spot's filament | `hero` | 329 | **31.2** | 30.7 | 31.6 |
| companion against the spot's filament | `sheet` | 118 | **28.6** | 27.9 | 28.9 |
| companion against the spot's filament | `spot` | 630 | **34.5** | 33.9 | 34.9 |
| spot against the globe | `hero` | 3024 | **22.8** | 20.2 | 26.5 |
| spot against the globe | `sheet` | 1641 | **21.4** | 19.0 | 24.8 |
| spot against the globe | `spot` | 4779 | **24.8** | 22.9 | 28.1 |
| bands against the globe | `hero` | 17238 | **105.8** | 45.2 | 132.1 |
| bands against the globe | `sheet` | 16659 | **104.4** | 45.2 | 132.1 |
| bands against the globe | `spot` | 17814 | **100.7** | 45.2 | 132.1 |

## The Anti-Sol piece

| question | frame | pixels | mean luma apart | least | most |
|---|---|---:|---:|---:|---:|
| companion against the globe | `hero` | 631 | **86.2** | 82.1 | 90.4 |
| companion against the globe | `sheet` | 502 | **83.7** | 79.2 | 87.9 |
| companion against the globe | `spot` | 680 | **87.2** | 83.4 | 90.6 |
| companion against the spot's filament | `hero` | 631 | **51.8** | 49.6 | 54.6 |
| companion against the spot's filament | `sheet` | 502 | **50.3** | 47.8 | 52.6 |
| companion against the spot's filament | `spot` | 680 | **52.5** | 49.9 | 54.6 |
| spot against the globe | `hero` | 4765 | **39.0** | 31.6 | 43.7 |
| spot against the globe | `sheet` | 3894 | **38.1** | 30.7 | 43.1 |
| spot against the globe | `spot` | 5008 | **39.1** | 32.5 | 43.3 |
| bands against the globe | `hero` | 19760 | **103.4** | 45.2 | 132.1 |
| bands against the globe | `sheet` | 19764 | **106.3** | 45.4 | 132.2 |
| bands against the globe | `spot` | 18047 | **95.6** | 45.3 | 132.1 |

## What the reader saw, and what the plastic is

At the `spot` frame -- the one a reader is given for this pair --
the companion is **34.5 luma levels** from the spot's filament on
the Sol piece and **52.5** on the Anti-Sol one, and **57.4 / 87.2**
from the globe it sits on. The three cloud bands on the same globe
separate from the same globe by 100.7 / 95.6.

Against this set's own shipped floor, read off its own reports:

| marking | separation | source |
|---|---:|---|
| Saturn's light bands against its globe | 9.4 | `measure/saturn-tone-separation.md` |
| Venus's beige highlands against its globe | 20.2 | `measure/venus-tone-separation.md` |
| **Neptune's companion against its dark spot** | **34.5** (Sol) / **52.5** (Anti-Sol) | this report |

**The companion separates from the dark spot by more than the
narrowest separation this set has already shipped** -- 34.5
against 9.4. It is not a marginal pairing by this set's own
standard.

### Why an unprimed reader still called it grey

Because it is not the separation that is small; it is the LIGHT.
`render_review` shades by surface normal from a light above the
piece and draws no shadow and no ground plane, and a flush colour
inlay's outer face IS the globe's own sphere -- a marking has the
same normal as the blue beside it. So every marking on the southern
face of a globe is rendered dim whatever filament it is printed in,
and every marking on the northern face is rendered bright. On this
globe the companion and the dark spot are both southern and both
come out in the 76-175 range across the two armies, while the two
northern cloud bands -- the same `white` spool the companion is
printed from -- come out at 200-235. The southernmost band, `b1`,
is `white` too and renders at about 103 on the Sol piece: a reader
of that image calls it grey as well, and `measure/neptune-flush.md`
records an earlier independent reader making the same call about
the same set of markings.

The two-render measurement above is immune to that, which is why it
is the one that decides: both renders carry the identical light and
the identical geometry, and only the filament differs.

**What this means for the printed object.** The companion prints in
`white` #FFFEF7, the same spool as the three cloud bands and as
Saturn's and Uranus's rings; the spot prints in `dark_gray` #6F6E6D.
Those are the channels the shop and the listing read. On a printed
piece in ordinary light the difference between them is the
difference between white and mid-grey plastic. **The grey reading
is the renderer's, not the plastic's** -- and it is recorded in the
product's limitations in exactly those terms rather than left for a
buyer to discover from an image.
