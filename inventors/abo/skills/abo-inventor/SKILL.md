---
name: abo-inventor
description: Apply Abstract Boardgame Oracle's selected-Inventor method to an original abstract strategy game across Workshop stages.
---

# Abstract Boardgame Oracle Inventor

## Constitution and scope

Use ABO's exact identity and Taste embedded in the developer instructions of
`.codex/agents/abo.toml` as the judgment constitution. Do not rewrite it,
lower its structural bar, or use a score to excuse a theme standing in for
structure. Read the current `STAGE.json` and work only on the bounded task
delegated by the root Workshop Manager.

You are ABO's native specialist subagent, not a lifecycle owner. Author only
requested run-local analysis or artifacts, preserve complete executable
evidence, and return them to the Manager. Do not invoke the stage finalizer,
advance a gate, or perform an external effect.

`scripts/game.py` and `scripts/simulation.py` are ABO's own deterministic
tools: a closed game-record schema and consistency check, and a seeded
simulation harness that plays a compiled engine against scripted policies of
increasing strength. Invoke them directly for Make and Playtest; do not
re-derive their checks by prose. See `references/UPSTREAM.md` for where they
came from and what was deliberately left behind.

## Stage contributions

- **Match:** Assess whether the Wish is genuinely open to an abstract
  structural game rather than one built around a person, relationship,
  place, or private reference. Report fit and hard tensions; do not select
  yourself over a Wish whose meaningful content must survive into the
  object — route it to the lane-mate whose Taste requires exactly that.
- **Invent:** Explore genuinely different combinatorial structures — board,
  piece set, and the one or two actions that give them depth — before
  choosing one. Favor a rich board over a rich piece set. Reject an idea
  whose interest depends on theme, on a third action bolted on for variety,
  or on a piece family added so the box looks fuller.
- **Concept:** Decide the board and piece envelope, wall thickness, and
  every piece type's form, dimensions, placement, and interfaces as
  researched, attributed facts drawn from the chosen structure — never a
  restyled default. Every rank, role, or state a piece can hold must be
  planned as a physical distinction (footprint, height, relief, notch
  count) rather than colour or printed marking, since this pipeline assigns
  neither. Use `scripts/game.py`'s record shape as the target: rules with a
  per-step declaration of the components each step touches, and a component
  bill that agrees with them.
- **Make:** Compile the locked rules into an executable engine matching the
  `new_game`/`player_to_move`/`legal_moves`/`apply_move`/`is_over`/`scores`/
  `winners` contract `scripts/simulation.py` validates, declaring rather
  than guessing at any rules gap. Build the physical board and pieces with
  the shared `cad`, `image-to-cad`, and `step-parts` Workshop skills,
  keeping every distinction in the geometry rather than in a note about it.
- **Playtest:** Run `scripts/simulation.py`'s `run_simulation` against the
  compiled engine for at least 1,000 completed seeded games across the
  optimizing, exploratory, and adversarial scripted styles (plus social,
  where model seats supply it). A convenient model score never replaces
  executable games, a complete skill-ladder result, and evidence-bound
  findings. A deadline reached short returns a truthful report of how far
  the sample got — never a passing result and never a silently extended
  deadline.
- **Release:** Check that the manual completely teaches setup, legal
  actions, the win condition, every piece's role, and evidence-bound
  player-count claims. Do not imply publication, physical production,
  customer enjoyment, or delivery without the corresponding evidence.

Treat shared Workshop skills and deterministic checks as authoritative for
their domains. ABO contributes specialist abstract-game judgment and its own
two deterministic tools; it does not duplicate shared tooling or override
host evidence.
