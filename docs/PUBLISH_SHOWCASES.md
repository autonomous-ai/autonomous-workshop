# Publish the sealed showcase toys

`tools/publish_showcase_products.py` publishes the checked-in toy bundles. It
does not run Make, Playtest, CAD generation, or the game simulator. It verifies
the exact artifact, AI Playtest evidence, and Instructions seals, then sends
those bytes through the shared Instructions publisher.

Provide both credentials through the process environment or a secret manager:

- `WORKSHOP_SHOP_TOKEN` — Shop bearer token
- `WORKSHOP_SHOP_OWNER_ID` — expected owner of every authenticated readback

Do not put either value in this repository, a command-line argument, or a log.

Publish Alice first:

```bash
python3 tools/publish_showcase_products.py --only alice --verify-live
```

`--only` also accepts a toy slug and may be repeated. After checking Alice,
publish all five by omitting it:

```bash
python3 tools/publish_showcase_products.py --verify-live
```

Before the first import, the tool makes an authenticated lookup for the exact
canonical slug. Only a `404` permits import; an existing slug or an uncertain
response stops without creating a collision-suffixed duplicate. A successful
receipt must return that exact slug.

Each toy keeps its durable publication outbox here:

```text
.runtime/showcase-publication/<toy-slug>/workshop.sqlite3
```

`.runtime/` is ignored by Git. Keep this state between retries: completed
imports, image uploads, page copy, and publication are replayed from the ledger
instead of being sent twice. If an effect has an uncertain outcome, the tool
stops rather than guessing or duplicating it.

The shared publisher always requires an authenticated public readback before it
records the canonical customer page
(`https://www.autonomous.ai/factory/product/<slug>`) in `workshop-run.json` and
the toy README and moves the checked-in run to its truthful Deliver wait.
`--verify-live` adds one more fresh authenticated GET after a successful publish
or durable replay. The backend's immutable project CDN URL remains separate
from the customer page.
