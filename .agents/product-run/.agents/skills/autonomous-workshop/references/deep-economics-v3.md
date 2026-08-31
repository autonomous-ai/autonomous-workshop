# Frozen Forge and Quest economics profile v3

This immutable marker freezes an enforceable stage-shaped Codex profile for
new Forge and Quest runs. The one persistent Codex thread remains bound to this
complete profile while each active stage selects its own turn policy: Invent
uses **high reasoning effort**; Make, Playtest, and Release use **medium**.
Every stage compacts automatically at 24,000 tokens. Normal turns have a
30-minute boundary and one `workshop wish` or `workshop resume` invocation may
launch at most eight native turns across all stages.

The first Make turn for each exact Make checkpoint is a 12-minute proof
boundary. It is not a separate stage, Goal, agent, attempt, or quality gate.
If the Make finalizer has not completed by that boundary, the existing bounded
recovery path resumes the same session, Goal, stage packet, and workspace with
a normal 30-minute turn. The shorter first boundary makes prolonged invisible
deliberation recoverable before it consumes a full Make turn.

The first Make deliverable is a persisted falsifier, not the complete product.
After reading the fixed stage packet, sealed Invent result, selected Inventor,
and only the CAD references needed for the immediate uncertainty, create the
smallest exact causal or kinematic proof and a neutral volumetric blockout.
Save its held and signature views, exact proof output, and concise finding under
the declared CAD project at `review/early-proof/`. Inspect those pixels and
numbers before authoring the complete part tree or detailed final geometry.
Do not batch-write the whole product first.

The early proof must answer both questions cheaply:

1. Does the defining action or relationship work at the required positions,
   clearances, and stops?
2. Does the held object and signature state read without the product name,
   Wish, labels, floating presentation pieces, or explanatory copy?

If either answer is no, repair or simplify the smallest proof immediately.
When both answers are yes, reuse its exact parameters and source in the final
CAD rather than rebuilding from a second design. Preserve the early proof in
the product tree so the public toy snapshot shows how the design was
falsified. Then follow one funnel: narrow generation and checks, all-printable
preflight once a complete baseline exists, final renders and one bounded blind
review, one focused repair at most, one integrated final verifier, and the
Make finalizer.

Use the exact CAD command shapes from the Make reference. Generate source
entries with `scripts/gen <entry.step.py> --write`; export STL from a generated
STEP with `scripts/export <part.step> --stl`; run iterative
`verify_project <cad-project> --print-preflight` without `--fresh`. Do not spend
a tool cycle rediscovering those interfaces or attempt generation against an
output `.step` file.

On resume, inspect durable files and the latest failing check first. Never
restart concept exploration, regenerate passed outputs, or wait on optional
delegation. A stage finalizer that can already pass takes priority over more
polish. This profile does not waive Wish fidelity, Inventor Taste, full-tier
CAD checks, Quest Playtest, manual quality, or authenticated Factory
publication. Lower spend counts only when the exact product remains
distinctive, desirable, truthful, and gate-complete.
