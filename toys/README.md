# Persistent toy projects

`workshop wish` creates one private, persistent Codex project here for each
Wish. Its host-assigned id is stable because the Inventor and product title do
not exist until Match and Invent have run.

Each generated project contains:

- `.workshop-product-run-root`, the exact Codex project boundary;
- `AGENTS.md`, the product-run constitution;
- `.codex/agents/*.toml`, the sole Inventor roster;
- `.agents/skills/**`, the workflow, Inventor, and Make skills;
- `WISH.json`, `STAGE.json`, and the exact product/evidence artifacts.

Codex runs with that directory as its working root. The trusted host keeps
checkpoints, credentials, effect intents, and receipts separately under
`$WORKSHOP_HOME/state/<toy-id>/`. Product-run Codex cannot read that state or
write into the Workshop source checkout or a sibling toy.

Runtime projects are intentionally ignored by Git. They can contain private
customer Wishes and large generated artifacts. Publishing happens through the
host's verified Factory adapter; it does not require committing the project.
