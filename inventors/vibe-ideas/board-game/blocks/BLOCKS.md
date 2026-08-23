# Golden blocks — board-game geometry

**Compose from these first. Hand-build only what they do not cover.**

Two libraries are in play and they do not overlap:

- `cadlib` (shipped with the cadcode skill) owns the generic vocabulary —
  `grid_points`, `slot_for`/`peg_for`, `add_dovetail_slot`,
  `add_press_fit_pocket`, `hollow_box`, `soften_edges`. Reach for it for
  anything that is not specific to board games.
- `blocks.py` (this directory) owns the board-game layer, and only patterns
  this project has **evidence** for.

## Policy

`blocks.py` is human-approved. An agent may *propose* a block as code plus a
testbench case, through a PR; it may not add one by editing the file. This is
deliberate and it is the one place in the pipeline where the LLM's authority
is narrowest, because a wrong block is wrong silently in every design that
composes it afterwards.

`testbench.py` must print ALL PASS before any change here is kept. It does not
inspect the library's internals — it writes a real project per block, builds
it through cadcode, and requires the same `GATE PASS` that products must earn.
When a threshold in `gate.py` tightens, the blocks re-earn their place.

## The blocks

| Block | What it is for | Evidence behind it |
|---|---|---|
| `shared_positions` | Generate a pattern **once** and feed the same list to every layer that must line up | t14 `cross_positions()` and t15 `small_centers()` — both turns' only clean structural passes, both praised independently for making alignment correct by construction |
| `add_piece_family` | Place N copies as **separately named** assembly children | The failure that ended t11–15: 48 tiles arriving as one mat, 65 pieces collapsing into one solid. `gate.py`'s bill check counts exactly these names |
| `cut_wells` | A seat a hand can actually get a piece out of — thumb scallop on by default | t15 Sluice Row: 7mm seeds on the floor of 26mm×16mm wells, 9mm below the rim. Every geometric check passed |
| `seated_pair` | One nominal in, both halves of the mate out | t14 shipped a bill saying 10mm against a threshold implying 11.4mm. Also caught a 4×-clearance drift bug **inside this very function** on its first commit |
| `tiled_board` | Split a board too big for the bed into interlocking tiles | Not a failure but a constraint: P2S caps any piece at 246mm and t15's board was 366mm |

## Using a block

Blocks are **copied into the project**, never imported across the repo:

```python
# board-game/ideas/<slug>/project/blocks.py   <- a copy
from blocks import shared_positions, add_piece_family, cut_wells
```

A shipped project has to keep building years later, after the library has
moved on. A project that imports a live library is a project whose geometry
can change without anyone editing it.
