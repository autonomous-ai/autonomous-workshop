# Security policy

Autonomous Workshop combines agent execution, generated artifacts, package
resources, durable state, and optional outside effects. Treat failures at those
boundaries as security-relevant even when they do not resemble a traditional
web vulnerability.

## Supported versions

Security fixes target the latest released minor version and the current `main`
branch. If a fix cannot safely be backported, the advisory will say so and name
the minimum safe version. Historical inventor snapshots and generated artifacts
are preserved evidence, not supported executables unless their documentation
explicitly says otherwise.

## Report privately

Do not open a public issue for a suspected vulnerability, exposed secret, or a
reproducible path to an unauthorized external or physical effect.

Use the repository's **Security → Report a vulnerability** form:

<https://github.com/autonomous-ai/autonomous-workshop/security/advisories/new>

Include, when available:

- affected version or commit;
- prerequisite configuration and trust boundary;
- minimal reproduction without live credentials or destructive effects;
- observed and expected behavior;
- impact on confidentiality, integrity, availability, artifact identity,
  durable evidence, or physical operation;
- whether any secret, customer data, provider account, or public listing may
  already be affected.

Do not include real secrets. Replace them with unmistakable placeholders and
state whether the originals have been rotated.

The maintainers target acknowledgement within three business days and an
initial assessment within fourteen days. Complex supply-chain, persisted-state,
or physical-effect issues may require longer coordination. We will keep the
reporter informed and credit them unless they prefer anonymity.

## Security boundaries

Particularly important reports include:

- credentials, tokens, cookies, private keys, transcripts, or customer data
  committed to artifacts, logs, packs, fixtures, or source archives;
- command, prompt, path, archive, or schema input escaping its intended
  sandbox or component boundary;
- lock, provenance, signature, receipt, canonicalization, or hash bypass;
- a Playtest, Instructions, delivery, or publishing floor that can be skipped
  or falsely reported as passed;
- retries that can duplicate a Factory, carrier, publication, or other outside
  effect after an ambiguous outcome;
- cross-owner access, confused-deputy behavior, or use of a human credential
  by an unattended inventor;
- unsafe CAD, slicing, printer, machine, or material instructions represented
  as verified physical evidence;
- dependencies, skills, models, or snapshots whose origin or license has been
  substituted without an intentional lock update.

## Maintainer response

Maintainers will reproduce the issue in an isolated environment, assess
affected artifacts and durable state, prepare a fix and regression test, and
coordinate disclosure. If a secret or live effect is involved, containment and
credential rotation take priority over preserving a failing service.

Security fixes do not silently rewrite old evidence. When an old record is
unsafe to trust, readers must surface that status explicitly and migration
notes must identify the affected versions.

## Safe research

Use local fixtures, fakes, disposable state, and accounts you own. Do not access
other users' data, degrade shared services, publish or ship products, drive
physical equipment, or incur charges without explicit authorization. Stop when
an ambiguous external effect could be repeated.
