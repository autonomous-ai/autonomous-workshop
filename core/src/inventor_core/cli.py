"""Small operator CLI; it validates and inspects without running an inventor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .artifacts import build_artifact_manifest, build_publish_packet
from .errors import CoreError
from .manifest import discover_inventors, validate_entrypoints
from .scaffold import scaffold_inventor
from .store import InventorStore


def _registry(args: argparse.Namespace) -> int:
    manifests = discover_inventors(args.root)
    problems = validate_entrypoints(manifests) if args.check_entrypoints else []
    if args.json:
        print(json.dumps([item.to_dict() for item in manifests], indent=2, sort_keys=True))
    else:
        for item in manifests:
            print(
                "%-12s %-18s %-20s %s"
                % (item.inventor_id, item.status, item.autonomy, item.niche)
            )
        print("%d inventor manifests valid" % len(manifests))
    for problem in problems:
        print("error: %s" % problem, file=sys.stderr)
    return 1 if problems else 0


def _manifest(args: argparse.Namespace) -> int:
    manifest = build_artifact_manifest(args.source, args.exclude)
    if args.output:
        manifest.write(args.output)
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    return 0


def _pack(args: argparse.Namespace) -> int:
    result = build_publish_packet(args.source, args.output, args.exclude)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _init_state(args: argparse.Namespace) -> int:
    InventorStore(args.database)
    print(str(args.database))
    return 0


def _audit_state(args: argparse.Namespace) -> int:
    if not args.database.is_file():
        raise FileNotFoundError("state database does not exist: %s" % args.database)
    store = InventorStore(args.database)
    valid = store.verify_event_chain(args.product_id)
    print("valid" if valid else "INVALID")
    return 0 if valid else 1


def _new_inventor(args: argparse.Namespace) -> int:
    destination = scaffold_inventor(args.root, args.inventor_id, args.name, args.niche)
    print(str(destination))
    return 0


def parser() -> argparse.ArgumentParser:
    root = Path.cwd()
    command = argparse.ArgumentParser(prog="inventor-core")
    subcommands = command.add_subparsers(dest="command", required=True)

    registry = subcommands.add_parser("registry", help="list and validate inventors")
    registry.add_argument("--root", type=Path, default=root)
    registry.add_argument("--json", action="store_true")
    registry.add_argument("--check-entrypoints", action="store_true")
    registry.set_defaults(handler=_registry)

    artifact = subcommands.add_parser("artifact", help="hash a product artifact tree")
    artifact.add_argument("source", type=Path)
    artifact.add_argument("--output", type=Path)
    artifact.add_argument("--exclude", action="append", default=[])
    artifact.set_defaults(handler=_manifest)

    pack = subcommands.add_parser("pack", help="build a reproducible Panda zip")
    pack.add_argument("source", type=Path)
    pack.add_argument("output", type=Path)
    pack.add_argument("--exclude", action="append", default=[])
    pack.set_defaults(handler=_pack)

    state = subcommands.add_parser("init-state", help="initialize the durable database")
    state.add_argument("database", type=Path)
    state.set_defaults(handler=_init_state)

    audit = subcommands.add_parser("audit-state", help="verify a product event hash chain")
    audit.add_argument("database", type=Path)
    audit.add_argument("product_id")
    audit.set_defaults(handler=_audit_state)

    new = subcommands.add_parser("new", help="scaffold a core-connected inventor")
    new.add_argument("inventor_id")
    new.add_argument("--name", required=True)
    new.add_argument("--niche", required=True)
    new.add_argument("--root", type=Path, default=root)
    new.set_defaults(handler=_new_inventor)
    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except (CoreError, OSError, ValueError, KeyError) as exc:
        print("inventor-core: %s" % exc, file=sys.stderr)
        return 2
