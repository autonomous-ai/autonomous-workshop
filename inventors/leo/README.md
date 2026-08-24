# Leo

Leo is the canonical **invented-games** inventor. He demonstrates Workshop's
maximum customization level: Leo owns game-specific **Make** and **Playtest**;
Workshop owns the Wish boundary, Taste binding, durable run, artifact identity,
product Instructions, and Deliver effects. Known classics belong to Alice; Leo creates
rules and table play that did not exist before the Wish.

```text
creation:       Wish + Leo's Taste -> Leo Make <-> Leo Playtest -> Workshop Instructions -> Deliver
after delivery: customer Reviews -> future Makes
```

## What Leo owns

- The invention of rules, mechanisms, topology, and table-specific play.
- The custom Make implementation that returns exact Workshop `Made` artifacts.
- The custom Playtest loop that binds evidence and feedback to those artifacts.
- At least 1,000 seeded games across optimizing, social, exploratory, and
  adversarial AI players, with evidence-bound feedback returned to Make.

Playtest is the AI-player simulation loop. Physical production belongs to
Deliver; real customer feedback arrives afterward as Reviews and can improve a
future Make.

The typed custom seams intentionally return `waiting` until real
`MakeContext -> Made` and `PlaytestContext -> Playtested` adapters are installed.
This makes ownership explicit without pretending a legacy harness is integrated.

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
