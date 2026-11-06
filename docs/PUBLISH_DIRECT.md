# Publish directly from a CAD project

`tools/publish_direct.py` publishes a toy that was built outside Workshop, in
autonomous-product-to-cad. It applies Release's host-owned Factory effect
without the Workshop lifecycle that normally comes before it. It reuses the
Spark publication path ([ADR 0061](adr/0061-spark-make-owned-verification.md),
[Publish a terminal Release](PUBLISH_SEALED_PRODUCT.md)): the same Release
carrier, the same Factory adapter, ledger and readback. There is no second
publisher.

Status: implemented and deterministically tested. Its dry run was checked
against a real staged archive. It has not published live. The gate evidence
requirement and the publication record follow the owner's decisions of
2026-10-28.

## Use

```bash
# evidence: run autonomous-product-to-cad's verify_project --fresh --print-gates
# on the project, in place, and write measure/direct-publish-evidence.json
PYTHONPATH=src uv run python tools/publish_direct.py --cad-dir <project> \
  --inventor rowan-vale --verify --verifier-repo ../autonomous-product-to-cad

# dry run (default): stage, build the exact handoff ZIP, print it with the
# evidence status and every reason --live would refuse; nothing is sent
PYTHONPATH=src uv run python tools/publish_direct.py \
  --archive ../toy-archives-staging/rowan-vale-<slug> --inventor rowan-vale \
  [--known-gate-failure check_thickness:<reason>]

# what autonomous-product-to-cad's skills/toy-archive/scripts/publish runs
PYTHONPATH=src uv run python tools/publish_direct.py --cad-dir <staged project> \
  --primary-step <name>.step --product-id <id> --title "<Title>" \
  --summary "<...>" --inventor <id> --verifier-repo <repo> \
  [--known-gate-failure <gate>:<reason>] [--live]
```

