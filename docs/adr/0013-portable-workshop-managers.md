# ADR 0013: Portable Workshop Manager runtimes

- Status: Accepted; adapter implementation complete, live Claude acceptance pending
- Date: 2026-08-26
- Owners: Runtime, Workflow, and CLI maintainers
- Amends: ADR 0012

## Context

ADR 0012 established the durable native-session architecture using Codex. Its
trusted boundary is vendor-independent: one native coding-agent Manager owns
reasoning and tool use, while the Workshop host owns lifecycle state, exact-byte
gates, isolation, authorization, and effects. Inventor sources are also
vendor-independent even though Codex and Claude Code use different project
formats for agents and skills.

Workshop needs multiple native runtimes without introducing a Python agent
framework, duplicating Inventor identity, or letting a resume silently change
the agent that owns an existing session.

## Decision

Workshop has one closed Manager registry and a narrow native-session launcher
port. Codex and Claude Code are registered implementations. New Wishes accept
`--manager`; omission selects Codex. The selected Manager is persisted in the
host checkpoint before the first native launch, reported in receipts/status,
and used for every resume. Resume is not a runtime selector.

The Claude adapter, CLI selection, projection, isolated API-key profile
policy, terminal attestation, and same-session resume binding have deterministic
test coverage. A real private Claude Wish has not yet completed the live
acceptance bar, so this decision does not claim production validation from
mocked execution.

One Wish has one active root Manager and one runtime-native session identity.
Codex and Claude Code may both work on projects produced from the same canonical
Workshop and Inventor sources, but they do not concurrently mutate one Wish and
cannot silently resume each other's sessions. A future cross-runtime handoff
must be an explicit, host-checkpointed session epoch with invalidation rules.

### Canonical sources and projections

The source of truth remains:

```text
.agents/product-run/**
src/workshop/make/skills/**
inventors/<id>/{inventor.json,TASTE.md,skills/**}
```

At run creation, the host validates and hashes those bytes, then emits exactly
one selected-runtime projection:

```text
Codex:       .codex/agents/*.toml + .agents/skills/**
Claude Code: .claude/agents/*.md  + .claude/skills/**
```

`MANAGER.json` records the selected runtime, instruction entrypoint, agent
directory, skill directory, namespace, and native work-control convention. The
generated projection is immutable run input, not a second independently edited
Inventor catalog.

Claude's `.claude` projection is an explicit, immutable, namespaced plugin.
Claude starts in a non-bare profile with empty filesystem setting sources,
private `0700` home/configuration/internal-temp directories, disabled built-in
agents, the host-generated plugin, explicit settings and tools, and strict empty
MCP. Normal user/project settings, hooks, plugins, agents, and skills are
excluded, and the normal keychain/OAuth login path is not selected. Claude's bundled unnamespaced skills
and slash commands may still appear as version-bound vendor surface and are not
projected-plugin evidence. The adapter requires `ANTHROPIC_API_KEY`, rejects
`ANTHROPIC_AUTH_TOKEN` and `CLAUDE_CODE_OAUTH_TOKEN`, and resumes only the exact
recorded session while repeating every policy flag.

OS-, MDM-, and server-managed Claude settings, managed instructions, plugins,
hooks, and administrator policy remain part of the host trusted computing base.
Claude's native `/goal` command rejects `disableAllHooks`, so Workshop cannot
use that setting. Empty filesystem setting sources exclude ordinary
user/project hooks, while managed hooks remain trusted. Workshop does not claim
isolation from a malicious or compromised host administrator.

The parent receives only the API key. Workshop binds
`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0` because enabling that feature in Claude
Code 2.1.246 silently changes the effective permission mode from `dontAsk` to
`default`. The sandbox credential policy instead denies the API key to Bash;
ordinary hooks and stdio MCP are absent, managed hooks remain in the host TCB,
and the deny-read-root policy keeps Linux `/proc` outside the explicit read
roots. Workshop does not rely on the scrub feature's PID namespace. Session and
subagent transcripts are plaintext in the private configuration directory.
Workshop sets `cleanupPeriodDays: 36500` so routine vendor cleanup cannot
silently delete the transcript required by the bound `--resume`; private
`0700` host-state permissions are the at-rest boundary.

Managed hooks run with the host user's authority and may inspect the API key,
host-readable files, or host effect credentials. Workshop does not place effect
credentials in the Manager environment, prompt, or sandbox-readable paths, but
trusted managed hooks and administrators are outside that guarantee.

