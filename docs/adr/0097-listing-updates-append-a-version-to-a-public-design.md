# ADR 0097: A Listing Update appends a version to a public Factory design

- **Status:** Accepted on 2026-11-06. It was proposed the same day, and the
  owner answered its open questions then (§ Owner decisions).
- **Implementation:** see § Implementation status. That section is the
  current account of what is built.
- **Amends:** [ADR 0065](0065-published-toy-correction-runs.md). Its rule that
  a correction run publishes a new design stays the default; this ADR adds an
  opt-in alternative.
- **Builds on:**
  - the direct publish tool (`docs/PUBLISH_DIRECT.md`);
  - its non-printed-bodies fix (#219), which strips props and bought hardware
    from the STEP Factory weighs and bills the hardware as extra materials;
  - the refusals of #221 and autonomous-product-to-cad#3.

## Context

Three toys are live and billed wrongly: the lamp-post headphone stand, the
palm bud vase and the otter pen cup. Their primary STEP still carries props
and bought hardware, and Factory weighs every solid as filament. The
2026-11-06 audit weigh of the lamp is an example:

- the whole scene weighs 494.73 g;
- the printed parts weigh 225.49 g;
- the headphones prop alone weighs 253.05 g.

The owner wants these listings repriced in place: same listing, same URL.
Before this ADR every path that tried refused:

| Path | What happens |
|---|---|
| `tools/publish_direct.py --reimport-slug` | refused |
| product-to-cad `scripts/publish --reimport` | refused |
| `--archive` of a published toy | refused |
| `--cad-dir` of a toy published under another product id | refused (#221 / p2c#3) |
| `--cad-dir` under the same product id with changed bytes | refused by the effect ledger |
| `workshop fix` | publishes a new design (ADR 0065) |

### What Factory already offers

This is from panda-social-backend at `aea8c67`. Paths are relative to that
repository.

**The version route:**

- `POST /designs/:slug/import` (`apis/router.go:216`, handler
  `apis/handlers_import.go:134-193`, service
  `services/import_version.go:53-208`) appends a version to an existing
  design.
- It needs a bearer token whose user can write the design
  (`services/design_admin.go:82-90`). Another user gets 403 on a public
  design. An active generation job on the design gets 409
  (`import_version.go:62-64`).
- It takes `file`, plus optional `usage` and `extra_materials`.
- It refuses `title`, `description`, `category`, `tags`, `status` and
  `license` with a 400, because metadata belongs to `PATCH /designs/{slug}`
  (`handlers_import.go:143-148`). So the slug and URL cannot change through
  this route.
- `extra_materials`:
  - when absent, the current list stays;
  - when `[]`, the list is cleared (`import_version.go:44-48`).

**What it does:**

- It writes a new immutable `design_history` folder and moves
  `current_history_id` to it (`import_version.go:182-186, 221-244`).
- On a public design the version is published at once. There is no draft
  step: `SetPublished` runs and re-stamps `published_at`
  (`import_version.go:217-220, 258-271`; `repo/design.go:47-62`).
- It replaces the covers when the zip carries one.
- It replaces `print_overrides` from the new `project.json`. Without
  overrides, infill falls back to the shop's 15 %
  (`import_version.go:235-243`).
- It queues a slice (`import_version.go:255`).
- It writes `extra_materials` best-effort. A failure is only logged, and the
  call still returns 200 (`import_version.go:282-295`).
- **No idempotency:** the backend has no `Idempotency-Key` handling, so a
  retried POST appends a second version.

**The extras route:**

- `PUT /designs/:slug/extra-materials` (`apis/router.go:236`,
  `apis/handlers_design_extra_materials.go:57-72`,
  `services/design_extra_materials.go:22-54`) replaces the whole list. It is
  open to the owner.
- It does not touch `updated_at`.
- It reprices a platform-priced listing at once against the **last
  measurement**.
- Because it replaces the whole list, sending it again changes nothing.

**A second create does not update anything.** It creates a new design.
`Slugify` keeps `[a-z0-9-]` (`services/slug.go:28-47`), and a taken slug gets
a random `-xxxx` suffix (`slug.go:91-131`).

**Price.** Per unit (`models/slice_job.go:135-217`):

```text
material = ceil(grams × 5.2) cents                  (4.0 print + 1.2 freight/duty, per gram)
cost     = material + 1500 (operations) + 0 (packaging) + Σ extras.price_cents
price    = cost rounded up to the whole dollar      (margin 0 % since 2026-11-02)
           clamped to 100 … 1,000,000 cents         (services/listing.go:26-27, listing_pricing.go:209-225)
```

- **Mass:** Orca's support-on mass at the shop's 15 % infill or the design's
  override, measured on a bounded bed first and on an unbounded bed if a part
  does not fit (`services/slice_worker_engines.go:80-115`).
- **Extras:** an extra material is `{name, price_cents, material}` with no
  count, at most 20 entries (`models/design_extra_material.go:43-65`).
  Workshop's adapter already folds count × unit price into one entry.
- **The listing** belongs to the design, not to a version
  (`models/design.go:62, 344-352`).
- **Repricing:** `RepriceOnMeasurement` (`services/listing_pricing.go:59-143`)
  reprices a `measured` or `estimate` listing when a slice lands or the
  extras change. A listing priced by hand is never moved; it is only paused
  if it falls below the new floor.
- **Failure:** a slice that fails for good pauses a platform-priced listing
  (`listing_pricing.go:167-201`).

**Readback and orders:**

- `GET /designs/:slug` returns `current_history_id`,
  `published_history_id`, `project_url`, `print_specs`, the resolved
  `print_settings`, `extra_materials` and `listing.{sku, price_cents,
  active}` (`apis/responses_design.go:73-215`).
- It does **not** return the listing's `priced_from`, which is `json:"-"` at
  `models/design.go:93`. So a reader cannot tell a price set by hand from one
  Factory has not repriced yet.
- `GET /designs/:slug/slice` (`apis/handlers_slice.go:97-110`) returns the
  current version's slice job, owner only: its `history_id`, `status`
  (`queued`, `slicing`, `done` or `failed`), `will_retry` and
  `totals.weight_g`.
- The listing SKU never changes, and orders key on it, not on a version
  (`services/listing.go:150-195`).

**Workshop already has the client side.** `FactoryClient.import_model_version`
(`src/workshop/integrations/factory.py:1664`) and the
`factory-import-version` ledger kind serve root repair of a still-private
draft. That path refuses a public design ("Factory root repair cannot change
a public design").

## Owner decisions (2026-11-06)

1. **`workshop fix` defaults are unchanged.** It still creates a new design.
   `--update-listing` is opt-in.
2. **Allowed reasons are `fix` and `reprice` only.** A changed print
   override, such as infill, is a `fix`, not a `reprice`.
3. **Re-floating is acceptable.** Re-floating in Factory's "latest
   published" feed after an update is fine.
4. **Confirm each update's price.** Before any update the command shows the
   listing's current price and the predicted new price. It runs only after
   the owner confirms that one run. There is no blanket override, because
   hand-set prices cannot be detected.
5. **No mixed interim price.** Bought-part extras are sent only after the
   new version's slice has landed. A price computed from the old mass and
   the new extras is never shown.
6. **Backend requests go into this ADR** as a list for the backend team
   (§ Requests to the backend team). Workshop does not wait for them.
7. **The palm vase's `unknown` publish intent** is reconciled by Factory
   readback only. Nothing new is sent.
8. **Buyers do not see version history.** It lives in the archive and the
   ledger only.

## Decision

### 1. When a Listing Update is allowed

A **Listing Update** appends one version to a public Factory design that this
Workshop published. All of these must hold:

- **The design is proven to be ours.**
  - A toy archive's `PUBLICATION.json` records the design's slug and page.
  - A local ledger receipt for that slug names its `design_id`.
  - Preflight readback shows the same `design_id` and slug, a public status,
    the Inventor's account as author, and no running generation job.
  - Without a local receipt the update is refused. A record copied from
    another machine is not proof.
- **The owner asks for this update and confirms its price.** It is never
  automatic. `--update-listing SLUG` is required, and the SLUG must equal the
  archive's slug. `--live` also needs the confirmation code from that run's
  preview (§ 5).
- **The reason is one of two:**
  - `fix`: changed printed geometry or print settings, with the same gate
    evidence a create needs.
  - `reprice`: the same printed geometry and print settings, re-published
    only to correct what Factory weighs and bills (#219: the primary
    stripped of display-only and bought bodies, plus `extra_materials`).
    The host reads the live `assembled.step` from `project_url` and requires
    that, after the declared bodies are removed, its body names and each
    body's volume and area equal the new primary's. Nothing printed changes,
    so a reprice needs no new gate evidence. A changed infill override is a
    `fix`.
- **Nothing of the listing's identity changes.** That covers the title, slug,
  URL, description, category, tags and license, and Factory refuses them on
  this route anyway. A rename stays a separate, out-of-scope owner action
  through `PATCH`.
- **Drafts are not covered.** A draft is still root repair's job.

**The ADR 0065 amendment:**

- `workshop fix` still creates a new design by default.
- `workshop fix TOY --update-listing` freezes the run as unreleased, exactly
  like `--no-publish`, and records the source toy's slug as its target
  listing.
- The owner then runs `workshop publish <wish-id> --update-listing` to
  preview the price. Running it again with `--confirm CODE` performs the
  update with the bytes the run sealed.
- The run keeps its own Wish, session, budget and ledger, as ADR 0065 says;
  only its Release effect changes.

### 2. The effect

There is one host effect, in the Factory adapter
(`FactoryListingUpdate`). Credentials stay host-only, and no native agent
turn performs or sees it. It runs in four steps:

1. **Preflight read** (authenticated, read-only):
   - `GET /designs/{slug}`: `design_id`, status, author,
     `current_history_id`, `published_history_id`, `project_url`, the
     listing, `print_settings` and `extra_materials`;
   - `GET /designs/{slug}/slice`: the current version's measured
     `weight_g`, which must be `done` and belong to `current_history_id`;
   - for a reprice, the live `assembled.step` from `project_url`.
2. **Send the version.** `POST /designs/{slug}/import` with:
   - `file`: the same single-STEP Make-output handoff a create sends;
   - `usage`, when a Workshop run supplies it;
   - **no `extra_materials` field**, so the live list stays as it is until
     the slice lands (owner decision 5).

   The handoff's `project.json` carries the toy's print override, if it has
   one (#216). A version that would drop or change the live override is a
   `fix`; a `reprice` refuses it.
3. **Wait for the slice.** The host polls `GET /designs/{slug}/slice` until
   the job for the new `history_id` is `done`. It is bounded, and a later
   rerun resumes the wait.
4. **Set the extras.** `PUT /designs/{slug}/extra-materials` with the new
   list. Factory reprices from the new mass and the new extras at once.

Between steps 3 and 4 the listing briefly shows the new mass with the
previous extras. For the three repriced toys those are empty. The price
computed from the old mass and the new extras, which owner decision 5
forbids, is never shown. A backend request (§ Requests) would remove even
this short window.

### 3. Ledger and idempotency

- **Ledger kind.** The update reuses the existing `factory-import-version`
  kind rather than adding a kind. A new kind would need a migration of every
  live ledger file. The request carries a `listing_update` object, which
  holds:
  - the reason;
  - the base `current_history_id` and base price;
  - the base and predicted grams;
  - the confirmed code;
  - the new extras.

  Root repair keeps its own refusals. It still cannot change a public
  design.
- **Where it lives.** In the ledger of the product id that first published
  the toy, found by its receipt slug (as #221 does). A new ledger is never
  started under another id. For the palm vase that is
  `synthwave-palm-bud-vase`, not `r24-synthwave-palm-vase-taper`.
- **Intent identity.** Its request includes `design_id`, the base history id
  and the handoff pack SHA-256. The base history id makes the update a
  compare-and-swap. If the design's current version is no longer the base,
  the update refuses and asks the owner to look.
- **Several updates over time.** A succeeded `factory-import-version`
  intent no longer blocks a later one carrying `listing_update`. One that is
  `sending` or `unknown` still does, until it is reconciled.
- **No blind resend.** The send is never repeated without first proving the
  earlier one did not land.
- **The extras step.** `PUT` replaces the whole list, so sending it again is
  safe. Its success is recorded in the same intent's receipt only after
  readback.

### 4. Readback

The update succeeds only when all of this reads back:

1. `current_history_id == published_history_id`, a new id different from
   the base, the same `design_id`, slug and page URL, and a public status.
2. The publication anchor under the new `project_url` hashes to what was
   sent (`verify_publication_anchor`).
3. The slice job for that `history_id` is `done`, with its `weight_g`.
4. `extra_materials` equal what was sent.
5. The listing reads back active, with its `price_cents`.

The receipt records each of these, with the price and grams before and
after. If the price read back is not the one Factory's formula gives for the
measured grams and extras, the update is still recorded. It is reported as
`price not repriced (possibly set by hand)`, and it is not a failure.

### 5. Price preview and confirmation

`--update-listing` without `--live` is a **preview**. It is the one dry run
that reads Factory, with authenticated reads only, and it sends nothing. It
prints:

- **Current state:** the current listing price, the current measured grams
  and the current extras. It also says whether the current price equals the
  formula's price for those grams and extras. When it does not, the listing
  may have been priced by hand: the new price would then not follow, and new
  extras might pause it.
- **Prediction:** the new extras, from the catalogue as in #219, and the
  predicted price, computed with Factory's formula (§ Context) from the
  predicted grams and the new extras.
- **The confirmation code:** a short hash of the slug, `design_id`, base
  history, current price, current grams, predicted grams, predicted price,
  extras, reason and the new primary's printed-body measures.

**Predicted grams.** Factory measures mass only by slicing, after a version
is live. So the predicted grams come from `--predicted-grams G
--predicted-grams-source TEXT`, measured with Factory's own slice worker on
the printed-only primary. Without them the preview prints the predicted
price as unknown and gives no confirmation code, so `--live` refuses. There
is no geometry estimate: tested on the lamp, it came out 21 % heavy,
because supports dominate.

`--live --confirm CODE` recomputes the code from a fresh preflight and
refuses on any difference: another base, another current price, other
extras or other bytes. Each code confirms one run, and there is no blanket
override (owner decision 4).

### 6. How the archive and PUBLICATION.json record versions

- **Where the archive lives.** A Listing Update writes into the **same**
  `toys/<inventor>-<slug>/` directory, never a new slug. Its `make/` tree
  becomes the new version's bytes, and the git history keeps the old ones.
- **Schema 2 fields.** `PUBLICATION.json` (schema 2) adds `versions[]`,
  appended once per update:
  - `history_id`, `observed_at`, `reason`, `pack_sha256`;
  - the primary model SHA-256;
  - `extra_materials`;
  - the price and grams before and after;
  - the confirmation code;
  - for a `fix`, the correction run's Wish id.
- **What stays.** `publication` keeps the slug, page URL and first
  publication. Its `listing` is the latest price.
- **Older records.** A schema 1 record is read as having no versions.
- **Buyers see none of this** (owner decision 8).

### 7. Command-line surface

```text
tools/publish_direct.py --archive toys/<inventor>-<slug> --inventor <id> \
    --update-listing <slug> --reason reprice [--display-only B] [--bought B=PART] \
    [--predicted-grams G --predicted-grams-source TEXT] [--live --confirm CODE]
tools/publish_direct.py --cad-dir <project> --published-archive toys/<inventor>-<slug> \
    --update-listing <slug> --reason fix ... [--live --confirm CODE]
tools/publish_direct.py --reconcile-publish <product-id> --inventor <id>
skills/toy-archive/scripts/publish output/<project> --inventor <id> \
    --update-listing <slug> --reason fix ... [--live --confirm CODE]
workshop fix toys/<inventor>-<slug> --prompt-file FIX.md --update-listing
workshop publish <wish-id> --update-listing [--predicted-grams …] [--confirm CODE]
```

- `--update-listing` replaces `--reimport-slug` and `--reimport`.
- `--reconcile-publish` settles a ledger's `unknown` publish intent from
  readback alone (owner decision 7). It can never send.

### 8. Failure and reconciliation

| Outcome | What the host does |
|---|---|
| Preflight shows another author, a non-public design, a running job, a base slice not `done`, or a base that moved | Refuse (exit 2). Nothing is sent. |
| The confirmation code differs from a fresh preview | Refuse (exit 2). Nothing is sent. |
| A `reprice` whose printed bodies differ from the live STEP | Refuse (exit 2). It is a `fix`. |
| 4xx on the version POST | The intent is rejected. Nothing changed; report it. |
| Timeout or lost response on the POST | The intent is `unknown`, exit 3. A rerun re-reads and never resends. If `current_history_id` moved off the base and the new folder's anchor is ours, the send landed, and the rerun continues with steps 3–4. If it is still the base, the rerun reports exit 3, and the owner decides. Any other version means a stop for the owner. |
| Slice still pending at the end of the wait | Exit 3, with the version recorded and the extras not yet sent. A rerun resumes the wait. |
| Slice failed for good (Factory pauses the listing) | Exit 3, reported as "slice failed". The extras are not sent. Never unpublish, and never revert on our own; the owner decides. |
| `PUT` extras fails or reads back different | Exit 3. A rerun sends the same `PUT` again and reads back. |
| Price not the formula's after the extras | Success, reported as `price not repriced (possibly set by hand)`. |

The adapter never unpublishes, never deletes, and never `PATCH`es metadata.

### 9. Tests

The Factory fake transport gains, for a public design:

- `POST /designs/{slug}/import`, with a history list and
  `published_history_id`;
- a slice job per version that lands later;
- `PUT /designs/{slug}/extra-materials`;
- repricing by Factory's formula, or a price set by hand.

With it, the tests cover:

- the preview sends nothing and prints current and predicted prices with a
  code;
- `--live` without the code, or with a stale code, is refused;
- a reprice appends exactly one version, sends extras only after the slice,
  keeps the slug, URL and SKU, and reads back the new price;
- a lost response, then a rerun: the rerun reconciles without a second
  version;
- a base that moved is refused;
- another author's design, or a draft, is refused;
- a `reprice` whose printed geometry changed is refused;
- a slice that never lands gives exit 3, and a rerun resumes without
  resending;
- an extras write that reads back different is retried by `PUT` only;
- a listing priced by hand reports `possibly set by hand`;
- `--reconcile-publish` settles an `unknown` publish from readback and never
  sends;
- schema 2 `PUBLICATION.json` appends a version, and schema 1 still reads;
- the #221 and p2c#3 refusals still hold without `--update-listing`.

## Requests to the backend team

Workshop is built without these; each would make it safer or simpler:

1. **`Idempotency-Key` on `POST /designs/:slug/import`.** It is the only
   effect Workshop cannot retry safely today. A duplicate key should return
   the first response.
2. **A content hash in readback.** The SHA-256 of the uploaded zip, or of
   `assembled.step`, on each `design_history` row, so that a lost response
   is proven by hash rather than by our anchor file.
3. **`listing.priced_from` in owner readback.** Then a hand-set price can be
   told from one the platform priced.
4. **Extras applied at measurement.** A way to send `extra_materials` with a
   version but apply them only when that version's slice lands. That would
   remove the short window of new mass with the previous extras.
5. **A dry-run quote:** the price a given STEP would get, without creating a
   version. It would replace the operator-measured `--predicted-grams`.

## Consequences

- A fixed or repriced toy keeps its URL, SKU and order history. The listing
  now shows what the buyer gets and is charged for it.
- The toy re-floats to the top of Factory's "latest published" feed, because
  `SetPublished` re-stamps `published_at`. Its covers change when the new
  handoff carries one. The owner accepts both.
- Without server-side idempotency, safety rests on the base-history
  compare-and-swap and on reading back before any resend.
- The predicted price is only as good as the operator's measured grams. The
  receipt records the real price beside the predicted one.
- Whatever an external cart has cached of the old price is outside this
  repository and is not handled.

## Implementation status

Proposed and accepted on 2026-11-06. Implementation follows in its own PR,
and this section is updated with what is built.
