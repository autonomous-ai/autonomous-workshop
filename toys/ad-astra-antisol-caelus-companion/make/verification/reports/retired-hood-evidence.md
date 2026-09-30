# What happened to the hood evidence

The Antisol Caelus revision removed Uranus's two polar hoods. Several pieces of
evidence in this project existed only to measure them, and a report that
measures a feature nobody can hold is worse than no report: a reader browsing
`measure/` or `snap/worlds/` would take it for a description of the piece.

The Wish asks that none of it be silently dropped and none of it silently kept.
So each item is named here with what it measured and what was done with it.

The rule applied throughout: **carry it forward when it is the record of a
decision someone will want to read, remove it when it is a picture or a row
that would be mistaken for the current piece.**

## Carried forward, under a heading saying the feature is gone

| evidence | what it measured | why it is kept |
|---|---|---|
| `measure/uranus-facing.md` | which pole faced which camera on which army at which frame, and therefore why a hood was needed at BOTH poles rather than one | it is the measurement item 23 of the design contract argues from, and the ring-projection half of it is still the shape of the question `measure/uranus-ring.md` now answers on this run's solids |
| `measure/uranus-tone-separation.md` | what every one of the thirteen stocked filaments was worth as a hood tone against the `cyan` globe, and why `beige` #F7E6DE was chosen over `white` | it is the measurement that answered the hoods' brief's own fallback question -- is ANY filament usable against `cyan`? It came back yes, at 29.0 luma levels, which is why "leave Uranus bare" was not taken at the time. The owner has taken it anyway, and that is only legible with the number in front of you |
| `measure/uranus_facing.py` | the script | kept as the method; **not run on this build**, and it exits on an empty marking table |
| `measure/uranus_tone_separation.py` | the script | kept as the method; **not run on this build**, same reason |

Both reports now open with a block quote saying, in the first line, that the
feature they measure no longer exists. Neither is current evidence for this
build and neither is cited as such anywhere in it.

## Removed, and why

| evidence | what it measured | why it is gone |
|---|---|---|
| `snap/worlds/uranus-hood-tone.png` | the Sol piece with its hoods in the chosen `beige`, at the product's own frame | it is a photograph of two pale discs on a globe that no longer has them. A reader opening `snap/worlds/` is looking at the piece, not at history, and this is the one form of stale evidence that cannot be headed with a caveat |
| `snap/worlds/uranus-bare-globe.png` | the same piece with the hoods repainted the globe's own `cyan` -- the "bare globe" outcome the hoods' brief allowed, rendered as a what-if | it was a simulation of an outcome that is now the actual product, and it is superseded by real frames of the real piece: `snap/worlds/uranus-sol-hero.png`, `uranus-anti-hero.png`, the two ring-plane frames and the four polar frames. Keeping a mock-up beside the real thing invites the wrong one to be cited |
| the hood rows of `measure/uranus-atlas-resolution.md` | the hood's angular radius, printed extent, boundary chord, boundary circumference and the bare globe between the two hoods, each against the 0.4 mm nozzle | that report is regenerated from source on every run, and on this run there is no hood to measure. It now states in its own words that the published edition measured those rows, that the feature is gone, and that the rows are not carried forward as live numbers. The ring section of the same report is unchanged and still live |
| `snap/worlds/neptune-uranus-hero.png`, `-hero-anti.png` and `measure/neptune-uranus-separation.md` | Neptune beside Uranus at the product's own frame, from Neptune's side | the renders showed the hoods, so both the pictures and the report were stale. **The pair is not dropped:** it is re-rendered and re-measured from Uranus's side on this run's own solids, as `snap/worlds/uranus-neptune-hero.png`, its Anti-Sol mirror and `measure/uranus-neptune-separation.md`. `measure/neptune-earth-separation.md` is untouched -- neither of those two worlds changed |

## Kept exactly as they were, and regenerated

The per-piece **polar and south-polar renders stay**, and they are regenerated
from this build's solids:
`snap/worlds/uranus-sol-polar.png`, `uranus-sol-south-polar.png`,
`uranus-anti-polar.png`, `uranus-anti-south-polar.png`.

They were made to show the hoods and they are kept for the opposite reason. A
bare globe photographed straight down its own leaning pole is the strongest
possible evidence that there is nothing there: a cap bounded at 60 degrees of
latitude would fill the middle of that frame, and four of these cameras look
straight down the four poles of the two pieces. If anything at all had survived
on either globe, this is the frame it could not hide in.

## What replaced the retired measurements

| new evidence | what it measures |
|---|---|
| `measure/uranus-bare.md` | that nothing is drawn on either globe, asked three ways: the marking table, the built colour bodies, and whether each globe's volume is its published volume plus both removed hoods |
| `measure/uranus-ring-tone.md` | what the ring's `white` is worth against the `cyan` globe, by the same two-render method the hood tone used |
| `measure/uranus-neptune-separation.md`, `measure/uranus-saturn-separation.md`, `measure/uranus-earth-separation.md` | what a bare Uranus has left to tell it apart from its three nearest neighbours, answered on size, colour, silhouette and surface separately |
| `snap/rank-ladder-sol.png` | all eight globes at one scale in one orthographic frame, in rank order, so the size ladder can be read rather than taken on trust |
