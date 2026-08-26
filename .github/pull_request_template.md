# Pull request

## Outcome

<!-- What user, inventor, maintainer, or operator outcome does this change improve? -->

## Ownership

- Owning component:
- Primary DRI:
- Backup or second reviewer:
- Risk: standard / high / critical

<!-- Use .github/components.toml. Name every affected component for a contract change. -->

## Change class

- [ ] Component implementation
- [ ] Cross-component contract
- [ ] CLI
- [ ] Inventor specialist bundle or custom tool
- [ ] Product-run constitution or workflow skill
- [ ] Skill or locked dependency
- [ ] Schema, canonical bytes, or artifact identity
- [ ] Durable state, event, migration, receipt, or external effect
- [ ] Documentation, governance, CI, packaging, or release
- [ ] Security-sensitive change

## Current and resulting behavior

Before:

-

After:

-

Explicitly out of scope:

-

## Boundaries and contracts

- Public contract added or changed:
- Components consuming it:
- Dependency direction:
- External ports or effects:
- Durable formats read or written:

- [ ] The change stays in its owning source and mirrored test directories.
- [ ] Components import public contracts, not sibling private implementations.
- [ ] Workflow remains the only stage sequencer.
- [ ] Product work remains one persistent native session per Wish and one
      active Codex Goal per cognitive stage attempt; Python does not own the
      improvement loop.
- [ ] CLI and inventor code depend on Workshop; Workshop does not import them.
- [ ] No new `core`, `foundation`, `common`, or `utils` dumping ground was added.

## Conditional review

### Inventor

- Inventor ID and Taste boundary:
- Declared Codex skill trees:
- [ ] Root `TASTE.md` remains canonical and workflow-bound.
- [ ] The schema-v8 manifest and exact skill-tree hashes match the submitted bytes.
- [ ] The run materializes identity, Taste, and skill bindings only through `.codex/agents/`.
- [ ] Inventor scripts are deterministic specialist tools, not agent or lifecycle orchestration.
- [ ] Shared Workshop machinery is reused instead of copied.

### Skill or dependency

- Owner component:
- Source URL and exact revision:
- License and provenance record:
- Lock or fingerprint change:
- [ ] Executable modes and installed bytes were verified.
- [ ] A lock change represents an intentional byte change, not only a move.

### Schema, artifact, or durable state

- Format and old/new versions:
- Reader/writer compatibility:
- Canonicalization or hash impact:
- Rollback or reconciliation path:
- [ ] Existing state and evidence remain readable through tested readers.
- [ ] Historical records, receipts, hashes, and artifact bytes were not rewritten.
- [ ] Malformed, unknown, partial, retry, and ambiguous outcomes fail truthfully.

### Outside or physical effect

- Effect and authorization boundary:
- Idempotency key and receipt binding:
- Ambiguous-outcome behavior:
- [ ] Intent is durable before execution and retries cannot duplicate the effect.
- [ ] Offline tests use explicit fakes and do not claim live readiness.

## Verification

<!-- Paste exact commands and summarize results. Do not paste credentials. -->

```text

```

- [ ] Narrow component or CLI tests
- [ ] Contract/integration tests for every affected boundary
- [ ] Full repository test suite
- [ ] Architecture dependency checks
- [ ] Installed wheel and resource smoke tests when packaging/resources changed
- [ ] Skill/schema/runtime-asset identities when applicable
- [ ] Secret and provenance checks
- [ ] `git diff --check`

## Compatibility and release note

- [ ] Added `changes/<id>.<kind>.md`
- [ ] No changelog required; reason:
- Breaking Python API:
- Durable compatibility impact:
- Migration or deprecation window:

## Reviewer guide

<!-- Point reviewers to the highest-risk files, invariants, evidence, and tradeoffs. -->
