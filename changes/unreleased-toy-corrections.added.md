- Add `--no-publish` to `workshop wish` and `workshop fix`. Release still seals
  and projects the toy, but performs no Factory effect at all and records
  `publication.status = "unreleased"` in `toys/<inventor>-<slug>/`. The
  restriction is frozen in the run authorization (schema 4,
  `local_release_only`), so a resume can neither add nor drop it, and it cannot
  be combined with `--github`.
- Add `workshop publish <wish-id>`, which lists the sealed Release of a run kept
  local with `--no-publish`. It runs no model, spends no tokens and regenerates
  no geometry: the exact bytes that run accepted are the ones published, so the
  listing is what was reviewed locally. The restriction is dropped only for the
  attempt and restored unless publication reaches verified public readback; any
  durable Factory draft is kept so a second `workshop publish` finishes that
  draft rather than uploading twice, and a run that already published is
  reported rather than resent.
- `workshop fix` now accepts an unreleased archive, and a private run workspace
  that has sealed its Release, in addition to a published archive. A workspace
  is projected into the same archive contract before import, so a chain of
  single-change corrections can stay local until its last run publishes. A
  Factory `draft` is still rejected.
