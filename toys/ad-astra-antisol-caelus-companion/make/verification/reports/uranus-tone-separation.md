> **CARRIED FORWARD. THE FEATURE THIS MEASURED NO LONGER EXISTS.**
>
> This report measured what each stocked filament was worth as a HOOD TONE
> against the `cyan` globe, and it is why the hoods were drawn in `beige`
> #F7E6DE rather than `white`. **The owner removed both hoods in the Antisol
> Caelus revision.** Uranus now carries no surface marking of any kind, so
> every candidate below is a tone for a region that is not on the piece.
>
> It is kept, not deleted, for two reasons. It is the measurement item 23 of
> the design contract argues from, and it is the measurement that answered the
> question the hoods' own brief asked -- whether any filament measured usable
> against `cyan` at all. The answer was yes, at 29.0 luma levels, which is why
> the fallback of leaving Uranus bare was NOT taken at the time. The owner has
> taken it anyway. Nothing in this report is current evidence for this build.
>
> `measure/uranus_tone_separation.py` is no longer run: it exits on an empty
> marking table. The two evidence images it wrote,
> `snap/worlds/uranus-hood-tone.png` and `snap/worlds/uranus-bare-globe.png`,
> were REMOVED from this build's render family, because a picture of two hoods
> in a folder a reader browses is a picture of a feature that does not exist.
> The equivalent measurement for the feature that IS on the piece -- the ring's
> `white` against the `cyan` globe -- is
> `measure/uranus-ring-tone.md`. See `measure/retired-hood-evidence.md`.

# Uranus's hood tone against `cyan`

Every filament this set stocks, measured against the `cyan` #00FFFF globe
on the Uranus Sol piece. Sealed is the catalogue hex the shop reads;
as rendered is what every image in `snap/` shows; measured is the two-
render difference over the hoods' own pixels, which is the one that
decides. Luma is Rec. 709 on 0..255.

Invisible is below 9.4 and a stripe is above 45.5. Neither number is
in the Wish; both are this set's own measured history.
`measure/saturn-tone-separation.md` accepted 9.4 as the narrowest
separation it could still see, and `measure/mercury-tone-separation.md`
rejected 45.5 as too loud on a small ball against a quiet reference.

| candidate | sealed hex | lighter or darker | sealed apart | as rendered apart | measured, hero | measured, sheet | measured, world hero | reads as |
|---|---|---|---:|---:|---:|---:|---:|---|
| `beige` | #F7E6DE | lighter | 32.2 | 44.3 | 27.8 | 28.1 | 27.8 | faint but present |
| `black` | #000000 | darker | 200.8 | 200.8 | 125.6 | 127.0 | 125.6 | a stripe |
| `blue` | #004EA8 | darker | 132.9 | 78.1 | 48.9 | 49.5 | 48.9 | a stripe |
| `cocoa_brown` | #8E3C06 | darker | 127.3 | 60.6 | 38.0 | 38.4 | 38.0 | faint but present |
| `cyan` | #00FFFF | -- | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | invisible |
| `dark_gray` | #6F6E6D | darker | 90.6 | 25.2 | 16.0 | 16.2 | 16.0 | faint but present |
| `gray` | #9FA19F | darker | 40.4 | 7.0 | 4.3 | 4.4 | 4.3 | invisible |
| `green` | #00BB31 | darker | 63.5 | 33.0 | 20.8 | 21.0 | 20.8 | faint but present |
| `orange` | #FF671F | darker | 70.7 | 17.7 | 11.2 | 11.3 | 11.2 | faint but present |
| `red` | #FF0000 | darker | 146.6 | 146.6 | 91.7 | 92.7 | 91.7 | a stripe |
| `sunflower_yellow` | #FFB549 | darker | 11.9 | 20.7 | 12.9 | 13.0 | 12.9 | faint but present |
| `white` | #FFFEF7 | lighter | 52.9 | 53.6 | 33.7 | 34.1 | 33.7 | faint but present |
| `yellow` | #FFD834 | lighter | 11.7 | 31.9 | 20.0 | 20.2 | 20.0 | faint but present |

## What the numbers say

- **`beige` #F7E6DE measures 27.9** averaged over the three frames,
  which is faint but present.
- **`white` #FFFEF7 measures 33.9**, faint but present. It is the tone this
  correction is replacing, and on a `cyan` globe it is what read as a
  tennis ball.
- **8 of the 13 stocked filaments read as faint but present**: `beige`, `cocoa_brown`, `dark_gray`, `green`, `orange`, `sunflower_yellow`, `white`, `yellow`.

## The filter the table above does not apply, and the Wish does

`ref/uranus-sol.png` shows a region LIGHTER than the globe around it.
A darker patch would be a different feature, not a quieter one, so the
choice is only among the filaments lighter than `cyan`'s own 200.8 luma.

**There are exactly 3 of them: `beige`, `white`, `yellow`.**

