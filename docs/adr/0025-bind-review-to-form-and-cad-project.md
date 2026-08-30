# ADR 0025: Bind Make review to form and the declared CAD project

- Status: Accepted
- Date: 2026-08-30
- Owners: Make, product-run instruction, CAD skill, and public archive maintainers
- Relates to: ADR 0020 (signature evidence), ADR 0022 (blind review), ADR 0023 (semantic review)
- Supersedes for new runs: ADR 0023's schema-v3 signature review

## Context

Orbit Cradle was a real published Spark v3 run. Its review correctly identified
the moon, star, rocking action, and joined relationship. The sealed concept also
promised a pillow-rounded lunar cabochon rather than a flat crescent plaque, but
the exact product remained a constant-depth extrusion. Schema v3 had no
separate blind form read or concept-bound anti-generic comparison, so semantic
nouns and action could pass while the promised sculptural character disappeared.

The same run spent two additional Make turns on an avoidable directory error.
The native session ran final verification at the product root, then declared a
`cad/` directory containing only renders. The finalizer accepted an unrelated
root-level verification report; the trusted isolated host rebuild correctly
rejected `cad/` because it contained no combined entry.

## Decision

New Make finalizers require schema-v4 `SIGNATURE-REVIEW.json`. Before reveal,
the one bounded critic separately records the exact product's volumetric form,
cross-section, and surface language. After learning the Wish and canonical
Invented concept, it must affirm both visible form fidelity and the concept's
anti-generic signature. The review stores the canonical `concept_sha256` in
addition to the exact image hashes. Form, subjects, action, relationship,
anti-generic signature, desirability, and overall experience must all pass.

The finalizer also requires `cad_verification_path` to be inside the declared
`cad_project_path`. The product-run instruction names that project as a
self-contained directory containing its build/import entry, local source,
render family, and final verification report. Root assembled exports may remain
delivery copies, but cannot stand in for the isolated build project.

## Consequences

- Correct nouns no longer conceal a generic extrusion that contradicts the
  selected concept's form language.
- The critic remains one native reviewer with at most two rounds; no Python
  vision judge or additional model call is introduced.
- A mismatched CAD project/report fails in the cheap run-local finalizer before
  a host rejection and another native turn.
- Frozen older runs retain their materialized schema and verifier bytes.

## Verification

- Finalizer tests reject false form fidelity, a missing anti-generic signature,
  a stale concept hash, and a verification report outside the CAD project.
- CAD tests reject malformed schema-v4 review evidence before geometry work.
- Deterministic Spark, Forge, and Quest end-to-end fixtures use an in-project
  report and concept-bound schema-v4 review.
