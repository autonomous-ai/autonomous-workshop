# TASK

`git merge --squash {{BRANCH}}` onto `{{TARGET_BRANCH}}` stopped with
conflicts. The branch implements issue {{ISSUE}}.

1. Run `git status` and `git diff` to list the conflicted files.
2. Resolve each conflict by reading both sides and keeping the intent of
   both. The branch's own history is `git log {{TARGET_BRANCH}}..{{BRANCH}}`.
3. Run the repository's checks that cover the touched code and fix anything
   the combination broke.
4. Stage every resolved file with `git add`.

Do NOT commit, and do NOT close or comment on the issue: the orchestrator
writes the single squash commit and closes the issue itself.

Once no conflicted files remain, output <promise>COMPLETE</promise>.
