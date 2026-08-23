# Inventor Workshop

Workshop is the standard-library-first shared package beneath every autonomous
inventor in this repository.

Inventors bring Taste and a workflow. Workshop brings the reusable machinery:

```text
Wish + Taste
     |
     v
Workbench.make() --> MakeResult
                         |
              Workbench.inspect()
                         |
                    Inspection
                    exact evidence
                         |
                  pack_artifact()
                         |
                   PackedArtifact
                         |
                Sender --> Door --> Stamp

Clockwork keeps state, workflows, leases, budgets, retries, and effect fences.
```

This developer pipeline stays backstage. The customer sees only
`WISH -> WAIT -> RECEIVE`.

## Install and inspect

```bash
python -m pip install -e workshop
workshop --help
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
```

The distribution is `inventor-workshop`, the Python package is
`inventor_workshop`, and the CLI is `workshop`.

## Canonical Python surface

```python
from inventor_workshop import (
    Clockwork,
    Sender,
    Wish,
    Workbench,
    load_taste,
    pack_artifact,
)

wish = Wish.create("product-42", "A beautiful printable object")
taste = load_taste(inventor_root)

# Inventor-owned Doors are injected here.
workbench = Workbench(model_door, cad_door, cad_inspection_door, inspection_door)
made = workbench.make(wish, inventor_root, run_root, budget_micros=2_000_000)

# Make and Inspect are separate boundaries. Inspect binds every result and
# evidence file to the exact content-addressed artifact made above.
inspection = workbench.inspect(made)

packed = pack_artifact(made.cad_build.artifact_root, output_zip)
clockwork = Clockwork(runtime_root / "clockwork.sqlite3")
clockwork.register_product(
    "product-42",
    "packed",
    {},
    artifact_sha256=packed.artifact_sha256,
)
sender = Sender(clockwork)
sent = sender.send(
    "product-42",
    packed,
    delivery_door,
    {"material": "PLA", "destination": delivery_request},
)
```

The injected `delivery_door` implements the qualified Delivery Door contract
and returns an authenticated Stamp. Concrete inventors normally wrap these
primitives rather than putting this whole composition in one file. If the
product should also be sold, configure `ShopDoor` separately and use
`send_draft()`; a storefront is not required for direct delivery.

## Contracts

| Contract | What Workshop guarantees |
|---|---|
| `Taste` | exact UTF-8 bytes and SHA-256 of root `TASTE.md` |
| `Wish` | bounded, typed intent passed into Make |
| `Workbench` | injected model/CAD Doors, explicit Inspect boundary, budget, fresh workspace, Taste continuity |
| `Inspection` | every result passes, names the exact artifact hash, and points to matching evidence inside its manifest |
| `PackedArtifact` | deterministic ZIP ordering, timestamps, permissions, inventory, secret scan, and SHA-256 |
| `Clockwork` | revision fencing, event chain, leases, budgets, durable outbox, and ambiguous-effect holds |
| `Sender` | generic record-before-send outbox, unknown-effect holds and reconciliation; draft-first Shop helpers |
| `Stamp` | authenticated external evidence bound to exact Pack and artifact identities |

Qualified Doors keep provider details at the edge: `ModelDoor`, `CadDoor`,
`CadInspectionDoor`, `InspectionDoor`, `ShopDoor`, and `DeliveryDoor`.

## Included making skills

The wheel and source checkout expose the same fingerprinted trees:

- `skills/cad` — printable CAD project structure and deterministic checks;
- `skills/step-parts` — STEP-part design and verification guidance;
- `skills/product-to-cad` — product-to-CAD workflow composition.

Discover the exact installed paths and hashes:

```bash
workshop skills list
workshop skills path
```

An inventor may declare a skill feature only when its checked-in runtime
actually invokes that skill. Merely discovering an installed skill does not
count as adoption.

## Manifests and schemas

New inventors use schema v3 and only reviewed `workshop_features` values.

```bash
workshop schemas path
workshop schemas list
```

The distribution ships `inventor.schema.json`, `inspection-result.schema.json`,
and `stamp.schema.json`.
Schema v1 (`core_features`) and v2 (`foundation_features`) remain readable for
migration; new scaffolds emit only schema v3.

## Scaffold

```bash
workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

The generated inventor is runnable both from a checkout and from its wheel.
Its identity files are installed with the package, while mutable state defaults
to the user's data directory outside the installed wheel. `doctor` and
`status` do not create a database. The offline `make` is credential-free and
intentionally does not claim production readiness.

## Verify Workshop

```bash
PYTHONPATH=workshop/src python -m unittest discover \
  -s workshop/tests -p 'test_*.py' -v
workshop check inventors --run
python workshop/tools/verify_skill_locks.py
python workshop/tools/verify_snapshot_locks.py
python workshop/tools/scan_secrets.py
```

Workshop has no runtime dependency outside Python's standard library. Imported
skill trees retain their own documented requirements and provenance.

## Compatibility boundary

Workshop 0.3 is canonical. Former imports are direct shims:

```python
import inventor_foundation  # compatibility only
import inventor_core        # compatibility only
```

They point to the same `inventor_workshop` classes and modules. They do not own
separate state, schemas, or behavior. Old `_foundation_*` and `_core_*`
metadata can be read only when it agrees with canonical `_workshop_*` values;
new output uses Workshop names.

See [MIGRATION.md](docs/MIGRATION.md) for the complete compatibility contract.
