#!/usr/bin/env python3
"""Verify reviewed local snapshot trees and overlays without network access."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "snapshots.lock.json"
INVENTORS_ROOT = ROOT / "inventors"


def _repository_paths(folder: str):
    repository_folder = "inventors/" + folder
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            repository_folder,
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    paths = []
    prefix = repository_folder + "/"
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8")
        if not relative.startswith(prefix):
            raise ValueError(
                "snapshot inventory escaped %s: %s" % (repository_folder, relative)
            )
        paths.append(relative)
    return sorted(paths)


def snapshot(folder: str):
    entries = []
    total_bytes = 0
    for repository_path in _repository_paths(folder):
        path = ROOT / repository_path
        info = path.lstat()
        relative = repository_path[len("inventors/" + folder) + 1 :]
        if stat.S_ISLNK(info.st_mode):
            content = os.readlink(str(path)).encode("utf-8")
            mode = "120000"
        elif stat.S_ISREG(info.st_mode):
            content = path.read_bytes()
            mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
        else:
            raise ValueError("snapshot entry is not a file or symlink: %s" % path)
        total_bytes += len(content)
        entries.append(
            {
                "path": relative,
                "mode": mode,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    canonical = json.dumps(
        entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "files": len(entries),
        "bytes": total_bytes,
        "tree_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> int:
    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        if not isinstance(lock, dict):
            raise ValueError("snapshot lock top level must be an object")
        if (
            lock.get("schema_version") != 1
            or lock.get("algorithm") != "canonical-files-v1"
            or lock.get("scope")
            != "local-monorepo-snapshot-trees-with-reviewed-overlays"
        ):
            raise ValueError("unsupported snapshot lock contract")
        snapshots = lock.get("snapshots")
        if not isinstance(snapshots, dict) or not snapshots:
            raise ValueError("snapshot lock has no entries")
        manifests = {}
        for manifest_path in sorted(INVENTORS_ROOT.glob("*/inventor.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            source = manifest.get("source") if isinstance(manifest, dict) else None
            if isinstance(source, dict) and source.get("kind") == "upstream-snapshot":
                manifests[manifest_path.parent.name] = source.get("commit")
        if set(snapshots) != set(manifests):
            raise ValueError(
                "snapshot locks must exactly cover upstream-snapshot inventor manifests"
            )
        failures = []
        for folder, expected in sorted(snapshots.items()):
            if not isinstance(folder, str) or not isinstance(expected, dict):
                raise ValueError("snapshot lock entries must be named objects")
            if expected.get("commit") != manifests[folder]:
                raise ValueError("snapshot lock commit drift for %s" % folder)
            observed = snapshot(folder)
            locked = {
                key: expected.get(key)
                for key in ("files", "bytes", "tree_sha256")
            }
            if observed != locked:
                failures.append(folder)
        if failures:
            print(
                "snapshot-lock: drift in %s; review and regenerate the pinned lock"
                % ", ".join(failures),
                file=sys.stderr,
            )
            return 1
        print("snapshot-lock: %d local snapshot trees match" % len(snapshots))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("snapshot-lock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
