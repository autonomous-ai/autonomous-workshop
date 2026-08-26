# Catalog and provenance schema

Read this only when maintaining the design-reference client or adding a source.

## Source registry

`data/sources.json` is shipped with the skill. Each source has:

- `id`: stable namespace used in catalog ids and output paths;
- `repository`: human-facing source repository;
- `revision`: immutable upstream commit used for sync and fetch;
- `archiveUrl`: archive containing the source batches at that revision;
- `rawBaseUrl`: raw-file origin used to fetch one selected batch, contact
  sheet, and license;
- `license`: name, URL, and a short use restriction that must be shown in
  search and fetch output;
- `adapter`: parser name and expected record count.

Pin revisions. A moving branch makes a cached function hash and a later fetch
refer to different geometry.

## Local index

`sync` writes JSON Lines to `.design-reference-cache/<source>.jsonl` at the
worktree root and an adjacent metadata file. The cache is regenerated data and
must stay ignored by Git. One line represents one callable model:

```json
{
  "id": "source/model_name",
  "function": "model_name",
  "title": "upstream document title",
  "description": "visual description",
  "operationBucket": "4to5ops",
  "operationMin": 4,
  "operationMax": 5,
  "sourcePath": "03_4to5ops/batch_001.py",
  "contactSheetPath": "03_4to5ops/batch_001_contact_sheet.png",
  "position": 0,
  "volume": 1.0,
  "area": 6.0,
  "functionSha256": "..."
}
```

`position` is the zero-based function order in the batch. Volume and area are
upstream validation values, not assumed millimetre-scale dimensions.

## Fetched provenance

`fetch` writes only a selected function excerpt, never the entire batch. The
provenance record contains:

- the complete catalog record;
- repository, pinned revision, upstream paths, and immutable raw URLs;
- the license summary and local license file;
- UTC fetch time;
- SHA-256 and byte size for every managed local file.

The source excerpt intentionally ends in `.txt`. Do not rename it to `.py`
inside this worktree: cadgen scans Python files beyond the named target, and a
reference corpus must never become part of generator discovery.
