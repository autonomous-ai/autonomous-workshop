# Venus and Saturn, told apart

Venus's globe is `sunflower_yellow` #FFB549 and Saturn's is `yellow` #FFD834,
and since this correction four of Saturn's five bands are
`sunflower_yellow` too. The two pieces are therefore no longer merely
neighbours in hue: they are built out of the same spools. The Venus
run made this check before that was true; the Wish asks for it to be
made again afterwards, and this is that check, on three counts
separately.

| | Venus | Saturn |
|---|---|---|
| surface filaments | `beige`, `cocoa_brown`, `sunflower_yellow` | `cocoa_brown`, `sunflower_yellow`, `white`, `yellow` |

**Shared: `cocoa_brown`, `sunflower_yellow`.** Before this correction they shared
`cocoa_brown` alone, and that was on Venus's lowlands against
Saturn's four bands. Now they share the tone that carries Venus's
whole globe.

## 1. Size

| measure | Venus | Saturn | difference |
|---|---:|---:|---:|
| rank | 3 | 7 | -- |
| globe diameter mm | 16.53 | 26.00 | **9.47** |
| piece height mm | 19.53 | 29.00 | **9.47** |

The globe ladder is the set's own first read and these two are 9.47 mm
apart on it -- 57 per cent of Venus's own diameter, and 73 times
the ladder's own tightest adjacent step of 0.13 mm. They are four
ranks apart rather than neighbours. **Nothing in this correction
touches either number.**

## 2. Silhouette

| measure | Venus | Saturn |
|---|---|---|
| widest feature | Ø34.00, the disc | Ø34.00, the disc |
| a ring | no | yes, Ø30.00 x 1.40, leaning 26.73 degrees |
| globe against its own disc | sits well inside it | fills it and overhangs it |

Saturn's ring is unchanged by this correction: `RING_OUTER_D` is
still 30.00 and `RING_THICKNESS` still 1.40.

## 3. Surface, by value

| filament | on | sealed hex | sealed luma | as rendered | rendered luma |
|---|---|---|---:|---|---:|
| `sunflower_yellow` | Venus's globe, Saturn's bands | #FFB549 | 188.9 | #FFDB92 | 221.5 |
| `yellow` | Saturn's globe | #FFD834 | 212.5 | #FFED7D | 232.7 |
| `beige` | Venus's highlands | #F7E6DE | 233.0 | #FBF4F0 | 245.1 |
| `cocoa_brown` | Venus's lowlands, Saturn's one dark band | #8E3C06 | 73.5 | #C5852A | 140.2 |
| `white` | Saturn's ring and cap | #FFFEF7 | 253.7 | #FFFFFB | 254.4 |

**The two globes are 23.5 luma levels apart sealed and 11.2 as the
render shows them** -- the same numbers the Venus run reported, and
they have not moved because neither globe has. That is a small
number and it is the weakest cue in the set. What this correction
adds is that Saturn's bands are now that same
`sunflower_yellow`, so where Venus's globe is one flat field of it,
Saturn wears it as five stripes on a lighter ball.

## Rendered side by side

- **hero frame** (azimuth -55, elevation 22): Venus occupies 436 x 321
  pixels of silhouette and Saturn 436 x 438, so Saturn stands 36
  per cent the taller and exactly as wide -- every disc in the
  set is Ø34.00 and on both pieces the disc, not the globe, is
  the widest thing -- with 184 columns of clear background
  between the two.
- **state sheet frame** (azimuth -45, elevation 35.264): Venus occupies 383 x 306
  pixels of silhouette and Saturn 383 x 403, so Saturn stands 32
  per cent the taller and exactly as wide -- every disc in the
  set is Ø34.00 and on both pieces the disc, not the globe, is
  the widest thing -- with 290 columns of clear background
  between the two.

`snap/worlds/venus-saturn-hero.png` is the image, at the product's
own frame, with the two pieces 84 mm apart on the board's own
pitch.

## The verdict, on the three counts the Wish asks for

Read off the rendered image rather than off the tables above,
because the Wish asks for what a reader sees at arm's length and not
for what the numbers predict. It also asks for the answer not to be
rounded up, so each count is reported on its own.

**On size: yes, easily.** Saturn's globe is 26.00 mm against Venus's 16.53 and
its piece stands 29.00 mm against 19.53 -- a third taller in the frame, and the
gap is 57 per cent of Venus's own diameter. Venus's ball sits well inside its
Ø34.00 disc with a clear margin all round; Saturn's fills its disc and hangs
over the edge of it. Nothing in this correction touches either.

**On silhouette: yes, easily.** Saturn wears a Ø30.00 ring leaning 26.73
degrees, which crosses its own disc in projection and stands clear of the board
on both sides. Venus has no such feature and nothing like that outline. This is
the cue the Venus run already identified as the one that carries the pair, and
it is unchanged.

**On surface: weaker than it was, and it is the weakest of the three.** The two
pieces now share `sunflower_yellow`, and that is a real cost rather than a
neutral one. It does not make them read alike, and the reason is in the drawing
rather than in the tone. Read off the image: Venus is a flat amber ball with
one pale sinuous highland across its middle and nothing else, and Saturn is a
lighter `yellow` ball wearing four soft amber stripes, one darker brown one and
a bright white cap over its north. Which colour is the field and which is the
mark is the other way round on the two pieces, and a field and a stripe pattern
are different pictures even in one colour. The white cap helps more than it was
meant to: it is the one tone on Saturn that Venus has nowhere on it, and at
this size it is the first thing the eye lands on. But the two ambers do read as
the same family, the `yellow` globe is only 11.2 rendered luma levels from the
`sunflower_yellow` one, and Saturn's own bands are only 9.4 levels from its
globe -- so at arm's length the surface of each piece is a soft, low-contrast
thing, and it is not what tells the two apart.

**Taken together: the silhouette and the size carry it, and the surface does
not.** That is the same verdict the Venus run reached and it is stated in those
words rather than rounded up. What has changed is the margin: before this
correction Saturn's four hard brown bands were a loud surface cue that happened
also to separate the two pieces, and that cue is deliberately gone. Saturn does
not read as a large Venus -- the ring, the size and the striping all say
otherwise -- so `sunflower_yellow` is kept rather than abandoned for `beige`,
and the fallback is not taken. The honest statement of the cost is that this
pairing now rests on geometry alone.

Measured by `measure/venus_saturn_separation.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
