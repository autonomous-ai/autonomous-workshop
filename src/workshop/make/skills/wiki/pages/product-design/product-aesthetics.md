---
title: Designing a product to look good
tags: [aesthetics, industrial-design, form, proportion, silhouette, hierarchy, cmf, surface]
aliases: [splendid, ornate, carousel horse, harness ornament, jewels, stylised wing, feathers, mane, tail plume, beautiful product, good looking design, form language, design language, visual hierarchy, primary secondary tertiary forms, proportion, visual weight, stance, silhouette test, design direction, mood board, precedent, cmf, colour material finish, surface continuity, g2 continuity, highlight, design critique, cad default look]
sources:
  - https://www.core77.com/posts/12752/a-periodic-table-of-form-the-secret-language-of-surface-and-meaning-in-product-design-by-gray-holland-12752 (G0 / G1 / G2 surfaces and what each reads as)
  - http://www.neilblevins.com/art_lessons/composition_primary_secondary_and_tertiary_shapes/composition_primary_secondary_and_tertiary_shapes.htm (primary, secondary and tertiary shapes; 70/30 rather than 50/50 divisions)
  - http://www.neilblevins.com/art_lessons/composition_areas_of_visual_rest/composition_areas_of_visual_rest.htm (areas of visual detail and areas of visual rest)
  - https://www.waltdisney.org/sites/default/files/2020-05/T&T_Silhouette-final2.pdf (the silhouette test: fill the design black, remove interior detail, it must still read)
  - https://www.designcouncil.org.uk/resources/framework-for-innovation/ (Double Diamond: diverge then converge, twice)
  - https://resources.rand3d.com/insights-from-within/catia-v5-surface-continuity-explained (curvature continuity is what polished surfaces need)
  - https://formlabs.com/blog/what-is-cmf-color-material-finish-opportunities-for-3d-printing/ (CMF decides whether a product feels cheap or premium)
  - https://www.kidsamusementrides.com/the-carousel-horse-a-complete-guide-to-history-design-amusement-ride-magic/ (carousel figures: jumpers, the carved romance side, jewels, armour and drapery)
  - https://carouselworkshop.com/illion-s-jumper-carousel-horse-roached-mane-inner-row.html (a carved jumper: harness, rosettes, deeply carved mane)
  - "experience: a sliced-sphere case framing a square 84 mm display in a round 125 mm face was rejected as ugly; a barchan-dune case whose 34 deg face held the same display needed a 21 cm deep body and read as a blob"
related: [form-and-finish-heuristics, fdm-surface-finish, colour-matching, fdm-multi-material-design, stability-and-tipping, handheld-ergonomics, printed-part-count, fillet-chamfer-pitfalls]
updated: 2026-10-04
---

# Designing a product to look good

Every geometry gate passes an ugly object. Validity, interference, fit and
printability say nothing about whether anyone wants the thing on their desk,
so beauty has to be designed on purpose, in order, and reviewed against rules
rather than left to whatever the first CAD pass happens to produce. The edge
and seam rules are [[form-and-finish-heuristics]]; this page is the order and
the vocabulary above them.

## Design big to small

A form is read in three levels (Blevins's primary, secondary and tertiary
shapes):

- **Primary** — the one mass that sets the silhouette and the stance: the
  bowl's body, the stand's leaning slab, the horse's barrel.
- **Secondary** — the few forms that break the primary up and carry the
  function: a handle, a lip, legs, a lid.
- **Tertiary** — detail: grooves, texture, lettering, small radii, a vent
  pattern. Without any, a form reads unfinished; with it everywhere, it reads
  busy.

Design and review in that order. A detail cannot rescue a primary form with
the wrong proportion, and every hour spent on tertiary detail before the
primary form is settled is spent twice. In a critique, judge the primary form
from a blurred or distant view first, then the secondary forms, then detail.

## One direction, stated before any shape

Before sketching a concept, write the product's **character in three words**
(calm, precise, friendly; playful, chunky, bold) and find two or three
**precedents** that already have that character — the best-looking products
of the kind, award-listed designs, the most-liked published models. Record what
gives each its look (a single tapering line, one generous radius, a floating
base), not its shape.

Every later choice is then traced to those words: a radius, an angle, a colour
or a detail that does not serve the direction is removed. This is what makes a
design coherent rather than a collection of individually reasonable features.
The process is the Design Council's Double Diamond in small: diverge on
concepts, converge on one, diverge on its details, converge on the spec.

