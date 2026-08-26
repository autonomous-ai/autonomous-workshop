# Third-party notices and provenance

Autonomous Workshop is licensed under Apache-2.0. The following bundled or
required materials retain their own licenses.

## Peter's text-to-3D tools

The `cad` and `step-parts` skills under `src/workshop/make/skills/` derive from
[`peterat617/text-to-3d`](https://github.com/peterat617/text-to-3d). Their exact
reviewed revisions and local adaptations are recorded in
`src/workshop/make/skills/PROVENANCE.md` and their installed byte identities in
`src/workshop/make/skills/LOCK.json`.

Each skill includes its MIT license, copyright 2026 Thompson Labs LLC. The
`cadgen` material used by the CAD skill, including the pinned `cadgen==0.4.19`
distribution, carries the same included MIT notice.

## Repository-authored work

The `product-to-cad` skill and the Workshop Python host were authored for this
repository. `product-to-cad` applies general measurement-provenance,
multi-view-form, manufacturing, and fail-closed evidence principles without
copying the unlicensed `text-to-3d/skills/image-to-cad` source.

Earlier research examined internal Inventor projects including `text2cad`,
`text2game`, and `vibe-ideas`. Their legacy Python workers and source snapshots
are not shipped in this repository.
