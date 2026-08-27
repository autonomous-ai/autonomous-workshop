# Design vault provenance

The seed nodes under `mechanisms/`, `anti-patterns/`, `rule-patterns/`,
`constraints/`, and `components/` were imported on 2026-08-27 from the
maintainers' internal board-game design vault. Every `## Definition` and
`## Notes` body was written by the maintainers or their agents; mechanism
*names* trace to the public BoardGameGeek taxonomy, and no BoardGameGeek prose
or ranking data is included. Evidence rows recorded from private pipeline runs
were removed before import; `[yt:<id>]` rows distil public design talks.

`games/` case studies are deliberately not shipped: they were seeded from the
TidyTuesday 2022-01-25 BoardGameGeek dataset, whose terms the maintainers do
not redistribute under this repository's licence. `workshop vault seed` copies
only these folders; a local vault may add `games/` nodes by hand.

Every node is validated by `workshop vault lint` and the packaging tests; the
packed vault a product run receives is content-addressed by
`workshop.invent.vault.Vault.sha256`.
