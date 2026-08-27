#!/usr/bin/env python3
"""Run-local design-vault queries over the packed ``vault.json`` beside this file.

Standard library only, deterministic, offline.  The same questions — read a
node, follow typed links, resolve a name, check a combination, brief a
mechanism — are answered by ``workshop.invent.vault`` on the host; the two are
kept in parity by test.  This file is immutable product-run tooling: the
stage finalizer imports it to apply the Invent vault rules, and the agent runs
it as a command.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

VAULT_KIND = "autonomous-workshop.design-vault"
VAULT_SCHEMA_VERSION = 1
DEFAULT_RESOLVE_CUTOFF = 0.75
LEAD_ID_HEX = 16
MAX_NOVEL_MECHANISMS = 16
NOVEL_DEFINITION_MIN = 20
NOVEL_DEFINITION_MAX = 2_000
EVIDENCE_ROW_RE = re.compile(r"^- \[([^\]]+)\]\s*(.*)$")


class VaultToolError(Exception):
    """A malformed snapshot, an unknown node, or a refused concept."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def normalize_path(path: str) -> str:
    value = str(path).replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    value = value.strip("/")
    return value[:-3] if value.endswith(".md") else value


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


def evidence_rows(notes: str) -> list[dict[str, str]]:
    rows = []
    for line in notes.splitlines():
        match = EVIDENCE_ROW_RE.match(line.strip())
        if match:
            rows.append({"ref": match.group(1), "text": match.group(2).strip()})
    return rows


def lead_id(kind: str, nodes: Sequence[str]) -> str:
    return hashlib.sha256(_canonical_json([kind, list(nodes)])).hexdigest()[:LEAD_ID_HEX]


