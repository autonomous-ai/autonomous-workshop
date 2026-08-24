# Inventors

Each immediate subfolder is one inventor or reviewed reference snapshot. It
contains that inventor's complete code, `inventor.json`, `TASTE.md`, operating guide, tests,
creative thesis, and niche-specific adapters. `TASTE.md` is the inventor's
human-owned creative constitution: agents read it, outcomes may motivate a
proposed revision, and self-improvement code cannot rewrite it. Inventors may depend on
the shared [Workshop root](../README.md); Workshop never imports an
inventor.

| Inventor | Focus | Status |
|---|---|---|
| [Alice](alice/) | books-and-history-informed printable board games | autonomous, blocked on authenticated production adapters |
| [Bob](bob/) | budgeted multi-agent printable board-game invention | experimental |
| [text2cad](text2cad/) | trend-driven printable mechanisms and products | reference snapshot |
| [text2game](text2game/) | end-to-end FDM board-game creation | human-checkpointed |
| [vibe-ideas](vibe-ideas/) | deep playtest and CAD workflow | reference snapshot |

Create the next inventor from the repository root:

```bash
python3 -m pip install -e .
workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --root inventors
```

The command writes `inventors/deduction-games/`. Give the inventor a Wish
boundary, its own Taste, and niche-specific Make and Inspect work. Reuse the
Workshop's artifact handling, durable runtime, and adapters instead of creating
new branded stages for those implementation details. Keep prompts, generators,
evaluators, and the reward hypothesis in the inventor folder.
