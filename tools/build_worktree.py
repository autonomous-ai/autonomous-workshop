#!/usr/bin/env python3
"""Create a light Workshop worktree: code without every toy.

`git worktree add` checks out every tracked file, and toys/ and toys-spec/
hold gigabytes of tracked toy archives a run never reads. This tool makes
the worktree sparse instead: everything except toys/*, toys-spec/* and
inbox/* (toys/README.md stays, so toys/ exists for the release projection
and the source-checkout checks, and the few tracked toy files the test
suite reads, TEST_FIXTURES, stay too). Then it copies from the main checkout only
the input files named with --input (the round's contract, its reference,
guide and print-art images, an existing toy directory) and, for
--seed-source, exactly the Approved Proof's seed files (APPROVAL.json plus
`workshop.wish.seed.seed_manifest`, the files the host checks), each to the
same relative path. Copies keep their modification time, so the Stop hook
(tools/sync-to-main.sh, newer wins) never copies them back.

Deterministic plumbing only: it decides nothing about a run.

    uv run python tools/build_worktree.py DEST [--at origin/main] [-b BRANCH]
        [--input FILE_OR_DIR ...] [--seed-source DIR] [--dry-run]

It prints one JSON object: the worktree, its sparse patterns and every copy.
Inputs must lie under the main checkout's toys/, toys-spec/ or inbox/.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

EXCLUDED_TOPS = ("toys", "toys-spec", "inbox")
# Tracked toy files the test suite reads, kept so `uv run pytest` passes in
# a light worktree as in a full one (about 12 MB of the ~3 GB of archives).
TEST_FIXTURES = (
    "/toys/ad-astra-antisol-v13/make/source/",
    "/toys/leo-false-lantern/MANUAL.pdf",
)
SPARSE_PATTERNS = (
    "/*",
    "!/toys/*",
    "/toys/README.md",
    *TEST_FIXTURES,
    "!/toys-spec/*",
    "!/inbox/*",
)


class WorktreeError(Exception):
    pass


def _git(cwd: Path, *args: str, stdin: Optional[str] = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        raise WorktreeError("git %s failed: %s" % (" ".join(args), result.stderr.strip()))
    return result.stdout


def main_checkout(start: Path) -> Path:
    common = _git(start, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    if Path(common).name != ".git":
        raise WorktreeError("cannot find the main checkout from %s" % start)
    return Path(common).parent


def _relative_input(main: Path, path: Path) -> Path:
    absolute = (path if path.is_absolute() else Path.cwd() / path).resolve()
    try:
        relative = absolute.relative_to(main.resolve())
    except ValueError:
        raise WorktreeError("%s is not inside the main checkout %s" % (path, main))
    if not relative.parts or relative.parts[0] not in EXCLUDED_TOPS or len(relative.parts) < 2:
        raise WorktreeError("%s is not under toys/, toys-spec/ or inbox/" % path)
    if not absolute.exists():
        raise WorktreeError("%s does not exist" % path)
    return relative


def _files_under(root: Path) -> List[Path]:
    if root.is_symlink():
        raise WorktreeError("%s is a symlink" % root)
    if root.is_file():
        return [root]
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise WorktreeError("%s is a symlink" % path)
        if path.is_file():
            files.append(path)
    return files


def plan_copies(main: Path, inputs: Sequence[Path], seed_source: Optional[Path]) -> Dict[str, Path]:
    """Relative destination path -> main checkout source file."""

    copies: Dict[str, Path] = {}
    for item in inputs:
        relative = _relative_input(main, item)
        for source in _files_under(main / relative):
            copies[source.relative_to(main).as_posix()] = source
    if seed_source is not None:
        relative = _relative_input(main, seed_source)
        root = main / relative
        approval = root / "APPROVAL.json"
        if not approval.is_file():
            raise WorktreeError("%s has no APPROVAL.json; it is not a sealed Approved Proof" % seed_source)
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from workshop.wish.seed import seed_manifest

        names = ["APPROVAL.json", *seed_manifest(root)]
        for name in names:
            copies[(relative / name).as_posix()] = root / name
    return dict(sorted(copies.items()))


def create(destination: Path, at: str, branch: Optional[str], copies: Dict[str, Path],
           main: Path, dry_run: bool) -> dict:
    report = {
        "worktree": str(destination),
        "at": at,
        "branch": branch,
        "sparse": list(SPARSE_PATTERNS),
        "copied": sorted(copies),
        "dry_run": dry_run,
    }
    if dry_run:
        return report
    if destination.exists():
        raise WorktreeError("%s already exists" % destination)
    add = ["worktree", "add", "--no-checkout"]
    add += ["-b", branch] if branch else ["--detach"]
    _git(main, *add, str(destination), at)
    _git(destination, "sparse-checkout", "init", "--no-cone")
    _git(destination, "sparse-checkout", "set", "--stdin", stdin="\n".join(SPARSE_PATTERNS) + "\n")
    _git(destination, "checkout", "-q")
    for relative, source in copies.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("destination", type=Path)
    parser.add_argument("--at", default="origin/main", help="commit to check out (default origin/main)")
    parser.add_argument("-b", "--branch", help="create this branch instead of a detached HEAD")
    parser.add_argument("--input", action="append", type=Path, default=[],
                        help="a file or directory under toys/, toys-spec/ or inbox/ to copy")
    parser.add_argument("--seed-source", type=Path, help="an Approved Proof directory to copy as its seed")
    parser.add_argument("--dry-run", action="store_true", help="print the plan; create nothing")
    args = parser.parse_args(argv)
    try:
        main_root = main_checkout(Path.cwd())
        copies = plan_copies(main_root, args.input, args.seed_source)
        destination = args.destination if args.destination.is_absolute() else Path.cwd() / args.destination
        report = create(destination, args.at, args.branch, copies, main_root, args.dry_run)
    except Exception as error:  # noqa: BLE001 - one clear refusal line
        print("build_worktree: %s" % error, file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
