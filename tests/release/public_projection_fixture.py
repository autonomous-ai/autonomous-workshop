"""Opaque sealed fixtures for publication identity and disclosure tests.

These are transport fakes, not accepted engineering or manufactured products.
"""

import hashlib
import json
from pathlib import Path


PRIVATE_SENTINEL = b"private-supplier-and-manufacturing-test-sentinel"


def add_public_presentation(root: Path, *, public_readme: bool = False):
    def binding(path):
        return {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}

    (root / "public").mkdir(exist_ok=True)
    (root / "internal").mkdir(exist_ok=True)
    (root / "public/assembled.step").write_bytes((root / "assembled.step").read_bytes())
    (root / "public/hero.png").write_bytes(b"\x89PNG\r\n\x1a\ncomplete-mixed-material-scene")
    (root / "internal/occurrences.json").write_bytes(b'{"private":"' + PRIVATE_SENTINEL + b'"}')
    (root / "internal/assembly.md").write_bytes(PRIVATE_SENTINEL)
    (root / "README.md").write_bytes(PRIVATE_SENTINEL)
    (root / "private-build.py").write_bytes(b"# " + PRIVATE_SENTINEL)
    public_paths = ["public/assembled.step", "public/hero.png"]
    if public_readme:
        (root / "public/README.md").write_bytes(b"# Finished product\n\nEnjoy the complete toy.\n")
        public_paths.append("public/README.md")
    document = {
        "schema_version": 1, "kind": "workshop.manufacturing", "delivery": "assembled-product",
        "assembly": {"step": binding("assembled.step"), "occurrences": binding("internal/occurrences.json")},
        "components": [{"private": PRIVATE_SENTINEL.decode()}],
        "stock": [], "consumables": [], "tools": [], "assembly_steps": [],
        "public_assets": [binding(path) for path in sorted(public_paths)],
    }
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    (root / "internal/manufacturing.json").write_bytes(payload)
    return {"schema_version": 1, "manifest_path": "internal/manufacturing.json", "manifest_sha256": hashlib.sha256(payload).hexdigest()}
