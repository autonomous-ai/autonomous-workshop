# ADR 0065: Toy corrections start independent runs

- Status: Implemented; live-validated by corrected publications
- Date: 2026-09-11
- Updated: 2026-09-17

`workshop fix TOY_DIRECTORY --prompt TEXT` (or `--prompt-file FILE`) verifies
and clones a schema-v4 toy archive into a new Spark run. The source must
contain a manifest-bound publication record and editable CAD source. Its
recorded status may be `public` or `unreleased`; a Factory `draft` is still
rejected, because a draft is half of an external effect rather than a finished
local toy. This is a local archive import, not a live check that a listing
remains public. URLs are not a supported input format.

A private run workspace is also accepted, identified by its
`.workshop-product-run-root` marker and requiring a sealed
`artifacts/release/release.json`. It is not a second import path: the host
first projects that run into the ordinary unreleased archive from its accepted
Made and Release contracts, then imports that archive through the single
existing route. Only contracts the run itself sealed are read; host state,
gates, the effect ledger, credentials and the native session are never touched,
so a workspace import grants no authority an archive import would not.

The exact correction prompt becomes the new Wish. Its context records the
source title, its publication status, its public URL when it has one, the
archive identity and the baseline ZIP hash. The original
Inventor is retained through the ordinary explicit-selection binding; its
currently installed eligible bundle is frozen with current tools for the new
run. An unavailable Inventor fails normally rather than silently substituting.

Each invocation allocates a new Wish id, workspace, native root session, budget
and effect ledger. The normal Spark Make-to-Release path applies. The old
session, gates, budget, credentials and publication authority are never copied
or resumed. The new host publication creates its own import through the normal
Factory path. The original listing and archive remain unchanged.

`revision-source.zip` is an immutable input bound both to the Wish and the
checkpoint and rechecked on resume. It has its own 128 MiB compressed limit;
expanded source is also bounded to 128 MiB. It does not consume the instruction
or image-reference byte allowance. `revision-work/` contains separate writable
files made before the first checkpoint is committed. No symlinks, hidden files,
agent-control files or unmanifested content are imported. The unbound root
README is omitted; all manifest-bound source and historical evidence survive.

The native Manager reuses that work and preserves original behavior outside
the correction brief. It creates a clean current product tree, uses a distinct
revision title and new Wish identity, and regenerates current checks and review
evidence. Historical review/publication files are data, not passing gates for
the new run. Existing independent blind review first records unprimed reads,
then compares each positive and negative correction requirement separately.
Python neither interprets the correction nor judges the images. Spark retains
Make-owned verification and host-only publication; no extra host CAD gate or
native Release turn is added.

## Unreleased corrections

`--no-publish` on `workshop wish` or `workshop fix` freezes one restriction in
the run authorization (schema 4, `local_release_only`). Release still evaluates
its whole gate: local package acceptance, the print-ready CAD guard and the
sealed Release-to-Made binding. It then performs no Factory effect at all — no
credential read, no ledger row, no receipt — and projects
`toys/<inventor>-<slug>` with `publication.status = "unreleased"`, no page URL,
no listing and no readback identities. The gate records
`release.local-unreleased-output-v1`, `publication_status: unreleased` and
`factory_readback_verified: false` rather than claiming a publication.

The slug is derived from the exact sealed Release title and the timestamp from
when the Release contract was sealed, so reprojecting the same run is
idempotent rather than a collision. `--no-publish` and `--github` are mutually
exclusive: an unreleased run has no public archive to push.

The restriction is frozen against everything the run itself can do. A resume can
neither add nor drop it, no agent turn can reach it, and the Factory effect
helper is a single choke point that refuses such a run outright, so neither a
legacy Deliver promotion nor any automatic path can publish a toy the operator
asked to keep local, and a run started to publish cannot be silently downgraded.
Because an unreleased archive is an accepted `fix` source, a chain of
single-change corrections can be kept private and published only by the last run
in the chain.

`workshop publish <wish-id>` is the one exception, and it is the operator
changing their mind rather than the run escaping its restriction. It requires a
run already complete at Release, drops `local_release_only` as a deliberate,
explicit act, and drives the same choke point with the bytes that run already
sealed: no agent session, no tokens and no regenerated geometry, so what gets
listed is exactly what was reviewed locally. If publication does not reach
verified public readback the restriction is restored, so the run reports
`unreleased` again and no automatic path can resend it. Restoring the
restriction does not erase Factory state: a durable draft receipt and its
ledger intents are kept deliberately, so the next `workshop publish` reconciles
that draft and completes the transition instead of uploading the design twice.
This is a
deliberate revision of the original "no later path" guarantee: the guarantee now
binds the run and every automatic path, not the person who owns the toy.

Tests cover exact prompt preservation, deterministic snapshots, distinct ids,
editable-copy isolation, archive drift and link rejection, draft rejection,
unreleased-archive acceptance, unsafe ZIP paths, immutable baseline
revalidation, CLI controls and a fake native launch with a fresh Spark
checkpoint. An end-to-end Spark run with `--no-publish` asserts that no Factory
mock is ever reached, that the projected archive records `unreleased`, and that
both the archive and the run workspace are then accepted as correction sources.
A second end-to-end test publishes that same sealed run afterwards: it asserts
no native session may start, that the model bytes handed to Factory are the ones
the unreleased archive already carried, that the checkpoint is unchanged, that a
Factory that never answers leaves the restriction in place, and that a second
publish reports the existing listing instead of resending it.
Rainward Sun's checked-in archive also passes read-only intake.

The path is live-validated end to end. Correction runs from the Rainward Sun
archive published two corrected toys, each with its own Wish identity and its
own publication record: Rainward Flow (`wish-20260911-161806-46d9d5ed`) and
Rainward Lowflow (`wish-20260912-042535-b2afa8bf`). The original Rainward Sun
run, listing and archive are unchanged, as the contract requires.

The deterministic tests still do not measure repair quality. Whether a given
correction brief achieves its intent remains a per-run judgement, and a
correction may itself be corrected.
