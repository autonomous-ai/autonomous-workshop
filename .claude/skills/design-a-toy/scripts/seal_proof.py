#!/usr/bin/env python3
"""Seal the owner's approval of a Contract Proof (design-a-toy Stage 5, ADR 0096).

    uv run python .claude/skills/design-a-toy/scripts/seal_proof.py seal PROOF \\
        --contract CONTRACT.md --checklist CONCEPT-CHECKLIST.md --nozzle 0.4 \\
        --approved-by NAME [--date YYYY-MM-DD] [--cost UNITS] [--open-lines-approved]
    uv run python .claude/skills/design-a-toy/scripts/seal_proof.py verify PROOF [--contract CONTRACT.md]

`seal` records what the owner approved in `PROOF/APPROVAL.json`, the input
`workshop wish|fix --seed-source PROOF` will check:

- each Component's B-rep identity, STEP sha256, contract rows hash and carry
  key, and the assembly identity, computed by `make_round --identities-only`:
  the code a component round runs, never a copy of it;
- each Component's approved STEP, copied into `PROOF/approved/`, with every
  Part's volume and bounding box read by `workshop.make.proof_diff`;
- the hashes of the contract, `CRITIC.json`, `CONCEPT-CHECKLIST.md` (copied
  into PROOF), the make_round tool, the skills' `LOCK.json` and the installed
  `features/print_details.py`;
- the nozzle, who approved it and when, the design's cost, and a manifest of
  every file of the seed tree.

It refuses a Proof that breaks ADR 0096 decision 1b: no installed
`features/print_details.py` with the library's bytes, no passing Shared Helper
freeze, or a helper changed since it froze (so every joint value still carries
its `# wiki:` citation and `assert`). It refuses a Proof Critic that did not
agree unless the owner approved its open lines at Stage 4
(`--open-lines-approved`).

`verify` recomputes the manifest and exits 1 on a missing, extra or changed
file, or a contract whose sha256 is not the sealed one.

Exit 0 on success, 1 on a refusal, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MAKE_SKILLS = ROOT / "src/workshop/make/skills"
MAKE_ROUND = MAKE_SKILLS / "make-round/scripts/make_round"
PRINT_DETAILS = MAKE_SKILLS / "print-details/scripts/print_details.py"
LOCK = MAKE_SKILLS / "LOCK.json"
SCHEMA_VERSION = 1
APPROVAL = "APPROVAL.json"
APPROVED_DIR = "approved"
CHECKLIST = "CONCEPT-CHECKLIST.md"
CRITIC = "CRITIC.json"
FREEZE = Path("measure/shared-helpers-freeze.json")
# Never part of the seed tree: evidence, caches and the built STEP beside each
# source (its approved copy is under approved/).
EXCLUDED_DIRS = {"measure", "__cadgen__", "__pycache__", "compare", ".cache"}


class Refusal(Exception):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(proof: Path) -> dict[str, str]:
    """Project-relative path -> sha256 of every file of the seed tree."""

    files = {}
    for path in sorted(proof.rglob("*")):
        relative = path.relative_to(proof)
        if path.is_symlink():
            raise Refusal("%s is a symlink; the seed tree holds only plain files" % relative.as_posix())
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in relative.parts[:-1]):
            continue
        if relative.as_posix() == APPROVAL or (len(relative.parts) == 1 and path.suffix in (".step", ".log")):
            continue
        files[relative.as_posix()] = sha256(path)
    return files


def manifest_sha256(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def identities(proof: Path, contract: Path) -> dict:
    """make_round --identities-only's record of the Proof."""

    done = subprocess.run([sys.executable, str(MAKE_ROUND), str(proof), "--identities-only",
                           "--contract", str(contract)], capture_output=True, text=True, cwd=ROOT)
    if done.returncode != 0:
        raise Refusal("make_round --identities-only failed: %s" % (done.stderr.strip() or done.stdout.strip()))
    return json.loads(done.stdout)


def part_measures(step: Path) -> dict:
    """Every Part's volume (mm^3) and bounding box (mm) in one STEP."""

    from workshop.make import proof_diff

    measured = {}
    for name, shape in proof_diff.read_parts(step).items():
        box = shape.bounding_box()
        measured[name] = {"volume_mm3": round(shape.volume, 3),
                          "bbox_mm": [round(v, 3) for v in (box.min.X, box.min.Y, box.min.Z,
                                                             box.max.X, box.max.Y, box.max.Z)]}
    return measured


def check_rules(proof: Path, record: dict) -> None:
    """ADR 0096 decision 1b: the Proof was written as Make writes."""

    installed = proof / "features/print_details.py"
    if not installed.is_file():
        raise Refusal("features/print_details.py is not installed; run print_details.py --install %s" % proof)
    if installed.read_bytes() != PRINT_DETAILS.read_bytes():
        raise Refusal("features/print_details.py differs from the library; it is installed, never edited")
    try:
        freeze = json.loads((proof / FREEZE).read_text(encoding="utf-8"))
        helpers = freeze["helpers"]
        if not isinstance(helpers, dict):
            raise ValueError("helpers is not an object")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Refusal("no passing Shared Helper freeze (%s): run make_round %s --shared-helpers --contract "
                      "CONTRACT.md" % (exc, proof)) from exc
    for path, digest in sorted(helpers.items()):
        target = proof / path
        if not target.is_file() or sha256(target) != digest:
            raise Refusal("Shared Helper %s changed since it froze; rerun make_round --shared-helpers" % path)
    for role, component in sorted(record["components"].items()):
        for path, digest in sorted((component.get("imported_helpers") or {}).items()):
            if helpers.get(path) != digest:
                raise Refusal("part_%s.step.py imports %s, which no passing Shared Helper freeze covers"
                              % (role, path))


