"""Design vault: a typed-link graph of mechanisms, failure modes, and fixes.

Nodes are Obsidian-compatible markdown: YAML-style frontmatter, a
``## Definition`` section, a ``## Relations`` section holding Dataview-style
typed wikilinks (``- risks:: [[anti-patterns/runaway-leader]]``), and a
``## Notes`` section whose ``- [ref] text`` bullets are banked evidence rows.

This module reads that shape with the standard library only, packs one vault
directory into a single hash-stable JSON document that fits a product run's
input budget, and answers three deterministic questions: what a node says,
what links into or out of it, and whether a combination of mechanisms declares
conflicts, unmet requirements, or known risks with recorded fixes.  There is
no model call and no search index; agents traverse the links the vault
actually declares.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import WorkshopError


VAULT_KIND = "autonomous-workshop.design-vault"
VAULT_SCHEMA_VERSION = 1
LINK_TYPES = (
    "requires",
    "conflicts-with",
    "risks",
    "mitigated-by",
    "variant-of",
    "example-of",
    "component",
    "uses",
)
NODE_TYPES = (
    "mechanism",
    "game",
    "rule-pattern",
    "anti-pattern",
    "constraint",
    "component",
)
# Where a typed link must point; other link types are free of a target type.
TARGET_TYPE = {
    "risks": "anti-pattern",
    "mitigated-by": "rule-pattern",
    "example-of": "game",
    "component": "component",
    "uses": "mechanism",
}
MAX_NODE_BYTES = 64 * 1024
MAX_VAULT_NODES = 4_096
# The packed vault rides into a product run as one input file; keep it well
# under the run's 4 MiB input budget.
MAX_PACKED_BYTES = 3 * 1024 * 1024
DEFAULT_RESOLVE_CUTOFF = 0.75

FIELD_RE = re.compile(r"^\s*-?\s*(\w[\w-]*)::\s*(.*)$")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
EVIDENCE_ROW_RE = re.compile(r"^- \[([^\]]+)\]\s*(.*)$")
_NODE_PATH_RE = re.compile(r"^[a-z][a-z0-9-]*/[a-z0-9][a-z0-9._-]*$")
_FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
_BLOCK_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")


class VaultError(WorkshopError):
    """The vault directory or a packed vault is malformed."""


class VaultNodeNotFound(VaultError):
    """A node path does not exist; carries close matches for self-correction."""

    def __init__(self, path: str, suggestions: Sequence[str]) -> None:
        self.path = path
        self.suggestions = tuple(suggestions)
        hint = (
            " Close matches: %s" % ", ".join(self.suggestions)
            if self.suggestions
            else ""
        )
        super().__init__("no vault node at %r.%s" % (path, hint))


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise VaultError("vault values must be finite JSON") from exc


def normalize_path(path: str) -> str:
    """Return the vault-relative node path without an ``.md`` suffix."""

    value = str(path).replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    value = value.strip("/")
    return value[:-3] if value.endswith(".md") else value


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


def _scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "" or text in ("null", "~"):
        return None
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def _inline_list(raw: str) -> list[Any]:
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(item) for item in inner.split(",")]


def parse_frontmatter(lines: Sequence[str]) -> dict[str, Any]:
    """Parse the YAML subset the vault uses: scalars, inline and block lists."""

    result: dict[str, Any] = {}
    pending: Optional[str] = None
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = _BLOCK_ITEM_RE.match(line)
        if item and line.startswith((" ", "-")) and pending is not None:
            result[pending].append(_scalar(item.group(1)))
            continue
        match = _FRONTMATTER_KEY_RE.match(line)
        if match is None:
            raise VaultError("frontmatter line %d is malformed: %r" % (number, line))
        key, raw = match.group(1), match.group(2).strip()
        if key in result:
            raise VaultError("frontmatter repeats %r" % key)
        if raw.startswith("[") and raw.endswith("]"):
            result[key] = _inline_list(raw)
            pending = None
        elif raw == "":
            result[key] = []
            pending = key
        else:
            result[key] = _scalar(raw)
            pending = None
    return result


def parse_node(text: str) -> dict[str, Any]:
    """Parse one node's markdown into frontmatter, sections, and typed links."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise VaultError("node lacks frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        raise VaultError("node frontmatter is unterminated") from None
    frontmatter = parse_frontmatter(lines[1:end])
    body = lines[end + 1 :]
    sections: dict[str, list[str]] = {}
    current: Optional[str] = None
    for line in body:
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    relations: dict[str, list[str]] = {}
    for line in body:
        match = FIELD_RE.match(line)
        if match is None:
            continue
        targets = [
            normalize_path(item.split("|")[0]) for item in WIKILINK_RE.findall(match.group(2))
        ]
        if targets:
            relations.setdefault(match.group(1), []).extend(targets)
    return {
        "type": frontmatter.get("type"),
        "name": frontmatter.get("name"),
        "frontmatter": frontmatter,
        "definition": "\n".join(sections.get("definition", [])).strip(),
        "relations": relations,
        "notes": "\n".join(sections.get("notes", [])).strip(),
    }


