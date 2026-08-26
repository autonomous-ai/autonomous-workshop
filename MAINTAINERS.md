# Maintainers

Autonomous Workshop assigns one directly responsible individual (DRI) and one
backup to every component. The machine-readable source of truth is
[`.github/components.toml`](.github/components.toml); [CODEOWNERS](.github/CODEOWNERS)
is its GitHub review projection.

Only accounts confirmed by repository history are listed. `Vacant` is an
explicit staffing gap, not an alias or a hidden team. The repository currently
has one verified maintainer account, so all backup seats must be assigned to
real people as the team onboards. Until then, the DRI remains accountable and a
second reviewer is required for critical changes whenever one is available.

## Component roster

| Component | Owned paths | Primary DRI | Backup | Risk |
|---|---|---|---|---|
| Wish | `src/workshop/wish`, `tests/wish` | `@deehw` | Vacant | Standard |
| Match | `src/workshop/match`, `tests/match` | `@deehw` | Vacant | High |
| Invent | `src/workshop/invent`, `tests/invent` | `@deehw` | Vacant | Standard |
| Make | `src/workshop/make`, `tests/make` | `@deehw` | Vacant | High |
| Playtest | `src/workshop/playtest`, `tests/playtest` | `@deehw` | Vacant | High |
| Release | `src/workshop/release`, `tests/release` | `@deehw` | Vacant | High |
| Deliver | `src/workshop/deliver`, `tests/deliver` | `@deehw` | Vacant | High |
| Reviews | `src/workshop/reviews`, `tests/reviews` | `@deehw` | Vacant | Standard |
| Workflow | `src/workshop/workflow`, `tests/workflow`, end-to-end tests | `@deehw` | Vacant | Critical |
| Product | `src/workshop/product`, `tests/product` | `@deehw` | Vacant | Standard |
| Artifacts | `src/workshop/artifacts`, `tests/artifacts` | `@deehw` | Vacant | Critical |
| Runtime | `src/workshop/runtime`, `tests/runtime` | `@deehw` | Vacant | Critical |
| Integrations | `src/workshop/integrations`, `tests/integrations` | `@deehw` | Vacant | Critical |
| Contributor SDK | `src/workshop/contributors`, `tests/contributors` | `@deehw` | Vacant | High |
| CLI | `src/cli`, `tests/cli` | `@deehw` | Vacant | Standard |
| Inventor profiles | `inventors`, `tests/inventors` | `@deehw` | Vacant | Standard |
| Repository and releases | governance, CI, packaging, architecture tests | `@deehw` | Vacant | Critical |

## What ownership means

The primary DRI:

- keeps the component purpose and public boundary clear;
- triages issues and reviews contributions in that area;
- maintains its README, contracts, tests, schemas, and skills;
- coordinates changes that affect another component;
- names operational and compatibility risks before merge.

The backup can approve routine changes when the DRI is unavailable and must
understand the component well enough to respond to regressions. Backup is not
honorary ownership.

Ownership does not grant unilateral authority over durable state, security
floors, external effects, artifact identity, or cross-component contracts.
Those changes follow the additional review rules in [GOVERNANCE.md](GOVERNANCE.md).

## Filling or changing a seat

An ownership change is a pull request that updates all of:

1. `.github/components.toml`;
2. `.github/CODEOWNERS`;
3. this roster.

The candidate must have demonstrated understanding through reviewed changes,
issue triage, documentation, or incident response in the area. The current DRI
or repository maintainer approves the transfer. Ownership removal never blocks
a person from contributing later.
