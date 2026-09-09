#!/usr/bin/env python3
"""Search step.parts for common standard parts and download STEP files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ORIGIN = "https://api.step.parts"
DEFAULT_OUT_DIR = tempfile.gettempdir()
DEFAULT_FACET_TOP = 8
USER_AGENT = "step-parts-skill/1.0"
COMPACT_PART_KEYS = (
    "id",
    "name",
    "category",
    "family",
    "standard",
    "attributes",
    "stepUrl",
    "pageUrl",
    "apiUrl",
    "sha256",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search the step.parts hosted catalog for low-level common standard parts "
            "(screws, bolts, bearings, electronics parts, motors, connectors, etc.) "
            "and optionally download canonical STEP files. Search stdout is compact "
            "JSON (items + totals, no facets dump) unless --pretty or --facets."
        ),
    )
    parser.add_argument("query", nargs="?", help="Fuzzy search query, for example 'M3 socket head 12'.")
    parser.add_argument("--id", dest="part_id", help="Fetch a specific part id instead of searching.")
    parser.add_argument("--origin", default=DEFAULT_ORIGIN, help=f"API origin. Default: {DEFAULT_ORIGIN}")
    parser.add_argument("--download", action="store_true", help="Download the selected STEP file.")
    parser.add_argument("--all", action="store_true", help="With --download, download every result on the returned page.")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Directory for downloaded STEP files. Default: active temp directory.")
    parser.add_argument("--filename", help="Filename to use when downloading one selected part.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing downloaded file.")
    parser.add_argument("--limit", type=int, default=10, help="Search page size. The API caps this at 500.")
    parser.add_argument("--page", type=int, default=1, help="1-based search page.")
    parser.add_argument("--tag", action="append", default=[], help="Repeatable tag filter.")
    parser.add_argument("--category", action="append", default=[], help="Repeatable category filter.")
    parser.add_argument("--family", action="append", default=[], help="Repeatable family filter.")
    parser.add_argument("--standard", action="append", default=[], help="Repeatable standard filter, for example 'ISO 4762'.")
    parser.add_argument(
        "--facets",
        action="store_true",
        help="Include a compact top-N facets object. Default search omits facets entirely.",
    )
    parser.add_argument(
        "--facet-top",
        type=int,
        default=None,
        help=f"With --facets, keep this many values per facet key. Default: {DEFAULT_FACET_TOP}.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indent=2. Default stdout is compact one-line JSON.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Run compact-output fixtures and exit. Does not touch the network.",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    return parser.parse_args()


def origin_url(origin: str) -> str:
    parsed = urllib.parse.urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit(f"Invalid origin: {origin!r}")
    return origin.rstrip("/")


def build_url(origin: str, path: str, params: list[tuple[str, str]] | None = None) -> str:
    url = f"{origin_url(origin)}{path}"
    if params:
        return f"{url}?{urllib.parse.urlencode(params)}"
    return url


def request(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} for {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc.reason}") from exc


def fetch_json(url: str, timeout: float) -> Any:
    data = request(url, timeout)
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Expected JSON from {url}: {exc}") from exc


def search_parts(args: argparse.Namespace) -> dict[str, Any]:
    params: list[tuple[str, str]] = [
        ("page", str(max(1, args.page))),
        ("pageSize", str(max(1, args.limit))),
    ]
    if args.query:
        params.append(("q", args.query))
    for key in ("tag", "category", "family", "standard"):
        for value in getattr(args, key):
            params.append((key, value))
    return fetch_json(build_url(args.origin, "/v1/parts", params), args.timeout)


def get_part(args: argparse.Namespace, part_id: str) -> dict[str, Any]:
    safe_id = urllib.parse.quote(part_id, safe="")
    return fetch_json(build_url(args.origin, f"/v1/parts/{safe_id}"), args.timeout)


def selected_parts(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.part_id:
        return [get_part(args, args.part_id)]

    result = search_parts(args)
    items = result.get("items", [])
    if not items:
        raise SystemExit("No parts matched the query.")
    if args.download and args.all:
        return items
    return [items[0]]


def filename_for(part: dict[str, Any], requested_filename: str | None, allow_requested: bool) -> str:
    if requested_filename and allow_requested:
        return requested_filename
    step_url = str(part.get("stepUrl") or "")
    name = Path(urllib.parse.urlparse(step_url).path).name
    if name:
        return name
    return f"{part['id']}.step"


def step_download_url(part: dict[str, Any], origin: str) -> str:
    step_url = part.get("stepUrl")
    if not step_url:
        raise SystemExit(f"Part {part.get('id', '<unknown>')} does not include stepUrl.")
    return urllib.parse.urljoin(f"{origin_url(origin)}/", str(step_url))


def write_download(part: dict[str, Any], args: argparse.Namespace, allow_requested_filename: bool) -> dict[str, Any]:
    step_url = step_download_url(part, args.origin)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename_for(part, args.filename, allow_requested_filename)
    if path.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {path}")

    data = request(step_url, args.timeout)
    path.write_bytes(data)

    actual_sha256 = hashlib.sha256(data).hexdigest()
    expected_sha256 = part.get("sha256")
    checksum_ok = expected_sha256 is None or expected_sha256 == actual_sha256
    if not checksum_ok:
        raise SystemExit(
            f"Checksum mismatch for {path}: expected {expected_sha256}, got {actual_sha256}",
        )

    return {
        "id": part.get("id"),
        "name": part.get("name"),
        "path": str(path),
        "stepUrl": step_url,
        "pageUrl": part.get("pageUrl"),
        "apiUrl": part.get("apiUrl"),
        "byteSize": len(data),
        "sha256": actual_sha256,
        "checksumVerified": expected_sha256 is not None,
    }


def compact_part(part: dict[str, Any]) -> dict[str, Any]:
    return {key: part.get(key) for key in COMPACT_PART_KEYS}


def _facet_pairs(values: Any) -> list[tuple[str, int]]:
    ranked: list[tuple[str, int]] = []
    if isinstance(values, dict):
        for name, count in values.items():
            ranked.append((str(name), int(count) if isinstance(count, (int, float)) else 0))
        return ranked
    if not isinstance(values, list):
        return ranked
    for item in values:
        if isinstance(item, dict):
            # `or` would drop a legitimate 0 or "" facet value.
            name = next(
                (item[key] for key in ("value", "name", "key", "id") if item.get(key) is not None),
                None,
            )
            if name is None:
                continue
            count = item.get("count", 0)
            ranked.append((str(name), int(count) if isinstance(count, (int, float)) else 0))
        else:
            ranked.append((str(item), 0))
    return ranked


def compact_facets(facets: Any, top_n: int) -> dict[str, dict[str, int]]:
    if not isinstance(facets, dict):
        return {}
    keep = max(0, top_n)
    compact: dict[str, dict[str, int]] = {}
    for key, values in facets.items():
        ranked = _facet_pairs(values)
        ranked.sort(key=lambda pair: (-pair[1], pair[0]))
        compact[str(key)] = {name: count for name, count in ranked[:keep]}
    return compact


def compact_search(
    result: dict[str, Any],
    *,
    include_facets: bool = False,
    facet_top: int = DEFAULT_FACET_TOP,
) -> dict[str, Any]:
    facets = result.get("facets") or {}
    payload: dict[str, Any] = {
        "items": [compact_part(part) for part in result.get("items") or []],
        "page": result.get("page"),
        "pageSize": result.get("pageSize"),
        "total": result.get("total"),
        "totalPages": result.get("totalPages"),
        "hasNextPage": result.get("hasNextPage"),
        "hasPreviousPage": result.get("hasPreviousPage"),
        "facetKeys": sorted(facets) if isinstance(facets, dict) else [],
    }
    if include_facets:
        payload["facets"] = compact_facets(facets, facet_top)
    return payload


def dump_json(payload: Any, pretty: bool) -> None:
    if pretty:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    else:
        json.dump(payload, sys.stdout, separators=(",", ":"), ensure_ascii=False)
    sys.stdout.write("\n")


def _self_check() -> int:
    part = {
        "id": "iso4762_socket_head_cap_screw_m3x12",
        "name": "ISO 4762 M3x12",
        "description": "long prose that must not appear in compact output",
        "category": "fastener",
        "family": "socket-head-cap-screw",
        "tags": ["screw", "metric"],
        "aliases": ["SHCS M3x12"],
        "standard": {"body": "ISO", "number": "4762", "designation": "ISO 4762"},
        "attributes": {"thread": "M3", "lengthMm": 12},
        "stepUrl": "https://www.step.parts/step/iso4762_socket_head_cap_screw_m3x12.step",
        "glbUrl": "https://example.invalid/preview.glb",
        "pngUrl": "https://example.invalid/preview.png",
        "pageUrl": "https://www.step.parts/parts/iso4762_socket_head_cap_screw_m3x12",
        "apiUrl": "https://api.step.parts/v1/parts/iso4762_socket_head_cap_screw_m3x12",
        "byteSize": 12345,
        "sha256": "abc",
    }
    compact = compact_part(part)
    if set(compact) != set(COMPACT_PART_KEYS):
        raise SystemExit(f"compact_part keys drifted: {sorted(compact)}")
    leaked = {"description", "tags", "aliases", "glbUrl", "pngUrl", "byteSize"}
    if leaked & set(compact):
        raise SystemExit(f"compact_part leaked {sorted(leaked & set(compact))}")

    result = {
        "catalog": {"partCount": 9000, "schemaUrl": "https://example.invalid/schema"},
        "items": [part],
        "page": 1,
        "pageSize": 10,
        "total": 1,
        "totalPages": 1,
        "hasNextPage": False,
        "hasPreviousPage": False,
        "filters": {"q": "M3"},
        "facets": {
            "tags": {"screw": 120, "metric": 80, "extra": 1},
            "families": [
                {"name": "socket-head-cap-screw", "count": 40},
                {"name": "hex-bolt", "count": 9},
                {"value": 0, "count": 3},
            ],
        },
    }
    search = compact_search(result)
    if "facets" in search:
        raise SystemExit("default compact_search must omit facets")
    if search["facetKeys"] != ["families", "tags"]:
        raise SystemExit(f"facetKeys wrong: {search['facetKeys']}")
    if "catalog" in search or "filters" in search:
        raise SystemExit("compact_search leaked catalog metadata")
    if search["items"][0]["id"] != part["id"]:
        raise SystemExit("compact_search dropped items")

    with_facets = compact_search(result, include_facets=True, facet_top=2)
    if with_facets["facets"]["tags"] != {"screw": 120, "metric": 80}:
        raise SystemExit(f"facet top-N failed: {with_facets['facets']['tags']}")
    if "extra" in with_facets["facets"]["tags"]:
        raise SystemExit("facet top-N kept overflow values")
    all_families = compact_search(result, include_facets=True, facet_top=9)["facets"]["families"]
    if "0" not in all_families:
        raise SystemExit(f"a falsy facet value was dropped: {all_families}")

    compact_text = json.dumps(search, separators=(",", ":"), ensure_ascii=False)
    pretty_text = json.dumps(search, indent=2, ensure_ascii=False)
    if len(compact_text) >= len(pretty_text):
        raise SystemExit("compact JSON is not smaller than pretty JSON")
    raw_text = json.dumps(result, indent=2)
    if "description" in compact_text or "glbUrl" in compact_text:
        raise SystemExit("compact JSON still contains dropped part fields")
    if len(compact_text) >= len(raw_text):
        raise SystemExit("compact search did not shrink the pretty API payload")

    print("download_step_part self-check: ok")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_check:
        return _self_check()
    if args.filename and (not args.download or args.all):
        raise SystemExit("--filename can only be used with --download for one selected part.")
    if args.facets and (args.part_id or args.download):
        raise SystemExit("--facets applies to a search only; it has no effect with --id or --download.")
    if args.facet_top is not None and not args.facets:
        raise SystemExit("--facet-top requires --facets.")
    if not args.part_id and not args.query and not any([args.tag, args.category, args.family, args.standard]):
        raise SystemExit("Provide a query, --id, or at least one facet filter.")

    if not args.download:
        if args.part_id:
            output: Any = compact_part(get_part(args, args.part_id))
        else:
            output = compact_search(
                search_parts(args),
                include_facets=args.facets,
                facet_top=DEFAULT_FACET_TOP if args.facet_top is None else args.facet_top,
            )
        dump_json(output, args.pretty)
        return 0

    parts = selected_parts(args)
    downloads = [
        write_download(part, args, allow_requested_filename=len(parts) == 1)
        for part in parts
    ]
    dump_json({"downloads": downloads}, args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
