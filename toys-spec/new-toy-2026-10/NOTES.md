# New toy, October 2026

Subject: a brand-new toy for autonomous.ai/toys, chosen by picture. Tam, 2026-10-17 09:56 ICT,
answered "2" to "Tìm concept khác cho sản phẩm nào?" (a completely new toy, concepts with images).
CAD runs only after Tam says build, and then through t3d (nohope88/text-to-3d-pipeline).

Job: a hand-sized desk toy that *does* one thing when you turn, squeeze, wind or tilt it.
A buyer receives it finished.

## Constraints every image must honour

- Made of FDM-printed PETG in 2–4 solid filament colours; matte plastic, no paint, no decals, no fabric.
- Hand-sized: fits within about 150 × 150 × 150 mm; about 80–250 g.
- One clear mechanical action driven by the hand (crank, knob, key, squeeze, pull, tilt);
  no batteries, lights, screens or electronics. Small steel pins/shafts may hide inside.
- One standalone object. Original character: no licensed or trademarked characters.
- Not already in the catalogue: axolotl flexi, spider/web crawler, spider-to-star tree, crab pose dial,
  duck wind-up, cybercab, gear vortex, skyline chess, trotter horse, hawk/horse automata,
  bull/bear seesaw, city book.

## Rejections

(none yet; earlier Tam feedback on other subjects: "xấu và to thô" for a bulky black slider)

## Round 1 (N), 2026-10-17

Ask (Tam, TG): "Tìm concept khác" → answered "2" (a completely new toy, concepts with images).

Images: text only, hunyuan-image-3-t2i on Tam's media gateway (/root/docs/gen.sh; OpenRouter is banned
on this box, so the skill's generate_image.py was not used). Prompts in concepts/round1/prompts/.
N1, N3, N5 were redrawn once (*.r2.txt) because the first images missed the action; the first
drafts are kept in concepts/round1/first/.

- N1 Pumpkin Peekaboo: turn the stem, the lid lifts and a ghost rises. Flaw: lid floats, no visible lift post.
- N2 Penguin Slide: crank lifts 3 penguins up a snow hill, they slide down a spiral chute.
- N3 Owl Head-Turn: wind-up key turns the head and blinks the eyelids. Flaw: head turned ~90° not 180°; key on the side.
- N4 Dino Chomp Skull: squeeze trigger snaps the jaw. Flaw: pointed teeth (would be rounded); trigger not shown.
- N5 Hedgehog Roller: rolling raises leaf-shaped quill plates into a crown.
- N6 Woodpecker Pole: classic pecking descent down a pole on a rocking collar.
- N7 Chameleon Tongue: squeeze the tail, the tongue shoots out to a fly.
- N8 Gingerbread Carousel House: turn the chimney, shutters open, 4 gingerbread figures circle past the door.

### Novelty check, 2026-10-17 10:10 ICT

Tam: "Mấy cái này có tồn tại chưa?" Searched Printables (GraphQL) and MakerWorld (api.bambulab.com)
with product-type terms via t3d.novelty's helpers; looked at the 21 closest covers.

- N1 EXISTS: MakerWorld 3439351 "Pop-up Ghost Jack-o'-lantern" (+ "Pop-up Ghost Halloween Pumpkin").
- N2 no printed hand-crank version; the battery "penguin race" stair-and-slide toy is a long-standing mass-market product.
- N3 close: MakerWorld 1369639 "Owl Automaton" (crank) and several twist-head owls; wind-up head-turn + blink not found.
- N4 EXISTS: articulated-jaw T-rex skulls, "T-Rex Skull Grabber Handle", rubber-band chomp toys.
- N5 not found (only flexi/fidget hedgehogs). Most novel of the round.
- N6 EXISTS: Printables "Pecking Woodpecker Toy - stick-slip pole climber" + 2 MakerWorld copies; a classic toy.
- N7 close: MakerWorld 1611393 chameleon with a static snap-fit tongue; a squeeze-fired tongue not found.
- N8 close: Christmas carousels (incl. motorised) and gingerbread houses exist separately; the combination not found.
