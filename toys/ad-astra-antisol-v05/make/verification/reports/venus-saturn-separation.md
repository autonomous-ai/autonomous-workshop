# Venus and Saturn, told apart

Venus's globe becomes `sunflower_yellow` #FFB549 in this revision
and Saturn's is `yellow` #FFD834, so the two are now neighbours in
hue. This is the check that they are still separable, made rather
than assumed.

## What separates them before colour

| measure | Venus | Saturn | difference |
|---|---:|---:|---:|
| rank | 3 | 7 | -- |
| globe diameter mm | 16.53 | 26.00 | **9.47** |
| piece height mm | 19.53 | 29.00 | **9.47** |
| widest feature mm | 34.00 (the disc) | 30.00 (the ring) | -- |
| a ring | no | yes, Ø30.00 x 1.40 | the silhouettes are different shapes |
| markings | two, from outline rings | four latitude bands | -- |

The globe ladder is the set's own first read and these two are 9.47 mm
apart on it -- 57 per cent of Venus's own diameter. They are four
ranks apart rather than neighbours, so this is a wide gap by the
standards of the ladder, whose tightest adjacent step is 0.13 mm.

## The globes, by value

| filament | on | sealed hex | sealed luma | as rendered | rendered luma |
|---|---|---|---|---|---|
| `sunflower_yellow` | Venus | #FFB549 | 188.9 | #FFDB92 | 221.5 |
| `yellow` | Saturn | #FFD834 | 212.5 | #FFED7D | 232.7 |

**They are 23.5 luma levels apart sealed and 11.2 as the render shows
them.** That is the honest answer and it is a small number: on value
alone these two are close, which is exactly why the rest of this
report exists. Saturn's is the lighter and greener of the two, Venus's
the deeper and oranger.

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

## What the image shows

Read off the rendered image rather than off the table above, because
the Wish asks for what a reader sees and not for what the numbers
predict.

The two are not close to being confused. Saturn is plainly the
bigger ball -- it fills its disc and overhangs it, where Venus sits
well inside its own -- and it wears a white ring that leans clear of
the board on both sides, which is a silhouette Venus has nothing
like. Saturn's four `cocoa_brown` belts are the loudest markings on
either piece and Venus has no band system at all: one pale sinuous
highland across its middle and nothing else in this frame. The two
ambers do read as the same family of colour -- Saturn's is the
lighter and greener, Venus's the deeper and oranger, and side by side
that difference is visible but it is the weakest of the cues. The one
thing the two pieces genuinely share is the disc under them, and
every world in the set shares that.

The verdict is therefore what the geometry predicted and it is
recorded as read rather than as assumed: **the silhouette carries
it easily; the colour alone would not.** If these two globes had the
same diameter and no ring, this pairing would be a problem.

Measured by `measure/venus_saturn_separation.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
