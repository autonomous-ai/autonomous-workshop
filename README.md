# inventors

Autonomous AI inventors — each one a self-contained multi-agent system with a
name, a niche, and a 24/7 loop. An inventor studies its field, invents,
iterates against a frozen reward function, publishes to the Factory
marketplace as an AI creator, and gets better every week.

| Inventor | Niche | Status |
|---|---|---|
| [bob/](bob/) | 3D-printable board games | building |

Prior art that shaped this repo (sibling experiments, personal repos):
[reinSPQR/vibe-ideas](https://github.com/reinSPQR/vibe-ideas) (board-game
pipeline: 6 ideas → 1 shipped), [nohope88/text2cad](https://github.com/nohope88/text2cad)
(trend→product daily loop: 18 cycles / $430 → 1 shipped),
[peterat617/text-to-3d](https://github.com/peterat617/text-to-3d) (CAD skills,
budget + likeness patterns). Bob is the third-generation attempt, built on
their receipts — see `bob/docs/research/`.

House rules for every inventor:

1. **The evaluator is the product.** Frozen reward code, checksummed;
   generators never see the scoring internals.
2. **Budgets live in code, not prompts.** An agent that can read its own
   budget will negotiate with it.
3. **Files are the message bus.** Every loop reads and writes artifacts;
   no agent-to-agent chat.
4. **External reward outranks self-scores.** Sales, human "play it again",
   owner verdicts — never a rubric the loop can flatter.
5. **AI creators publish as themselves.** Own account, disclosure on every
   listing, never under a human's name.
