"""Plain-data contract for an explicitly unverified CAD handoff.

An interrupted inspection permits delivery of a prototype with limitations; it
never supplies positive geometry or print-readiness evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATUS = "geometry-unverified"
LIMITATION = "Geometry inspection is incomplete. This prototype is unverified and is not print-ready; see GEOMETRY-NOTES.md."
REPORT_NAME = "geometry-inspection.json"
NOTES_NAME = "GEOMETRY-NOTES.md"


def validate_report(value):
    if (not isinstance(value, dict) or type(value.get("schema_version")) is not int
            or value.get("schema_version") != 1 or set(value) != {
                "schema_version", "status", "print_ready_claim", "checks", "verification_sha256"}):
        raise ValueError("invalid geometry inspection report")
    if value.get("status") != "unverified" or value.get("print_ready_claim") is not False:
        raise ValueError("incomplete geometry cannot claim a passing or print-ready result")
    checks = value.get("checks")
    if not isinstance(checks, list) or not 1 <= len(checks) <= 4096:
        raise ValueError("geometry inspection report needs bounded check records")
    unknown = []
    for check in checks:
        if not isinstance(check, dict) or check.get("status") not in ("passed", "unverified"):
            raise ValueError("a measured geometry failure cannot be waived")
        if type(check.get("id")) is not str or not 1 <= len(check["id"]) <= 512 or any(c in check["id"] for c in "\n\r\x00"):
            raise ValueError("invalid geometry check identifier")
        if set(check) != ({"id", "status", "reasons", "completed"} if check["status"] == "unverified" else {"id", "status"}):
            raise ValueError("unexpected geometry check fields")
        if check["status"] == "unverified":
            reasons = check.get("reasons")
            if not isinstance(reasons, list) or not 1 <= len(reasons) <= 16 or any(
                type(reason) is not str or not 1 <= len(reason) <= 512 or any(c in reason for c in "\n\r\x00")
                for reason in reasons
            ):
                raise ValueError("unverified geometry needs bounded reasons")
            if type(check.get("completed", 0)) is not int or check.get("completed", 0) < 0:
                raise ValueError("invalid completed geometry check count")
            unknown.append(check)
    if not unknown:
        raise ValueError("unverified geometry report has no unfinished checks")
    return unknown


def notes_text(value):
    unknown = validate_report(value)
    lines = ["# Geometry inspection limitations", "", LIMITATION, "",
             "The following checks did not finish. No passing verdict is inferred from their interruption.", ""]
    for check in unknown:
        lines.append(f"- {check['id']}: {'; '.join(check['reasons'])} (completed measurements: {check.get('completed', 0)}).")
    return "\n".join(lines) + "\n"


def read_report(verification: Path):
    if verification.is_symlink() or not verification.is_file() or verification.stat().st_size > 1_000_000:
        raise ValueError("verification record is unavailable")
    content = verification.read_bytes()
    current = content.decode("utf-8").split("\n---\n\n## Previous pipeline record", 1)[0]
    final_mode = any(f"- Mode: `{mode}`\n" in current for mode in ("final", "image-derived final"))
    if not current.startswith("# Verification pipeline record\n") or not final_mode or "- Result: **UNVERIFIED** (exit 0)\n" not in current:
        raise ValueError("unverified handoff needs a current final UNVERIFIED report")
    path = verification.parent / REPORT_NAME
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("geometry inspection report is unavailable")
    def unique_object(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("duplicate geometry report field")
            result[key] = item
        return result
    value = json.loads(path.read_bytes(), object_pairs_hook=unique_object)
    validate_report(value)
    if value.get("verification_sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError("geometry inspection report does not bind this verification record")
    return value


def seal_disclosure(product_root: Path, verification: Path, product: dict):
    value = read_report(verification)
    notes = notes_text(value)
    for path in (product_root / NOTES_NAME, product_root / "README.md", product_root / "product.json"):
        if path.is_symlink():
            raise ValueError("geometry disclosure must not overwrite symlinks")
    limitations = product.get("limitations", [])
    if not isinstance(limitations, list) or not all(isinstance(item, str) for item in limitations):
        raise ValueError("product limitations must be a text list")
    product.update(status=STATUS, print_ready_claim=False,
                   limitations=[*([item for item in limitations if item != LIMITATION]), LIMITATION])
    (product_root / NOTES_NAME).write_text(notes, encoding="utf-8")
    readme = product_root / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else "# Product notes\n"
    marker = "\n<!-- workshop-geometry-disclosure -->\n"
    readme.write_text(text.split(marker, 1)[0].rstrip() + "\n" + marker + notes, encoding="utf-8")
    (product_root / "product.json").write_text(json.dumps(product, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_disclosure(product_root: Path, verification: Path, product):
    value = read_report(verification)
    if product.get("status") != STATUS or product.get("print_ready_claim") is not False or LIMITATION not in product.get("limitations", []):
        raise ValueError("unverified handoff lacks its product limitations")
    notes = product_root / NOTES_NAME
    readme = product_root / "README.md"
    if notes.is_symlink() or readme.is_symlink() or notes.read_text(encoding="utf-8") != notes_text(value) or notes_text(value) not in readme.read_text(encoding="utf-8"):
        raise ValueError("unverified handoff lacks its exact final documentation")
    return value
