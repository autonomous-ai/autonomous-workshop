# Operating production services

Inventors contribute Taste and, only when declared, a bounded custom Make or
Playtest hook. They do not own research credentials, private reference bytes,
Factory accounts, printers, QA, packing, or carrier integrations. Those common
components belong to one trusted Workshop Manager composition.

Select an installed composition with:

```bash
export WORKSHOP_MANAGER_SERVICES=production
workshop doctor --deep
workshop wish "I wish for a pocket-sized weather machine for my desk"
```

`doctor` prints only public provider identities and configuration digests. It
also materializes the prospective five-stage engine manifest without calling a
service effect, and labels that manifest as the Manager common defaults before
Inventor selection. It never prints, serializes, or hands live service objects
to Inventor code.

## Provider package

A trusted operator package exposes exactly one entry point in
`autonomous_workshop.manager_services`:

```toml
[project.entry-points."autonomous_workshop.manager_services"]
production = "my_workshop_services:build_services"
```

Install that composition as a dedicated distribution. Do not place it inside
the Workshop distribution or an Inventor package. Before any declared custom
Make/Playtest hook runs, the Manager resolves the selected distribution without
loading it and proves its complete code, sibling modules, data, `.pth`, and
metadata are unreadable to the isolated child. Ambiguous ownership fails closed.

Its zero-argument factory returns `ManagerServices`. Each capability is paired
with a bounded `ManagerProviderIdentity` through `ManagerServiceBinding`:

```python
from inventor_workshop import (
    ManagerProviderIdentity,
    ManagerServiceBinding,
    ManagerServices,
)

def bind(provider_id, version, config_sha256, service):
    return ManagerServiceBinding(
        ManagerProviderIdentity(provider_id, version, config_sha256),
        service,
    )

def build_services():
    return ManagerServices(
        "production",
        research=bind("acme.research", "1.0.0", RESEARCH_CONFIG_SHA256, research),
        classic_rules=bind("acme.classics", "1.0.0", CLASSIC_CONFIG_SHA256, classics),
        world_reference=bind("acme.world-input", "1.0.0", WORLD_INPUT_CONFIG_SHA256, world_reference),
        world_playtest=bind("acme.world-proof", "1.0.0", WORLD_PROOF_CONFIG_SHA256, world_playtest),
        factory_credentials=bind("acme.factory-broker", "1.0.0", FACTORY_CONFIG_SHA256, factory_broker),
        deliver=bind("acme.fulfillment", "1.0.0", DELIVER_CONFIG_SHA256, fulfiller),
    )
```

Fulfillment has a deliberately two-phase interface:

```python
class Fulfillment:
    def preflight(self, context):
        # Validate readiness only. Return None, or raise WaitingFor before any
        # print, shipment, charge, or other external effect.
        return None

    def fulfill(self, context):
        # Use context.idempotency_key and return a typed Delivered receipt.
        # Once this method begins, every non-Delivered outcome is ambiguous.
        return deliver_exact_product(context)

    def reconcile(self, context):
        # Authenticated GET/readback only. Never call fulfill or create a new
        # shipment. Return exact Delivered evidence, or None while the sealed
        # provider attempt remains unknown.
        return read_exact_attempt(context.idempotency_key)
```

The hashes identify non-secret configuration; never derive them from a secret
value. The live services stay in the Manager process and are deliberately not
picklable.

## Common capabilities

- `research` receives the exact Wish in the trusted process and returns typed,
  Wish-bound research. It is the shared Invent research provider.
- `classic_rules` selects independently modeled rules evidence for the exact
  classic game and Make. It extends common Playtest beyond the bundled pinned
  checkers provider.
- `world_reference` admits customer reference scopes before Invent without
  exposing raw private bytes to the Inventor.
- `world_playtest` runs in an isolated external service and returns raw-free,
  artifact-bound comparison evidence after Make.
- `factory_credentials` resolves a different typed Factory account for the
  matched Inventor. It replaces the legacy single-password environment seam.
- `deliver` performs real production, hands-on QA, packing, and carrier
  handoff, returning the four exact chained receipts required by shared
  Deliver.

Missing services produce typed Needs. They never silently become Inventor
responsibilities, lower a proof threshold, or fabricate success.

## Effects and recovery

Factory publication is authorized separately from the six jobs and occurs only
after Deliver. A public Factory page may activate a sale listing, so a verified
draft remains private while fulfillment is incomplete.

Deliver resume is fenced and checkpoint-bound. Only `preflight` may return a
typed, retryable no-effect wait. A provider must use the supplied stable
idempotency key and support authenticated reconciliation. Once `fulfill` begins,
a provider-authored wait, exception, malformed receipt, or Manager crash is an
ambiguous effect; the Workshop does not blindly call it again.
`workshop status WISH_ID` exposes the non-secret provider and attempt identities
and prints `workshop reconcile WISH_ID`. That command accepts only the provider
sealed in the working attempt, calls `reconcile` without calling `preflight` or
`fulfill`, and records `Delivered` only when the returned evidence binds the
same Wish, product bytes, Instructions, provider, and idempotency key. `None`
leaves the attempt working and safe to read back again.

The legacy `FACTORY_PASSWORD` remains a compatibility fallback for deployments
where all Inventors genuinely share one password. A per-Inventor credential
broker is the production path.
