# Reviewed upstream integration patches

These patches preserve audited changes that Alice requires in internal R&D
repositories but cannot currently push to their upstream owners.

## Vibe exact-rules draft contract

`vibe-ideas-exact-rules.patch` applies to
`reinSPQR/vibe-ideas` at base commit
`ed3d1e876faed95b1bf785af2fae2a8133354517`. It makes the project-owned
`RULES.md` authoritative in the Factory archive, preserves its bytes exactly,
and declares `RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"`.

Alice's `PageBuilderAdapter` statically verifies that declaration and pins the
operator source for the lifetime of the worker. An unpatched or subsequently
changed operator is not draft-ready and cannot create a remote draft.

The reviewed local upstream commits are:

- `bf73c43` — preserve reviewed rules in Factory drafts;
- `4be5410` — declare the machine-readable archive contract;
- `ab7394c` — accept only exact Alice exports as a private-draft alternative
  to Vibe's older pre-draft owner queue gate;
- `57aff9d` — bind Vibe's root `idea.json` copy and source-artifact manifest to
  the reviewed Alice export;
- `28e484e` — name the audited private-draft handoff and explicitly record that
  it does not mutate or require Vibe's legacy owner queue transition;
- `82fce0d` — reject noncanonical or duplicate-key export receipts before the
  draft operator can run;
- `73d9bfd` — reject aliased/noncanonical source-artifact paths.

Apply the portable patch from the root of the matching Vibe checkout:

```sh
git apply /path/to/alice/integrations/vibe-ideas-exact-rules.patch
python3 -m unittest board-game/tools/test_publish.py -v
```

Do not use `--3way` or apply it to an unknown revision. Re-audit and regenerate
the patch when the upstream publisher changes.
