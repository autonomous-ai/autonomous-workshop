# ADR 0044: Scope component-CAD network access

- Status: Accepted
- Date: 2026-09-05
- Owners: Runtime and Make maintainers

## Context

Workshop materializes the locked `step-parts` Make skill and requires native
Codex to search for purchasable component geometry before drawing an unaudited
stand-in. The production Codex permission profile nevertheless disabled all
command networking and used approval policy `never`. A correct product run
therefore could neither execute the required downloader nor obtain permission;
it could only stop at a waiting outcome.

Native web search is not a substitute. It can establish research claims, but
it does not place checksum-verified STEP bytes in the product's CAD project.
Broad command networking would expose more outbound authority than this
deterministic component workflow needs.

## Decision

Codex product runs enable the native managed network proxy in `limited` mode.
The permission profile allows only the Step.parts API/site, the exact asset
host families returned by its catalog, and a reviewed set of official supplier
drawing hosts used by the powered-product Make skills:

- `api.step.parts`
- `www.step.parts`
- `media.githubusercontent.com`
- `*.public.blob.vercel-storage.com`
- official Raspberry Pi, DFRobot, Seeed Studio, Waveshare, iFlight, and Visaton
  documentation/download hosts enumerated in the runtime policy

Every other command-network destination remains denied. Native web search is
unchanged. Factory and other effect credentials remain outside the Codex
subprocess. Codex authentication values required by the runtime may reach the
Codex process, but the shell environment policy excludes secret-named values,
including `OPENAI_*` and `CODEX_API_KEY`, from model-generated commands.

The exact proxy feature, mode, domain map, and shell filter are part of the
runtime-policy hash. Resume accepts the immediately preceding network-disabled
policy, and its already-supported historical derivatives, only as exact
predecessors; the resumed turn runs under this newly computed scoped policy.
A resumed waiting turn must retry its exact bounded access probe once before
repeating the need. Runtime-policy changes need not materialize an operator
file in the run, so absence of a new file is not evidence that access remains
unchanged.

## Consequences

- A normal `workshop wish` or `workshop resume` can execute the bundled
  Step.parts downloader and retrieve reviewed official supplier drawings
  without a host operator copying files into the run.
- Component searches and downloads remain native-agent actions inside the one
  persistent product-run session.
- The allowlist is intentionally product-tool-specific. Adding another direct
  network integration requires an explicit reviewed policy change.
- A proxy startup failure or unavailable allowed host remains a truthful
  waiting condition; Workshop does not silently substitute fabricated CAD.

## Verification

- Runtime command tests bind the proxy feature, limited mode, exact domain
  rules, and shell secret filters.
- Resume tests accept the exact network-disabled predecessor and reject
  arbitrary policy drift.
- A real CLI resume must demonstrate that the native Step.parts downloader can
  query the catalog and verify downloaded STEP checksums.
