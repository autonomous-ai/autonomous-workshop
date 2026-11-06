# ADR 0097: A Listing Update appends a version to a public Factory design

- **Status:** Proposed on 2026-11-06 from the owner's direction of the same
  day. Nothing is implemented.
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
Today that is impossible, and every path that tries now refuses:

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

**A second create does not update anything.** It creates a new design.
`Slugify` keeps `[a-z0-9-]` (`services/slug.go:28-47`), and a taken slug gets
a random `-xxxx` suffix (`slug.go:91-131`).

**Price:**

- Per unit: 4.0 ¢/g of print plus 1.2 ¢/g of freight and duty, on Orca's mass
  with support at the shop's 15 % infill or the design's override, plus a
  $15 operations fee, plus the sum of the extra materials. It is rounded up
  to the whole dollar and clamped to the catalogue band
  (`models/slice_job.go:142-217`, `services/listing_pricing.go:209-225`).
- An extra material is `{name, price_cents, material}` with no count, at
  most 20 entries (`models/design_extra_material.go:43-65`). Workshop's
  adapter already folds count × unit price into one entry.
- The listing belongs to the design, not to a version (`models/design.go:62,
  344-352`).
- `RepriceOnMeasurement` (`services/listing_pricing.go:30-143`) reprices a
  `measured` or `estimate` listing when the new slice lands. A listing priced
  by hand is never moved; it is only paused if it falls below the floor.
- Sending extras reprices at once, against the **old** mass, until the slice
  lands (`import_version.go:290-294`).
- A slice that fails for good pauses a platform-priced listing
  (`listing_pricing.go:167-201`).

**Readback and orders:**

- `GET /designs/:slug` returns `current_history_id`,
  `published_history_id`, `project_url`, `print_specs`, the resolved
  `print_settings`, `extra_materials` and `listing.{sku, price_cents,
  active}` (`apis/responses_design.go:73-215`).
- It does **not** return the listing's `priced_from`, which is `json:"-"` at
  `models/design.go:93`. So a reader cannot tell a price set by hand from one
  Factory has not repriced yet.
- `GET /designs/:slug/slice` returns the slice state (`apis/router.go:261`).
- The listing SKU never changes, and orders key on it, not on a version
  (`services/listing.go:150-195`).