| Option | Meaning |
|---|---|
| `--cad-dir DIR` or `--archive DIR` | The source. `--cad-dir` is a CAD project in its own layout (`*.step.py`, `*.step`, `snap/`, `measure/`). `--archive` is a schema 4 public toy archive packed by `toy_archive pack`. Its `MANIFEST.json` is re-hashed with Workshop's `build_public_archive_manifest` before use. |
| `--inventor ID` | Required. It must be a roster Inventor under `inventors/`, and `--live` needs that Inventor's own credential file. |
| `--primary-step NAME` | The top-level STEP that crosses as `assembled.step`. Default: the one top-level entry that declares `PRINTABLE = True`. |
| `--display-only BODY` | Repeatable. A body of the primary STEP that the buyer does not get, such as a prop placed for the renders. It is removed from `assembled.step` and is not billed. See [Printed bodies only](#printed-bodies-only). |
| `--bought BODY=PART` | Repeatable. A body of the primary STEP that is bought hardware the buyer gets (a rod, a nut, ballast). It is removed from `assembled.step` and billed as a Factory extra material under PART, a Bought Part catalogue id or a plain name. Bodies naming the same PART are counted together. |
| `--part-price PART=CENTS` | Repeatable. What one PART costs, in whole US cents. Required for every `--bought` part the catalogue does not price; refused when it differs from a catalogue price or names no `--bought` part. |
| `--product-id ID` | The ledger key and the unknown-import discovery slug. Default: the directory name, without the `<inventor>-` prefix for an archive. |
| `--title`, `--summary` | Default: the README's first heading and first paragraph. The title follows [TOY_NAMING.md](TOY_NAMING.md). |
| `--what-arrives`, `--limitation` | Optional and repeatable. These become Made facts, and Factory's copy auditor reads them. |
| `--verify` | `--cad-dir` only. Runs autonomous-product-to-cad's `skills/cad/scripts/verify_project --fresh --print-gates --assembly <primary entry>` on the project, in place, and writes `measure/direct-publish-evidence.json`. The checkout comes from `--verifier-repo`, `$PRODUCT_TO_CAD_REPO` or the sibling directory. The interpreter is `--verifier-python`, that checkout's `.venv`, or this one. |
| `--known-gate-failure GATE:REASON` | Repeatable. Lets one failing gate (for example `check_thickness`) through, with the owner's reason. See [Gate evidence](#gate-evidence). |
| `--update-listing SLUG` | Append a version to this public design instead of creating one. See [Update a published listing](#update-a-published-listing). |
| `--reason fix\|reprice` | Required with `--update-listing`. |
| `--published-archive DIR` | `--update-listing` with `--cad-dir`: the toy's packed archive, whose `PUBLICATION.json` names the listing. |
| `--predicted-grams G`, `--predicted-grams-source TEXT` | `--update-listing`: the printed-only primary's mass, measured with Factory's own slice worker, and how. Without them there is no confirmation code. |
| `--confirm CODE` | `--update-listing --live`: the code that run's preview printed. |
| `--reconcile-publish PRODUCT_ID` | Settle that product's `unknown` publish intent by Factory readback alone. Takes only `--inventor`, and never sends. |
| `--reimport-slug SLUG` | Retired: refused, naming `--update-listing`. |
| `--live` | Performs the publication. On success it prints `slug: …`, `public: <url>` and one `publication-record: <json>` line. |

Exit codes: `0` success, `2` input or state refusal, `3` Factory effect
unproven. For exit `3`, re-run the same command. The ledger reconciles the
earlier attempt and never uploads blindly.

Factory makes a design public at once but creates its shop listing a little
later; 20-90 s was observed on 2026-10-29. Workshop's public readback requires
that listing. After the publish call, `--live` therefore re-reads every 10 s
for up to 2 minutes. It does so only while the ledger records the publication
as `unknown`, and it never sends the publish request again. A design whose
listing never appears (Factory computed no `print_specs`) still ends with
exit `3`.

Every run, including a dry run, ends with `live: ready` or `live: refused` and
lists each reason. `--live` checks these before it reads a credential:

- the gate evidence is not `pass`;
- the Inventor has no credential file of its own;
- the archive already records a publication;
- another product id's local ledger records a Factory import, succeeded or of
  unknown outcome, under the slug this title gets (see
  [A toy published under another product id](#a-toy-published-under-another-product-id)).
- the archive was packed for another Inventor.

## Printed bodies only

Factory weighs exactly one file of the handoff: the root `assembled.step`.
It splits that STEP into its solids and slices each one, with no name filter
(`internal/slicer/tree.go` `PrintableSources`, `fetch.go` `splitSolids`).
The weight sets the floor price: `0.052 × grams + $15 + extras`. A
combined review entry places props and bought hardware beside the printed
parts, so publishing it unchanged billed a pair of headphones and a steel
rod as filament (the lamp-post stand, 2026-11-05: 494.7 g weighed, 225.5 g
printed).

So the staged `assembled.step` holds printed bodies only:

- A primary body counts as printed when every solid it holds has the volume
  and surface area of a solid that some top-level `PRINTABLE = True` entry's
  STEP builds. Labels may differ between the scene and the part entry;
  moving, turning or mirroring a part changes neither measure.
- Every other body must be declared, with `--display-only` or `--bought`.
  An undeclared body refuses the publication and is named in the error. So
  does a declaration that names a printed body, or names no body. Nothing is
  dropped without a declaration.
- Declared bodies are removed, and the rest are written with their names
  and colours. When nothing is removed, the primary's bytes cross unchanged.
  A primary that is itself a `PRINTABLE = True` entry is not re-read.
- The dry run lists the removed bodies, and the publication record's
  `primary_model` carries `printed_bodies_of` and `removed_bodies`. Its
  SHA-256 is then that of the printed-only file, not the archive's STEP.
- The handoff carries exactly one STEP, the primary, and no mesh. Factory
  weighs any mesh in preference to the STEP, so the adapter refuses one.
  The full scene stays in Made under `cad/` and does not cross.

`--bought` parts are recorded in Made's `product.json` as `bought_hardware`.
The adapter sends them as Factory `extra_materials` on import, one line per
part priced at unit price × count, for example `M6 nut (x2)`. Factory has no
quantity field. A unit price comes from the Bought Part catalogue's optional
`unit_price_cents` or from `--part-price`; nothing is estimated, and a part
with neither refuses. On 2026-11-06 no catalogue entry carries a price, and
the lamp's rod, nuts and ballast are not catalogued, so each needs
`--part-price`.

## Gate evidence

A Workshop product reaches Release only after Make's gates pass. A direct
publication has no Make, so `--live` requires fresh evidence instead: a
passing `verify_project --fresh --print-gates` run of the exact bytes being
published.

autonomous-product-to-cad's `verify_project` writes
`measure/verification-pipeline.md`. That Markdown table binds no bytes, and
`gen --write` stamps a wall-clock time into every STEP header, so an earlier
record cannot prove which STEP it checked. `--verify` therefore runs the
verifier itself and parses only the newest run in the record. It then writes
`measure/direct-publish-evidence.json` (`workshop.direct-publish-evidence`,
schema 1), which holds:

- the verifier script's SHA-256 and its arguments;
- the exit code and the record's SHA-256;
- each gate row, as its gate (the script name, or `measure/<audit>.py`), the
  entry it measured and `pass`, `fail` or `skipped`;
- the subject: the SHA-256 of every `.py`, `.step` and `.stp` file in the
  project and every `measure/*.json` manifest. `ref/` is included, because a
  source may import a reference STEP. Renders and reports are left out, and
  so is working material (`inputs/`, `transcripts/`), which the toy-archive
  wrapper drops before staging and which is never published.

The file sits in `measure/`, so `toy_archive pack` carries it into
`make/verification/reports/`, and an archive is checked the same way as a
project. Workshop's own vendored verifier is not used. It requires Make's
`snap/SIGNATURE-REVIEW.json` and ignores the project's declared bed, so it
refuses projects built outside Workshop.

The evidence is `pass` only when all of these hold:

- the subject equals the current bytes. Otherwise it is `stale`, and the
  changed paths are named;
- the run used `--fresh` and `--print-gates`;
- `check_mesh`, `check_overhang` and `check_thickness` each ran;
- every failing row (any status but `rc=0` or `skipped`, so a refusal or an
  `accepted-fail` counts) is a gate the owner declared with
  `--known-gate-failure`;
- every declared gate actually failed. A declaration that did not fail is
  refused rather than recorded.

The dry run prints each declared failure and each failing row. The accepted
evidence summary, including `known_gate_failures`, is recorded in the
listing's `workshop-product-facts.json` and in the `publication-record`.
The evidence file is ordinary JSON on the operator's machine. It proves which
bytes a verifier run on that machine saw. It is not a signed attestation.

Because the verifier rebuilds every STEP, run `--verify` on the project
itself, not on a staged copy, and pack the archive afterwards. Then the
upload and the archive carry the same STEP bytes. toy-archive's
`scripts/publish --verify` does this.

## Inventor

`--inventor` names the Inventor whose own Factory account publishes. There is
no fallback to a host-wide account. An archive's directory name
`<inventor>-<slug>` is its public identity under `toys/`. An archive packed
for one Inventor therefore cannot be published under another: the listing and
the archive would name different Inventors. The dry run still shows
everything (the product id drops the packed Inventor's prefix), but `--live`
is refused until the archive is re-packed with `toy_archive pack --inventor
<id>`.

## Publication record

After public readback, `--live` prints one `publication-record:` JSON line,
shaped like a Workshop archive's `PUBLICATION.json`. It contains:

- `identities`: the package (Release carrier), product artifact, Playtest
  omission, product page, primary model, product facts, handoff artifact and
  Pack hashes, the publication anchor path, and the anchor's sent and
  read-back hashes. Unlike a Workshop archive, it has no
  `native_release_sha256`, because no NativeRelease exists.
- `primary_model`: path, bytes and SHA-256, plus `printed_bodies_of` and
  `removed_bodies` when bodies were removed.
- `publication`: slug, page URL, observed time, listing, mode and anchor URL.
- `direct_publish`: `workshop_lifecycle: not-run` and the evidence summary.

toy-archive's `scripts/publish` passes the record to `toy_archive pack
--publication-record`, which merges it into `publication/PUBLICATION.json`
after checking that it names the page being packed.

## How a Workshop Spark run publishes

1. **Wish.** `workshop wish` seals the exact Wish and its product id. Starting
   the Wish is the authorization to publish that run's exact Release bytes.
2. **Inventor.** Selection happens before Make, or is pinned with
   `--inventor` ([ADR 0053](adr/0053-pin-the-inventor-a-start-run-builds-with.md)).
   Release publishes with
   `$WORKSHOP_HOME/credentials/inventors/<inventor>.env`, whose
   `FACTORY_INVENTOR_ID` must match. When that file is absent, Release falls
   back to the host-wide `factory.env`.
3. **Make** runs its own gates (CAD gate, Component reviews, signature
   review, final verifier). Its finalizer then seals the Made tree:
   `product.json` (`title`, `summary`, optional `what_arrives`,
   `limitations`, `status`), the root `assembled.step`, the `cad/` project
   with exactly one `snap/iso.png`, and its `made.json` contract.
4. **Release** is host-only. `prepare_make_output_release` writes
   `artifacts/release/publish-package/`. That package holds `product.json`
   (schema 6, `make-output-ready`, with title, summary and the lists copied
   from Made facts, the Made artifact hash, Playtest `not-run`, and claims),
   `PLAYTEST-NOT-RUN.json`, and an unchanged copy of the README when one
   exists. Release also writes the NativeRelease contract `release.json`.
5. **Effect.** `FactoryReleaseWriter` validates the sealed bytes and logs in.
   It records a hash-bound intent in the run's
   `host_state/factory-effects.sqlite3`. It then imports one ZIP as a private
   draft with category `toys`, tag `toy` and the run's token usage. The ZIP
   holds the whole Made tree except extra STEPs and caches, the root primary
   STEP, the cover aliased to `assembled_review/_assembled.png`,
   `workshop-release-page.json` (the publication anchor),
   `workshop-product-facts.json`, `project.json` and the import-root marker.
   The writer then reads the draft back (owner, title, description, tags,
   category, origin) and re-hashes the anchor from the CDN.
   `FactoryPublicTransition` publishes the draft and reads the public listing
   back the same way.
6. **Records.** The receipt is written to `release-effect.json`, and
   `workshop status` reports it. The public archive `toys/<inventor>-<slug>/`
   is projected with a `PUBLICATION.json` that carries every identity hash.

## Field-by-field gap

The table covers what Factory or Release needs, whether a toy archive (or a
`--cad-dir` project) supplies it, and what the direct tool does.

| Needed by Factory / Release | In the archive? | Direct tool |
|---|---|---|
| Wish text, Wish hash, authorization to publish | No | **Cannot be derived.** `workshop-product-facts.json` carries a `workshop.direct-publish` record with `"wish": null` and `"workshop_lifecycle": "not-run"` instead of a fabricated Wish. The owner's explicit request to run `--live` is the authorization. |
| Product id | Only implicitly, in the directory name | Derived from the directory name. The owner may override it. Keep it equal to the slug Factory will give the title: an unknown-import reconcile looks the design up by this id. |
| Inventor binding | Only in the directory name (`<inventor>-<slug>`); not recorded in Made facts | **Owner supplies `--inventor`.** The tool checks it against the roster and records its display name in product facts, as Release does. An archive packed for another Inventor must be re-packed before `--live`. |
| Factory credential | No, and it must never be | **Owner runs `workshop login <inventor>`.** `--live` refuses without `credentials/inventors/<inventor>.env`. Unlike a Workshop run, it never falls back to the host-wide account, because Factory shows the account that authorized the import as the public author. |
| Make's gates passing before Release | Only the reports in `make/verification/reports/`, which bind no bytes | **`--live` requires gate evidence.** It must bind a `verify_project --fresh --print-gates` run to the exact source and STEP bytes, and every failure must be owner-declared. See [Gate evidence](#gate-evidence). Make's reviews still do not run. |
| Made tree, sealed by Make's finalizer after its gates | `make/source/cad`, `make/models/cad`, `make/verification/{reports,renders}` | Restaged into the Spark Made shape: root `product.json`, root `assembled.step`, and `cad/` in the project's own layout. It is hashed at staging. A `--cad-dir` project and its packed archive stage identical Made bytes. No finalizer or gate runs. |
| `product.json` title and summary | The README heading and first paragraph | Derived, or set with `--title`/`--summary`. A title over 300 characters is refused, not truncated. |
| `what_arrives`, `limitations` | No | Optional and owner-supplied. When left empty they are empty, as Civic Skyline's are. Only the owner can state them honestly. |
| Made `status` / geometry disclosure (`GEOMETRY-NOTES.md`) | No | Not set. The page makes no geometry or print-ready claim. |
| Primary STEP | Yes, but which file is primary is not recorded | Derived: the single `PRINTABLE = True` entry, or `--primary-step`. It must start with `ISO-10303-21`. |
| Exactly one STEP in the handoff | All STEPs are present | The same adapter rule applies: only `assembled.step` crosses. Per-part STEPs stay local, and the dry run lists them. |
| Cover: exactly one `snap/iso.png` | `make/verification/renders/iso.png` | Mapped to `cad/snap/iso.png`. A likeness mask (more than 90 % neutral pixels) and a second `snap/iso.png` are refused. |
| Release carrier (schema 6 page, `PLAYTEST-NOT-RUN.json`, README copy) | No | Derived by the same `make_output_release_product`. Playtest is truthfully `not-run`. |
| NativeRelease contract, stage checkpoints, Release gate | No | **Skipped.** No `release.json`, checkpoint or gate exists. |
| `project.json` design notes, import metadata (category `toys`, tag `toy`, no prompt) | Not applicable | Produced by the unchanged adapter. |
| Token usage sent with the import | No | Omitted. No Workshop budget exists to report. |
| Wish reference images, the owner's request | `ref/`; a raw project also has `inputs/`, `transcripts/` | Dropped, as the toy-archive packer drops them. Spark never ships Wish references either. |
| Sanitized text (no host paths) | Yes; `toy_archive` sanitizes | The archive is already sanitized, and so is a `--cad-dir` staged by the wrapper. For a raw project the dry run warns about each text file that names a home directory. Workshop's own handoff does not sanitize either. |
| Secret scan, size limits (96 MiB Pack, 95 MiB file), STEP only | n/a | The same `build_pack` checks apply. Mesh files and hidden files are refused. |
| Part colours | Colour lives in the STEP (multi-material) | Not written, the same as Spark: Make-output imports skip the colour effect, so Factory renders its own mesh colours. |
| Price, BOM, material, print settings | README and spec only | Not sent: no explicit price is submitted, and the README and spec cross as files. A Workshop Spark run sends its contract's print material and assembly in `project.json` (ADR 0093, 2026-11-04); a direct publication has no sealed contract, so it does not. |
| Effect ledger, idempotency | No | `$WORKSHOP_HOME/direct-publish/<product-id>/factory-effects.sqlite3`. A re-run with the same bytes reconciles. Changed bytes for an already published product id are refused, so no second design is created. The ledger is machine-local, so another machine has no record. |
| Draft readback, anchor readback, public readback | n/a | The same adapter. Success is printed only after public readback. |
| `release-effect.json`, `workshop status`, `toys/` projection with identity hashes | No | `workshop status` never sees a direct publication. The `publication-record` line carries the receipt's identity hashes, and the toy-archive wrapper merges them into `PUBLICATION.json`. |
| Re-import of an existing design | No | `--update-listing SLUG --reason fix\|reprice` appends a version to the public design (see [Update a published listing](#update-a-published-listing)). `workshop fix` still publishes corrections as new designs by default ([ADR 0065](adr/0065-published-toy-correction-runs.md)). |
| An archive that already records a publication | `publication/PUBLICATION.json` | `--live` is refused, because a second create would duplicate the listing. |
| A CAD project for a toy already published under another product id | No | `--live` is refused when another product id's ledger records an import under the slug the title gets. See below. |

## What a direct publication skips

These run for a Workshop product and never run here. A direct listing claims
none of them:

- the Wish and the Inventor selection;
- Make's CAD gate and its Component, Contract and signature reviews. The
  print gates are covered by the required gate evidence instead;
- Playtest, which is recorded as `not-run` exactly as Spark records it;
- the NativeRelease contract, stage checkpoints and the Release gate;
- `release-effect.json` and `workshop status`.

Apart from `direct-publish-evidence.json`, the reports under
`make/verification/reports/` cross as plain files. Neither Workshop nor
Factory reads them as passing evidence.

## Per product, the owner supplies

1. The Inventor, and a stored credential for it (`workshop login <inventor>`).
   For the current products this is `rowan-vale`, and their archives are
   packed under that name.
2. Gate evidence (`--verify` on the project), and a `--known-gate-failure`
   with a reason for each failure they accept.
3. The decision to publish, given by running `--live`.
4. A `--display-only` or `--bought` declaration for every body of the
   primary STEP that is not printed, and a `--part-price` for each bought
   part the catalogue does not price.
5. Optionally, a product id, a title and summary other than the README's,
   and the `what_arrives`/`limitations` lines.

## A toy published under another product id

A `--cad-dir` source carries no `PUBLICATION.json`. Its product id is
derived from the project's directory name, while an earlier publication may
have used another one. The R24 palm vase is an example: its project is
`r24-synthwave-palm-vase-taper`, but it was published as
`synthwave-palm-bud-vase`. The ledger keyed by the new id is empty, so
before this check, `--live` would have created a second design.

For every source, `--live` and the dry run therefore read every local ledger
under `$WORKSHOP_HOME/direct-publish/`, without writing to them. A ledger
refuses the publication when all of these hold:

- it belongs to another product id;
- it records a `factory-import` that succeeded or whose outcome is unknown;
- its receipt slug, or its requested title, slugifies to the slug of this
  publication's title.

The refusal names the earlier product id, its slug, its page and the
import's state. An import whose outcome is unknown counts, because it may
have created a design. A rejected one created nothing, so it does not count.
The product id's own ledger is not part of this check. It still reconciles a
rerun of the same bytes and refuses different bytes.

The match is on the slug because the slug is what Factory and the public URL
share. A product id is only Workshop's local key, and Factory never sees the
CAD project's name.

The receipt slug comes from authenticated readback, so it is the strongest
local evidence. The toy archive's `PUBLICATION.json` is copied from that
receipt. The toy-archive wrapper checks it as well, because `toys/` travels
to other checkouts while the ledger is machine-local.

Limits:

- A toy re-titled with `--title` gets another slug, so this check does not
  catch it.
- A toy published only from another machine, with no archive record here, is
  not caught either.

Factory itself is not asked, so the dry run stays offline. To update the
listing the refusal names, see [Update a published listing](#update-a-published-listing).

## Update a published listing

[ADR 0097](adr/0097-listing-updates-append-a-version-to-a-public-design.md)
adds a Listing Update: one version appended to a public design that this
Workshop published. The listing, slug, URL and SKU stay. It is how a toy
published before #219 is repriced, now that props and bought hardware are
no longer weighed.

```sh
# preview: authenticated Factory reads only, nothing is sent
PYTHONPATH=src .venv/bin/python tools/publish_direct.py \
    --archive toys/rowan-vale-otter-bamboo-pen-cup --inventor rowan-vale \
    --primary-step r26-otter-bamboo-pen-cup.step \
    --bought washer_1=washer-m12-iso7089 --bought washer_2=washer-m12-iso7089 \
    --update-listing otter-bamboo-pen-cup --reason reprice \
    --predicted-grams 120.5 --predicted-grams-source "Orca, psb-worker aea8c67, bounded bed"

# the owner reads the prices, then runs exactly that update
... the same command ... --live --confirm lu-0123456789ab
```

**Proof that the design is ours.** The archive's `PUBLICATION.json` names
the slug, and `--update-listing` must repeat it. One local ledger must hold
a succeeded `factory-import` receipt for that slug. The update goes into
that product id's ledger, whatever the archive's directory is called. The
preview then checks, by authenticated readback, that:

- the design is public and its current version is the published one;
- its author is the Inventor's own account;
- its current version's slice is `done`;
- it prints at the shop's 15 % infill. Workshop does not send print
  overrides yet, so a new version would drop any other infill. That is a
  `fix`, and it is refused.

**`reprice` or `fix`.**

- A `reprice` must publish the live printed geometry. The preview reads the
  live version's own `workshop-product-facts.json` from the CDN, and its
  `primary_model.sha256` must be the source primary's SHA-256. After a
  first update it must be the `source_primary_sha256` of the archive's
  latest `versions[]` entry, for the current version. Nothing printed
  changes, so a reprice needs no new gate evidence.
- A `fix` changes printed geometry or print settings, and it needs fresh
  gate evidence exactly as a create does.

**Preview.** Without `--live`, `--update-listing` prints:

- the current price, the listing state, the version, the measured grams and
  the extras;
- Factory's formula applied to those, and whether the current price follows
  it. A price that does not follow it may have been set by hand: Factory
  will not move it, and new extras may pause it;
- the source primary against the live one;
- the new extras;
- the predicted price;
- any refusal;
- a confirmation code.

Factory measures mass only by slicing a live version. So the predicted
grams come from `--predicted-grams`, and without them there is no code.

The code is a short hash of the base design, version, price, grams and
extras, the reason, the source primary SHA-256, the removed bodies, the new
extras and the prediction. It does not hash the handoff ZIP, because those
bytes carry timestamps.

**Live.** `--live --confirm CODE` reads Factory again. It refuses if the
code no longer matches, for example because the base version, the price or
the extras moved. Otherwise it records a `factory-import-version` intent
with a `listing_update` object, keyed on the base version, and then:

1. `POST /designs/{slug}/import` with the handoff and **no** extras;
2. polls `GET /designs/{slug}/slice` until the new version is `done`;
3. `PUT /designs/{slug}/extra-materials` with the new list;
4. reads back the design, the anchor, the extras and the listing.

The extras wait for the slice, so Factory never shows the old mass with the
new extras. On success the tool prints:

- the slug and the page;
- the old and new version, and the old, new and predicted price and grams;
- one `listing-update-record:` line;
- a `publication-record:` line with the schema 2 `PUBLICATION.json`, which
  is the archive's record with `versions[]` appended and the latest price.

The toy-archive wrapper writes the record into the archive. A price that
does not follow the formula is reported as `price not repriced (possibly
set by hand)`, and it is not a failure.

**When it is not proven** (exit 3, rerun the same command):

| Outcome | What a rerun does |
|---|---|
| The POST lost its response | Reads back. If the version moved and its anchor is ours, it carries on from step 2. If Factory still shows the base, nothing is resent and the owner decides. |
| The slice is still running after 30 minutes | It keeps waiting. The extras are not sent until the slice is `done`. |
| The slice failed for good | The extras are not sent. Factory pauses a platform price. The owner decides. |
| The extras write failed or read back different | It sends the same `PUT` again. That is safe, because `PUT` replaces the whole list. |

While one update is `unknown`, every other update is refused until the
first is reconciled with its own `--confirm`. A Factory 4xx whose readback
still shows the base records the intent as rejected, and nothing changed.

## Reconcile an unknown publication

`--reconcile-publish PRODUCT_ID --inventor ID` settles a ledger whose
`factory-publish` intent is `unknown`. That happens when Factory accepted
the publish but its listing was not yet readable within the wait. The flag
runs the unchanged `FactoryPublicTransition` on the ledger's own import
receipt, which reproduces the exact intent. It works only through a session
whose transport refuses everything except `GET` and login:

- if readback proves an active public listing, the intent becomes
  `succeeded`;
- if not, it stays `unknown`, and the run exits `3`.

It never sends a publish.
