#!/usr/bin/env python3
"""Search and fetch cited parametric CAD design references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from catalog_build import extract_function, records_from_tar, validate_records, write_jsonl


SKILL_DIR = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = SKILL_DIR / "data" / "sources.json"
# Product-run skill trees are immutable package inputs. Keep downloaded indexes
# in the writable product workspace from which the client is invoked.
DEFAULT_CACHE_DIR = Path.cwd().resolve() / ".design-reference-cache"
USER_AGENT = "text-to-3d-design-reference/1.0"
TOKEN_RE = re.compile(r"[a-z0-9]+")
MANAGED_FETCH_FILES = {"reference.build123d.txt", "contact-sheet.png", "LICENSE.md", "provenance.json"}
SELF_CHECK_FIXTURE = b'''"""fixture"""
from build123d import *

# Description: A rounded mounting bracket with two holes.
def model_fixture_0001():
    """Model: Fixture"""
    return Box(1, 2, 3)

MODELS = {
    "model_fixture_0001": {
        "func": model_fixture_0001,
        "volume": 6.0,
        "area": 22.0,
    },
}
'''


def _json_output(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_registry() -> dict[str, Any]:
    payload = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1 or not isinstance(payload.get("sources"), list):
        raise SystemExit(f"Unsupported source registry: {SOURCE_REGISTRY}")
    return payload


def _sources_by_id() -> dict[str, dict[str, Any]]:
    return {source["id"]: source for source in _load_registry()["sources"]}


def _source(source_id: str) -> dict[str, Any]:
    sources = _sources_by_id()
    try:
        return sources[source_id]
    except KeyError as exc:
        raise SystemExit(f"Unknown source {source_id!r}; choose one of: {', '.join(sorted(sources))}") from exc


def _cache_paths(cache_dir: Path, source_id: str) -> tuple[Path, Path]:
    return cache_dir / f"{source_id}.jsonl", cache_dir / f"{source_id}.meta.json"


def _request(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} for {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc.reason}") from exc


def _download_to_temp(url: str, timeout: float) -> Path:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    handle = tempfile.NamedTemporaryFile(prefix="design-reference-", suffix=".tar.gz", delete=False)
    path = Path(handle.name)
    try:
        with handle, urllib.request.urlopen(request, timeout=timeout) as response:
            shutil.copyfileobj(response, handle)
        return path
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        path.unlink(missing_ok=True)
        if isinstance(exc, urllib.error.HTTPError):
            raise SystemExit(f"HTTP {exc.code} for {url}") from exc
        raise SystemExit(f"Failed to fetch {url}: {exc.reason}") from exc


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


def _sync(args: argparse.Namespace) -> int:
    source = _source(args.source)
    cache_dir = Path(args.cache_dir).resolve()
    index_path, meta_path = _cache_paths(cache_dir, source["id"])
    if index_path.exists() and meta_path.exists() and not args.force:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        index_data = index_path.read_bytes()
        cache_valid = (
            meta.get("revision") == source["revision"]
            and meta.get("recordCount") == source["expectedRecords"]
            and meta.get("indexByteSize") == len(index_data)
            and meta.get("indexSha256") == _sha256(index_data)
        )
        if cache_valid:
            _json_output({"ok": True, "outcome": "current", **meta, "license": source["license"]})
            return 0

    archive_path = _download_to_temp(source["archiveUrl"], args.timeout)
    try:
        archive_sha256 = _sha256(archive_path.read_bytes())
        with tarfile.open(archive_path, mode="r:gz") as archive:
            records = records_from_tar(archive, source["id"])
        records = validate_records(records, source["expectedRecords"])
        index_info = write_jsonl(records, index_path)
    finally:
        archive_path.unlink(missing_ok=True)

    meta = {
        "schemaVersion": 1,
        "source": source["id"],
        "repository": source["repository"],
        "revision": source["revision"],
        "recordCount": index_info["recordCount"],
        "indexPath": str(index_path),
        "indexByteSize": index_info["byteSize"],
        "indexSha256": index_info["sha256"],
        "archiveSha256": archive_sha256,
        "syncedAt": datetime.now(timezone.utc).isoformat(),
    }
    _write_atomic(meta_path, (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    _json_output({"ok": True, "outcome": "synced", **meta, "license": source["license"]})
    return 0


def _load_records(cache_dir: Path, source_id: str) -> list[dict[str, Any]]:
    source = _source(source_id)
    index_path, meta_path = _cache_paths(cache_dir, source_id)
    if not index_path.exists() or not meta_path.exists():
        raise SystemExit(
            f"Catalog is not synced: {source_id}. Run: "
            f"{sys.executable} {Path(__file__)} sync --source {source_id}"
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("revision") != source["revision"]:
        raise SystemExit(f"Catalog revision is stale for {source_id}; run sync --force")
    index_data = index_path.read_bytes()
    if meta.get("indexByteSize") != len(index_data) or meta.get("indexSha256") != _sha256(index_data):
        raise SystemExit(f"Catalog cache checksum failed for {source_id}; run sync --force")
    records = [json.loads(line) for line in index_data.decode("utf-8").splitlines() if line]
    return validate_records(records, source["expectedRecords"])


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _stems(token: str) -> set[str]:
    values = {token}
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            values.add(token[: -len(suffix)])
    return values


def _score(record: dict[str, Any], query: str) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 1.0
    title = str(record.get("title") or "").lower()
    description = str(record.get("description") or "").lower()
    identifier = str(record.get("id") or "").lower()
    title_tokens = set(_tokens(title))
    description_tokens = set(_tokens(description))
    score = 0.0
    matched = 0
    for token in query_tokens:
        variants = _stems(token)
        token_score = 0.0
        if any(variant in title_tokens for variant in variants):
            token_score = max(token_score, 6.0)
        if any(variant in description_tokens for variant in variants):
            token_score = max(token_score, 2.5)
        if token in identifier:
            token_score = max(token_score, 8.0)
        if token_score:
            matched += 1
            score += token_score
    lowered_query = query.strip().lower()
    if lowered_query and lowered_query in title:
        score += 12.0
    elif lowered_query and lowered_query in description:
        score += 7.0
    if matched == len(query_tokens):
        score += 5.0
    return score


def _public_record(record: dict[str, Any], source: dict[str, Any], score: float | None = None) -> dict[str, Any]:
    result = dict(record)
    if score is not None:
        result["score"] = round(score, 3)
    result["repository"] = source["repository"]
    result["revision"] = source["revision"]
    result["license"] = source["license"]
    result["sourceUrl"] = f"{source['repository']}/blob/{source['revision']}/{record['sourcePath']}"
    result["contactSheetUrl"] = f"{source['repository']}/blob/{source['revision']}/{record['contactSheetPath']}"
    return result


def _search(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    source = _source(args.source)
    records = _load_records(cache_dir, source["id"])
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        operation_max = record.get("operationMax")
        if args.min_ops is not None and operation_max is not None and operation_max < args.min_ops:
            continue
        if args.max_ops is not None and record["operationMin"] > args.max_ops:
            continue
        score = _score(record, args.query)
        if score > 0:
            ranked.append((score, record))
    ranked.sort(key=lambda item: (-item[0], item[1]["operationMin"], item[1]["id"]))
    selected = ranked[: max(1, args.limit)]
    results = [_public_record(record, source, score) for score, record in selected]
    if args.format == "text":
        for result in results:
            print(f"{result['score']:>6.1f}  {result['id']}  [{result['operationBucket']}]  {result['title']}")
            print(f"        {result['description']}")
        return 0
    _json_output(
        {
            "query": args.query,
            "source": source["id"],
            "totalMatches": len(ranked),
            "items": results,
            "license": source["license"],
        }
    )
    return 0


def _find_record(cache_dir: Path, catalog_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = _sources_by_id()
    if "/" in catalog_id:
        source_id, function_name = catalog_id.split("/", 1)
    else:
        function_name = catalog_id
        matching_sources = []
        for source_id in sources:
            try:
                if any(record["function"] == function_name for record in _load_records(cache_dir, source_id)):
                    matching_sources.append(source_id)
            except SystemExit:
                continue
        if len(matching_sources) != 1:
            raise SystemExit(f"Use a full catalog id; short id matched {len(matching_sources)} sources")
        source_id = matching_sources[0]
    source = _source(source_id)
    for record in _load_records(cache_dir, source_id):
        if record["function"] == function_name or record["id"] == catalog_id:
            return source, record
    raise SystemExit(f"Unknown catalog id: {catalog_id}")


def _show(args: argparse.Namespace) -> int:
    source, record = _find_record(Path(args.cache_dir).resolve(), args.catalog_id)
    _json_output(_public_record(record, source))
    return 0


def _verify_provenance(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings = []
    files = payload.get("files")
    ok = payload.get("schemaVersion") == 1 and isinstance(files, dict) and bool(files)
    if not ok:
        findings.append({"file": None, "ok": False, "error": "invalid provenance schema or empty file set"})
    for relative, expected in files.items() if isinstance(files, dict) else []:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            findings.append({"file": relative, "ok": False, "error": "unsafe path"})
            ok = False
            continue
        target = path.parent / relative_path
        if not target.is_file():
            findings.append({"file": relative, "ok": False, "error": "missing"})
            ok = False
            continue
        data = target.read_bytes()
        actual = _sha256(data)
        match = actual == expected.get("sha256") and len(data) == expected.get("byteSize")
        findings.append({"file": relative, "ok": match, "sha256": actual, "byteSize": len(data)})
        ok = ok and match
    return {"provenance": str(path), "ok": ok, "files": findings}


def _current_fetch(target_dir: Path, record: dict[str, Any], source: dict[str, Any]) -> dict[str, Any] | None:
    provenance = target_dir / "provenance.json"
    if not provenance.is_file():
        return None
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    if payload.get("catalog", {}).get("id") != record["id"]:
        return None
    if payload.get("source", {}).get("revision") != source["revision"]:
        return None
    verification = _verify_provenance(provenance)
    if not verification["ok"]:
        return None
    return {"ok": True, "outcome": "current", "path": str(target_dir), "verification": verification}


def _fetch(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    source, record = _find_record(cache_dir, args.catalog_id)
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        raise SystemExit(f"Project directory does not exist: {project_dir}")
    target_dir = project_dir / "ref" / "external" / source["id"] / record["function"]
    if target_dir.exists() and not args.overwrite:
        current = _current_fetch(target_dir, record, source)
        if current:
            _json_output(current)
            return 0
        raise SystemExit(f"Reference directory exists but is incomplete or changed: {target_dir}; use --overwrite")

    raw_base = source["rawBaseUrl"].rstrip("/")
    source_url = f"{raw_base}/{record['sourcePath']}"
    contact_url = f"{raw_base}/{record['contactSheetPath']}"
    license_url = f"{raw_base}/{source['licensePath']}"
    batch = _request(source_url, args.timeout)
    excerpt = extract_function(batch, record["function"])
    extracted_function = excerpt[excerpt.index(f"def {record['function']}") :].rstrip()
    actual_function_sha256 = _sha256(extracted_function.encode("utf-8"))
    if actual_function_sha256 != record["functionSha256"]:
        raise SystemExit(
            f"Pinned source hash mismatch for {record['id']}: expected {record['functionSha256']}, "
            f"got {actual_function_sha256}"
        )

    header = (
        '"""Reference-only build123d excerpt.\n\n'
        f"Catalog id: {record['id']}\n"
        f"Source: {source_url}\n"
        f"Revision: {source['revision']}\n"
        f"License: {source['license']['name']} ({source['license']['use']})\n"
        "This file intentionally uses a .txt suffix so cadgen will not discover it.\n"
        '"""\n\n'
    )
    files: dict[str, bytes] = {
        "reference.build123d.txt": (header + excerpt).encode("utf-8"),
        "LICENSE.md": _request(license_url, args.timeout),
    }
    if not args.no_contact_sheet:
        files["contact-sheet.png"] = _request(contact_url, args.timeout)

    target_dir.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        for name in MANAGED_FETCH_FILES:
            if name != "provenance.json" and name not in files:
                (target_dir / name).unlink(missing_ok=True)
    for name, data in files.items():
        _write_atomic(target_dir / name, data)

    file_records = {
        name: {"sha256": _sha256(data), "byteSize": len(data)}
        for name, data in sorted(files.items())
    }
    provenance = {
        "schemaVersion": 1,
        "catalog": record,
        "source": {
            "repository": source["repository"],
            "revision": source["revision"],
            "sourceUrl": source_url,
            "contactSheetUrl": None if args.no_contact_sheet else contact_url,
            "licenseUrl": license_url,
        },
        "license": source["license"],
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "files": file_records,
    }
    _write_atomic(
        target_dir / "provenance.json",
        (json.dumps(provenance, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    verification = _verify_provenance(target_dir / "provenance.json")
    _json_output(
        {
            "ok": verification["ok"],
            "outcome": "fetched",
            "catalogId": record["id"],
            "path": str(target_dir),
            "license": source["license"],
            "verification": verification,
        }
    )
    return 0 if verification["ok"] else 1


def _verify(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    if target.name == "provenance.json":
        provenance_paths = [target]
    elif (target / "provenance.json").is_file():
        provenance_paths = [target / "provenance.json"]
    elif (target / "ref" / "external").is_dir():
        provenance_paths = sorted((target / "ref" / "external").glob("*/*/provenance.json"))
    else:
        provenance_paths = sorted(target.glob("*/*/provenance.json"))
    if not provenance_paths:
        raise SystemExit(f"No provenance.json found under {target}")
    results = [_verify_provenance(path) for path in provenance_paths]
    ok = all(result["ok"] for result in results)
    _json_output({"ok": ok, "references": results})
    return 0 if ok else 1


def _self_check(args: argparse.Namespace) -> int:
    from catalog_build import parse_batch

    records = parse_batch("fixture", "01_2ops/batch_001.py", SELF_CHECK_FIXTURE)
    if len(records) != 1 or records[0]["title"] != "Fixture" or records[0]["volume"] != 6.0:
        raise SystemExit("catalog parser self-check failed")
    excerpt = extract_function(SELF_CHECK_FIXTURE, "model_fixture_0001")
    if "from build123d import *" not in excerpt or "def model_fixture_0001" not in excerpt or "MODELS" in excerpt:
        raise SystemExit("source extraction self-check failed")
    result: dict[str, Any] = {"ok": True, "parser": "pass", "sourceExtraction": "pass"}
    cache_dir = Path(args.cache_dir).resolve()
    cached = []
    for source in _load_registry()["sources"]:
        index_path, meta_path = _cache_paths(cache_dir, source["id"])
        if index_path.exists() and meta_path.exists():
            records = _load_records(cache_dir, source["id"])
            cached.append({"source": source["id"], "records": len(records), "revision": source["revision"]})
    result["cachedCatalogs"] = cached
    _json_output(result)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and fetch provenance-safe parametric CAD references.")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="Local generated catalog cache.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sources = subparsers.add_parser("sources", help="List configured reference sources.")
    sources.set_defaults(func=lambda args: (_json_output(_load_registry()), 0)[1])

    sync = subparsers.add_parser("sync", help="Build a local search index from a pinned upstream archive.")
    sync.add_argument("--source", default="fusion360-gallery-build123d")
    sync.add_argument("--force", action="store_true")
    sync.add_argument("--timeout", type=float, default=120.0)
    sync.set_defaults(func=_sync)

    search = subparsers.add_parser("search", help="Search the local design index.")
    search.add_argument("query")
    search.add_argument("--source", default="fusion360-gallery-build123d")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--min-ops", type=int)
    search.add_argument("--max-ops", type=int)
    search.add_argument("--format", choices=("json", "text"), default="json")
    search.set_defaults(func=_search)

    show = subparsers.add_parser("show", help="Show one exact catalog record.")
    show.add_argument("catalog_id")
    show.set_defaults(func=_show)

    fetch = subparsers.add_parser("fetch", help="Fetch one selected source excerpt into a project ref directory.")
    fetch.add_argument("catalog_id")
    fetch.add_argument("--project-dir", required=True)
    fetch.add_argument("--no-contact-sheet", action="store_true")
    fetch.add_argument("--overwrite", action="store_true")
    fetch.add_argument("--timeout", type=float, default=60.0)
    fetch.set_defaults(func=_fetch)

    verify = subparsers.add_parser("verify", help="Verify fetched reference checksums.")
    verify.add_argument("path")
    verify.set_defaults(func=_verify)

    self_check = subparsers.add_parser("self-check", help="Run offline parser and extraction checks.")
    self_check.set_defaults(func=_self_check)
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
