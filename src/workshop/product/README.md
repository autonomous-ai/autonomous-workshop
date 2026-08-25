# Product

Owns plaything lanes, blueprints, and shared product policy. It describes what
the Workshop may make; it does not run a lifecycle stage.

Public API: `workshop.product`.

Product consumes the small structural `TasteBinding` contract. The concrete
filesystem-backed `Taste` remains owned by Contributors.
