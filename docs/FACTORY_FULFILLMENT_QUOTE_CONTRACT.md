# Factory fulfillment quote contract

Status: required backend contract; not implemented by Factory or Workshop.

This document records the boundary Workshop needs before it may choose and
submit a Factory listing price automatically. It is intentionally narrower
than a general commerce-pricing design: one exact imported design history goes
in, and one authoritative single-unit print-and-ship quote comes back.

## Audit baseline

The Factory backend `main` commit
`85923b86b540d131758261b210702d36b2ed4b10` and the production OpenAPI document
were checked on 2026-08-27. Their relevant contracts agree:

- authenticated `GET /designs/{slug}/slice` returns `design_id`, `history_id`,
  slice status, the complete CuraEngine profile, filament rows, and measured
  totals such as material and weight;
- authenticated `GET /designs/{slug}` returns material usage and any existing
  listing, but deliberately omits cost and suggested-price fields;
- `POST /designs/{slug}/publish` accepts a creator-supplied
  `listing.price_cents` and checks a server-side fulfillment floor when a weight
  is already known; without a supplied listing it uses a best-effort archive
  heuristic; and
- neither OpenAPI nor the authenticated responses expose a monetary quote,
  minimum listing price, pricing-policy identity, or price-to-history binding.

The publish endpoint's validation formula and error text are enforcement, not
a quote contract. Copying that formula into Workshop would duplicate mutable
Factory policy. Sending a deliberately low price to discover the minimum from
a rejection would turn an error string into an API and is not acceptable.

Until the contract below exists, Workshop must not submit an explicit listing
price or describe Factory's returned auto-listing price as cost. That pricing
limitation does not weaken terminal Release: the exact ready-to-print CAD and
`MANUAL.pdf` still require public Factory publication and authenticated hash
readback under the current no-explicit-price path.

## Smallest sufficient Factory API

Factory should expose an owner-authenticated endpoint scoped to the exact
imported version:

```http
GET /api/v1/designs/{slug}/fulfillment-quote?history_id={history_id}
Authorization: Bearer ...
Accept: application/json
```

The endpoint must be read-only and idempotent. A `200` response means the
current quote is complete and may be used for publication. A queued or running
slice may return `202` with only status and identity fields. A missing, failed,
unmeasurable, superseded, or non-current history must not return money; use a
typed `409` response. Normal owner visibility rules still produce `401`, `403`,
or `404`.

A successful response needs this semantic shape (names may change once, before
Workshop integrates, but the information and bindings may not):

```json
{
  "schema_version": 1,
  "status": "quoted",
  "quote_id": "fq_...",
  "design_id": "...",
  "history_id": "...",
  "slice_job_id": "...",
  "project_url": "https://cdn.autonomous.ai/.../",
  "issued_at": "2026-08-27T00:00:00Z",
  "expires_at": "2026-08-28T00:00:00Z",
  "currency": "USD",
  "pricing_policy": {
    "id": "single-unit-fdm",
    "version": "..."
  },
  "slice": {
    "profile": {
      "slicer": "curaengine",
      "slicer_version": "...",
      "definition": "...",
      "settings_profile": "...",
      "preset_revision": "...",
      "layer_height_mm": 0.2,
      "infill_percent": 15,
      "material_type": "PLA",
      "material_diameter_mm": 1.75,
      "material_density_gcm3": 1.24,
      "support_enabled": false,
      "support_angle_deg": 0
    },
    "totals": {
      "weight_g": 44.33,
      "length_mm": 0,
      "volume_cm3": 0,
      "print_time_seconds": 0,
      "part_count": 6,
      "materials": ["PLA"]
    },
    "filaments": []
  },
  "cost": {
    "billed_weight_g": 57.63,
    "printed_material_cents": 221,
    "shipping_cents": 1000,
    "fulfillment_total_cents": 1221
  },
  "listing": {
    "minimum_price_cents": 1221,
    "price_cents": 1221
  }
}
```

The numbers above illustrate field meaning only; they are not Workshop pricing
constants and must never be copied into code or a product listing.

Required invariants:

- `quote_id` is immutable and uniquely identifies the exact response inputs
  and Factory pricing-policy version.
- `design_id`, `history_id`, `slice_job_id`, and `project_url` identify the
  same version. The requested history must equal the design's current history
  when quoted.
- `slice.profile`, `slice.totals`, and `slice.filaments` are the exact settled
  measurement used by pricing, not merged or operator-overridden page copy.
- A quote requires a positive finite measured weight and the diameter, density,
  material, slicer, and preset fields needed to audit it. Unknown values do not
  become zero.
- Every monetary value is a bounded integer in minor units. Currency is
  explicit. `fulfillment_total_cents` is the single-unit fulfillment cost;
  `minimum_price_cents` is the enforced floor; and `price_cents` is the exact
  Factory-selected listing price Workshop is authorized to copy. Factory, not
  Workshop, decides whether that price equals the floor or includes another
  declared policy.
- The cost breakdown adds exactly to its total. The returned listing price is
  at least the returned minimum. The backend rejects a response that cannot
  satisfy those relations.
- Expiry and pricing-policy identity are explicit. If immutable history quotes
  do not expire, omit `expires_at` by contract rather than using a sentinel.

## Quote-bound publication and readback

Factory must extend the existing publish body so the quote, version, and exact
price are one atomic authorization:

```json
{
  "listing": {
    "price_cents": 1221,
    "currency": "USD",
    "fulfillment_quote_id": "fq_..."
  }
}
```

Before publishing, Factory must require that the quote belongs to the caller,
design, and current history; is still valid under its recorded policy; and has
the exact `listing.price_cents` and currency from the quote. A stale history,
expired quote, altered price, or changed slice must reject the whole operation
with a typed conflict rather than silently re-pricing it.

The authenticated publish response and subsequent
`GET /designs/{canonical-slug}` readback must expose, inside `listing`:

```json
{
  "active": true,
  "price_cents": 1221,
  "currency": "USD",
  "sku": "...",
  "fulfillment_quote_id": "fq_...",
  "priced_history_id": "..."
}
```

The design readback must also retain `current_history_id` and
`published_history_id`, allowing Workshop to require that both equal the quoted
history. The public product lookup should return the same price, currency, and
SKU, but authenticated design readback remains the authority for completing
the external effect.

## Future Workshop adapter behavior

Once the Factory contract is deployed and its OpenAPI schema is authoritative,
the smallest fail-closed Workshop flow is:

1. Import the exact sealed handoff and authenticate its private design/history
   readback as today.
2. Poll the quote endpoint within a bounded publication budget. Require every
   identity, profile, material, weight, policy, expiry, currency, arithmetic,
   and integer-money invariant above.
3. Canonically serialize and hash the exact quote. Store its bytes/hash and
   `quote_id` in the private effect ledger, bound to the existing import,
   artifact, Release, and Playtest hashes.
4. Prepare the publication intent with the exact quoted `price_cents`, currency,
   quote id/hash, design id, and history id before network I/O.
5. Submit those exact values once. On timeout or disconnect, reconcile by
   authenticated readback; never blindly publish again.
6. Complete the effect only when authenticated readback proves the exact quote
   id, priced history, price, currency, active listing, SKU, and published
   history. Otherwise leave Release waiting or failed according to the typed
   effect outcome; never downgrade it to a successful local-only Release.

Workshop must not calculate Factory's floor, parse a rejection message, use
archive size or file counts as cost, ask the product-run agent to choose a
price, or treat an unbound auto-listing as a quote.
