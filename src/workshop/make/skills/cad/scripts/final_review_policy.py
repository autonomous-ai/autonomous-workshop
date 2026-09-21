"""Operator-owned final critic experiment; no image judgment or model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

OPTIONS = "FINAL-REVIEW-OPTIONS.json"
MARKER = "snap/FINAL-REVIEW-NOT-RUN.json"
DISCLOSURE = "Final independent visual review was not run (operator experiment)."


def enabled() -> bool:
    script = Path(__file__).resolve()
    if script.parents[3].name != ".agents":
        return True
    path = script.parents[4] / OPTIONS
    if not path.exists() and not path.is_symlink():
        return True  # Frozen legacy runs retain their gate.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024:
        raise ValueError("invalid final review options")
    payload = json.loads(path.read_bytes())
    if (not isinstance(payload, dict)
            or set(payload) != {"schema_version", "check_final_review"}
            or type(payload["schema_version"]) is not int or payload["schema_version"] != 1
            or type(payload["check_final_review"]) is not bool):
        raise ValueError("invalid final review options")
    return payload["check_final_review"]


def omission(project: Path) -> dict:
    if enabled():
        raise ValueError("final independent review is required by the operator policy")
    if (project / "snap/SIGNATURE-REVIEW.json").exists() or (project / "snap/SIGNATURE-REVIEW.json").is_symlink():
        raise ValueError("archive prior SIGNATURE-REVIEW.json outside the product before declaring not-run")
    files = sorted(project.rglob("*.py")) + [project / "snap/iso.png", project / "snap/signature.png"]
    hashes = {}
    for path in files:
        if any(part in ("__cadgen__", "__pycache__", ".venv") for part in path.relative_to(project).parts):
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("review omission requires regular source and final image files")
        hashes[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"schema_version": 1, "status": "not-run", "reason": "operator-disabled",
            "disclosure": DISCLOSURE, "sha256s": hashes}


def validate(project: Path) -> str:
    path = project / MARKER
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("missing or invalid final review not-run evidence")
    content = path.read_bytes()
    if json.loads(content) != omission(project):
        raise ValueError("stale or invalid final review not-run evidence")
    return hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    project = Path(sys.argv[1]).resolve()
    value = omission(project)
    (project / MARKER).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    print(DISCLOSURE)
