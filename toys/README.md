# Persistent toy projects

Each subdirectory is one persistent Codex project. New Wishes use their stable
host-assigned toy id because neither the matched Inventor nor product title
exists when Codex starts; the migrated historical projects use the readable
`<inventor>-<toy-slug>` names they already earned. Codex runs with that
directory as its working directory. The root Codex session is the **Workshop Manager**; the
`autonomous-workshop` skill is its workflow playbook, and each eligible
Inventor is a native Codex custom subagent with its own specialist skill and
Taste.

Every project carries its own exact product-run constitution in `AGENTS.md`,
runtime-discoverable skills in `.agents/skills/`, the complete eligible roster
in `catalog/inventors/`, and one deterministic project-scoped custom-agent file
per Inventor in `.codex/agents/`. This is the
[official Codex project convention](https://learn.chatgpt.com/docs/agent-configuration/subagents):
each TOML defines `name`, `description`, and `developer_instructions`. The
roster is identity and routing context, not another manager. Shared Make skills
are copied into the project so its CAD work remains available from the project
root.

The fourteen projects currently tracked here are migrations of historical
products from commit `db92e2b8f75262c9184455f794548909ce149748`. Their
product bytes and paths are preserved at project root. The only exclusions are
270 generated cadgen coordination records under
`parts/__cadgen__/models/`: `.*.(generation|generator).lock` and
`.*.(generation|generator).progress.json`. Those files contained ephemeral
run, process, host, or timing state rather than product craft. Every exact
excluded path and source blob is recorded in `legacy-migration.json`.

The audit retained all 142 product-specific Python files: CAD generators,
geometry/fit and slicer checks, render helpers, and playtest simulations. None
imports a model-agent SDK or launches Codex/Claude orchestration. The recovered
trees contained no symlinks, environment/credential files, backups, runtime
databases, or secret-shaped values; the one tracked publication ZIP was also
inspected after extraction.

These products predate the native Codex host, so their `TOY.json` files
explicitly contain no native session id or checkpoint. Existing product
manifests remain historical evidence; they are not resumable native host state.

For a new Wish, the host creates a new project here before Match, populates the
constitution, workflow and shared craft skills, full Inventor roster, every
eligible Inventor skill, and custom-agent TOMLs, then launches the Workshop
Manager with the new project as its working directory. The Manager may consult
candidate Inventor subagents during Match; Match records one selected Inventor
whose exact Taste and specialist method guide the rest of the run.
Durable lifecycle checkpoints, exclusive mutation locks, credentials, effect intents, and
authenticated receipts remain in host-controlled private state outside this
project. A project never stores Factory passwords, Codex authentication, or
other credentials.

Run `python tools/verify_toy_projects.py` from the source repository to verify
project enumeration, product inventories, copied bytes, executable modes,
custom-agent definitions, complete roster isolation, and the absence of
excluded runtime state.
