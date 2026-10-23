"""The host's check of a Made toy's Print Sheets (ADR 0091).

Make installs the sealed Design Contract's print section and art into its CAD
project (``print/pieces.json``, ``print/art/``), gates every part that hosts
a Print Piece, and lays the sheets out into ``print/sheets/``. Before Make is
accepted the host checks, on the exact sealed bytes and without rebuilding any
geometry (ADR 0061), that

- the installed section is the sealed contract's, byte for byte as JSON;
- every art file is the one the Wish sealed;
- the layout report passed, places every copy of every piece once, and
  names the PDF and previews the product carries.

The sheets the host accepts are the ones Release ships beside the STEP files.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError

PIECES_PATH = "print/pieces.json"
ART_DIRECTORY = "print/art"
SHEETS_DIRECTORY = "print/sheets"
REPORT_NAME = "print-sheets.json"
PDF_NAME = "print-sheets.pdf"
REPORT_KIND = "print-sheets"


def _labels(section: Mapping[str, Any]) -> Counter:
    """Every copy's label print_sheets.py gives, ``<id>`` or ``<id> n/count``."""

    labels: Counter = Counter()
    for piece in section["pieces"]:
        count = int(piece.get("count", 1))
        for copy in range(1, count + 1):
            labels[piece["id"] if count == 1 else "%s %d/%d" % (piece["id"], copy, count)] += 1
    return labels


def verify_made_print_sheets(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    sealed_art: Mapping[str, str],
) -> list[dict[str, Any]]:
    """The accepted sheets, one entry each, or ``[]`` for a toy without
    Print Sheets. ``sealed_art`` maps each sealed print art file to the
    sha256 the Wish bound. Raises ContractError naming what is wrong."""

    section = contract.get("print") if isinstance(contract, Mapping) else None
    if not isinstance(section, Mapping):
        return []
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)

    def read(relative: str) -> bytes:
        path = (prefix / relative).as_posix()
        entry = entries.get(path)
        if entry is None:
            raise ContractError("the Made CAD project lacks its Print Sheet file %s" % relative)
        content = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise ContractError("the Print Sheet file %s differs from the Made manifest" % relative)
        return content

    def json_file(relative: str) -> Any:
        try:
            return json.loads(read(relative).decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ContractError("the Print Sheet file %s is not JSON" % relative) from exc

    installed = json_file(PIECES_PATH)
    if not isinstance(installed, Mapping) or installed.get("print") != section:
        raise ContractError("%s is not the sealed Design Contract's print section" % PIECES_PATH)
    for item in section["art"]:
        name = item["file"]
        digest = hashlib.sha256(read("%s/%s" % (ART_DIRECTORY, name))).hexdigest()
        if sealed_art.get(name) != digest:
            raise ContractError("print art %s is not the file the Wish sealed" % name)

    report = json_file("%s/%s" % (SHEETS_DIRECTORY, REPORT_NAME))
    if not isinstance(report, Mapping) or report.get("kind") != REPORT_KIND:
        raise ContractError("the Print Sheet layout report is malformed")
    failures = report.get("failures")
    if report.get("passed") is not True or failures:
        shown = "; ".join(str(item) for item in (failures or [])[:4]) or "it did not pass"
        raise ContractError("the Print Sheets did not lay out: %s" % shown)
    sheets = report.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise ContractError("the Print Sheet layout report places no sheet")
    placed = Counter(
        piece.get("label") for sheet in sheets if isinstance(sheet, Mapping)
        for piece in sheet.get("pieces") or () if isinstance(piece, Mapping)
    )
    if placed != _labels(section):
        missing = sorted((_labels(section) - placed).elements())
        extra = sorted((placed - _labels(section)).elements())
        raise ContractError(
            "the Print Sheets do not place every piece once: missing %s; extra %s"
            % (", ".join(missing[:6]) or "none", ", ".join(str(item) for item in extra[:6]) or "none")
        )
    pdf = read("%s/%s" % (SHEETS_DIRECTORY, PDF_NAME))
    pdf_sha256 = hashlib.sha256(pdf).hexdigest()
    if not pdf.startswith(b"%PDF") or (report.get("pdf") or {}).get("sha256") != pdf_sha256:
        raise ContractError("the Print Sheet PDF is not the one its layout report names")
    previews = report.get("previews")
    if not isinstance(previews, list) or len(previews) != len(sheets):
        raise ContractError("the Print Sheet layout report lacks a preview per sheet")
    accepted = []
    for sheet, preview in zip(sheets, previews):
        relative = "%s/%s" % (SHEETS_DIRECTORY, preview)
        read(relative)
        accepted.append({
            "sheet": str(sheet.get("sheet")),
            "stock": str(sheet.get("stock")),
            "pieces": len(sheet.get("pieces") or ()),
            "preview": relative,
            "pdf": "%s/%s" % (SHEETS_DIRECTORY, PDF_NAME),
            "pdf_sha256": pdf_sha256,
        })
    return accepted


__all__ = ["verify_made_print_sheets"]