## A small form vocabulary

A product looks designed when a few rules are repeated, and assembled when
every feature brings its own:

- **One geometry family** for the primary form — soft (arcs, splines,
  G2-looking blends), geometric (planes, cylinders, crisp chamfers) or
  organic (lofted, no straight lines) — and secondary forms drawn in the same
  family.
- **A radius family**: two or three radius sizes, each a parameter, each used
  for one class of edge (large on the primary silhouette, medium on secondary
  forms, small on detail). One radius everywhere reads as a CAD default;
  a new radius per edge reads as no rule at all.
- **Lines that continue.** A split line, a lip, a groove and the top of a
  secondary form should line up with or run parallel to one another across the
  object. A line that stops for no reason, or two lines nearly but not quite
  aligned, is the most visible sign of an undesigned object.
- **Repeated angles.** One taper or lean angle, reused, rather than several
  close ones.

## Proportion and hierarchy

- **Divide unequally.** Split a mass 70/30 rather than 50/50 (Blevins): equal
  halves compete, a dominant part with a subordinate one reads intentional.
  The same holds for heights of a body and its base, a lid and its bowl, a
  colour region and its accent.
- **One focal feature.** Give the object a single place the eye goes first —
  the face of a toy, the cradle of a stand — and keep every other feature
  quieter.
- **Areas of rest.** Leave large calm surfaces between detailed ones (Blevins's
  areas of visual detail and visual rest). Detail spread evenly reads as
  texture, and nothing stands out.
- **Proportions are parameters.** Write the governing ratios (height ÷ width,
  base ÷ body, lid ÷ total) in the spec with the reason, and assert them; a
  repair that changes one dimension otherwise quietly breaks the proportion
  the design was chosen for.

## Silhouette and stance

- **The silhouette test.** Fill the main views solid black with no interior
  detail. The object must still be recognisable and must still look like the
  concept (the Disney character-design test). If two views give the same
  blob, the form lacks a defining secondary shape.
- **Design for the view people see.** A desk object is seen from above and
  in front, a wall object from the front, a floor toy from above. The best
  proportions go to that view.
- **Stance.** Mass low and wide reads stable; mass carried on a narrow or
  inset base reads light. An inset base casts a shadow line that separates
  the object from the table and makes it look lifted. Visual stance must agree
  with physical stability ([[stability-and-tipping]]).

## Surfaces and what they say

Holland's reading of surface transitions: a sharp edge (G0) reads precise and
structural, a tangent blend (G1, a constant-radius fillet) reads functional and
practical, and a curvature-continuous blend (G2) reads refined and fluid.
Polished and glossy surfaces show the difference as a kink in the reflection,
which is why premium products are surfaced to G2.

- A build123d/OCC `fillet` is a rolling-ball constant-radius blend: G1. A G2
  transition needs a lofted or spline surface, with the kernel costs in
  [[fillet-chamfer-pitfalls]].
- On a matte FDM print, layer lines dominate the highlight, so G1 versus G2
  matters far less than radius *size* and *consistency*. Spend the effort on a
  radius large enough to read at viewing distance and on the radius family; a
  sub-millimetre fillet on a hand-sized print only blunts the edge.
- Choose the edge character from the direction: crisp for precise, generous
  for friendly, and never a mixture without a rule.

## Colour, material and finish

CMF decides whether an object reads cheap or premium as much as its shape does.

- **A dominant colour and an accent**, the 70/30 rule applied to colour: the
  primary form carries the main colour, the focal feature the accent. Every
  extra colour needs a reason.
