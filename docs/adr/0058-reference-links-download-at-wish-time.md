# ADR 0058: A reference link is downloaded once at Wish time and sealed as bytes

- Status: Accepted
- Date: 2026-09-08
- Owners: Wish intake and CLI maintainers

## Context

`--ref` (ADR 0053 and the wish-reference-images change) attaches reference
images to a Wish as exact bytes: the CLI validates each file, `WISH.json`
binds it by size and SHA-256, the host materializes it read-only under
`wish-references/`, and every checkpoint re-verifies it. The value had to be
a local file. Operators driving the Workshop from a phone or a chat bridge
usually hold a link, not a file, and the manual detour (download, copy to the
box, pass the path) was the step that got skipped or done with the wrong
image.

## Decision

`--ref` accepts an `http://` or `https://` link next to a local path. The CLI
downloads the link once, inside `load_wish_references`, before the Wish is
created, and from then on the reference is bytes like any other:

- The download is bounded: at most `MAX_WISH_REFERENCE_BYTES` (12 MB, one
  byte more is read only to prove the excess), a 30-second timeout, a plain
  `User-Agent`, and redirects only to another http(s) location. A redirect to
  `file:`, `ftp:`, or `data:` is refused. A non-2xx status, an unreachable
  host, or a body that is not a single-frame PNG, JPEG, or WebP fails the
  command with the link named, before any run starts.
- The reference is named from the last segment of the link's path
  (`.../Grey%20Duck.png?raw=1` becomes `ref-NN-grey-duck.png`); a bare origin
  becomes `ref-NN-image.<ext>`. The extension always follows the decoded
  format, never the link.
- `WISH.json` records where each downloaded reference came from under
  `context.reference_sources` (`{name: link}`); local file paths are not
  recorded. The link is provenance for a human reader, not an input: the
  bytes stay bound by SHA-256, and the run never fetches anything itself.
- `--ref` values are strings now, not `Path`s; `Path("https://…")` would have
  collapsed the `//`. A `Path` object handed to the loader is still a file.

## Alternatives considered

- Downloading inside the run (the Manager fetches the link during Make):
  rejected. It hands the run a network side effect and a mutable input, and
  the checkpoint could not re-verify what the link served at the time.
- Storing the link in `WishReference` itself: rejected. The reference schema
  is sealed into every checkpoint and the toy archive; a link is context, not
  identity, and `context` is already the free-form provenance mapping.
- Accepting any URL scheme urllib supports: rejected. `file:` and `ftp:`
  would turn a typed command into a local file read or an unauthenticated
  fetch with different failure modes; http(s) is what a person pastes.

## Consequences

- One network call per link at Wish time, on the operator's machine, with the
  operator's network. There is no proxy, retry, or authentication support: a
  link that needs a login must be downloaded by hand as before.
- Error text names the link, so a Telegram-driven operator can see which
  reference failed without opening the box.
- `wish_reference_sources` and `is_reference_url` join the public
  `workshop.wish` surface; `LoadedWishReference` gains `source` and
  `downloaded`.

## Compatibility and migration

Local paths behave exactly as before, and a Wish with only local references
has an unchanged context. Existing `WISH.json` files need no migration; the
new `reference_sources` key appears only when a link was used.

## Verification

`tests/wish/test_references.py` runs a loopback HTTP origin and covers a
downloaded reference mixed with files, redirect within http, refused
redirects off http, 404, a declared and an undeclared oversize body, an
unreachable host, and a link whose bytes duplicate a file.
`tests/cli/test_cli.py` covers the sealed `reference_sources` context and the
progress line, and a dead link stopping the command before any run starts.
