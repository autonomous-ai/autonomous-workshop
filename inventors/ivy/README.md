# Ivy

Ivy is the canonical **holdable-science** inventor. She makes orreries,
pendulums, linkages, mathematical constructions, and physical explanations that
turn an abstract relationship into something a person can see and feel. Ivy is
a **taste-only** profile: she owns [`TASTE.md`](TASTE.md) and her identity;
Workshop supplies Make, Playtest, product Instructions, Deliver, artifact handling,
and durable runtime.

```text
creation:       Wish + Ivy's Taste -> Workshop Make <-> Workshop Playtest -> Instructions -> Deliver
after delivery: customer Reviews -> future Makes
```

## What Ivy owns

- A point of view about scientific truth, elegant geometry, interaction, and awe.
- Wish-specific parameters, cited sources, explicit units, and honest
  simplifications.
- The audience and product promise encoded in Taste.
- Future science-specific skills only after evidence shows the shared Workshop
  defaults cannot do the job.

Everything else begins with Workshop. A contributor should make Ivy more
recognizable by refining Taste, not by copying another inventor's harness.

## Profile commands

```bash
cd inventors/ivy
python3 -m pip install -e ../..
python3 profile.py profile
python3 profile.py wish tide-clock "I wish I could hold the tide cycle for our beach"
python3 profile.py preview tide-clock "I wish I could hold the tide cycle for our beach"
python3 profile.py run tide-clock "I wish I could hold the tide cycle for our beach" --playtest-rounds 6
```

The Workshop runner may wait for CAD, AI scientific review, simulation, images,
site, production, or carrier capabilities at their owning jobs. Waiting is
honest runtime state; Ivy never converts a model's confidence into observed
customer understanding. Exact printing and hands-on QA belong to Deliver;
customer comprehension and feedback arrive afterward as Reviews.
The optional `--playtest-rounds` value is checked from 1–100 and recorded with
the Wish rather than trusted from free-form text.
