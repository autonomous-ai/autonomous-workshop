# Private references for little worlds

The Workshop has a Wish-bound input contract for `little-worlds`
personalization. Eve and other Inventors must not own consent storage or invent
consent/recognition proof.

## Current truth boundary

The current `WorldReferenceVault` is a **same-OS-user local development
backend**, not a production security boundary. It stores content-addressed
reference and customer-attestation bytes with `0700` directories and `0600`
files, rejects symlinks/mutation, and omits raw bytes from its own receipts and
attestations. Inventor contribution code running as the same OS user can still
read those files directly. File modes do not isolate two same-user processes.

For that reason:

- the local backend refuses to open without an explicit
  `trust_same_user_processes=True` development opt-in;
- the CLI requires `--allow-same-user-local-vault` and labels every receipt
  `same-user-local-development`;
- `references add` stages input only; `workshop resume
  --allow-same-user-local-vault` explicitly lets the Manager pass its raw-free
  scope and hashes to shared Invent, while raw-reference Playtest still waits
  for an independent provider; and
- production must put raw bytes behind an authenticated service or OS sandbox
  whose credential/capability never enters the Inventor child process.

The consent file and reviewer id are customer/operator-supplied declarations.
The local HMAC proves only that this Workshop process admitted the exact record;
it does not authenticate the customer/reviewer, establish legal rights, or
prove likeness recognition.

Serialized `consent_*` fields are compatibility names for the supplied
declaration bytes. They do not mean that legal consent was verified.
The declared subject, rights basis, and allowed/excluded feature text is sent
to shared Invent and its model. Do not put passwords, tokens, private keys, or
other secrets in those fields; the Manager rejects known credential shapes
before constructing the handoff.

## Stage a development fixture

First make the Wish normally:

```console
workshop wish "a tiny moon garden with a guardian shaped like my dog"
```

Create the attestation record yourself outside the repository. The Workshop
never writes or invents this file. For a trusted local development fixture only:

```console
workshop references add wish-20260826-010101-abcdef12 customer-dog /secure/dog.jpg \
  --consent-file /secure/customer-attestation.txt \
  --media-type image/jpeg \
  --subject-kind customer-owned-subject \
  --subject "the customer's dog" \
  --rights-basis "customer owns the reference and authorizes this toy" \
  --allow "proud neck posture" \
  --allow "round ears" \
  --exclude "home address" \
  --reviewer-id customer-order-42 \
  --allow-same-user-local-vault
```

List raw-free local receipts:

```console
workshop references list wish-20260826-010101-abcdef12
```

Pass the original run's exact `--root` when the Wish lives in a retained
installed catalog. For a trusted development fixture, continue the exact Wish
with:

```console
workshop resume wish-20260826-010101-abcdef12 \
  --allow-same-user-local-vault
```

That explicit flag does not create isolation. It only exercises the raw-free
Manager-to-Invent binding. Playtest will still stop at `world-test` unless a
Manager-side independent evidence service is configured.

Supported media are signature-checked JPEG, PNG, and WebP. A reference is at
most 16 MiB and its customer-attestation record is at most 256 KiB. Supported
declared subject classes are the customer, a customer-owned pet/home/object,
and the customer's original work. Declared celebrity, public-figure, franchise,
and third-party likeness inputs fail closed. This declaration cannot detect a
concealed rights conflict in pixels.

## Workshop-owned integration

`WorldReferenceService` is the production seam. The local implementation's
`descriptors(...)` method returns exact raw-free scope records for the
Manager-to-Invent handoff; `authorized_provider_inputs(...)` binds later raw
retrieval to:

- the exact registered Wish bytes and `little-worlds` product;
- the exact Invent personalization map;
- one claimed reviewer id and one stable provider id; and
- each immutable reference/attestation blob, allowed feature list, and digest.

It returns `AuthorizedWorldReference` values whose `repr`, receipt, and public
attestation omit raw bytes. `verify_authorization(...)` replays the local HMAC
and detects a different Wish, map, reviewer, provider, record, blob, or file
permission. It never returns a Playtest pass.

`prepare_world_invent_inputs(...)` is the Manager-only descriptor fetch. It
verifies every admission against the exact saved Wish and produces a compact
`WorldInventInputs`. The v3 Manager handoff contains only scope, sizes, hashes,
and admission digests. The selected Inventor process never receives the
service object, key, consent bytes, or reference media. Shared Workshop runtime
then requires the accepted little-worlds lane contract to copy that exact scope
and binds its digest into the accepted Invent event.

After Make, an isolated integration uses
`prepare_world_playtest_evidence(...)` with a `WorldPlaytestService`. The
Manager verifies the typed `WorldPlaytestEvidence` first, then may resume the
same Make with only that raw-free envelope. Shared Playtest checks the exact
Wish, descriptor bundle, personalization map, artifact hash, provider identity,
and every recognition case before it can seal `world-test` evidence.

## Production adapter still required

The repository intentionally does not invent a production credential, consent
authority, or likeness service. A deployment must configure the two Manager
seams in `cli.py`: one returns an isolated `WorldReferenceService` plus its
public identity, and the other returns independently verified raw-free
`WorldPlaytestEvidence`. A real adapter should build the latter with
`prepare_world_playtest_evidence(...)`; it must keep its narrow raw-media
capability outside the Inventor subprocess.

Without those adapters, production fails closed at
`world-reference-descriptors` or `world-test`. The legacy `WorldEvidenceProvider`
hook remains only for deterministic low-level evidence tests. It runs in the
Workshop process, must not receive a production raw-media credential, and
cannot satisfy the canonical little-world release bar without the exact typed
Manager envelopes.

Every `little-worlds` run requires a Manager-admitted descriptor bundle before
Invent and independent Manager-verified evidence after Make. A Wish that needs
no private personalization should use another lane until a separately typed,
raw-free little-world contract exists.
