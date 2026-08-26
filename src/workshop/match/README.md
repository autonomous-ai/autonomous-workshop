# Match

Owns inventor discovery, semantic ranking, assignment, and the trusted handoff
that binds one Wish to one inventor. It never performs an inventor stage.

Public API: `workshop.match`.

Routing cards, decisions, one-shot assignments, and handoff contracts are
exported from this boundary. Contributor validation does not call Match.
