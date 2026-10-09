# Intern: Halloween pumpkin hat for the glowing tip

Concept images only, for picking a direction; no contract yet.
Selection page: `CONCEPTS.html` (private artifact https://claude.ai/artifact/TBctoobwGGfDDLQeuNqWv7).

The Intern (autonomous.ai/intern) is a matte black square pyramid, about
120 mm tall, with engraved circuit lines, a round button on the front face and
a translucent tip that glows. The owner wants a Halloween pumpkin hat for that
tip, with the face cut through so the tip's light shines out.

## Input

- `../intern-hat/source/Top_Intern.step` is the owner's model of the tip
  (also at the main checkout root as `Top_Intern.step`): a square pyramid with
  a 35.3 mm base at z = 88 and a 3 x 3 mm flat top at z = 120, so 32 mm tall,
  faces at about 63°, seated by an 8.4 mm square plug.
- `source/fit-ref_h6.jpg` is a copy of Christmas concept H6
  (`../intern-hat/concepts/h6_tree-cone.jpg`). It is our own image of the
  Intern with a small hat, attached as the fit reference; the prompts tell the
  model to drop its tree hat.

## Rules for every concept

- A hollow PLA pumpkin shell on the tip. Eyes, nose and mouth are cut right
  through so the tip's light shines out; the face looks forward, the same way
  as the front button.
- The front button stays uncovered.
- Two coverages, as the owner asked: the top two-thirds of the tip (the bottom
  ~10 mm band stays visible and lit), or the whole tip down to the body.
- Grown-up gift style, matte, not garish. No snowflakes or Christmas elements.
  The carved jack-o'-lantern face is the one face allowed; it is part of the
  ask.

## Rejections

- Carried over from the Intern Christmas hat: no garish candy-coloured
  overload.

## Round 1: pumpkin hats (`concepts/round1/`), 2026-10-09

The owner's ask: "Mũ sẽ theo theme pumpkin. Trên mũ sẽ có khoét lỗ phần mắt /
mũi / miệng để có thể nhìn thấy ánh sáng từ đèn. Thử cho tôi 8 ideas, 4 cái
theo hướng phủ 2/3 phần chóp của đèn, 4 cái theo hướng phủ toàn bộ phần chóp
của đèn."

| ID | Coverage | Name | Idea |
|---|---|---|---|
| J1 | 2/3 | Classic Jack | Ribbed orange pumpkin, curved stem, triangle eyes and nose, jagged grin |
| J2 | 2/3 | Tilted Vine | Burnt-orange pumpkin at a tilt with a vine tendril and leaf, crescent eyes and smile |
| J3 | 2/3 | Pixel Pumpkin | 8-bit voxel pumpkin with a pixel stem and leaf and a pixel face |
| J4 | 2/3 | Ghost Pumpkin | Cream-white pumpkin, sage stem, tall oval eyes and a round "oh" mouth |
| J5 | full | Round Lantern | Classic round jack-o'-lantern, deep ribs, thick stem, zig-zag grin |
| J6 | full | Pyramid Pumpkin | Four-sided pumpkin whose ribs follow the pyramid's edges, diamond eyes |
| J7 | full | Vine Wrapped | Orange pumpkin wrapped in a vine whose tendrils trail onto the body |
| J8 | full | Midnight Pumpkin | Matte charcoal pumpkin matching the body; the only orange is the glow |

Source: every image was generated with `openai/gpt-5.4-image-2` from a text
prompt plus `source/fit-ref_h6.jpg`. None needed regenerating.

Flags:
- J1's face shows a cool white light, because the tip glows blue-white. The
  others were drawn with a warm glow; the real colour depends on the tip's LED.
- J5 and J7 are larger than planned (about 70 mm).
- J7's thin tendrils would be hard to print.
- How the hat stays on (friction on the tip's faces or a clip) is still open.
