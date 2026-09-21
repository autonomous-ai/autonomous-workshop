# ADR 0069: Make visual continuity and an operator-controlled final-review experiment

- Date: 2026-09-21
- Status: Implemented; deterministic validation and live experiment tracked separately
- Supersedes ADR 0060's unconditional final critic only when explicitly disabled

Make's intermediate visual review remains the native Manager's own inspection,
not a newly spawned critic. The earlier feedback schema allowed a global form
finding to disappear after local repairs. New packets carry unresolved findings
with stable IDs, bind prior summaries/packets/images, and require each closure
to cite a current rendered image and describe the visible change. Pending
observations and failed renders retain the backlog. Overall form and assembly
have separate assessments; a pass requires both and no remaining findings.
Wish reference files are included even in component packets without an explicit
likeness argument. Python validates evidence continuity, never visual truth.
The Manager can still misjudge an image; these checks cannot prove likeness.

`wish`, `start`, `fix`, and `resume` accept `--check-final-review true|false`.
New runs default to true. Resume omission preserves the saved choice; an
explicit choice refreshes the carried CAD/Make-round tools and finalizer through
the existing recorded host correction and native-session rebind before changing
the option. The root read-only `FINAL-REVIEW-OPTIONS.json` is covered by the
immutable input manifest. Older workspaces without it retain mandatory review.
No existing run is modified merely by installing this change.

With false, Make omits the final independent still-image and animation critic.
The native round inspection, early proof, enabled engineering checks and Quest
Playtest remain. The deterministic omission helper writes
`snap/FINAL-REVIEW-NOT-RUN.json` bound to exact source and final image bytes.
Prior passing review files must be archived outside the product. Both the final
CAD verifier and Make finalizer require valid not-run evidence; product summary
must disclose the omission. The verifier reports not-run, never critic pass.
Motion sweeps still follow their separate option; an omitted animation critic
does not establish visual motion quality. Reenabling review restores its normal
gate and allowance. Host Spark acceptance/publication boundaries do not change.

Validation covers dropped findings, pending/error continuity, separate form and
assembly outcomes, incorrect closure evidence, altered history/references,
policy defaults and malformed inputs, source/image drift, disclosure, real
engineering dispatch while the critic is omitted, immutable input tampering,
and same-session resume with interrupted tool rebind recovery. A live Femto
comparison is requested, but software tests alone do not establish improvement,
token savings, physical printability, or successful publication.
