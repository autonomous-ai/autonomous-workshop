The silhouette-likeness gate is gone from the Make pipeline (ADR 0076). No IoU
is computed: `make_round` composes each reference beside the model rendered at
the reference's declared camera, and `verify_project` no longer takes
`--likeness-ref` or its acceptance flags. A Component now passes when it
builds, its print gates pass and an independent reviewer records agreement
with `make_round --component ... --record-review`. After five shape rounds a
disagreeing review is recorded as a component acceptance, written to
`measure/component-acceptance.json`, sealed into `product.json` as
`component_acceptances`, and reported when the run ends. Assembly rounds keep
the Manager's `--record-visual`, the blind review and `--full`. Frozen runs
keep their materialized tools and their `likeness_acceptances`. This is an
experiment on `rein/remove-likeness` and has not been validated by a live run.
