"""Opt-in Git push for one generated toy directory."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Mapping, Optional

from workshop.errors import EffectError, StateConflict


class GitPushError(EffectError):
    """The requested Git command failed."""


def push_toy_directory(
    repository_root: Path,
    target: Path,
    *,
    title: str,
    environment: Optional[Mapping[str, str]] = None,
) -> str:
    """Commit one toy folder and push it without losing concurrent remote work."""

    repository = Path(repository_root).resolve(strict=True)
    snapshot = Path(target).resolve(strict=True)
    try:
        relative = snapshot.relative_to(repository).as_posix()
    except ValueError as exc:
        raise StateConflict("toy folder is outside the repository") from exc
    if (
        not snapshot.is_dir()
        or not relative.startswith("toys/")
        or relative.count("/") != 1
    ):
        raise StateConflict("Git push target must be one toy folder")

    git_environment = dict(os.environ if environment is None else environment)
    for name in tuple(git_environment):
        if name.startswith("FACTORY_"):
            git_environment.pop(name, None)
    git_environment["GIT_TERMINAL_PROMPT"] = "0"

    def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        try:
            result = subprocess.run(
                ["git", "--literal-pathspecs", *arguments],
                cwd=repository,
                env=git_environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise GitPushError("Git could not run on the host") from exc
        if check and result.returncode != 0:
            raise GitPushError("Git add, commit, or push failed")
        return result

    git("add", "--", relative)
    changed = git("diff", "--cached", "--quiet", "--", relative, check=False)
    if changed.returncode not in (0, 1):
        raise GitPushError("Git could not inspect the toy folder")
    if changed.returncode == 1:
        heading = " ".join(title.split()) or snapshot.name
        git("commit", "--only", "-m", "Add %s" % heading, "--", relative)
    pushed = git("push", check=False)
    if pushed.returncode == 0:
        return relative

    push_error = pushed.stderr.decode("utf-8", errors="replace").lower()
    if not any(
        marker in push_error
        for marker in ("fetch first", "non-fast-forward", "failed to push some refs")
    ):
        raise GitPushError("Git add, commit, or push failed")

    # A product run can outlive another contributor's push. Rebase and retry
    # only when the checkout is otherwise pristine: Workshop must never stash,
    # rewrite, or accidentally include unrelated builder work.
    status = git("status", "--porcelain", "--untracked-files=all")
    if status.stdout.strip():
        raise GitPushError("Git push needs reconciliation in a dirty checkout")
    upstream = git(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    )
    if upstream.returncode != 0 or not upstream.stdout.strip():
        raise GitPushError("Git push has no upstream to reconcile")

    for _attempt in range(3):
        git("fetch")
        rebased = git("rebase", "@{upstream}", check=False)
        if rebased.returncode != 0:
            git("rebase", "--abort", check=False)
            raise GitPushError("Git could not rebase the toy commit")
        pushed = git("push", check=False)
        if pushed.returncode == 0:
            return relative
        push_error = pushed.stderr.decode("utf-8", errors="replace").lower()
        if not any(
            marker in push_error
            for marker in (
                "fetch first",
                "non-fast-forward",
                "failed to push some refs",
            )
        ):
            break
    raise GitPushError("Git push remained non-fast-forward after bounded retries")


__all__ = ["GitPushError", "push_toy_directory"]
