# Workshop inventor selection before Spark Make — v1

This marker freezes a Workshop setup boundary for new Spark runs only. It does
not change Make's code, finalizer, or product checks. Older runs retain their
materialized selection behavior. The host passes this boundary explicitly in
`STAGE.json.inputs.workshop_selection`.

## Pending selection

When `workshop_selection.status` is `pending`, select the inventor before
reading the Make reference, creating a Make Goal, researching a product, or
starting design/CAD. The host stage may already name `make` as the next creative
checkpoint; its work is not invoked until Workshop accepts this setup handoff.
Do not create a separate Goal or another root native session for selection.

1. Read the exact Wish and `inventor_discovery_index` in `STAGE.json`. Use only
   the immutable `.codex/agents/` roster named in that packet. An explicit
   `--inventor` already narrows this roster to that exact inventor: use it and
   do not search for a replacement.
2. Without an override, identify the Wish's hardest creative problem and rank
   every eligible inventor by that problem. Read the relevant full custom-agent
   files to understand their Taste and primary methods. The Manager makes this
   choice natively; Python does not choose, score, or rerank it.
3. Save compact choice/ranking work outside the Make product tree so a resumed
   selection can reuse it. Do not begin the product concept or fabrication.
4. Write the following JSON to the exact `workshop_selection.marker_path`,
   using the matching bindings from `STAGE.json`. Each ranking row has exactly
   `inventor_id` and a concise `rationale`. Cover the roster exactly once, with
   the selected inventor first. JSON whitespace is immaterial.

```json
{
  "schema_version": 1,
  "kind": "autonomous-workshop.inventor-selection-ready",
  "product_id": "<STAGE.product_id>",
  "checkpoint_sha256": "<STAGE.checkpoint_sha256>",
  "wish_sha256": "<inputs.workshop_selection.wish_sha256>",
  "inventor_roster_sha256": "<inputs.workshop_selection.inventor_roster_sha256>",
  "selected_inventor_id": "<exact roster id>",
  "ranking": [{"inventor_id": "<exact roster id>", "rationale": "<fit to this Wish>"}]
}
```

Return immediately. Do not write `agent-outcome.json`, call `match` or `make`,
claim a gate passed, or start Make in this turn. The marker is a proposal for
Workshop setup only. The host binds the exact native choice into a private
receipt, then resumes this same native session. Selection and any resumed
selection work share the one product token allowance.

If the host reports a malformed selection, correct only that selection record
and return it again. If a prior marker exists with the current bindings, reuse
it instead of reranking. A changed checkpoint requires the newest packet's
binding, not a new choice. Do not infer acceptance from marker existence.

## Selected handoff to unchanged Make

When `workshop_selection.status` is `selected`, its `assignment` is the
Workshop-accepted `NativeMatchAssignment`. Read the exact selected custom
agent and proceed to the Make reference and Make Goal. Roster comparison has
already happened: do not repeat it or choose a different inventor.

For Make's existing compound creative source, reuse `selected_inventor_id`
and `ranking` from the accepted assignment verbatim, adding only the `concept`
and `research` that Make normally authors. The existing Make finalizer remains
unchanged and seals these familiar fields with the finished product. The
selection receipt is neither product-quality evidence nor permission to bypass
any Make check. Make receives the chosen specialist; Workshop owns choosing
that specialist and the durable handoff.
