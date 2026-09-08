# Direct Release protocol v1

This immutable capability marker means Release is the terminal executable
Workshop stage and that publication is required to complete it: there is no
executable Deliver stage, and printing, delivery, and review are Operations
after Workshop completes.

The active route is defined by `effort-routes-v1.md` and the `STAGE.json` the
host writes, which take precedence over any lifecycle listed here. Spark is
`Wish -> Make -> Release`, Forge is `Wish -> Invent -> Make -> Release`, and
Quest is `Wish -> Invent -> Make -> Playtest -> Release`. Frozen historical
runs without `effort-routes-v1.md` kept `Wish -> Match -> Invent -> Make ->
Release`.

Where the frozen route has no Playtest (Spark, Forge, and those historical
runs), Release must not claim that Playtest ran or passed; the package instead
contains the canonical `PLAYTEST-NOT-RUN.json` omission record and binds its
exact hash. Where the route includes Playtest (Quest), Release binds the exact
passing Playtest evidence. Ready-to-print CAD still must pass the host's full
deterministic verifier before Release and again before publication.
