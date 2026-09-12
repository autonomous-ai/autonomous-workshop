# ADR 0068: Explicit recovery after runtime filesystem device renumbering

- Status: Accepted; implemented and deterministically tested
- Date: 2026-09-12

Atlas's saved native runtime policy stopped matching after its runtime filesystem
changed device number from 16777231 to 16777230. Reconstructing the policy with
the old device number reproduced the saved SHA-256 exactly. Paths, resolved
paths, inodes, file modes, CLI version, environment rules, model, profile and
session bindings had not changed. Ordinary resume correctly refused the drift,
but there was no explicit way to recover it without replacing the session.

`workshop resume ID --runtime-device-from DEVICE` authorizes one narrow host
correction. Initially it supports unfinished Codex Spark token-budget runs in
Make. The host opens the existing run under its exclusive mutation lock and
selects the same frozen launch policy as normal token-budget execution, before
applying any separately requested budget or effort changes.

All trusted Python and Codex runtime identities must share one current device
number. The supplied old number replaces only their `device` and
`resolved_device` fields in an in-memory candidate. That candidate must recreate
the entire saved checkpoint exactly, including its runtime-policy digest and
checkpoint digest. No other drift, CLI upgrade, multi-volume migration or
historical-policy conversion is admitted by this operation. There is no search
for a matching identity and no automatic recovery on ordinary resume.

The operator must establish that this is the same trusted filesystem after
renumbering. The legacy checkpoint contains no volume UUID or executable-content
hash: this correction is not proof of filesystem provenance or support for
copying an installation onto a different volume. Path, inode and mode checks
retain their existing meaning and limitations.

Before atomically replacing the native checkpoint, the host persists an
immutable owner-only recovery record named by the old checkpoint digest. It
contains the old and new device numbers and the exact before/after checkpoints.
It rechecks both the original checkpoint and current runtime identities before
replacement. Conflicting, linked or unsafe records fail closed. An interruption
between recording and replacement can retry the same explicit command. After
replacement, ordinary resume works; repeating the option is a no-op if the
checkpoint already matches the exact current policy.

The root session UUID, Wish, stage, Goal, inventor, artifacts, frozen tool bytes,
Make checks, effect authority and consumed token ledger remain unchanged. The
native agent receives neither the recovery option nor its private record. This
is a trusted runtime operation, not a product gate or a native-agent repair.

Tests cover exact-session recovery and later ordinary resume; unchanged artifact
and usage bytes; wrong device, inode, path, resolved path, mode, model, CLI,
compaction or constitution; malformed checkpoint binding; multiple devices;
conflicting/linked receipts; runtime drift during correction; interrupted
replacement and idempotent retry; CLI forwarding; and host lock/order/refusal.
