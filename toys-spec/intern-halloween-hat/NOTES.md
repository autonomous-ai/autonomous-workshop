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
- Coverage: the top two-thirds of the tip; the bottom ~10 mm band stays
  visible and lit. (Round 1 also tried the whole tip; the owner dropped it.)
- Grown-up gift style, matte, not garish. No snowflakes or Christmas elements.
  The carved jack-o'-lantern face is the one face allowed; it is part of the
  ask.

## Rejections

- Carried over from the Intern Christmas hat: no garish candy-coloured
  overload.
- **2026-10-09, round 1:** full coverage (J5–J8) is out: "phủ toàn bộ thì nó
  bị to quá" (too big). Every later hat covers only the top two-thirds of the
  tip and stays about 40–45 mm wide.

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

**2026-10-09:** the owner chose the two-thirds coverage: "Chắc lấy 2/3 đi,
phủ toàn bộ thì nó bị to quá". J5–J8 are out (see Rejections).

## Round 2: tech pumpkins (`concepts/round2/`), 2026-10-09

The owner's ask: "thử lấy bí ngô theo theme tech xem sao". Every concept
covers the top two-thirds of the tip.

| ID | Name | Idea |
|---|---|---|
| G1 | Circuit Pumpkin | Ribbed orange pumpkin engraved with circuit traces and vias like the body |
| G2 | Dot Matrix | Face made only of a grid of small square holes, like a dot-matrix LED display |
| G3 | Robot Pumpkin | Panel seams and rivets, a short antenna stem, slot eyes and a grille mouth |
| G4 | Low-poly | Faceted triangular low-poly pumpkin like a 3D model |
| G5 | USB Stem | Stem is a coiled cable ending in a USB-C plug, with a circuit-board leaf |
| G6 | Terminal Face | Chevron eyes like > and <, and an underscore cursor mouth |
| G7 | Heatsink | Ribs are burnt-orange anodised heatsink fins; the stem is a fan hub |
| G8 | Cyber Visor | A dark smoked visor band across the front; the eyes are two lit bars |

Source: text prompts with `--ref` set to `concepts/round1/j1_classic-jack.png`
(our own image), kept for the device, the camera and the two-thirds coverage
and size. None needed regenerating.

Flags:
- G3's seams and rivets are faint, and its antenna is thin.
- G5's cable and leaf are thin and would be hard to print.
- G7's fins are thin; a print needs them thicker.

**2026-10-09:** the owner switched the Halloween hat to the Lamp: "Giờ đổi
lại lần nữa là làm cho lamp chứ không làm cho intern. Cái idea G4, G6, J1 tôi
thấy ok, chuyển nó qua cho lamp". J1, G4 and G6 are marked chosen and continue
in `../lamp-halloween-hat/` as N1–N3. The Intern Halloween hat stops here.
