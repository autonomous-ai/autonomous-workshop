"""The host's check of a Made kit's Manual (ADR 0092 decision 9).

Final verification writes a schema 7 kit's Manual into its CAD project
(``manual/manual.pdf`` and its report ``manual/manual.json``) with the
run-local ``make-round/scripts/kit_manual.py``, from the installed Assembly
Tree and the build. Before Make is accepted the host checks, on the exact
sealed bytes and without rebuilding any geometry (ADR 0061), that

- the report is a passing Manual report for the sealed tree;
- every leaf of the tree (printed Part, Bought Part, Print Piece) is in
  exactly one section's material list, and every Assembly Step and Check
  Step is in it;
- the PDF is the one the report names.

Release adds nothing: it ships the accepted PDF beside the STEP files and the
Print Sheets. A route whose host reruns final verification (Forge, Quest)
also proves the Manual deterministic, because every declared file must come
back byte for byte.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError
from workshop.make.kit_tree import TREE_SCHEMA_VERSION, install_document, tree_digest

MANUAL_DIRECTORY = "manual"
PDF_PATH = "manual/manual.pdf"
REPORT_PATH = "manual/manual.json"
REPORT_KIND = "kit-manual"
REPORT_SCHEMA = 1


def _leaves(contract: Mapping[str, Any]) -> list[str]:
    tree = contract["assembly_tree"]
    section = contract.get("print")
    pieces = section.get("pieces") if isinstance(section, Mapping) else None
    return sorted([item["id"] for item in tree["parts"]] + [item["id"] for item in pieces or ()])


def verify_made_manual(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    catalogue: Any,
) -> dict[str, Any] | None:
    """The accepted Manual's account, or None for a contract before schema 7.
    ``catalogue`` is the Wish's sealed ``kit_catalogue``. Raises
    ContractError naming what is wrong."""

    if not isinstance(contract, Mapping) or contract.get("schema_version") != TREE_SCHEMA_VERSION:
        return None
    if not isinstance(catalogue, Mapping):
        raise ContractError("the Wish seals no kit_catalogue beside its schema 7 Design Contract")
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)

    def read(relative: str) -> bytes:
        path = (prefix / relative).as_posix()
        entry = entries.get(path)
        if entry is None:
            raise ContractError("the Made CAD project lacks its kit Manual file %s" % relative)
        content = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise ContractError("the kit Manual file %s differs from the Made manifest" % relative)
        return content

    try:
        report = json.loads(read(REPORT_PATH).decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("the kit Manual report %s is not JSON" % REPORT_PATH) from exc
    if (
        not isinstance(report, Mapping) or report.get("kind") != REPORT_KIND
        or report.get("schema_version") != REPORT_SCHEMA
    ):
        raise ContractError("%s is not a kit Manual report" % REPORT_PATH)
    if report.get("tree_sha256") != tree_digest(install_document(contract, catalogue)):
        raise ContractError("%s was written for another Assembly Tree than the sealed one" % REPORT_PATH)
    failures = report.get("failures")
    if report.get("passed") is not True or failures:
        shown = "; ".join(str(item) for item in (failures or [])[:4]) or "it did not pass"
        raise ContractError("the kit Manual was not written: %s" % shown)
    sections = report.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ContractError("the kit Manual report has no section")
    listed: Counter = Counter()
    steps: Counter = Counter()
    for section in sections:
        materials = section.get("materials") if isinstance(section, Mapping) else None
        if not isinstance(materials, Mapping) or set(materials) != {"printed", "paper", "bought"}:
            raise ContractError("a kit Manual section lacks its three-column material list")
        for column in materials.values():
            for row in column if isinstance(column, list) else ():
                listed[row.get("id") if isinstance(row, Mapping) else None] += 1
        for step in section.get("steps") or ():
            steps[step] += 1
    expected = Counter(_leaves(contract))
    if listed != expected:
        missing = sorted((expected - listed).elements())
        extra = sorted(str(item) for item in (listed - expected).elements())
        raise ContractError(
            "the kit Manual does not list every leaf in exactly one material list: missing %s; "
            "extra or repeated %s" % (", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    tree = contract["assembly_tree"]
    if steps != Counter(item["id"] for item in tree["steps"]):
        raise ContractError("the kit Manual does not show every Assembly Step exactly once")
    checks = [item.get("id") for item in report.get("checks") or () if isinstance(item, Mapping)]
    if checks != [item["id"] for item in tree.get("checks") or ()]:
        raise ContractError("the kit Manual does not show every Check Step first")
    pdf = read(PDF_PATH)
    pdf_sha256 = hashlib.sha256(pdf).hexdigest()
    named = report.get("pdf") if isinstance(report.get("pdf"), Mapping) else {}
    if not pdf.startswith(b"%PDF") or named.get("sha256") != pdf_sha256:
        raise ContractError("the kit Manual PDF is not the one its report names")
    company = report.get("company") if isinstance(report.get("company"), Mapping) else {}
    return {
        "pdf": (prefix / PDF_PATH).as_posix(),
        "pdf_sha256": pdf_sha256,
        "pages": report.get("pages"),
        "sections": len(sections),
        "check_steps": len(checks),
        "after_sales_confirmed": company.get("confirmed") is True,
    }


__all__ = ["PDF_PATH", "REPORT_PATH", "verify_made_manual"]
