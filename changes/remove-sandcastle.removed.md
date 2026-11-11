- The unused Sandcastle agent-orchestration tooling is gone: `.sandcastle/`,
  the root `package.json`/`package-lock.json` that existed only to run it,
  its `/node_modules/` ignore rule, and its backlog note. Historical benchmark
  records keep the branch names they were measured on. `tools/render/` keeps
  its own npm dependencies.
