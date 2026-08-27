- Build Make in bounded groups: Invented schema 5 requires a `build_plan`
  partitioning the concept's components; each component ships as
  `parts/<key>.stl`; `stage_proposal.py make-group` seals one group's exact
  part bytes under `groups/<group>.json`; the `make` finalizer and the host
  gate refuse unsealed or stale groups. Schema 3 and 4 concepts need no groups.
