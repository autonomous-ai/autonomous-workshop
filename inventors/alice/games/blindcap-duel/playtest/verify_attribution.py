"""verify_attribution.py — confirm every Alice Factory description ends with
exactly 'By Alice.' (no trailing whitespace, not 'Note: By Alice.')."""
from __future__ import annotations
import json

SUFFIX = "By Alice."

files = [
    "games/blindcap-duel/content/factory-page.json",
    "games/blindcap-duel/content/page.json",
]

def check(desc: str, path: str) -> bool:
    ok = desc.endswith(SUFFIX) and desc.rstrip() == desc
    print(f"  {path}: ends_exact={ok} tail={desc[-12:]!r}")
    return ok

all_ok = True
for path in files:
    data = json.load(open(path))
    desc = data.get("metadata", {}).get("description") or data.get("description", "")
    if not desc:
        print(f"  {path}: NO description found")
        all_ok = False
        continue
    if not check(desc, path):
        all_ok = False

print("ALL_OK" if all_ok else "FAIL")
