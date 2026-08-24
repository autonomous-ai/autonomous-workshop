# prompts/v1 — MANIFEST

Prompt version: **v1** (2026-08-22). The prompt files ARE Bob's policy; this
manifest pins exactly what v1 says, byte for byte.

**Pin rule: games pin the prompt version they started with.** When a game is
sparked, the harness stamps `prompt_version: "v1"` into its `idea.json`; every
later stage of that game composes its prompts from THIS version, even after
the meta loop ships v2 (the rainbow-deploy move — a mid-flight prompt change
would make a game's verdicts incomparable with its own history). New versions
are new `prompts/vN/` directories with their own MANIFEST; a pinned version is
never edited in place. A file whose sha256 no longer matches this table means
v1 was mutated — that is an integrity finding, not an update.

Hashes: `shasum -a 256 <path>` over the file as committed.

| file | sha256 |
|---|---|
| `.claude/agents/bob-architect.md` | `0be37f41c2ed141ff910d942c3bb046da2a9d9b942074c6a2ad2918c8987bbb0` |
| `.claude/agents/bob-auditor.md` | `fb81c4681dacc007554b778811c27ea284635a5859cb615f01fa528b6ad23b78` |
| `.claude/agents/bob-brief-writer.md` | `deeaa7fa1b60e14aab34bde1ce61c2544e09234d18ed5fb9a1c1a191b5438793` |
| `.claude/agents/bob-build-lens.md` | `8fb45b633dff76e3513142439c51c498db65a0020153f03f674147a24aec256c` |
| `.claude/agents/bob-builder.md` | `2ae440f1275a45958d90067690a0c913c5f0b531ac7bdbeb2a80303665dfafb8` |
| `.claude/agents/bob-engine-writer.md` | `fe6478e11d475406205378dd0c2a3d52e543577a4a024606223e30877e534bad` |
| `.claude/agents/bob-fresh-reader.md` | `7315ea25e1ce5fd22bf59c3cc3321c3a3e7b8ebaa6d0cc32d3a1545fe3709320` |
| `.claude/agents/bob-ideator.md` | `6076b8145a72791f032cc338c49e331bb3d012a055cffa99b94a17a682888ece` |
| `.claude/agents/bob-improver.md` | `15547f60bf8649faaf3faef967c0fce0c40ab507d87786b80a594b5c069b164f` |
| `.claude/agents/bob-librarian.md` | `1e80b96498cc187791db1f80c818a063c98b5085d01ece7eb39c464af8a0e322` |
| `.claude/agents/bob-novelty-judge.md` | `3acd14c0eb00f1e317375f75edb716b3937d2d259479a901143edd770f8d9f01` |
| `.claude/agents/bob-page-writer.md` | `b9607472179de8c105727b4d7ff710268109c1d166f6fb54b1aa35235c0838c7` |
| `.claude/agents/bob-rules-lens.md` | `f801a79b65381499727ab220f4d0aa0481b8ce7a17826fd3b1c553bc396fc55c` |
| `.claude/agents/bob-rules-writer.md` | `6e41382a8ff60b79df83e0812cca619b63dd06be214b22969aa68b1adba1f96f` |
| `.claude/agents/bob-scholar.md` | `92c5115df4d66807a77a2160f2e405c72aab7d81900836cead4a62c065034a8d` |
| `.claude/agents/bob-table-breaker.md` | `8f2e423838775e71aec4bee1c325e2eaaf318e249eaad8d2469b36ec124be9de` |
| `.claude/agents/bob-table-player.md` | `071b994b2d706de44e8d590162fd37e75f76e7dc52acf5d3e0472b0d9e54fff6` |
| `.claude/agents/bob-triage-judge.md` | `c9940b02ec3e76f7f30b2d5de1b178c82f311756c7cf6bc7d059aa3ebf3c046e` |
| `.claude/commands/bob.md` | `372384732153c126ea792e5b514471cc4f6de2b7fa4f7b9c2988ed839d3b7d22` |
