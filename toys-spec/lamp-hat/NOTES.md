# Lamp: Christmas hat on a head module

Concept images only, for picking a direction; no contract yet.
Selection page: `CONCEPTS.html` (private artifact https://claude.ai/artifact/GsWW36N8WykBoR7UBheRVg).

The Lamp (autonomous.ai/lamp) is a robotic desk lamp, about 20 x 20 x 47 cm
and 3 kg, sold in Charcoal, Dune, Cloud and Matcha. It has a rounded square
base, a two-link arm of flat links driven by five servos, and a
truncated-cone head whose open face holds an LED ring and a small camera at
the centre. The head moves and turns to look. The owner wants a Christmas hat
for it: a module is fixed to the lamp head, and the hat attaches to that
module.

## Input

- `source/Head_dock.step` (5.9 MB, not committed; the owner put it at the main checkout root) is the owner's model (2026-10-09) of the head with
  the module, in mm. The shade's open front is about 155 mm across; the shade
  and neck together run about 143 mm front to back. The module is a block
  about 14 x 25 x 20 mm standing on a T-shaped foot (solid 67, 15 x 11 mm) on
  the top of the shade, on the centre line, about 10 mm behind the front rim,
  and roughly perpendicular to the shade's surface (bbox x -77.9 to -57.7,
  z 359 to 379.5).
- `source/head-dock-render.png` is our own shaded render of that STEP, with
  the module in orange. Every image in round 1 attached it as the fit
  reference.

## Rules for every concept

- The hat mounts on the module on top of the head and sits at a jaunty tilt.
- It never hangs over the open face: the LED ring and the camera stay fully
  visible.
- Small and light (about 60–90 mm, about a third of the shade's diameter),
  so the servos can still move the head.
- Grown-up gift style, no faces and no snowflakes, printed in PLA.
- Carried over from the Intern hat (`../intern-hat/NOTES.md`): no colour-count
  rule, and no garish candy-coloured overload.

## Rejections

- Carried over from the Intern hat: round 2's colourful hats were "nhìn ghê
  quá" (too garish).
- **2026-10-09, round 1:** L3 Slouchy Santa is out: "L3 thì có một teammate
  làm rồi" (a teammate already made it). Later rounds exclude a classic red
  Santa hat with a white fur band.

## Round 1: 8-bit chimney + soft concepts (`concepts/round1/`), 2026-10-09

The owner's ask: "Thử đổi lại cái ống khói 8bit, với thử thêm các concept xmas
sao cho nhìn nó mềm mại xem". In other words, move the chosen Intern F8 pixel
chimney onto the lamp, and add Christmas concepts that look soft.

| ID | Name | Idea |
|---|---|---|
| L1 | Pixel Chimney | The Intern's F8 8-bit chimney (brick, pixel snow, pixel smoke) on the lamp |
| L2 | Soft Chimney | A plump marshmallow chimney with a cushion of snow and a three-ball cotton smoke puff |
| L3 | Slouchy Santa | A soft red Santa hat with a puffy cream band; the tip flops back to a big pompom |
| L4 | Chunky Knit | A cream and cranberry cable-knit beanie with a big fluffy pompom |
| L5 | Snow Cloud | A puffy pillow of snow with a holly sprig and three berries |
| L6 | Elf Nightcap | A long green nightcap; its tail curls back in an S to a gold bell |
| L7 | Plush Tree | Three puffy quilted fir tiers with baubles and a rounded star |
| L8 | Pudding Cap | A Christmas pudding dome with currants, dripping cream and holly |

Sources: every image was generated with `openai/gpt-5.4-image-2` from a text
prompt plus `source/head-dock-render.png`. L1 also attached
`../intern-hat/concepts/round3/f8_pixel-chimney.png` as the look to keep.

Flags:
- L1, L5, L7 and L8 were regenerated once, because the first images drew the
  hat as large as the head, wrapping the whole top.
- L1 is now quite small and its smoke is thin.
- L5 sits back toward the neck rather than just behind the front rim.
- All the hats are drawn as fabric, knit or soft foam. Printed in PLA, they
  become rigid shells with that texture.
- How the hat holds on to the module (clip, slide or magnet) is still open.

**2026-10-09:** the owner said L1 Pixel Chimney and L7 Plush Tree "trông ok";
both are marked chosen.

## Round 2: more pixel and plush ideas (`concepts/round2/`), 2026-10-09

The owner's ask: "Giờ gợi ý thêm 8 cái khác nữa xem" (suggest 8 more). This
round builds on the two chosen styles. W1–W3 attach L1 as the 8-bit style
reference, and W4–W8 attach L7 as the plush style reference. Every image also
attaches `source/head-dock-render.png` as the fit reference.

| ID | Name | Idea |
|---|---|---|
| W1 | Pixel Tree | A stepped 8-bit fir tree with pixel baubles and a pixel star |
| W2 | Pixel Gift | A voxel present with a cream pixel ribbon and bow |
| W3 | Pixel Cabin | A tiny voxel gingerbread cabin with a snowy roof, lit window and chimney |
| W4 | Plush Gift | A puffy quilted present with a plump ribbon and soft bow |
| W5 | Plush Star | A plump gold star standing upright as a tree topper (the lamp is the tree) |
| W6 | Soft Antlers | Chubby felt antlers and two small ears, with no face |
| W7 | Plush Wreath | A puffy wreath standing upright like a halo, with berries and a bow |
| W8 | Mistletoe | A mistletoe bunch hanging from a soft curved stalk |

Flags:
- Every hat in this round came out small, about 40–70 mm rather than 60–90 mm.
- W4 sits back toward the neck.
- W7 was regenerated once, because the first wreath lay flat. It is still
  small.
- W8 was regenerated once, because the first image had no stalk. The base of
  the stalk now looks like a coil spring.
