# Create the sealed showcase drafts

`tools/publish_showcase_products.py` creates **private Factory model drafts** from
the five checked-in toy bundles. This is the shared Workshop Instructions
handoff: it derives a model-only Pack from the exact Make, includes structured
facts and attribution, and finishes only after authenticated readback proves
the canonical design is still a private draft. It uploads no local marketing
images and writes no final page copy.

Every showcase seals `artifact/assembled.stl` as an exact byte alias of its
Playtested `artifact/cad/product.stl`. Factory therefore renders the assembled
toy instead of guessing among nested part meshes. The shared handoff also sends
a bounded factual story prompt derived from the sealed Wish, description,
components, design facts/specifications, rules/instructions, optional story and
art direction, limitations, and inventor credit; Factory still owns the resulting page copy and media.

The tool never calls Factory's `/publish` endpoint. Making a reviewed draft
public is an explicit owner action outside the Workshop pipeline.

The tool does not run Make, Playtest, CAD generation, or the game simulator. It
verifies the exact artifact, AI Playtest evidence, and Instructions seals before
any remote effect.

Provide both credentials through the process environment or a secret manager:

- `WORKSHOP_SHOP_TOKEN` — Shop bearer token
- `WORKSHOP_SHOP_OWNER_ID` — expected owner of every authenticated readback

Do not put either value in this repository, a command-line argument, or a log.

Create Alice's draft first:

```bash
python3 tools/publish_showcase_products.py --only alice --verify-draft
```

`--only` also accepts a toy slug and may be repeated. After reviewing Alice's
result, create all five drafts by omitting it:

```bash
python3 tools/publish_showcase_products.py --verify-draft
```

Every imported description ends with the inventor attribution already sealed
in the bundle, such as `By Alice.` or `By Bob.`

Before the first import, the tool makes an authenticated lookup for the exact
canonical slug. Only a `404` permits import; an existing slug or an uncertain
response stops without creating a collision-suffixed duplicate. A successful
receipt must return that exact slug.

Each toy keeps its durable Instructions outbox here:

```text
.runtime/showcase-publication/<toy-slug>/workshop.sqlite3
```

`.runtime/` is ignored by Git. Keep this state between retries: completed
imports and draft readback are replayed from the ledger instead of being sent
twice. If an effect has an uncertain outcome, the
tool stops rather than guessing or duplicating it.

An authenticated exact draft readback records the model handoff and moves the
checked-in Workshop run to its truthful Deliver wait. `workshop-run.json`
records the draft receipt and canonical owner-visible page URL while keeping
`site_page_live` false. The receipt also keeps `enrichment_status=pending` and
`page_ready=false`: Factory images, copy, or video require separate confirmed
enrichment and are not promised by this command. The toy README says that the
draft still awaits owner review and the explicit public flip. `--verify-draft` adds one more fresh
authenticated GET after a successful draft or durable replay.

The backend's immutable project CDN URL remains separate from the canonical
product page (`https://www.autonomous.ai/factory/product/<slug>`). That page may
require the owner session until the draft is made public.