def _read_node_file(path: Path) -> str:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise VaultError("vault node is unreadable: %s" % path) from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise VaultError("vault node must be a regular file: %s" % path)
    if identity.st_size > MAX_NODE_BYTES:
        raise VaultError("vault node exceeds %d bytes: %s" % (MAX_NODE_BYTES, path))
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise VaultError("vault node is not UTF-8 text: %s" % path) from exc


def evidence_rows(notes: str) -> list[dict[str, str]]:
    """Return the ``- [ref] text`` bullets banked in a node's notes, in order."""

    rows = []
    for line in notes.splitlines():
        match = EVIDENCE_ROW_RE.match(line.strip())
        if match:
            rows.append({"ref": match.group(1), "text": match.group(2).strip()})
    return rows


@dataclass(frozen=True)
class Vault:
    """An immutable, content-addressed set of parsed nodes."""

    nodes: Mapping[str, Mapping[str, Any]]
    sha256: str = field(init=False)
    _reverse: Mapping[str, tuple[tuple[str, str], ...]] = field(init=False, repr=False)
    _aliases: Mapping[tuple[str, str], str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, Mapping):
            raise VaultError("vault nodes must be a mapping")
        if len(self.nodes) > MAX_VAULT_NODES:
            raise VaultError("vault exceeds %d nodes" % MAX_VAULT_NODES)
        nodes: dict[str, Mapping[str, Any]] = {}
        for path in sorted(self.nodes):
            if not isinstance(path, str) or _NODE_PATH_RE.fullmatch(path) is None:
                raise VaultError("vault node path is invalid: %r" % (path,))
            node = self.nodes[path]
            if not isinstance(node, Mapping) or set(node) != {
                "type",
                "name",
                "frontmatter",
                "definition",
                "relations",
                "notes",
            }:
                raise VaultError("vault node record is malformed: %s" % path)
            relations = node["relations"]
            if not isinstance(relations, Mapping) or any(
                not isinstance(targets, (list, tuple))
                or any(not isinstance(target, str) for target in targets)
                for targets in relations.values()
            ):
                raise VaultError("vault node relations are malformed: %s" % path)
            nodes[path] = MappingProxyType(
                {
                    **{key: node[key] for key in ("type", "name", "definition", "notes")},
                    "frontmatter": MappingProxyType(dict(node["frontmatter"])),
                    "relations": MappingProxyType(
                        {key: tuple(value) for key, value in relations.items()}
                    ),
                }
            )
        reverse: dict[str, list[tuple[str, str]]] = {}
        aliases: dict[tuple[str, str], str] = {}
        for path, node in nodes.items():
            for link_type, targets in node["relations"].items():
                for target in targets:
                    reverse.setdefault(target, []).append((path, link_type))
            folder = path.split("/", 1)[0]
            declared = node["frontmatter"].get("aliases") or []
            if isinstance(declared, (list, tuple)):
                for alias in declared:
                    if isinstance(alias, str) and slugify(alias):
                        aliases.setdefault((folder, slugify(alias)), path)
        object.__setattr__(self, "nodes", MappingProxyType(nodes))
        object.__setattr__(
            self,
            "_reverse",
            MappingProxyType({key: tuple(sorted(value)) for key, value in reverse.items()}),
        )
        object.__setattr__(self, "_aliases", MappingProxyType(aliases))
        object.__setattr__(
            self, "sha256", hashlib.sha256(_canonical_json(self._node_payload())).hexdigest()
        )

    # ---- construction -------------------------------------------------

    @classmethod
    def from_directory(cls, root: Path) -> "Vault":
        """Load every ``folder/slug.md`` node; ``_``-prefixed folders are skipped."""

        root = Path(root)
        if root.is_symlink() or not root.is_dir():
            raise VaultError("vault root must be a real directory: %s" % root)
        nodes: dict[str, Mapping[str, Any]] = {}
        for path in sorted(root.rglob("*.md")):
            relative = path.relative_to(root)
            if len(relative.parts) != 2 or relative.parts[0].startswith("_"):
                continue
            node_path = normalize_path(relative.as_posix())
            if _NODE_PATH_RE.fullmatch(node_path) is None:
                raise VaultError("vault node path is invalid: %s" % relative.as_posix())
            try:
                nodes[node_path] = parse_node(_read_node_file(path))
            except VaultError as exc:
                raise VaultError("%s: %s" % (relative.as_posix(), exc)) from None
        return cls(nodes)

    @classmethod
    def from_packed(cls, value: Any) -> "Vault":
        if not isinstance(value, Mapping) or set(value) != {
            "schema_version",
            "kind",
            "nodes",
            "sha256",
        }:
            raise VaultError("packed vault fields are invalid")
        if value["schema_version"] != VAULT_SCHEMA_VERSION or value["kind"] != VAULT_KIND:
            raise VaultError("packed vault schema or kind is invalid")
        vault = cls(value["nodes"])
        if value["sha256"] != vault.sha256:
            raise VaultError("packed vault sha256 does not match its nodes")
        return vault

    @classmethod
    def from_packed_bytes(cls, content: bytes) -> "Vault":
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise VaultError("packed vault is not JSON") from exc
        return cls.from_packed(value)

    def _node_payload(self) -> dict[str, Any]:
        return {
            path: {
                "type": node["type"],
                "name": node["name"],
                "frontmatter": dict(node["frontmatter"]),
                "definition": node["definition"],
                "relations": {key: list(value) for key, value in node["relations"].items()},
                "notes": node["notes"],
            }
            for path, node in self.nodes.items()
        }

    def packed(self) -> dict[str, Any]:
        return {
            "schema_version": VAULT_SCHEMA_VERSION,
            "kind": VAULT_KIND,
            "nodes": self._node_payload(),
            "sha256": self.sha256,
        }

    def packed_bytes(self) -> bytes:
        content = _canonical_json(self.packed())
        if len(content) > MAX_PACKED_BYTES:
            raise VaultError("packed vault exceeds %d bytes" % MAX_PACKED_BYTES)
        return content

    # ---- reads --------------------------------------------------------

    def paths(self, folder: Optional[str] = None) -> tuple[str, ...]:
        if folder is None:
            return tuple(self.nodes)
        return tuple(path for path in self.nodes if path.startswith(folder + "/"))

    def read_node(self, path: str) -> Mapping[str, Any]:
        key = normalize_path(path)
        node = self.nodes.get(key)
        if node is None:
            raise VaultNodeNotFound(
                path, difflib.get_close_matches(key, list(self.nodes), n=3, cutoff=0.4)
            )
        return node

    def links_into(self, path: str) -> tuple[tuple[str, str], ...]:
        return self._reverse.get(normalize_path(path), ())

    def follow_links(
        self,
        path: str,
        link_type: Optional[str] = None,
        depth: int = 1,
        reverse: bool = False,
    ) -> dict[str, Any]:
        """Traverse typed links out of (or, reversed, into) a node.

        Returns ``{other: {"type", "link_type", "children"}}`` nested to
        ``depth`` (1..3).  A declared target that does not exist still appears
        with ``type`` ``None``; the linter is where that becomes a finding.
        """

        depth = max(1, min(3, int(depth)))
        start = normalize_path(path)
        self.read_node(start)

        def expand(current: str, remaining: int, seen: frozenset[str]) -> dict[str, Any]:
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
        self,
        name: str,
        folder: str = "mechanisms",
        cutoff: float = DEFAULT_RESOLVE_CUTOFF,
    ) -> Optional[str]:
        """Best node in ``folder`` for a foreign name, or ``None``.

        Exact slug first, then a declared alias, then difflib at ``cutoff``,
        because each step is strictly less trustworthy than the one before.
        ``None`` means none: a caller must say it could not resolve a name
        rather than round it to the nearest node.
        """

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
        """Violations declared by a combination of nodes, sorted and complete.

        ``conflict``: a ``conflicts-with`` edge inside the set, either
        direction.  ``unmet-requirement``: a ``requires`` target outside the
        set.  ``risk``: a ``risks`` edge to an anti-pattern, with that node's
        ``mitigated-by`` rules as fixes and its newest two evidence rows.
        """

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
                        "apply %s" % rule
                        for rule in target["relations"].get("mitigated-by", ())
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
        """Design-side briefing for nodes: definition, known risks, exemplars."""

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

    # ---- lint ---------------------------------------------------------

    def lint(self) -> tuple[list[str], list[str]]:
        """Return ``(errors, warnings)`` for the whole graph.

        Errors: a type outside :data:`NODE_TYPES`, an unknown link type, a
        broken link, a link whose target type contradicts :data:`TARGET_TYPE`,
        and alias problems.  Warnings: one-sided ``conflicts-with`` and orphan
        nodes; nodes still ``status: seeded`` are exempt from the orphan check
        because an imported node no case study uses yet is pending review, not
        a defect.
        """

        errors: list[str] = []
        warnings: list[str] = []
        conflicts: dict[str, set[str]] = {}
        linked: set[str] = set()
        claimed: dict[tuple[str, str], str] = {}
        for path, node in self.nodes.items():
            if node["type"] not in NODE_TYPES:
                errors.append(
                    "%s: type %r not in %s" % (path, node["type"], "/".join(NODE_TYPES))
                )
            aliases = node["frontmatter"].get("aliases")
            folder = path.split("/", 1)[0]
            if aliases is not None and (
                not isinstance(aliases, (list, tuple))
                or any(not isinstance(alias, str) for alias in aliases)
            ):
                errors.append("%s: aliases must be a list of strings" % path)
            else:
                for alias in aliases or ():
                    slug = slugify(alias)
                    key = (folder, slug)
                    if "%s/%s" % (folder, slug) in self.nodes:
                        errors.append(
                            "%s: alias %r shadows the real node %s/%s"
                            % (path, alias, folder, slug)
                        )
                    elif key in claimed:
                        errors.append(
                            "%s: alias %r already claimed by %s" % (path, alias, claimed[key])
                        )
                    else:
                        claimed[key] = path
            for link_type, targets in node["relations"].items():
                if link_type not in LINK_TYPES:
                    errors.append(
                        "%s: unknown link type %s:: (defined: %s)"
                        % (path, link_type, ", ".join(LINK_TYPES))
                    )
                    continue
                for target in targets:
                    linked.add(path)
                    linked.add(target)
                    other = self.nodes.get(target)
                    if other is None:
                        errors.append("%s: broken link [[%s]]" % (path, target))
                        continue
                    wanted = TARGET_TYPE.get(link_type)
                    if wanted is not None and other["type"] != wanted:
                        errors.append(
                            "%s: %s:: must point at a %s, [[%s]] is a %s"
                            % (path, link_type, wanted, target, other["type"])
                        )
                    if link_type == "conflicts-with":
                        conflicts.setdefault(path, set()).add(target)
        for left, targets in sorted(conflicts.items()):
            for right in sorted(targets):
                if left not in conflicts.get(right, set()):
                    warnings.append(
                        "%s: conflicts-with [[%s]] is one-sided (%s does not declare it back)"
                        % (left, right, right)
                    )
        for path, node in self.nodes.items():
            if path in linked or node["frontmatter"].get("status") == "seeded":
                continue
            warnings.append("%s: orphan: no links in or out" % path)
        return errors, warnings


