# Eve

Eve is the canonical **little-worlds** inventor. She turns a person's dog,
gaming rig, homelab, room, or familiar objects into an epic personalized model
or character. Eve is a **taste-only** profile: she owns [`TASTE.md`](TASTE.md)
and her identity; Workshop supplies Invent, Make, Playtest, product Instructions,
Deliver, artifact handling, and durable runtime.

```text
creation:       Wish + Eve's Taste -> Invent -> Make <-> Playtest -> Instructions -> Deliver
after delivery: customer Reviews -> future Makes
```

This folder was created fresh for little worlds. It does not restore or reuse
the earlier Eve prototype.

## What Eve owns

- A point of view that makes a real, consented subject recognizable and epic.
- The bar that personalization lives in geometry, layout, and relationships,
  not a caption or nameplate.
- The audience and the product promise encoded in Taste.
- Future niche skills only when the shared Workshop genuinely cannot express
  the needed character work.

Everything else begins with the shared Workshop defaults. A new contributor
should change `TASTE.md` before adding code.

## Profile commands

```bash
cd inventors/eve
python3 -m pip install -e ../..
python3 profile.py profile
python3 profile.py wish rig-world "I wish my gaming rig were an engine room"
python3 profile.py preview rig-world "I wish my gaming rig were an engine room"
python3 profile.py run rig-world "I wish my gaming rig were an engine room" --playtest-rounds 4
```

The Workshop runner may wait for model, CAD, AI Playtest, image, site,
production, or carrier capabilities at their owning jobs. Waiting is honest
runtime state; the profile must not fabricate evidence or silently substitute
concept art for a printable product. Physical production and QA belong to
Deliver; customer feedback begins after delivery as Reviews.
The optional `--playtest-rounds` value is checked from 1–100 and recorded with
the Wish rather than trusted from free-form text.
