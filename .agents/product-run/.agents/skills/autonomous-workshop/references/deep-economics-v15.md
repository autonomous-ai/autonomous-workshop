# Frozen Forge and Quest economics profile v15

This immutable profile retains v14's reasoning, 256,000-token compaction,
20-minute initial Invent boundary, 10-minute Invent recovery, 16-minute first
Make proof boundary, 15-minute first final-product continuation, normal
30-minute recovery, one native Codex thread, one Goal per active stage, and
every deterministic product and publication gate.

Its only behavioral change is the `invent-concept-v3` source handoff. Invent
recovery checks only for `drafts/invent-source.json` and the exact
`STAGE.json.inputs.visual_instructions_path`. When both exist, its next action
invokes the packet-bound finalizer with `--source` and
`--visual-instructions`. When one is missing or invalid, it authors or repairs
only that smallest input and then invokes the finalizer. It does not rerank
Inventors, restart research, delegate, review, polish, or reopen exploration
before the first finalizer attempt.

The finalizer remains the stopping boundary for the native Invent turn. The
host alone derives the fixed front, top, bottom, exploded, and per-component
requests and hashes, performs image effects after native exit, reconciles
receipts, evaluates gates, and resumes the same session at Make. Make,
Playtest, Release, credential isolation, and effect authority are unchanged.