- **Colour boundaries on edges or grooves**, never mid-surface — the same rule
  as seams ([[form-and-finish-heuristics#seams-and-parting-lines]]), and how
  to build them for a multi-material print is [[fdm-multi-material-design]].
- **Finish is part of the design**: matte hides layer lines, silk and gloss show
  every one; the face printed on the bed takes the plate's texture. Which faces
  look best on a print is [[fdm-surface-finish#which-faces-look-best]]. Put the
  faces people look at (the A-surfaces) on top or side faces, never on
  support-contact faces, and give every round visible part a designed seam line.

## Stylising feathers, manes and tails

A stylised figure's plates are where its character is won or lost, and the
first construction is usually wrong in a recognisable way:

- **Rows on the lead feathers' own lines.** Build each covering row of a wing
  on the primaries themselves — same base, same direction, cut short at a
  fraction of each primary — so the row ends form parallel scallops. Feathers
  clustered in their own directions read as a gloved hand, most of all from
  above.
- **Closed, then grooved.** Feathers that taper to thin tips with open gaps
  read as a comb. Keep the tips wide enough that neighbours touch, and part
  them with a groove at least two lines wide.
- **Strands run together.** Tail and mane strands fanning from one root read
  as fingers; run them parallel and let them part only at the tips.
- **One lean.** Feathers, strands and fins lean back at the direction's one
  repeated angle.
- **A bone along the leading edge.** A flat wing with no raised leading
  element reads as a sail.

## Making a figure splendid

A figure can pass every rule above and still look plain: a clean body in one
colour. "More splendid" is almost never a different subject; it is more
craft on the same one. The carousel figure is the proven precedent — a calm,
muscular body carrying a harness of carved ornament, painted in a few strong
colours and jewelled where the straps cross:

- **Ornament follows a structure the subject already has.** On a horse that
  is the harness: bridle, breast collar, saddle cloth with a braided border,
  rosettes where straps meet, a medallion on the chest. Ornament that follows
  no structure reads as stickers.
- **Carve it proud of the body**, a strap about 1 mm, a border or rosette
  more, so it catches light and casts an edge; painted-flat ornament on a
  print reads as a decal.
- **Hair and feathers in the metal colour**, parted into locks and strands,
  are ornament too, and cost nothing in a two-half print.
- **A restrained palette with one metal**: a pale dominant body (bone white),
  a gold for everything carved and every lock, one deep accent for cloth and
  jewels (dark red), and a dark ground for the base. Gold on white on dark
  reads rich; five equal colours read as a toy box.
- **Detail at the head and the saddle, rest on the flank and haunch.** The
  areas-of-rest rule still holds: splendour concentrated reads as luxury,
  spread evenly it reads as noise.
- **Anatomy is part of the splendour.** Rounded shoulders and haunches,
  knobby knees and fetlocks, slim cannons, a carved eye with a lid line, ears
  a third of the head's length. A bare, correct body in a harness looks
  finished; a tube body in the same harness looks dressed up.

## Failure classes

| Failure | What it looks like | Rule that prevents it |
|---|---|---|
| CAD default look | a box or cylinder with one small fillet on every edge | primary form from a direction; a radius family |
| Feature soup | every surveyed feature added, each in its own shape vocabulary | one geometry family; features drawn in it |
| Equal division | body and base, lid and bowl, split 50/50 | divide 70/30 |
| Orphan lines | grooves, lips and splits that align with nothing | lines continue across the object |
| Even detail | texture everywhere, no calm surface | areas of rest; one focal feature |
| Blob silhouette | the black-filled view does not say what it is | a defining secondary form in the main views |
| Timid radius | fillets too small to read at viewing distance | radius sized to the object and the finish |
| Ugly bed face | support scars or the seam on the side people see | A-surfaces up or sideways; designed seam line |
| Glove wing, finger tail | feathers or strands fanning each their own way from one root | rows on the lead feathers' lines; strands parallel |
| Plain figure | a correct body in one colour, judged ugly | a carved harness in a metal colour, jewels at the crossings, one accent |
| Frame fights the payload | a square screen in a round face: wide dead corners, a body far larger than what it carries | frame the payload in its own shape; size the host form from the payload, not the reverse |
| Archetype lost at size | the form whose identity needs a long gentle slope, a wide crescent or a slender leg, squeezed to the size a fixed part forces, reads as a blob | before selecting, size the concept around the fixed part and check its identifying proportions survive; drop it if they do not |

No gate catches any of these. They are caught by a design review of shaded
renders and silhouettes against the direction, done as rounds with the finding
and the change written down.

## Design review checklist

Review shaded renders (front, side, top, the viewing angle) and black
silhouettes, in this order:

1. Silhouette reads in the main views, and differs between them.
2. The primary form's proportion matches the stated ratios; divisions are
   unequal.
3. One focal feature; the rest are quieter; there are areas of rest.
4. Every radius belongs to the family; edge character matches the direction.
5. Lines continue and align; angles repeat.
6. Stance matches the direction and the stability check.
7. Colour regions follow the dominant/accent split and end on edges.
8. A-surfaces avoid supports and seams.
9. Each feature traces to the three direction words; anything that does not is
   removed.
