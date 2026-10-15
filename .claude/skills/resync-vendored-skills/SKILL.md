---
name: resync-vendored-skills
description: Resync the Make skills Workshop vendors from autonomous-product-to-cad (cad, image-to-cad, wiki, ...) to upstream origin/main - check what moved, three-way merge it into a fresh worktree, refresh LOCK.json and PROVENANCE.md, run the suite, then fast-forward main or open a PR. Use when the owner asks to resync, sync the wiki, or pull upstream lessons into Workshop; the owner aims to run it about every 12 hours.
---

# Resync the vendored Make skills

Upstream `autonomous-product-to-cad` writes Wiki Rules and tool fixes every
day, Workshop's own write-backs included (`build-a-toy` pushes them there).
Runs only read them once this skill brings them into
`src/workshop/make/skills/`. Run it from a Workshop checkout.

Upstream is read through GitHub only. Never read or write the owner's local
checkout of `autonomous-product-to-cad`: sessions run there, and its hooks
merge every commit into its `main`.

## 1. Check

```bash
.claude/skills/resync-vendored-skills/scripts/check.sh
```

`up-to-date ...` ends the skill: say so in one line. `changed <locked>
<head> <skills>` names the trees that moved; the last line is a private
cache clone of upstream (hooks off) to read and diff in.

## 2. Worktree

Work in a fresh worktree from Workshop `origin/main`, never in the owner's
checkout:

```bash
git fetch origin && git worktree add -b vendor-sync/<head8> <dir> origin/main
```

## 3. Merge each changed tree

Do it exactly as every earlier section of `PROVENANCE.md` did: a three-way
merge per file, where the base is upstream at `<locked>`, one side is the
Workshop tree and the other is upstream at `<head>`.

- List what upstream changed with `git -C <cache> log --oneline
  <locked>..<head> -- skills/<name>` and `git -C <cache> diff --stat`.
- Merge with `git merge-file <workshop> <base> <upstream>` per file. A new
  upstream file is copied in, and a file upstream deleted is deleted.
- Only the skills `LOCK.json` attributes to `autonomous-product-to-cad` move.
  `make-round` and `print-details` are Workshop's own. Upstream's
  `toy-archive`, `step-to-source` and `stl-to-step` stay out.
- Resolve a conflict so that both the Workshop adaptation and the upstream
  change survive. The usual Workshop adaptations are `workshop skills path`
  and `$CAD_SKILL_ROOT` script paths, the restricted-run cache rule, the
  consult-only wiki preamble and the ADR-driven gate rules. After the merge,
  read each file's residual diff against upstream `<head>`. It must be
  exactly the Workshop adaptation.
- A page that cites upstream-only tooling or a bare `skills/<name>/` path
  stays as written; the wiki preamble already explains both.

## 4. Lock, provenance, verify

- Refresh `LOCK.json`: set `source_commit` to `<head>` for every upstream
  skill, including the ones that came out byte-identical, and set `sha256`
  from
  `PYTHONPATH=src uv run python -c "from workshop.make.skill_registry import discover_skills as d; [print(s.name, s.sha256) for s in d()]"`.
- Add a new top section to `PROVENANCE.md` in the same shape as the last
  one: what upstream brought per skill, the merge decisions, a Workshop
  review of any new behaviour that could move a gate, and what was verified.
- Run `uv run python tools/verify_skill_locks.py`, the self-checks of any
  changed script that has one, `python3 src/workshop/make/skills/wiki/scripts/wiki lint`,
  and the full suite:
  `PYTHONPATH=src uv run python -m unittest discover -s tests -t . -p 'test_*.py'`.

## 5. Land it

- **All green:** commit with the subject `Resync vendored Make skills to
  upstream <head8>`, then `git fetch origin && git rebase origin/main`, run
  the suite again, and push to `main` as a fast-forward
  (`git push origin HEAD:main`). Never force-push.
- **Something fails that the merge cannot fix:** push the branch and open a
  PR with `gh pr create`. Its body lists each failing test or check with its
  output.
- Remove the worktree afterwards.

Report in one short paragraph: the commit range, the trees that moved, the
number of wiki pages, and whether it landed on `main` or as a PR.
Only new runs get the new bytes. A frozen run keeps its own.