- `beige` #F7E6DE, 233.0 luma, measures 27.9 against the globe. A pale warm off-white: the quietest of the three that is not a hue clash.
- `white` #FFFEF7, 253.7 luma, measures 33.9 against the globe. The tone this correction replaces.
- `yellow` #FFD834, 212.5 luma, measures 20.1 against the globe. A saturated yellow against a saturated cyan: near-opposite in hue, so it is quiet in luma and loud in colour, which is the one way a number can mislead here.

Everything else in the palette is darker than the globe. The quietest
of those by luma is `gray` at 4.4, which is invisible, and the next
are `orange` and `sunflower_yellow` -- warm oranges on a cyan ball,
quiet in luma for exactly the reason they are loud in hue.

## The recommendation

`beige`, the intended answer, and the measurement agrees with the
argument -- but it is worth being exact about how much of the
correction the tone is doing.

`beige` measures 27.9 and `white` measures 33.9, so the tone change
on its own is 6.0 luma levels, about 18 per cent quieter. That is
real and it is in the right direction, and it is **not** what stops
this piece reading as a tennis ball. What does that is the shape:
the marking was a belt of latitude encircling the ball, which the
obliquity stood upright across the visible face, and it is now a
broad region ENCLOSING each pole. Both have a boundary -- a flush
inlay always does -- but a cap's boundary shrinks to a point at the
pole and a belt's runs right round the ball and comes back. A
quieter stripe is still a stripe; this is not a stripe.

`beige` also loads no new spool -- it is already Earth's dryland and
Jupiter's and Saturn's zones -- and at 27.9 it sits inside the band
this set has already proved it can both see and live with. `white`
stays on the shelf as the fallback and is not needed.

## The thing no filament can fix

`ref/uranus-sol.png` is a pale desaturated ice blue -- its ball means
161, 200, 206, luma 192.7, measured in `measure/uranus-reference.md`.
`cyan` #00FFFF is a saturated neon with no red in it at all.

**There is no pale blue in this set's palette, and the shop has none to
sell it either.** The 13 filaments here are exactly the Bambu Lab PLA
Lite range, all of it, and its only blue-family colours are `cyan` and
`blue` #004EA8 at luma 67.9 -- a dark navy, further from the reference
than `cyan` is. The one plausible pale blue the shop lists at all,
`misty blue` #688197, is a Bambu Lab PETG Basic colour, and at luma
125.3 it is a mid slate rather than an ice blue; loading it would also
put a second material family in a box whose whole point is that it
prints in one.

So **the gap between the globe's own colour and the reference cannot be
closed inside this correction**, whatever the hood is painted, and a
paler marking on a neon globe does not make the globe paler. The
limitation is recorded in `product.json`, in the design contract and in
the README rather than compensated for here. If the set should acquire
a pale blue, that is a recommendation for a future revision: it would
mean a new material family or a custom spool, and `cyan` is shared with
the Anti-Sol flames and the Anti-Sol corona cells, so changing it
reaches well outside two printed parts.

## The ring, which is a different question

A ring is a silhouette rather than a surface marking, so the quietness
argument above does not automatically reach it, and the brief says to
take `white` -- the tone Saturn's ring already wears -- unless a reason
not to is MEASURED. Here is the measurement, by the same two-render
method with only the ring repainted.

| candidate | sealed hex | measured, hero | measured, sheet | measured, world hero |
|---|---|---:|---:|---:|
| `beige` | #F7E6DE | 33.6 | 33.8 | 33.6 |
| `black` | #000000 | 143.8 | 146.1 | 143.8 |
| `blue` | #004EA8 | 54.7 | 55.6 | 54.7 |
| `cocoa_brown` | #8E3C06 | 42.0 | 42.5 | 42.0 |
| `cyan` | #00FFFF | 0.0 | 0.0 | 0.0 |
| `dark_gray` | #6F6E6D | 16.5 | 16.6 | 16.5 |
| `gray` | #9FA19F | 7.0 | 7.3 | 7.0 |
| `green` | #00BB31 | 22.1 | 22.3 | 22.1 |
| `orange` | #FF671F | 11.6 | 11.7 | 11.6 |
| `red` | #FF0000 | 105.0 | 106.6 | 105.0 |
| `sunflower_yellow` | #FFB549 | 16.4 | 17.1 | 16.4 |
| `white` | #FFFEF7 | 38.7 | 39.3 | 38.7 |
| `yellow` | #FFD834 | 24.7 | 25.4 | 24.7 |

`white` measures 38.9 against the globe and `cyan` -- the globe's own
filament, which makes the hoop a silhouette and nothing else --
measures 0.0 by construction.

Evidence: `snap/worlds/uranus-hood-tone.png` is the piece as built,
in `beige`; `snap/worlds/uranus-bare-globe.png` is the same piece with
the hoods painted the globe's own cyan, which is the bare-globe
outcome the Wish allows, rendered so the two can be compared.
