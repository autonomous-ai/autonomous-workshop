# ADR 0028: Bound Forge and Quest turns without lowering reasoning

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, workflow, and product-run protocol maintainers
- Relates to: ADR 0023 (bounded Spark turns), ADR 0027 (all-printable preflight)
- Superseded for new runs by: ADR 0030 (stage-shaped deep economics)

## Context

Moonseed Bloom tested Forge with a six-part kinetic celestial flower. Invent
used one 23m23s high-reasoning turn to reject an overpacked barrel cam and seal
a simpler concept. Make then used a 60-minute timeout and a 44m58s failed turn.
One explicit operator resume spent another full 60-minute turn without a Made
proposal, then 39m48s reaching a host-rejected proposal, then 24m31s reaching a
second host-rejected proposal. The CLI automatically opened another Make turn;
the operator stopped it after 30s with the session and all artifacts preserved.
Across Make, only two of five completed turns reported terminal usage, yet they
already recorded 20,073,838 input tokens and 46,763 output tokens. The Invent
turn separately recorded 6,705,241 input and 48,490 output tokens.

The run's exact visual evidence remained weak: its schema-v5 critic described a
mechanical sculpture with cactus forms, exposed linkages, and faceting that may
read rough, yet marked it finished and desirable. More unrestricted turn time
did not create a better concept or a cheaper proof path.

Spark already showed that a frozen compaction ceiling and shorter native-turn
boundary can limit runaway spend without weakening deterministic gates. Forge
and Quest still need high reasoning for concept selection, causal design, and
Playtest interpretation, so simply copying Spark's low-reasoning profile would
trade away the quality side of the objective. The deep profile uses a smaller
32k ceiling because Moonseed's measured Make rows were dominated by repeated
cached context, while durable stage files and artifacts remain authoritative.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v1.md`. Their one native
Manager session retains high reasoning effort while adding:

- a 32,000-token automatic context-compaction ceiling;
- a 30-minute boundary for every Invent, Make, Playtest, and Release turn; and
- at most eight native turns across one `wish` or `resume` invocation.

A timeout uses the existing same-session bounded recovery path. It does not
restart a stage, create a replacement Manager, or waive a gate. Two consecutive
recoverable turns therefore bound one unattended failure window to at most one
hour instead of two.

The frozen product-run guidance also requires deep efforts to earn complexity:
novelty should come from one memorable relationship or interaction. Invent
must prove the hardest causal or kinematic relationship with the smallest exact
geometry that can falsify it before Make commits to detailed parts. Recovery
continues from exact existing bytes and the remaining failure instead of
repeating passed research, modeling, export, review, or verification work.

The Make finalizer also requires exactly one non-part `*.step.py` combined CAD
entry. Auxiliary presentation or state generators remain ordinary helper
modules. This matches the isolated host verifier's deterministic inference and
rejects ambiguity before another host rebuild.

Frozen older runs retain their historical runtime profile on resume.

## Consequences

- Forge and Quest keep the reasoning profile intended to protect concept and
  Playtest quality.
- Compaction bounds context growth across their longer Wish-wide sessions.
- One runaway native turn loses at most 30 minutes; the existing automatic
  recovery window loses at most 60 minutes.
- Rejected proposals cannot silently expand one unattended deep-effort command
  toward the historical 32-turn ceiling; an explicit resume is required after
  eight total turns.
- The change does not add a Python planner, judge, retry loop, or quality waiver.
- A fresh production Quest and Forge run must still demonstrate the combined
  quality-and-economics improvement; the policy alone is not proof of success.

## Verification

- Launcher tests bind the new settings to marked Forge and Quest checkpoints.
- Compatibility tests prove older Forge and unmarked Spark checkpoints retain
  the historical high-reasoning profile.
- Full runtime and workflow tests must pass before publication of the change.
