"""Check every Alice product-description-bearing JSON ends exactly 'By Alice.'"""
import json, glob, sys

SUFFIX = "By Alice."
ok = True

# Candidate files that may carry a product description.
candidates = sorted(glob.glob("toys/blindcap-duel/**/factory-page.json", recursive=True)
                    + glob.glob("toys/blindcap-duel/**/page.json", recursive=True)
                    + glob.glob("toys/blindcap-duel/**/content/*.json", recursive=True))

seen = set()
for path in candidates:
    if path in seen:
        continue
    seen.add(path)
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f"  {path}: unreadable {e}")
        ok = False
        continue
    desc = None
    if isinstance(data, dict):
        m = data.get("metadata", {})
        if isinstance(m, dict):
            desc = m.get("description")
        if desc is None:
            desc = data.get("description")
    if desc is None or not isinstance(desc, str):
        # Not a description-bearing page (e.g. internal), skip
        print(f"  {path}: (no top-level description) skip")
        continue
    good = desc.rstrip().endswith(SUFFIX) and desc == desc.rstrip()
    if not good:
        ok = False
    print(f"  {path}: ends_exact={good} tail={desc[-14:]!r}")

print("ALL_OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
