# Inventors

Each immediate subfolder is one inventor or reviewed reference snapshot. It
contains that inventor's complete code, `inventor.json`, `TASTE.md`, operating guide, tests,
creative thesis, and niche-specific adapters. `TASTE.md` is the inventor's
human-owned creative constitution: agents read it, outcomes may motivate a
proposed revision, and self-improvement code cannot rewrite it. Inventors may depend on
[`../workshop`](../workshop/README.md); Workshop never imports an
inventor.

| Inventor | Focus | Status |
|---|---|---|
| [Alice](alice/) | books-and-history-informed printable board games | autonomous, blocked on authenticated production adapters |
| [Bob](bob/) | budgeted multi-agent printable board-game invention | experimental |
| [Eve](eve/) | printable board games with a great-books loop | experimental |
| [text2cad](text2cad/) | trend-driven printable mechanisms and products | reference snapshot |
| [text2game](text2game/) | end-to-end FDM board-game creation | human-checkpointed |
| [vibe-ideas](vibe-ideas/) | deep playtest and CAD workflow | reference snapshot |

Create the next inventor from the repository root:

```bash
python3 -m pip install -e workshop
workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --root inventors
```

The command writes `inventors/deduction-games/`. Reuse Workshop's Clockwork,
Make, Inspect, Pack, Send, and Door machinery; keep the new inventor's
Taste, prompts, generators, evaluators, and reward hypothesis in its own folder.