class PackedVault:
    """Read-only view over one packed vault document."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        if not isinstance(document, Mapping) or set(document) != {
            "schema_version",
            "kind",
            "nodes",
            "sha256",
        }:
            raise VaultToolError("packed vault fields are invalid")
        if (
            document["schema_version"] != VAULT_SCHEMA_VERSION
            or document["kind"] != VAULT_KIND
            or not isinstance(document["nodes"], Mapping)
        ):
            raise VaultToolError("packed vault schema or kind is invalid")
        self.nodes: dict[str, Mapping[str, Any]] = {
            path: document["nodes"][path] for path in sorted(document["nodes"])
        }
        self.sha256 = hashlib.sha256(_canonical_json(self.nodes)).hexdigest()
        if document["sha256"] != self.sha256:
            raise VaultToolError("packed vault sha256 does not match its nodes")
        self._reverse: dict[str, list[tuple[str, str]]] = {}
        self._aliases: dict[tuple[str, str], str] = {}
        for path, node in self.nodes.items():
            for link_type, targets in node["relations"].items():
                for target in targets:
                    self._reverse.setdefault(target, []).append((path, link_type))
            folder = path.split("/", 1)[0]
            for alias in node["frontmatter"].get("aliases") or []:
                if isinstance(alias, str) and slugify(alias):
                    self._aliases.setdefault((folder, slugify(alias)), path)
        for key in self._reverse:
            self._reverse[key] = sorted(self._reverse[key])

    @classmethod
    def load(cls, path: Path) -> "PackedVault":
        try:
            return cls(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError) as exc:
            raise VaultToolError("cannot read packed vault %s: %s" % (path, exc)) from exc

    def paths(self, folder: Optional[str] = None) -> tuple[str, ...]:
        if folder is None:
            return tuple(self.nodes)
        return tuple(path for path in self.nodes if path.startswith(folder + "/"))

    def constraints(self) -> tuple[str, ...]:
        return self.paths("constraints")

    def read_node(self, path: str) -> Mapping[str, Any]:
        key = normalize_path(path)
        node = self.nodes.get(key)
        if node is None:
            close = difflib.get_close_matches(key, list(self.nodes), n=3, cutoff=0.4)
            hint = " Close matches: %s" % ", ".join(close) if close else ""
            raise VaultToolError("no vault node at %r.%s" % (path, hint))
        return node

    def follow_links(
        self,
        path: str,
        link_type: Optional[str] = None,
        depth: int = 1,
        reverse: bool = False,
    ) -> dict[str, Any]:
        depth = max(1, min(3, int(depth)))
        start = normalize_path(path)
        self.read_node(start)

        def expand(current: str, remaining: int, seen: frozenset) -> dict[str, Any]:
            result: dict[str, Any] = {}
            if reverse:
                edges = list(self._reverse.get(current, ()))
            else:
                node = self.nodes.get(current)
                edges = (
                    [
                        (target, kind)
                        for kind, targets in node["relations"].items()
                        for target in targets
                    ]
                    if node is not None
                    else []
                )
            for other, kind in edges:
                if link_type is not None and kind != link_type:
                    continue
                if other in seen:
                    continue
                target = self.nodes.get(other)
                result[other] = {
                    "type": target["type"] if target is not None else None,
                    "link_type": kind,
                    "children": expand(other, remaining - 1, seen | {other})
                    if remaining > 1
                    else {},
                }
            return dict(sorted(result.items()))

        return expand(start, depth, frozenset((start,)))

    def resolve(
        self, name: str, folder: str = "mechanisms", cutoff: float = DEFAULT_RESOLVE_CUTOFF
    ) -> Optional[str]:
        slug = slugify(name)
        if not slug:
            return None
        candidate = "%s/%s" % (folder, slug)
        if candidate in self.nodes:
            return candidate
        alias = self._aliases.get((folder, slug))
        if alias is not None:
            return alias
        tails = [path.split("/", 1)[1] for path in self.paths(folder)]
        match = difflib.get_close_matches(slug, tails, n=1, cutoff=cutoff)
        return "%s/%s" % (folder, match[0]) if match else None

    def check_compatibility(self, paths: Sequence[str]) -> list[dict[str, Any]]:
        members = [normalize_path(path) for path in paths]
        nodes = {path: self.read_node(path) for path in members}
        inside = set(members)
        findings: list[dict[str, Any]] = []
        for index, left in enumerate(members):
            for right in members[index + 1 :]:
                declared = right in nodes[left]["relations"].get(
                    "conflicts-with", ()
                ) or left in nodes[right]["relations"].get("conflicts-with", ())
                if declared:
                    findings.append(
                        {
                            "kind": "conflict",
                            "nodes": [left, right],
                            "explanation": "%s and %s declare conflicts-with; they "
                            "cannot coexist in one design." % (left, right),
                            "evidence": [],
                            "suggested_fixes": ["drop %s or drop %s" % (left, right)],
                        }
                    )
        for path in members:
            for required in nodes[path]["relations"].get("requires", ()):
                if required not in inside:
                    findings.append(
                        {
                            "kind": "unmet-requirement",
                            "nodes": [path, required],
                            "explanation": "%s requires %s, which is not in the "
                            "combination." % (path, required),
                            "evidence": [],
                            "suggested_fixes": ["add %s to the set" % required],
                        }
                    )
        for path in members:
            for risk in nodes[path]["relations"].get("risks", ()):
                target = self.nodes.get(risk)
                if target is None:
                    fixes: list[str] = []
                    rows: list[str] = []
                else:
                    fixes = [
                        "apply %s" % rule for rule in target["relations"].get("mitigated-by", ())
                    ]
                    rows = [
                        "[%s] %s" % (row["ref"], row["text"])
                        for row in evidence_rows(target["notes"])[-2:]
                    ]
                findings.append(
                    {
                        "kind": "risk",
                        "nodes": [path, risk],
                        "explanation": "%s tends to produce %s." % (path, risk),
                        "evidence": rows,
                        "suggested_fixes": fixes
                        or ["no recorded mitigation - add one to the vault"],
                    }
                )
        return sorted(findings, key=lambda item: (item["kind"], item["nodes"]))

    def guidance(
        self, paths: Sequence[str], *, risks: int = 3, exemplars: int = 3
    ) -> list[dict[str, Any]]:
        briefing = []
        for path in paths:
            node = self.read_node(path)
            risk_entries = []
            for risk in tuple(node["relations"].get("risks", ()))[:risks]:
                target = self.nodes.get(risk)
                if target is None:
                    continue
                rows = evidence_rows(target["notes"])
                risk_entries.append(
                    {
                        "anti_pattern": risk,
                        "fixes": list(target["relations"].get("mitigated-by", ())),
                        "latest_evidence": rows[-1]["text"] if rows else None,
                    }
                )
            used_by = sorted(
                source
                for source, kind in self._reverse.get(normalize_path(path), ())
                if kind == "uses" and source.startswith("games/")
            )[:exemplars]
            briefing.append(
                {
                    "node": normalize_path(path),
                    "definition": " ".join(node["definition"].split())[:320],
                    "risks": risk_entries,
                    "exemplars": used_by,
                }
            )
        return briefing

    def resolve_concept_mechanisms(self, concept: Mapping[str, Any]) -> dict[str, Optional[str]]:
        declared = concept.get("mechanisms")
        if not isinstance(declared, (list, tuple)):
            raise VaultToolError("concept mechanisms must be a list")
        return {str(item): self.resolve(str(item)) for item in declared}

    def leads_for_concept(self, concept: Mapping[str, Any]) -> list[dict[str, Any]]:
        resolved = self.resolve_concept_mechanisms(concept)
        members = [node for node in resolved.values() if node is not None]
        members += [path for path in self.constraints() if path not in members]
        return [
            {"id": lead_id(finding["kind"], finding["nodes"]), **finding}
            for finding in self.check_compatibility(members)
        ]


def assert_concept_compatible(vault: PackedVault, concept: Mapping[str, Any]) -> dict[str, Any]:
    """Mirror of ``workshop.invent.vault.assert_concept_compatible``."""

    resolved = vault.resolve_concept_mechanisms(concept)
    novel_raw = concept.get("novel_mechanisms", [])
    if not isinstance(novel_raw, (list, tuple)) or len(novel_raw) > MAX_NOVEL_MECHANISMS:
        raise VaultToolError(
            "concept novel_mechanisms must be a list of at most %d entries" % MAX_NOVEL_MECHANISMS
        )
    novel: dict[str, str] = {}
    for item in novel_raw:
        if not isinstance(item, Mapping) or set(item) != {"id", "definition"}:
            raise VaultToolError("concept novel_mechanisms entries need exactly id and definition")
        identifier, definition = item["id"], item["definition"]
        if not isinstance(identifier, str) or identifier not in resolved or identifier in novel:
            raise VaultToolError(
                "concept novel_mechanisms id %r must name one declared mechanism once" % (identifier,)
            )
        if (
            not isinstance(definition, str)
            or not NOVEL_DEFINITION_MIN <= len(definition.strip()) <= NOVEL_DEFINITION_MAX
        ):
            raise VaultToolError(
                "concept novel mechanism %r needs a definition of %d to %d characters"
                % (identifier, NOVEL_DEFINITION_MIN, NOVEL_DEFINITION_MAX)
            )
        if resolved[identifier] is not None:
            raise VaultToolError(
                "concept mechanism %r resolves to vault node %s and is not novel "
                "(mechanism-not-novel)" % (identifier, resolved[identifier])
            )
        novel[identifier] = definition.strip()
    for slug, node in resolved.items():
        if node is None and slug not in novel:
            raise VaultToolError(
                "concept mechanism %r is not a design-vault node; resolve it with "
                "vault_tools.py or declare it under novel_mechanisms (mechanism-unknown)"
                % slug
            )
    leads = vault.leads_for_concept(concept)
    for finding in leads:
        if finding["kind"] == "conflict":
            raise VaultToolError(
                "concept mechanisms %s and %s are declared conflicts-with in the design "
                "vault (vault-conflict)" % tuple(finding["nodes"])
            )
        if finding["kind"] == "unmet-requirement":
            raise VaultToolError(
                "concept mechanism %s requires %s, which the concept lacks "
                "(vault-requirement)" % tuple(finding["nodes"])
            )
    return {"mechanisms": resolved, "novel": novel, "leads": leads}


def default_vault_path() -> Path:
    return Path(__file__).resolve().parent / "vault.json"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="query the run-local design vault")
    parser.add_argument("--vault", type=Path, default=None, help="packed vault.json")
    commands = parser.add_subparsers(dest="command", required=True)
    node = commands.add_parser("node")
    node.add_argument("path")
    links = commands.add_parser("links")
    links.add_argument("path")
    links.add_argument("--type", dest="link_type", default=None)
    links.add_argument("--depth", type=int, default=1)
    links.add_argument("--reverse", action="store_true")
    resolve = commands.add_parser("resolve")
    resolve.add_argument("name")
    resolve.add_argument("--folder", default="mechanisms")
    check = commands.add_parser("check")
    check.add_argument("paths", nargs="+")
    check.add_argument("--with-constraints", action="store_true")
    guidance = commands.add_parser("guidance")
    guidance.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    try:
        vault = PackedVault.load(args.vault or default_vault_path())
        if args.command == "node":
            result: Any = vault.read_node(args.path)
        elif args.command == "links":
            result = vault.follow_links(
                args.path, link_type=args.link_type, depth=args.depth, reverse=args.reverse
            )
        elif args.command == "resolve":
            result = {"name": args.name, "node": vault.resolve(args.name, folder=args.folder)}
        elif args.command == "check":
            members = list(args.paths)
            if args.with_constraints:
                members += [path for path in vault.constraints() if path not in members]
            result = [
                {"id": lead_id(item["kind"], item["nodes"]), **item}
                for item in vault.check_compatibility(members)
            ]
        else:
            result = vault.guidance(args.paths)
    except VaultToolError as exc:
        print("vault-tools: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
