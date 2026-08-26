# Third-party notices and provenance

Autonomous Workshop is licensed under Apache-2.0. The following bundled or
required materials retain their own licenses.

## Peter's product-to-CAD tools

The `cad`, `design-reference`, `image-to-cad`, and `step-parts` skills under
`src/workshop/make/skills/` derive from
[`autonomous-ai/autonomous-product-to-cad`](https://github.com/autonomous-ai/autonomous-product-to-cad).
Their exact reviewed revisions and local adaptations are recorded in
`src/workshop/make/skills/PROVENANCE.md` and their installed byte identities in
`src/workshop/make/skills/LOCK.json`.

The `cad` and `step-parts` skills include their MIT licenses, copyright 2026
Thompson Labs LLC. The complete vendored `cadgen` 0.4.19 source inside the CAD
skill, and the pinned `cadgen==0.4.19` distribution dependency, carry the same
included MIT notice.

The pinned upstream `design-reference` and `image-to-cad` trees do not contain
standalone license files. Their inclusion does not imply that the MIT license
above applies to them. `design-reference` can explicitly download a separately
licensed dataset restricted to non-commercial research; fetched references
retain their own license and provenance records.

## Repository-authored work

The `product-to-cad` skill and the Workshop Python host were authored for this
repository. `product-to-cad` remains a distinct workflow for broader
product-design briefs.

Earlier research examined internal Inventor projects including `text2cad`,
`text2game`, and `vibe-ideas`. Their legacy Python workers and source snapshots
are not shipped in this repository.
