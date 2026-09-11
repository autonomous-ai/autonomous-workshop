# ADR 0065: Published toy corrections start independent runs

- Status: Implemented; deterministic tests only, no live corrected publication yet
- Date: 2026-09-11

`workshop fix TOY_DIRECTORY --prompt TEXT` (or `--prompt-file FILE`) verifies
and clones a schema-v4 public toy archive into a new Spark run. The source must
contain a manifest-bound public publication record and editable CAD source.
This is a local archive import, not a live check that its listing remains public.
URLs and private run directories are not supported input formats.

The exact correction prompt becomes the new Wish. Its context records the
source title, public URL, archive identity and baseline ZIP hash. The original
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

Tests cover exact prompt preservation, deterministic snapshots, distinct ids,
editable-copy isolation, archive drift and link rejection, draft rejection,
unsafe ZIP paths, immutable baseline revalidation, CLI controls and a fake
native launch with a fresh Spark checkpoint. Rainward Sun's checked-in archive
also passes read-only intake. These checks do not establish repair quality or
live publication of a corrected Rainward Sun.
