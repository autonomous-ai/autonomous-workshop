# The Wish — front-of-house mockup

A single self-contained HTML page that shows the customer experience the Workshop is built to serve:
a person makes a wish, chooses what to spend, pays, and a box turns up.

Open it directly — no build, no server:

```
open web/wish/index.html
```

## What it shows

1. **The sky.** Night over the lit workshop. "What toy do you wish for?" and one line to write in. The
   line rotates through real example wishes — one per craft — so the category is taught by example, never
   by a rule. The field grows as you type: a wish can be a letter, not a search query. Enter sends,
   Shift+Enter starts a new line.
2. **Every star is a granted wish.** Hover one (or wait — one surfaces on its own every few seconds) and a
   card shows the photo of what arrived, "Ida's wish came true yesterday", the wish in quotes, and
   **✦ I wish this too** — the free demand signal that clusters wishes for the elves.
3. **The budget.** After sending: "What's your budget?" — $10 · $20 · $50 · $100 · your own amount. One
   line says what that buys. This is the checkout boundary that sets `playtest_rounds`: money buys more
   rounds on the wish, never a lower bar.
4. **The confirmation.** The workshop windows glow: "The elves are on it." — your wish — "A box will turn
   up at your door in about a week. Don't look for it." No tracker, no receipt page, no elf names.
5. **The unboxing** (prototype only, press `u`): a box opens in layers — lid, tissue, the thing, the tag
   with your wish and the night you made it, the maker's mark under the base.

## Demo hooks

| URL | What it does |
|---|---|
| `?w=a+gravity+well+for+my+desk` | pre-fills the wish |
| `&go=1` | sends it and opens the budget step |
| `&pay=1` | runs the whole flow to the confirmation |
| `?wall=1` | opens the wall of opened boxes |
| press `u` | opens the unboxing |

## Honest notes

- Nothing here is wired to anything: no payment, no Workshop run, no order. It is a feel-test of the
  front door, not an implementation.
- `assets/` holds 38 photos of real Factory products (ours), standing in for customer unboxing photos
  until real ones exist. Two files pulled from the CDN turned out to be video and were dropped.
- Apple Pay is drawn, not integrated. The real page opens the platform sheet at the pay step.
- The product canon this page follows — the thesis, the five crafts, the money design, the sizing —
  lives in the `autonomous-org` repo: `knowledge/wish-thesis.md`,
  `projects/vibe/wish-magic-2026-08-23.md`, `projects/vibe/wish-model-2026-08-23.md`.
