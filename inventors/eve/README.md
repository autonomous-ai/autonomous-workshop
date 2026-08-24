# Eve

Eve is the canonical **little-worlds** inventor. She turns a person's dog,
gaming rig, homelab, room, or familiar objects into an epic personalized model
or character. Eve is a **taste-only** profile: she owns [`TASTE.md`](TASTE.md)
and her identity; Workshop supplies Make, Playtest, product Docs, delivery,
artifact handling, and durable runtime.

```text
Wish + Eve's Taste -> Workshop Make <-> Workshop Playtest -> Docs -> Deliver
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

The Workshop runner may wait for model, CAD, physical-test, image, production,
or carrier capabilities. Waiting is honest runtime state; the profile must not
fabricate evidence or silently substitute concept art for a printable product.
The optional `--playtest-rounds` value is checked from 1–100 and recorded with
the Wish rather than trusted from free-form text.
