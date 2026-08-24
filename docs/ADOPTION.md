# Workshop 0.5 adoption

Autonomous Workshop 0.5 is the shared Toy Workshop for playthings for grown-ups
(14+). Its product journey is exactly:

```text
Wish -> Make <-> Playtest -> Docs -> Deliver
             feedback
```

This page records what the five canonical profiles can do **now**. A valid
profile or passing offline test is not a claim that its model, physical
playtest, printer, product-page, or carrier capability is live.

## Current profiles

| Profile | Category | Customization level | Truthful 0.5 status |
|---|---|---|---|
| Alice | classics made yours (`classics-made-yours`) | Taste only | Alice deliberately demonstrates the minimum extension level and delegates Make and Playtest to shared tools. Her Blindcap laboratory is provenance that taught Workshop, not her active profile or a second invented-game elf. |
| Leo | games that don't exist yet (`invented-games`) | custom Make + custom Playtest | Leo owns the sole invented-game category. He waits honestly at unfinished typed adapter and independent-human-table boundaries; simulations cannot release his games. |
| Bob | machines that move (`moving-machines`) | custom Make | His profile, machine Taste, Wish, preview, and typed seam work. A run waits at Bob's typed custom-Make seam; the preserved board-game laboratory is not a moving-machine Make adapter. |
| Ivy | science you can hold (`holdable-science`) | Taste only | Her science profile delegates Make and Playtest to shared tools. Without configured shared model/CAD and scientific-evidence tools, a run truthfully waits at Make or Playtest. |
| Eve | little worlds (`little-worlds`) | Taste only | Her fresh personalized-world profile delegates Make and Playtest to shared tools. Without configured shared tools, a run truthfully waits at Make. This profile does not restore the old Eve implementation. |

All five categories share the same bar: the result could not have been
downloaded before the Wish; cool, clever, or striking beats merely cute or
twee; and personalization plus design intelligence must do more than decorate a
generic print. Kits and numbered series are later product variants, not current
profiles, jobs, or V1 promises.

Invented games have one additional non-negotiable release gate: an independent
human table must play the exact game and want another play. AI simulations are
diagnostic evidence only; 1,000 passing simulations do not release a game.

Leo and Bob are blocked at their unfinished custom typed seams. Alice, Eve, and
Ivy are Taste-only and wait for real shared capabilities when those are not
configured. Mature legacy code remains useful migration material, but it is not
silently invoked through a canonical profile. That separation prevents an
apparently successful run from crossing an unreviewed artifact or evidence
boundary.

Alice, Eve, and Ivy demonstrate the smallest adoption level: the inventor owns
`TASTE.md`; Workshop owns Make, Playtest, the improvement loop, Docs, Deliver,
artifact identity, and runtime. “Taste only” means the profile is wired to
shared capabilities—not that those external capabilities are bundled,
credentialed, or proven live in this checkout.

## What is shared today

All five profiles use the same 0.5 contracts for:

- bounded Wishes that preserve the person's words;
- exact, human-owned Taste bytes and SHA-256 identity;
- one of the five Workshop product categories;
- the `MakeContext -> Made` and `PlaytestContext -> Playtested` seams;
- actionable Playtest feedback and bounded immutable rounds;
- typed `Need` and `WaitingFor` results instead of fabricated success;
- content-addressed product, evidence, and Docs identities;
- the shared Docs and Deliver boundaries;
- durable state, leases, and a recorded per-Wish Playtest allowance.

The platform operator still has to install real shared tools. A complete live
path needs, as applicable, authenticated model and CAD workers, executable AI
players, independent reviewers, a pinned slicer and printer profile, exact
physical prototypes, independent human playtests, a product renderer or photo
pipeline, production QA, packing, and USPS/UPS/FedEx integration.

Missing tools remain a `waiting` result. Simulation does not become human-fun
evidence; slicer output does not become a physical print; concept art does not
become a product photograph; a generated label does not become carrier handoff.

## Per-Wish Playtest allowance

The Workshop default can be overridden by a trusted service boundary for one
Wish:

```python
result = workshop.run(wish, playtest_rounds=6)
```

`playtest_rounds` must be an integer from 1 through 100. Workshop records it
with the Wish and exposes it to custom Make and Playtest contexts. It is the
maximum number of Make–Playtest improvement rounds, not the number of AI games
inside a round.

The checkout, quote, or product tier may select the allowance. Free-form Wish
text cannot authorize spend or raise it. A larger allowance buys more chances
to find and repair problems; it **never changes required evidence, weakens a
gate, lowers a threshold, or permits Docs and Deliver after failure**. When the
allowance is exhausted, the run stops truthfully.

## Preserved laboratories are provenance

Alice's invented-game laboratory already has stronger local leases, evidence,
release, physical-production, and effect-reconciliation machinery. Bob's
preserved board-game laboratory has useful queue, research, budget, simulation,
reward, draft, and readback behavior. Both also exercise older shared artifact
and outside-effect boundaries.

Those facts are evidence for Workshop's extracted workflow, not proof of 0.5
adoption and not active category ownership. Alice's canonical classics profile
does not invoke Blindcap. The custom profiles that still need strict typed jobs
wait explicitly:

```text
Leo: MakeContext -> Made -> PlaytestContext -> Playtested   WAITING
Bob: MakeContext -> Made                                    WAITING
```

Each bridge must preserve exact Taste, product, evidence, tool-version, budget,
and external-effect identities. Until golden fixtures show parity, the legacy
laboratory remains separate and any stronger invariant stays in place.

Some native files, commands, database columns, and event payloads retain older
terminology. They remain only because renaming persisted operational state can
break replay or create a second authority. They are not additional 0.5 jobs.

The text2cad, text2game, and vibe-ideas projects remain research provenance for
shared Workshop decisions. They are not canonical elves, do not occupy product
categories, and should not appear as inventor folders or manifests.

## What offline checks prove

The repository checks prove contracts and fail-closed behavior without paid
providers. They cover profile discovery and entry points, exact Taste and
artifact binding, truthful waits, per-Wish allowances, feedback loops,
tamper rejection, schema and skill locks, credential exclusion, and ambiguous
outside-effect handling.

They do **not** prove that a real product was invented, enjoyed, printed,
published, packed, handed to a carrier, or delivered.

Run the shared checks from the repository root:

```bash
python3 tools/scan_secrets.py
python3 tools/verify_skill_locks.py
python3 tools/verify_snapshot_locks.py
workshop inventors --root inventors --check-entrypoints
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Then run each profile's declared checks. No offline check should require a
model credential, catalog credential, printer, carrier, or paid service.

## Next adoption slices

1. Keep Alice's classics profile Taste-only and prove shared Make and Playtest
   can preserve known rules while producing a genuinely personal edition.
2. Implement Leo's invented-game `Made`, `Playtested`, and `Feedback` adapters,
   including the independent-human-table replay gate.
3. Implement Bob's new moving-machine `MakeContext -> Made` path; do not route
   machine Wishes into the preserved board-game laboratory.
4. Configure and test shared Make and Playtest tools for the Taste-only
   profiles.
5. Rehearse one exact Wish per category through truthful waiting, then through each
   real capability as it becomes available.
6. Enable Docs and Deliver only after exact product, physical, human,
   production, and carrier evidence can support their claims.

The target architecture is not a claim about current completeness. Adoption is
complete only when the canonical profile crosses every typed boundary with the
same or stronger evidence than the code it replaces.
