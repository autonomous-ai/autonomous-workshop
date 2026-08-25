# Pip

Pip is an **invented-games** inventor for brand-new physical games with
one-decision turns, where the printed object itself carries the balance and
the drama — not rulebook-deep strategy, editions of known games, or machines
with no players. Pip owns `TASTE.md`, `inventor.py:make`, and
`inventor.py:playtest`. Workshop still owns the loop, Instructions, Deliver,
artifact identity, and durable state.

```text
Wish -> Make <-> Playtest -> Instructions -> Deliver
          ^          |
          + feedback +
```

## Thesis and audience

Grown-ups (14+) playing face to face. A Pip game teaches in one breath (rules
on a card, one decision per turn) and gets its depth from the printed object:
geometry, mass, and tolerances are the game design. When a playtest finds an
imbalance, Pip reshapes the part — never patches fairness with point tables
or compensating rule text. Output is recognizable without a logo by exactly
that: a table-legible physical mechanism, a one-card rulebook, endings the
object declares by itself.

## Workflow: the text2game bridge

Pip's craft runs in the **text2game** pipeline, an operator-run toolchain
(game design rounds with an AI critic and referee -> build123d CAD with a
contract gate -> fit probes -> slicing under a pinned PETG profile). A
completed run lives at `<TEXT2GAME_ROOT>/out/<slug>/`; `TEXT2GAME_ROOT`
defaults to `/root/text2game`.

- **Make** (`custom-make`): adopts the run whose slug equals the Wish
  `product_id` and imports its exact bytes as the product artifact — rules
  (`gdd.md`, `rulebook.md`, `components.json`), part sources (`parts/*.py`,
  `export_all.py`), CAD (`assembled.step`), meshes (`fe_parts/*.stl`), and
  assembly data (`parts_index.json`, `part_colors.json`). Gcode and pipeline
  logs stay behind. A missing pipeline, missing run, or post-feedback
  revision is a typed wait naming the exact operator command — pipeline
  rounds cost real money and are never launched implicitly.
- **Playtest** (`custom-playtest`): binds the same run's recorded verdicts as
  artifact-bound evidence — `agent-playtest` from the referee/critic/evaluator
  rounds (`phase1.json`, `referee.md`), `mechanical-test` from the CAD
  contract gate and fit probes (`gate.json`, `fit.json`), `print-test` from
  the slicer report (`slice_report.json`). Pip's referee bar is asymptotic:
  a kept design round passes, and open findings ride along as non-blocking
  note feedback destined for the print kit's watch-at-the-table list.

## Evidence classes and the honest gaps

Every result is sealed as its own byte-exact JSON document naming the exact
Make bytes and the AI roles that produced it. Against the Workshop's release
bar, text2game can fully prove **`agent-playtest`** today; the other three
lane proofs are typed waits until the pipeline grows them:

- **`game-simulation`** needs >= 1,000 seeded traces across optimizing,
  social, exploratory, and adversarial players plus a sealed simulator and
  analysis — the referee plays a handful of deep games per round, not a
  thousand.
- **`mechanical-test`** needs motion, load, and failure-mode case evidence —
  the contract gate measures watertightness, bodies, and fit only.
- **`print-test`** needs per-part G-code receipts under at least three
  pinned profiles — text2game slices once under one PETG profile.

So a real Pip run imports the product, seals the referee/gate/slicer
verdicts, and parks at Playtest with exactly those needs. Nothing is
invented to get past the bar; each need names the pipeline stage to build
next. The upstream Invent stage is Workshop-owned and shared: without an
operator-configured Invent provider a run truthfully waits at `invent`
before Pip's seams are reached.

## Try the profile

```bash
python3 -m pip install -e ../.. -e .
one_decision_games profile
one_decision_games preview last-road-out "I wish for a magnetic gravity race"
one_decision_games run last-road-out "I wish for a magnetic gravity race" --playtest-rounds 2
workshop check . --run
```

`preview` is read-only and shows the exact Wish-, Taste-, and lane-bound
brief. `run` imports and playtests an existing pipeline run; every missing
capability returns a typed `waiting` result instead of pretending a product
was made or tested. The trusted checkout or product tier supplies
`--playtest-rounds` per Wish (an allowance from 1 to 100, not a value the
Wish or inventor may raise). Tests run offline against a synthetic fixture
run — no credentials, network, CAD service, or paid provider. Runtime state
stays in `.workshop/` and is never committed.
