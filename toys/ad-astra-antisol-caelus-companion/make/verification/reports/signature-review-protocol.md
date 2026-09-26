# The independent blind review of this correction

`snap/SIGNATURE-REVIEW.json` is the sealed record. This is the same account
without field-length limits. It replaces the file of the same name carried in
from the source archive, which described the previous edition's review of
Uranus; that account was not used as evidence for anything here.

## Who reviewed it, and how

ONE independent native critic, TWO rounds, ONE repair between them.

The critic was allowed only the Read tool, and only on the exact image paths it
was given. It was told to open no source, JSON, report or directory listing, run
no shell command, and not to infer anything from file names. It confirmed its
compliance at the end of every answer.

## Round 1: unprimed

The critic saw nineteen canonical renders and was told nothing about the
object: the whole set (`snap/iso.png`), the three-state sheet
(`snap/signature.png`), both rank ladders, and every Neptune frame under
`snap/worlds/`, including the Neptune-Earth and Uranus-Neptune pairs.

**Cold, it read the object correctly.** It saw a two-player board game of
planet pieces in two mirrored armies, with sizes stepping down from Jupiter,
and it named the worlds from their markings.

**It inventoried every marking on both Neptune pieces**, and before it knew
anything about the brief it found the new one:

> "A small grey spot below the oval, fully visible ... directly below the
> oval, offset slightly right of the oval's centre ... roughly 1/3 of the
> oval's width ... a clear blue strip of about 7 px separates it from the oval,
> so they do not touch."

On the Sol piece it found the same mark "mostly hidden by the collar".

**Two narrow follow-ups, both still blind.**

1. It was asked to rank the tones of the oval, the small ellipse and the
   nearby band. In the shaded level frames it matched the ellipse to the grey
   oval. Pixel sampling agreed with the renderer's behaviour: the companion
   renders at about 156/255, the white band beside it at about 143, and the
   dark-gray spot at about 131. The renderer lights every scene from above, so
   the southern hemisphere is in shade.
2. It was then shown two new frames, `neptune-<side>-companion-lit.png`. They
   are the exact piece turned toward the fixed light, with the base disc
   omitted and labelled as such. It reversed its tone reading: "(b) and (c)
   are tied as the lightest; both are white ... (b) now matches (c), not
   (a)."

**Reveal and comparison.** The brief was then disclosed. The critic graded
each requirement separately, quoting its own blind reads. It found one
BLOCKING defect caused by this correction: on the Sol piece about 41% of the
companion lay under the seat collar. It saw "a sliver" and a truncated oval,
so R1 and R3 were only partial on that piece.

## The repair

The seat cone springs from the sphere at latitude -42, measured about the
piece's own vertical. Neptune's lean carries the southern hemisphere at the
spot's longitude down toward it on the Sol army. The spot's own southern rim is
already at piece latitude -40 there, so no printable oval directly south of it
can clear the seat.

A grid search over longitude offset and latitude found the smallest offset
that clears the seat and keeps a printable gap to the spot: 10 degrees west,
at latitude -33.5. That point is still inside the spot's east-west span.
`measure/neptune-companion.md` measures the result:

- the companion is 100% above the seat on both armies;
- its nearest approach to the spot is 0.526 mm at the inlay floor;
- the spot, bands, disc and numeral are unchanged.

Every downstream artefact was regenerated: the assembly, production parts,
all renders and the reports.

## Round 2: disclosed re-review

The critic already knew the brief, and this round is marked as a re-review,
not a naive read. It recorded fresh observations of ten re-rendered images
before judging:

> "Complete and clear of the collar edge" (Sol spot view); "bright white, a
> closed ellipse ... roughly 30x62 px, 2:1" (Sol lit); "bright white, a closed
> ellipse ... about 2.2:1, 0.35 of the oval's width ... Nothing covers it"
> (Anti-Sol lit).

Its grades:

- MATCH on R1-R4 and R6.
- MATCH on R7 and R8 by visual recall. The measurements cover those two
  properly: the render diff, B-rep identities and body volumes.
- PARTIAL on R5, stated plainly:

  > "it still reads as a companion hugging the spot's southern side, since it
  > is well inside the spot's east-west span ... It fails the brief's 'same
  > longitude' as written. The 10° relaxation has a measured reason ... and
  > the result still reads as 'just south of the Great Dark Spot'."

It found no blocking defect caused by this correction.

The R5 departure is therefore written into the requirement text itself in
`SIGNATURE-REVIEW.json`, into `product.json`'s limitations and into the README.
It is recorded as a disclosed departure, not a silent match.

## Pre-existing issues the critic raised, not caused by this correction

- The thin Uranus hoop and its foot gusset.
- The hairline Neptune bands.
- Pixel digits that garble in oblique views.
- Sharp cone tips on the terrain tiles.
- The two Saturn copies differing, which is the set's mirrored lean.
- The Sol Neptune's dark spot sitting low near its collar.

None of these was touched, because the brief forbids changing anything else.