**Workshop already has the client side.** `FactoryClient.import_model_version`
(`src/workshop/integrations/factory.py:1664`) and a `factory-import-version`
ledger kind exist. Both serve only root repair of a still-private draft, and
that path refuses a public design ("Factory root repair cannot change a
public design").

## Decision

### 1. When a Listing Update is allowed

A **Listing Update** appends one version to a public Factory design that this
Workshop published. All of these must hold:

- **The design is proven to be ours.** A toy archive's `PUBLICATION.json`
  records the design's slug and page, and either a local ledger receipt or the
  archive's own receipt identities name the same `design_id`. Preflight
  readback must show the same `design_id`, a public status, the Inventor's
  account as owner, and no running generation job.
- **The owner asks for this update.** It is never automatic.
  `--update-listing SLUG` is required on every path, and the SLUG must equal
  the archive's recorded slug.
- **The reason is one of two:**
  - `fix`: a correction run's sealed output for the same toy;
  - `reprice`: the same printed geometry, re-published only to correct what
    Factory weighs and bills (#219: the primary stripped of display-only and
    bought bodies, plus `extra_materials`). A `reprice` is refused when any
    printed body's volume or area differs from the live version's, as read
    back from `project_url`. A geometry change is a `fix`.
- **Nothing of the listing's identity changes.** That covers the title, slug,
  URL, description, category, tags and license, and Factory refuses them on
  this route anyway. A rename stays a separate, out-of-scope owner action
  through `PATCH`.
- **Drafts are not covered.** A draft is still root repair's job.

**The ADR 0065 amendment:** `workshop fix` still creates a new design by
default. `workshop fix TOY --update-listing` makes the new run's Release
append to the source toy's listing instead, and `workshop publish <wish-id>
--update-listing` does the same for a finished unreleased run. The run keeps
its own Wish, session, budget and ledger, exactly as ADR 0065 says; only its
Release effect changes.

### 2. The effect

There is one host effect, in the existing Factory adapter: a new ledger kind,
`factory-listing-version`. It is separate from root repair's
`factory-import-version`, so the rule "root repair cannot change a public
design" stays true.

The steps:

1. **Preflight read.** `GET /designs/{slug}` returns `design_id`, status,
   author, `current_history_id`, `published_history_id`, the listing
   (`price_cents`, `active`), `print_specs`, `print_settings` and the current
   `extra_materials`.
2. **Send the version.** `POST /designs/{slug}/import` with:
   - `file`: the same single-STEP Make-output handoff a create sends;
   - `extra_materials`: **always sent**, `[]` when nothing is bought, so a
     version never inherits a stale list;
   - `usage`, when a Workshop run supplies it.
3. **Carry the print overrides.** The handoff's `project.json` carries the
   same print override the toy was sealed with (#216's infill). If the live
   design's `print_settings` show an override that the new version would
   drop, the update is refused, not silently reset to 15 %.

Credentials stay host-only, as for every Factory effect. No native agent
turn performs or sees it.

### 3. Ledger and idempotency

- **Where it lives:** in the ledger of the product id that first published
  the toy, taken from the archive's receipt. A new ledger is never started
  under another id. For the palm vase that is `synthwave-palm-bud-vase`, not
  `r24-synthwave-palm-vase-taper`.
- **Intent identity:** the kind, `design_id`, the **base**
  `current_history_id` read at preflight, the handoff pack SHA-256, the
  canonical `extra_materials`, and the reason. The base history id makes the
  update a compare-and-swap. If the design's current version is no longer the
  base, because someone else appended one, the intent refuses and asks the
  owner to look.
- **Several updates over time are allowed.** Each update has its own base, so
  each one is its own intent. The ledger's "a product has one import" rule
  applies to `factory-import` only.
- **No blind resend.** Factory has no idempotency, so the adapter never sends
  the same intent twice without first proving the earlier send did not land.

### 4. Readback

The update succeeds only when all of this reads back:

1. `current_history_id == published_history_id`, a new id different from
   the base, the same `design_id`, slug and page URL, and a public status.
2. The publication anchor and product facts under the new `project_url`
   hash to what was sent. This reuses `verify_publication_anchor` and
   `verify_import_root_facts`.
3. The design's `extra_materials` equal what was sent. This is needed
   because the backend writes them best-effort.
4. The slice of the new version has landed, and `print_specs` describe it.
   The adapter polls `GET /designs/{slug}/slice`, bounded like the existing
   listing wait, but longer, because it is a re-slice.
5. The listing reads back active, with its new `price_cents`.

The receipt records the listing price before and after, the measured grams
before and after, and the extras.

When the listing was priced by hand, Factory does not move it. The readback
does not say who set a price, so a price that has not changed after the new
slice landed is recorded as `price: unchanged after slice (possibly
owner-set)`. It is not reported as a failure. The backend request in open
question 6 would make this exact.

### 5. Price and extra materials

Workshop still submits no price. Factory computes it with its own formula
(§ Context). Workshop's part is to make what Factory weighs and bills true:

- a printed-only primary;
- one `extra_materials` entry per bought part, `count × unit_price_cents`
  from the catalogue, with the 2026-11-06 Vietnamese estimates, or from an
  operator `--part-price`;
- the same print override.

The dry run prints the old price, the old extras and the new extras. It
cannot print the new price, because only Factory's slice measures it. Between
the 200 and the slice, Factory briefly shows the old mass plus the new
extras.

### 6. How the archive and PUBLICATION.json record versions

- **Where the archive lives.** A Listing Update writes into the **same**
  `toys/<inventor>-<slug>/` directory, never a new slug. Its `make/` tree
  becomes the new version's bytes, and the git history keeps the old ones.
- **New fields.** `PUBLICATION.json` gains schema 2 fields:
  - `publication` keeps the design's slug, page URL, `design_id` and first
    publication time;
  - `versions[]` is appended once per published version, starting with the
    original create:
    - `history_id`, `published_at`, `reason`, `pack_sha256`;
    - the primary model path and SHA-256;
    - `extra_materials`;
    - `listing.price_cents` before and after, and the measured grams;
    - the receipt identities;
    - for a `fix`, the correction run's Wish id.
- **Older records.** A schema 1 record is read as one version.
  `workshop fix` and the toy-archive packer keep reading `publication` for the
  page URL.

### 7. Command-line surface

```text
tools/publish_direct.py --archive toys/<inventor>-<slug> --update-listing <slug> \
    --reason reprice [--display-only B] [--bought B=PART] [--part-price PART=CENTS] [--live]
tools/publish_direct.py --cad-dir <project> --published-archive toys/<inventor>-<slug> \
    --update-listing <slug> --reason fix|reprice ... [--live]
skills/toy-archive/scripts/publish output/<project> --inventor <id> \
    --update-listing <slug> --reason fix|reprice ... [--live]
workshop fix toys/<inventor>-<slug> --prompt-file FIX.md --update-listing
workshop publish <wish-id> --update-listing
```

- `--update-listing` replaces `--reimport-slug` and `--reimport`.
- Without `--live`, the commands stay offline and send nothing.
- For the lamp, the reprice would be the flags already drafted
  (`--display-only headphones_ref --bought rod_m6x250=threaded-rod-m6x250 …`)
  with `--update-listing
  victorian-lamp-post-headphone-stand-on-a-paving-slab-tray --reason
  reprice`.

### 8. Failure and reconciliation

| Outcome | What the host does |
|---|---|
| Preflight shows another owner, a non-public design, a running job, or a base that moved | Refuse (exit 2). Nothing is sent. |
| 4xx on the POST | The intent is rejected. Nothing changed; report it. |
| Timeout or lost response | The intent is `unknown`. Exit 3. A rerun re-reads first. If `current_history_id` moved off the base and the new folder's anchor hash is ours, the send landed: continue with readback. If it is still the base after a bounded wait, the send did not land, and the same intent may send once more. Any other version means a stop for the owner. |
| `extra_materials` read back differ | Not proven (exit 3). A rerun appends no new version. It re-reads, and if a correcting route exists, uses it (open question 6). |
| Slice still pending at the end of the wait | Exit 3, with the version recorded and the price `pending`. A rerun only re-reads. |
| Slice failed for good (Factory pauses the listing) | Exit 3. Report "listing paused by Factory: slice failed". Never unpublish, and never send a revert on our own; the owner decides. |
| Price unchanged after the slice landed (possibly priced by hand) | Success, with the price reported as unchanged. |

The adapter never unpublishes, never deletes, and never `PATCH`es metadata.

### 9. Tests

The Factory fake transport gains `POST /designs/{slug}/import` for a public
design. It holds a history list, `published_history_id`, a slice that lands
later, best-effort extras and repricing by `priced_from`. With it, the tests
cover:

- the dry run sends nothing and reads no credential;
- a reprice appends exactly one version, keeps the slug, URL and SKU, and
  reads back the new price and extras;
- a lost response, then a rerun: the rerun reconciles without a second
  version;
- the base moving between preflight and send is refused;
- another owner's design, or a draft, is refused;
- a `reprice` whose printed geometry changed is refused;
- dropping a live print override is refused;
- an extras write the backend drops is not reported as success;
- a slice that never lands gives exit 3 and a re-read-only rerun;
- a listing priced by hand reports its price unchanged;
- schema 2 `PUBLICATION.json` appends a version, and schema 1 still reads;
- `workshop fix --update-listing` keeps a fresh Wish and ledger but publishes
  onto the source listing, and `workshop fix` without it still creates a new
  design;
- the #221 and p2c#3 refusals still hold without `--update-listing`.

## Consequences

- A fixed or repriced toy keeps its URL, SKU and order history. The listing
  now shows what the buyer gets and is charged for it.
- The toy re-floats to the top of Factory's "latest published" feed, because
  `SetPublished` re-stamps `published_at`. Its covers change when the new
  handoff carries one, and it always does.
- Without server-side idempotency, safety rests on the base-history
  compare-and-swap and on reading back before any resend.
- Whatever an external cart has cached of the old price is outside this
  repository and is not handled.

## Open questions for the owner

1. **Default for `workshop fix`:** keep ADR 0065's new design by default and
   update only with `--update-listing`, as proposed, or make updating the
   default?
2. **Allowed reasons:** only `fix` and `reprice`? Should a `reprice` also
   allow a changed print override, such as infill?
3. **Re-floating:** an update re-stamps `published_at`, so the toy jumps to
   the top of "latest". Is that acceptable, or should the backend gain a
   version publish that keeps `published_at`?
4. **Prices set by hand:** leave them untouched and report them, as proposed,
   or let a Listing Update ask Factory to reprice them?
5. **The interim price:** accept the short window of old mass plus new
   extras, or send the version without extras first and the extras only after
   the slice lands? The second needs a two-step effect.
6. **Backend requests:** should we ask panda-social-backend for an
   `Idempotency-Key` on `POST /designs/:slug/import`, a content hash and the
   listing's `priced_from` in its readback, and a route to rewrite
   `extra_materials` without a new version?
7. **The palm vase:** its ledger has a publish intent left `unknown` since
   2026-11-03. Reconcile it by readback before its first update, as proposed?
8. **Version history for buyers:** keep `versions[]` only in the archive, or
   also show "updated on …" on the toy page?