For every new Claude cognitive-stage attempt, the host sends the exact text
`/goal <condition>` as standard input to
`claude -p --input-format text`. An interrupted attempt resumes with one
fixed continuation prompt rather than another `/goal`, because Claude restores
the active Goal and a new command would replace it. Immutable
`claude-session.json` and mutable `claude-goal.json` bind the session, stage,
host checkpoint, condition hash, attempt, and
prepared/active/returned/completed state. The native terminal result moves the
sidecar to returned; only host validation of the exact stage proposal records
completed.

### Shared authority boundary

Each adapter must preserve ADR 0012's ownership split:

- the native Manager owns Match, research, Invent, Make, Playtest reasoning,
  repair, Release authorship, native goals, and native subagent delegation;
- the host owns exact inputs, lifecycle order, stage and round checkpoints,
  deterministic gates, artifact sealing, credentials, authorization, external
  effects, receipts, and reconciliation;
- Inventor children receive exact Taste and declared skill bytes but never gate
  or external-effect authority;
- model prose and self-scores remain proposals.

Adapter-specific session checkpoints are private host files. The generic host
uses the checkpoint name registered for the persisted Manager and never probes
another runtime's session state.

### Asset evolution

Future Wishes always project the latest validated canonical Inventor, Taste,
workflow, and domain-skill bytes available to the host. Implemented runs are
currently immutable and hash-pinned for their whole session; resume does not
silently copy newer repository files into an established conversation.

The accepted follow-on design for active-run upgrades is a controlled asset
revision at a safe host checkpoint, never a hot swap during a Manager turn.
Its default policy should follow the latest validated stable asset release;
projects may explicitly pin a release for reproducibility:

- a compatible procedural skill update may open a new Manager session epoch
  against the same accepted upstream artifacts;
- an Inventor identity or `TASTE.md` change invalidates Match and every
  dependent stage before the new epoch starts;
- a Manager/runtime change is an explicit handoff and invalidates all
  runtime-owned unsealed work;
- released history and reconciled receipts remain bound to their original
  bytes; a later upgrade creates a new product revision.

“Latest validated stable” means an atomically promoted, content-addressed
release rather than raw Git `HEAD`. Self-improvements first become candidates;
deterministic schema, exact skill-lock, Manager-compatibility, and regression
checks must pass before promotion. `follow-stable` resolves only that promoted
channel and never an unreviewed self-edit or branch tip.

That upgrade protocol is target work, not behavior implemented by this ADR.

## Consequences

Workshop can add native runtimes by implementing one adapter and projection
spec rather than extending the workflow host with vendor branches. Inventors
and skills improve once at their canonical source and are compiled into each
runtime's native format. Exact projection hashes make failures reproducible and
prevent runtime layout differences from changing host gate semantics.

The design deliberately pays for adapter-specific security and stream
attestation. “Similar concepts” are not treated as equivalent CLI flags:
session resume, ambient-state exclusion, plugin discovery,
permissions, sandboxing, event completion, and process termination must each
fail closed for the concrete runtime.

## Verification

The following deterministic implementation checks pass:

- CLI tests prove Codex is the default and Claude can be selected only at Wish
  creation.
- Checkpoint tests prove the Manager is persisted and schema-v3 runs remain
  implicit Codex without rewrite.
- Projection tests round-trip exact Inventor identity/Taste/skill bindings for
  both runtime formats.
- Native-host tests prove resume selects the persisted Manager and its private
  session checkpoint.
- Claude adapter tests prove isolated API-key authentication, new-attempt `/goal`
  stdin, interrupted-Goal continuation, host acknowledgement, the exact plugin,
  every projected namespaced skill in both reported sets, rejection of
  unexpected namespaced entries, bounded unnamespaced CLI entries, exact
  projected agent and normalized tool rosters, empty MCP, model,
  session, sandbox, environment, and terminal-result attestation.

Live acceptance remains pending: one Claude Code 2.1.246-or-newer private Wish
with a real host-provided `ANTHROPIC_API_KEY` must demonstrate the exact
`/goal` loop, stage finalization, same-session resume, successful invocation of
one host-projected Inventor agent and at least one host-projected namespaced
skill rather than discovery metadata alone, and the sandbox boundary without
public effects. That acceptance must also prove sandboxed Bash cannot read the
API key, Linux `/proc` environment, network, paths outside the run root, or any
Workshop-controlled Factory/effect credential, while Agent, Skill, Write, and
the stage finalizer still work.
