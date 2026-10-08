# Intern: Christmas hat for the glowing tip

Concept images only, for picking a direction; no contract yet.

The Intern (autonomous.ai/intern) is a matte black square pyramid, about
120 mm (4.7 in) tall, with engraved circuit lines, a round button on the front
face and a translucent tip that glows. The owner wants a Christmas hat for
that tip.

## Input

- `source/Top_Intern.step` is the owner's model of the tip. It is a square
  pyramid with a 35.3 mm base at z = 88 and a 3 x 3 mm flat top at z = 120,
  so 32 mm tall. Its faces rise at about 63° from horizontal. Under the base,
  an 8.4 mm square plug with a 2.5 mm cross hole (z 80.5–88) seats it in the
  body.
- `source/owner-sketch.png` is the owner's sketch. The hat sits diagonally
  over the apex so the light still shows; part of it may hang onto the body.

## Rules for every concept

- The hat is tilted: it covers the apex and one side, and about half of the
  tip stays visible and lit.
- It may drape onto the body but must not cover the front button.
- Grown-up gift style, no faces and no snowflakes, in matte PLA.

## Concepts (`concepts/`), 2026-10-08

| ID | Name | Idea |
|---|---|---|
| H1 | Santa Slouch | A classic red Santa hat with a cream band; the pompom rests on the body's side face |
| H2 | Elf Cap | A green pointed cap with a red zig-zag cuff and a gold bell |
| H3 | Holly Beret | A cranberry beret at an angle, with a holly sprig |
| H4 | Pixel Santa Hat | An 8-bit voxel Santa hat that matches the Pixel Tree Key |
| H5 | Candy-Cane Stocking | A long red and cream striped cap; its tail runs down an edge of the body to a pompom |
| H6 | Tree Cone | A three-tier fir-tree hat with a gold star |
| H7 | Antler Beanie | A cream knit beanie with a brown cuff and small antlers |
| H8 | Gift Bow Cap | A short cranberry cap with a gold ribbon and bow, like a wrapped present |

Flags:
- H1, H3, H5 and H7 are drawn as fabric or knit. In printed PLA they become
  rigid shells with a fabric texture.
- H7 sits nearly straight rather than tilted.
- H1, H4 and H5 hang onto the body, so a contract has to decide how they hold
  on without marking it.
- How the hat stays on is still open. Options are a friction fit on the tip's
  faces, or a clip.

`sheet.jpg` shows all eight. Images were made with OpenRouter
`openai/gpt-5.4-image-2`, using a crop of the Intern product photo and the
owner's sketch as references. H6 and H8 were regenerated once because the
first images had wrong logo text.
