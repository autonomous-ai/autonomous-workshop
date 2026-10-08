# Intern: Christmas hat for the glowing tip

Concept images only, for picking a direction; no contract yet.
Selection page: `CONCEPTS.html` (private artifact https://claude.ai/artifact/QSLVb8nmhpLqKuvYFNps9j).

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

## Rejections

- **2026-10-08, round 1 (H1–H8):** "mấy cái này nhìn hơi đơn điệu". Each hat used one or two colours. Every later round needs at least four bright colours per hat.
- **2026-10-08, round 2 (M1–M8):** "Thôi nhìn ghê quá, bỏ hết constraint về nhiều màu hay ít màu đi." Too garish. Every rule about colour count is dropped: later rounds set no colour requirement and exclude a garish candy-coloured overload.

## Round 1 (`concepts/`), 2026-10-08

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
owner's sketch as references. (The product photo came from the web and should
only have been looked at, not attached; later rounds attach H1 instead.) H6 and H8 were regenerated once because the
first images had wrong logo text.

## Round 2: more colour (`concepts/round2/`), 2026-10-08

The owner's ask: "Tôi muốn một concept nào đó nhiều màu sắc hơn, mấy cái này
nhìn hơi đơn điệu". Each hat has at least four saturated colours.

| ID | Name | Idea |
|---|---|---|
| M1 | Patchwork Santa | A Santa hat of red, green, gold, teal and pink patches with a mixed-yarn pompom |
| M2 | Fair-Isle Knit | Knit bands of red, green, cream, gold and blue with reindeer and tree motifs |
| M3 | Harlequin Elf | A two-point hat in red, green, gold and purple diamonds, with a bell on each point |
| M4 | Fairy-Light Hat | A pine-green hat wrapped in multi-colour bulbs, with a gold star |
| M5 | Gingerbread Roof | A gingerbread roof with white icing, gumdrops and a peppermint |
| M6 | Candy Shop | Red, mint, white and lemon spiral stripes, with a lollipop pompom |
| M7 | Pixel Lights | A voxel Santa hat whose band is dotted with multi-colour pixel lights |
| M8 | Bauble Cluster | A cap formed from mini baubles in six colours, with a curly gold ribbon |

Source: every image was generated from its text prompt with `--ref` set to
round 1's `h1_santa-slouch.jpg` (the device to keep) and
`source/owner-sketch.png` (how the hat sits), through
`.claude/skills/brainstorm-trend/scripts/generate_image.py`.

Flaws:
- M4 was regenerated once, because the first image covered almost all of the
  tip.
- M5 still covers most of the tip.
- M3 reads more like a jester than Christmas.
- M7's coloured lights are small.
- M8 has many small parts and is hard to print.
- M1 and M2 look like fabric, which becomes a rigid shell in PLA.

## Round 3: chimney (`concepts/round3/`), 2026-10-08

The owner's ask: "Giờ xem thử idea theo hướng ống khói thử xem". Each topper is
a chimney sitting tilted on the tip, with no colour requirement.

| ID | Name | Idea |
|---|---|---|
| F1 | Brick Chimney | A red-brick stack with a snow cap, worn at an angle like a hat |
| F2 | Santa Stuck | Santa's boots and legs stick up out of the chimney; no face |
| F3 | Smoke Puff | A grey stone chimney with a solid curl of white smoke |
| F4 | Rooftop Corner | A snowy tiled roof piece following the pyramid's slope, with a small chimney |
| F5 | Stocking Chimney | A cream stone chimney with a red stocking and holly |
| F6 | Gift Delivery | A brick chimney with a present wedged in its top |
| F7 | Beacon Chimney | An open hollow flue, so the tip's light glows out of the top |
| F8 | Pixel Chimney | A voxel brick chimney with stepped pixel smoke |

Source: text prompts with `--ref` set to `concepts/h1_santa-slouch.jpg` and
`source/owner-sketch.png`, as in round 2.

Flaws:
- F7's rising light beam is a photo effect. In reality only the chimney's
  mouth would glow.
- F8 was regenerated once, because the first image sat straight. The second
  image floats beside the tip instead of covering the apex.

## Owner decisions, 2026-10-08

- **Chosen: H6 Tree Cone, H7 Antler Beanie and F8 Pixel Chimney.**
- F8 was regenerated, because "cái ảnh nó nhìn kiểu ống khói nằm ngoài hoàn
  toàn". The new image used `--ref` set to the previous F8 (the concept to
  keep) and H1 (the correct over-the-apex fit). The chimney's open bottom now
  slips over the apex. It sits almost upright, with little tilt.

## Round 4: traditional Santa hat with one tech detail (`concepts/round4/`), 2026-10-08

The owner's ask: "thử theo hướng khác thú vị hơn, kết hợp mũ giáng sinh
truyền thống với một trang trí kiểu tech". Each hat is a red Santa hat with a
white band and pompom, plus one tech detail.

| ID | Name | Tech detail |
|---|---|---|
| T1 | Circuit Band | Gold circuit traces on the band; the pompom is a tiny gold chip |
| T2 | LED Pompom | A small LED bulb on a wire leg replaces the pompom |
| T3 | USB-C Tip | The tip ends in a USB-C plug |
| T4 | Keycap Pompom | A blank mechanical keycap replaces the pompom |
| T5 | Antenna | A router antenna sticks up from the hat |
| T6 | Headset Santa | A headset with a boom mic, because the Intern is a voice assistant |
| T7 | Fiber-Optic Pompom | A burst of glowing fiber-optic strands |
| T8 | Cursor Charm | A mouse-pointer cursor hangs from the tip |

Source: text prompts with `--ref` set to `concepts/h1_santa-slouch.jpg` and
`source/owner-sketch.png`.

Flaws:
- T5 was regenerated once, because the first antenna looked like a bird.
- T2's bulb and T4's keycap are small.
- T7's thin strands are hard to print in PLA.
