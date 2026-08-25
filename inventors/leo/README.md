# Leo

Leo is the canonical **invented-games** inventor. His Taste guides rules and
table play that did not exist before the Wish; Workshop supplies the common
Make/CAD, AI Playtest, Instructions, Deliver, artifact identity, and durable
runtime. Known classics belong to Alice.

```text
creation:       Wish + Leo's Taste -> Workshop Make/CAD <-> Workshop Playtest -> Instructions -> Deliver
after delivery: customer Reviews -> future Makes
```

## What makes Leo's path special

- His Taste steers the invention of rules, mechanisms, topology, and
  table-specific play.
- At least 1,000 seeded games across optimizing, social, exploratory, and
  adversarial AI players, with evidence-bound feedback returned to Make.
- Shared Make/CAD and Playtest enforce that game-specific requirement. A caller
  may explicitly replace both workers when genuinely custom behavior is needed.

Playtest is the AI-player simulation loop. Physical production belongs to
Deliver; real customer feedback arrives afterward as Reviews and can improve a
future Make.

The optional typed seams fail closed when selected without real
`MakeContext -> Made` and `PlaytestContext -> Playtested` adapters. They are
overrides, not dependencies of the default path.

## Profile commands

```bash
cd inventors/leo
python3 -m pip install -e ../..
python3 profile.py profile
python3 profile.py wish first-game "I wish for a tense duel made for our table"
python3 profile.py preview first-game "I wish for a tense duel made for our table"
python3 profile.py run first-game "I wish for a tense duel made for our table" --playtest-rounds 10
```

`--playtest-rounds` is a checked 1–100 allowance recorded with the Wish. It is
not inferred from free-form prompt text, and increasing it never weakens the
AI-player evidence gate.
