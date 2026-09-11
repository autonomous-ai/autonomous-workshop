# Integrations

Owns the authenticated Factory adapter used for the host-effect portion of
Release. `factory.py` builds an exact sealed model-and-Release ZIP handoff,
uses the selected Inventor's host-only generated Factory username/password,
carries the existing Make assets for Spark or the canonical `MANUAL.pdf` for
the other release routes, and proves public publication by
authenticated hash readback. The existing session exchanges the pair for a
365-day bearer and keeps it in memory only. The selected Inventor remains
sealed product provenance and selects a local credential file; it is not the
Factory authentication identity.
The local product must pass its frozen stage contracts before this effect
starts. Spark accepts Make's engineering evidence without a host CAD rebuild
or another PDF. Release remains incomplete
until Factory readback verifies the exact public bytes. Unsupported remote
field limits fail closed; Python never rewrites Codex copy. Credentials remain
in the host process and never enter the Codex toy project, ledger, Receipt, or
artifact tree.

The handoff is bounded by Workshop's 50 MiB client limit. Import-specific
HTTP 500 and 524 responses are recorded as proven no-effect rejections, per
Factory's import contract, so the exact request may be reopened safely. Other
uncertain import, content, or publication outcomes remain fenced until an
authenticated readback can reconcile them. That fence protects the remote
effect and leaves Release waiting rather than claiming success or blindly
repeating a possibly completed publication.

For mixed Spark products, the handoff carries only the exact hash-bound public
projection. It preserves all declared public paths, plus Factory's root
`assembled.step` and selected hero aliases. Internal manufacturing records,
sources, and the Wish remain private. This projection is unchanged by transport
compression; it adds no native stage, geometry check, or engineering claim.

New mixed imports use the explicit host-only
`carrier_format: "factory-mixed-deflate-v1"` request and receipt field. This
separate codec uses ZIP DEFLATE with fixed metadata, sorted members and level 9
when first built. Canonical Packs and all print imports remain ZIP_STORED.
Every existing import intent without a format field retains its exact stored
contract; unknown formats and format changes are refused. The public projection
and native Make/Release schemas do not change.

Both codecs retain the same bounds: 50 MiB transport, 95 MiB per expanded file,
512 MiB total expanded content, and 4,096 artifact entries plus the inventory.
Compression can reduce upload size; it cannot make an oversized member valid.
The expanded inventory remains `_inventor-artifact.json`. Standard DEFLATE is
supported by the inspected Factory archive importer; this is not a claim that
the current deployment or a live upload has been verified.

Compressed byte identity is not promised across zlib versions. Before preparing
an effect, the host exclusively installs the first exact carrier at
`factory-carriers/<handoff-artifact-sha256>.zip` beside its private effect ledger
(directory 0700, file 0600), with file and directory durability barriers. It
reuses an orphan left before intent creation. Once bound, every planned,
rejected, unknown or completed import requires that exact saved ZIP hash and
the same current expanded handoff identity. Missing, stale, altered or unsafe
cache files fail closed; reconciliation never silently recompresses or uploads
different bytes. The private carrier is transport evidence, not a new agent
input or public manufacturing artifact.

Outside the mixed projection, the handoff carries every sealed regular file produced by Make except content
inside `__cadgen__` or `__pycache__`. Paths, sizes, and hashes are recorded in
the handoff facts so source, exports, renders, and evidence cross the Factory
import boundary as exact bytes. Make files that collide with Release-owned
root metadata are preserved under `_workshop/make/`; the canonical Release
version retains the root path.

Multipart occurrence transport remains optional. When the complete Factory
sidecar, or the exact hash-bound native CAD descriptor and product inventory
from which it is derived, validates, the adapter additionally writes Factory's
canonical assembly aliases. Original Make bytes remain present, with conflicting
`*.step.json` files preserved under `_workshop/make/` so Factory cannot interpret
unvalidated metadata as its transport sidecar.

Public API: `workshop.integrations` exports the canonical Factory credentials,
session, client, Release writer, and public transition. The adapter depends on
runtime-owned `Receipt` and `EffectLedger` contracts; runtime never imports an
integration.
