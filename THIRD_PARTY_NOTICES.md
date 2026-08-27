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

The Workshop Python host, its contracts, and its schemas were authored for
this repository.

Earlier research examined internal Inventor projects including `text2cad`,
`text2game`, and `vibe-ideas`. Their legacy Python workers and source snapshots
are not shipped in this repository.

## PDF rendering runtime

Workshop depends on `pypdfium2` for portable offline inspection of printable
manuals. The project is available under Apache-2.0 or BSD-3-Clause, and its
PDFium wheels carry PDFium's BSD-style license plus notices for bundled
third-party components. Those license files remain part of the separately
distributed dependency wheel; Workshop does not vendor its binaries.

## Process supervision runtime

Workshop depends on `psutil` to enumerate and identity-pin every member of a
native Codex run's isolated POSIX process session before termination. `psutil`
is distributed under the BSD 3-Clause license; its complete license remains in
the separately distributed dependency wheel.
