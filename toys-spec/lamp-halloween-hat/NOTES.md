# Lamp: Halloween pumpkin hat on the head module

Concept images only, for picking a direction; no contract yet.
Selection page: `CONCEPTS.html` (private artifact https://claude.ai/artifact/EZKDMoMDTMGh7X28pEP5QY).

The owner moved the Halloween pumpkin hat from the Intern to the Lamp
(autonomous.ai/lamp), the same robotic desk lamp as the Christmas hat in
`../lamp-hat/NOTES.md`. The hat mounts on the square module fixed on top of
the lamp head.

## Input

- `../lamp-hat/source/Head_dock.step` (not committed): the head with the
  module, about 14 x 25 x 20 mm, on the centre line about 10 mm behind the
  front rim of the 155 mm shade. See `../lamp-hat/NOTES.md`.
- `../lamp-hat/source/head-dock-render.png`: our shaded render of it, attached
  first to every image as the fit reference.
- The chosen Intern pumpkins J1, G4 and G6 (`../intern-halloween-hat/`).

## Rules for every concept

- From the Lamp Christmas hat: a hollow shell with a chunky closed flat base
  (at least 32 x 38 mm) that slips over the module and hides it; no stalks,
  rings or loose parts; never over the LED ring or camera; small and light.
- A pumpkin about 50–60 mm wide with a jack-o'-lantern face cut through,
  looking forward like the lamp's open face.
- The images show the face glowing from a small light inside the hat. The
  module has no light today, so a real glow needs one (or the face stays
  dark, lit only by the room).
- Grown-up, matte, tasteful autumn colours, not garish. No Christmas elements.

## Rejections

- Carried over: no garish candy-coloured overload (Intern hats); no thin
  stalks or open shapes that cannot hold the module (Lamp Christmas W5–W8).
- From the Intern pumpkins: full coverage hats were "to quá" (too big).

## Round 1 (`concepts/round1/`), 2026-10-09

The owner's ask: "Giờ đổi lại lần nữa là làm cho lamp chứ không làm cho
intern. Cái idea G4, G6, J1 tôi thấy ok, chuyển nó qua cho lamp, xong thêm 5
ideas mới nữa (không theo hướng tech)".

| ID | Name | Idea |
|---|---|---|
| N1 | Classic Jack | Intern J1 on the lamp: ribbed orange pumpkin, triangle eyes and nose, jagged grin |
| N2 | Low-poly | Intern G4 on the lamp: faceted triangular low-poly pumpkin |
| N3 | Terminal Face | Intern G6 on the lamp: > and < eyes, underscore cursor mouth |
| N4 | Witch Pumpkin | Small pumpkin wearing a wide-brimmed black witch hat with a plum band |
| N5 | Stacked Pumpkins | Orange carved pumpkin with a small cream pumpkin on top |
| N6 | Black Cat | Black cat curled behind the pumpkin; only ears and tail show, no cat face |
| N7 | Sleepy Pumpkin | Closed curved eyes and a small smile, with a plum and cream striped nightcap |
| N8 | Ghost Sheet | Pumpkin half draped in a cream sheet ghost; eyes glow through its holes |

Source: every image was generated with `openai/gpt-5.4-image-2`, with `--ref`
set to `../lamp-hat/source/head-dock-render.png` and then the Intern image it
ports (N1 J1, N2 G4, N3 G6) or, for N4–N8, Intern J1 as the pumpkin look.
None needed regenerating.

Flags:
- N2's carved face glows only faintly.
- N4 and N8 sit back toward the middle of the shade, not just behind the
  front rim. N4's witch hat makes it nearly 80 mm tall.
- The glowing faces assume a light inside the hat (see Rules).