def bundled_vault_root() -> Path:
    """The seed vault shipped with the Workshop distribution."""

    return Path(__file__).resolve().parent / "vault"


def seed_vault(destination: Path, source: Optional[Path] = None) -> dict[str, int]:
    """Copy seed nodes into ``destination`` without overwriting existing files.

    Hand-written definitions and linter fixes in a working vault survive
    re-seeding; the result reports how many nodes were written and kept.
    """

    source_root = Path(source) if source is not None else bundled_vault_root()
    Vault.from_directory(source_root)  # fail closed before touching the target
    destination = Path(destination)
    if destination.exists() and (destination.is_symlink() or not destination.is_dir()):
        raise VaultError("vault destination must be a directory: %s" % destination)
    written = kept = 0
    for path in sorted(source_root.rglob("*.md")):
        relative = path.relative_to(source_root)
        if len(relative.parts) != 2 or relative.parts[0].startswith("_"):
            continue
        target = destination / relative
        if target.exists() or target.is_symlink():
            kept += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_read_node_file(path).encode("utf-8"))
        written += 1
    return {"written": written, "kept": kept}


__all__ = [
    "LINK_TYPES",
    "MAX_NODE_BYTES",
    "MAX_PACKED_BYTES",
    "MAX_VAULT_NODES",
    "NODE_TYPES",
    "TARGET_TYPE",
    "VAULT_KIND",
    "VAULT_SCHEMA_VERSION",
    "Vault",
    "VaultError",
    "VaultNodeNotFound",
    "bundled_vault_root",
    "evidence_rows",
    "normalize_path",
    "parse_frontmatter",
    "parse_node",
    "seed_vault",
    "slugify",
]