def seal(args) -> dict:
    proof = Path(args.proof).resolve()
    contract = Path(args.contract).resolve()
    checklist = Path(args.checklist).resolve()
    for path, what in ((proof, "Proof directory"), (contract, "contract"), (checklist, "Concept Checklist")):
        if not path.exists():
            raise Refusal("no %s at %s" % (what, path))
    try:
        critic = json.loads((proof / CRITIC).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal("no readable %s in the Proof: %s" % (CRITIC, exc)) from exc
    verdict = critic.get("verdict") if isinstance(critic, dict) else None
    if verdict != "agree" and not args.open_lines_approved:
        raise Refusal("the Proof Critic's verdict is %r; seal only after it agrees, or pass "
                      "--open-lines-approved when the owner approved its open lines at Stage 4" % verdict)
    record = identities(proof, contract)
    if record.get("contract_sha256") != sha256(contract):
        raise Refusal("make_round read another contract than %s" % contract)
    check_rules(proof, record)

    copied = proof / CHECKLIST
    if checklist != copied:
        if copied.exists() and copied.read_bytes() != checklist.read_bytes():
            raise Refusal("%s already holds another checklist" % copied)
        shutil.copyfile(checklist, copied)
    approved = proof / APPROVED_DIR
    if approved.exists():
        shutil.rmtree(approved)
    approved.mkdir()
    components = {}
    for role, component in sorted(record["components"].items()):
        built = proof / ("part_%s.step" % role)
        if not built.is_file() or sha256(built) != component["step_sha256"]:
            raise Refusal("part_%s.step is not the STEP make_round built" % role)
        target = approved / built.name
        shutil.copyfile(built, target)
        components[role] = {**component, "approved_step": "%s/%s" % (APPROVED_DIR, built.name),
                            "parts": part_measures(target)}
    files = manifest(proof)
    document = {
        "schema_version": SCHEMA_VERSION,
        "tool": "design-a-toy seal_proof",
        "contract_sha256": record["contract_sha256"],
        "components": components,
        "assembly_identity": record["assembly_identity"],
        "critic": {"sha256": sha256(proof / CRITIC), "verdict": verdict,
                   "open_lines_approved": bool(args.open_lines_approved and verdict != "agree")},
        "checklist_sha256": sha256(copied),
        "make_round_sha256": sha256(MAKE_ROUND),
        "skills_lock_sha256": sha256(LOCK),
        "print_details_sha256": sha256(proof / "features/print_details.py"),
        "nozzle_mm": args.nozzle,
        "approved_by": args.approved_by,
        "date": args.date or datetime.date.today().isoformat(),
        "design_cost_units": args.cost,
        "manifest": files,
        "manifest_sha256": manifest_sha256(files),
    }
    (proof / APPROVAL).write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def verify(args) -> list[str]:
    """Every way the Proof no longer matches its APPROVAL.json."""

    proof = Path(args.proof).resolve()
    try:
        document = json.loads((proof / APPROVAL).read_text(encoding="utf-8"))
        sealed = document["manifest"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Refusal("no readable %s: %s" % (APPROVAL, exc)) from exc
    if document.get("schema_version") != SCHEMA_VERSION:
        raise Refusal("%s schema_version %r is not %d" % (APPROVAL, document.get("schema_version"), SCHEMA_VERSION))
    problems = []
    if manifest_sha256(sealed) != document.get("manifest_sha256"):
        problems.append("the manifest does not hash to manifest_sha256")
    current = manifest(proof)
    problems += ["missing: %s" % path for path in sorted(set(sealed) - set(current))]
    problems += ["extra: %s" % path for path in sorted(set(current) - set(sealed))]
    problems += ["changed: %s" % path for path in sorted(set(sealed) & set(current)) if sealed[path] != current[path]]
    if args.contract and sha256(Path(args.contract)) != document.get("contract_sha256"):
        problems.append("the contract's sha256 is not the sealed contract_sha256")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("seal")
    p.add_argument("proof")
    p.add_argument("--contract", required=True)
    p.add_argument("--checklist", required=True)
    p.add_argument("--nozzle", type=float, required=True)
    p.add_argument("--approved-by", required=True)
    p.add_argument("--date")
    p.add_argument("--cost", type=float, help="the design's cost in units, from build-a-toy's tokens.py")
    p.add_argument("--open-lines-approved", action="store_true")
    p = sub.add_parser("verify")
    p.add_argument("proof")
    p.add_argument("--contract")
    args = parser.parse_args(argv)
    try:
        if args.command == "seal":
            document = seal(args)
            print("seal_proof: sealed %d Component(s), manifest %s" % (len(document["components"]),
                                                                       document["manifest_sha256"][:12]))
            return 0
        problems = verify(args)
    except Refusal as exc:
        print("seal_proof: %s" % exc, file=sys.stderr)
        return 1
    for line in problems:
        print("seal_proof: %s" % line, file=sys.stderr)
    if not problems:
        print("seal_proof: the Proof matches its approval")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
