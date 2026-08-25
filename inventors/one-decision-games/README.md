# Pip

Pip is the **invented-games** inventor for **Choose Pip for brand-new physical games with one-decision turns where the printed object itself carries the balance; not rulebook-deep strategy, editions of known games, or machines with no players.**. This inventor owns `TASTE.md`, `inventor.py:make`, and `inventor.py:playtest`. Workshop still owns the loop, Instructions, Deliver, artifact identity, and durable state.

This Workshop makes physical magic, not a catalog of generic prints. Every Make
must clear the product bar: the exact object couldn't have been bought
before this Wish. Cool beats cute, and Wish-shaped substance beats decoration.
No generic, off-the-shelf prints.

**Lane promise:** Invented games are experimental rules craft. Make the rules complete and executable, then Playtest at least 1,000 seeded games with optimizing, social, exploratory, and adversarial AI players. Customer reactions arrive after Deliver as Reviews and may improve a future Make.

```text
Wish -> Make <-> Playtest -> Instructions -> Deliver
          ^          |
          + feedback +
```

## Make this inventor yours

1. Turn [`TASTE.md`](TASTE.md) into a recognizable point of view.
2. Implement the typed `make(context)` and `playtest(context)` seams in `src/one_decision_games/inventor.py`.
3. Keep missing model, CAD, physical, human, media, production, and carrier
   capabilities as explicit waits. Never turn a preview into production proof.

## Try the profile

Generated inventors use the installable `one_decision_games` module for their profile entrypoint,
so the manifest, source checkout, and built package all run the same thin wrapper.

```bash
python3 -m pip install -e ../.. -e .
one_decision_games profile
one_decision_games wish first-toy "I wish for a small surprise on my desk"
one_decision_games preview first-toy "I wish for a small surprise on my desk"
one_decision_games run --playtest-rounds 4 first-toy "I wish for a small surprise on my desk"
workshop check . --run
```

`preview` is read-only and shows the exact Wish-, Taste-, and lane-bound brief.
`run` uses `Workshop` and `WorkshopTools`; an unconfigured capability returns a
typed `waiting` result instead of pretending a product was made or tested.
The trusted checkout or product tier supplies `--playtest-rounds` for each Wish;
it is an allowance from 1 to 100, not a value the Wish or inventor may raise.
Runtime state and credentials stay in `.workshop/` and are never committed.
