#!/usr/bin/env python3
"""Seal the owner's approval of a Contract Proof (design-a-toy Stage 5, ADR 0096).

    uv run python .claude/skills/design-a-toy/scripts/seal_proof.py seal PROOF \\
        --contract CONTRACT.md --checklist CONCEPT-CHECKLIST.md --nozzle 0.4 \\
        --approved-by NAME [--date YYYY-MM-DD] [--cost UNITS] [--open-lines-approved]
    uv run python .claude/skills/design-a-toy/scripts/seal_proof.py verify PROOF [--contract CONTRACT.md]
    uv run python .claude/skills/design-a-toy/scripts/seal_proof.py inputs PROOF --contract CONTRACT.md

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

It also refuses what final verification would reject (the beaver pilot,
B2-B5): no passing `make_round --print-gates-only` summary of every
Component at the sealed nozzle, written by a make_round that checks each
Component's validity in its Display Pose and its print stance on the bed,
over the current sources; and no `*_spec.md` (exactly one, passing
`check_spec_format` and `check_spec_numbers`) or no `measure/check_fit.py`,
`measure/check_spec.py` and `measure/check_landmarks.py`.

ADR 0098: it refuses a Proof without every check input its contract needs
(`workshop.wish.seed.required_check_inputs`: `SEED-PRODUCT.json` and the
Stage 4 renders always, the motion manifest, presentation and the Proof
Critic's motion review for a moving toy, and the power, mount and Bought
Part placement inputs for a powered one), and it runs the seeded batch's
design plan on the Proof (`workshop.make.seeded_batch`) and refuses on any
failure. The approval records the inputs by sha256 and the passing batch
record. Schema 3 (ADR 0102's 2026-11-11 amendment) also renders the Approved
Proof's assembly, with the CAD skill's own `render_review`, at each assembly
Reference Camera of the contract into `PROOF/approved/assembly/` and records
each as `assembly_renders` (`{file, camera, sha256}`): what a seeded run's
assembly look compares with instead of a Reference Image. `verify` still
accepts a schema 2 seal. `inputs` lists what a Proof lacks and which design
step writes each: the re-seal path for a Proof sealed before ADR 0098,
which a new `workshop wish|fix --seed-source` refuses.

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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MAKE_SKILLS = ROOT / "src/workshop/make/skills"
MAKE_ROUND = MAKE_SKILLS / "make-round/scripts/make_round"
PRINT_DETAILS = MAKE_SKILLS / "print-details/scripts/print_details.py"
LOCK = MAKE_SKILLS / "LOCK.json"
SCHEMA_VERSION = 3
# Seals before ADR 0102's 2026-11-11 amendment carry no assembly renders;
# `verify` still checks them, and a run seeded from one keeps its reference look.
VERIFIED_SCHEMAS = (2, 3)
RENDER_TIMEOUT_SECONDS = 1800
APPROVAL = "APPROVAL.json"
APPROVED_DIR = "approved"
CHECKLIST = "CONCEPT-CHECKLIST.md"
CRITIC = "CRITIC.json"
FREEZE = Path("measure/shared-helpers-freeze.json")
PRINT_GATES = Path("measure/print-gates/summary.json")
# What a print-gate summary must have checked; kept in step with make_round's
# PRINT_GATES_ONLY_CHECKS.
REQUIRED_CHECKS = ("build", "thickness", "overhang", "mesh", "datum", "posed")
AUDITS = ("measure/check_fit.py", "measure/check_spec.py", "measure/check_landmarks.py")
CAD_SCRIPTS = MAKE_SKILLS / "cad/scripts"


class Refusal(Exception):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(proof: Path) -> dict[str, str]:
    """Relative path -> sha256 of every file of the seed tree: the host's own
    definition (`workshop.wish.seed.seed_manifest`), so design seals exactly
    the files `--seed-source` checks."""

    from workshop.errors import ContractError
    from workshop.wish.seed import seed_manifest

    try:
        return seed_manifest(proof)
    except ContractError as exc:
        raise Refusal(str(exc)) from exc


def manifest_sha256(files: dict[str, str]) -> str:
    from workshop.wish.seed import manifest_sha256 as digest

    return digest(files)


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


def geometry_sources(proof: Path) -> dict:
    """The Proof's Geometry Sources and their sha256, by the CAD skill's one
    definition (what make_round binds a print-gate summary to)."""

    import runpy

    tool = runpy.run_path(str(CAD_SCRIPTS / "geometry_sources.py"))
    return dict(sorted(tool["geometry_sources"](proof).items()))


def check_final_inputs(proof: Path, roles, nozzle: float) -> None:
    """What final verification rejects, checked before the owner's approval
    is sealed: the print gates with Display-Pose validity and the bed datum,
    and the spec and project audits the seeded run's verifier needs."""

    command = ("make_round %s --print-gates-only --nozzle %g --overhang-angle 45 --contract CONTRACT.md"
               % (proof, nozzle))
    try:
        summary = json.loads((proof / PRINT_GATES).read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            raise ValueError("not an object")
    except (OSError, ValueError) as exc:
        raise Refusal("no print-gate summary (%s): run %s" % (exc, command)) from exc
    missing = [check for check in REQUIRED_CHECKS if check not in (summary.get("checks") or ())]
    if missing:
        raise Refusal("the print-gate summary did not check %s; rerun %s" % (", ".join(missing), command))
    if sorted(summary.get("parts") or ()) != sorted(roles):
        raise Refusal("the print-gate summary covers %s, not every Component; rerun %s without --component"
                      % (", ".join(sorted(summary.get("parts") or ())) or "nothing", command))
    if summary.get("nozzle") != nozzle:
        raise Refusal("the print gates ran at nozzle %s, not %g; rerun %s" % (summary.get("nozzle"), nozzle, command))
    if summary.get("sources") != geometry_sources(proof):
        raise Refusal("a source changed since the print gates ran; rerun %s" % command)
    if summary.get("ok") is not True:
        failed = sorted(role for role, item in (summary.get("print") or {}).items()
                        if isinstance(item, dict) and item.get("verdict") != "PASS")
        failed += sorted(role for role, item in (summary.get("build") or {}).items()
                         if isinstance(item, dict) and item.get("verdict") != "PASS")
        raise Refusal("the print gates failed for %s (a self-intersection in the Display Pose and a part off "
                      "the bed are failures too); see %s" % (", ".join(sorted(set(failed))) or "a part",
                                                            PRINT_GATES.parent))
    specs = sorted(path.name for path in proof.glob("*_spec.md"))
    if len(specs) != 1:
        raise Refusal("final verification needs exactly one *_spec.md in the Proof; found %d" % len(specs))
    absent = [name for name in AUDITS if not (proof / name).is_file()]
    if absent:
        raise Refusal("final verification needs the project audits %s; write them as proof-prompt's "
                      "\"Final verification inputs\" says" % ", ".join(absent))
    for tool in ("check_spec_format", "check_spec_numbers"):
        code, output = run_spec_tool(proof, tool)
        if code != 0:
            raise Refusal("%s fails on %s: %s" % (tool, specs[0], output.strip()[-600:]))


def run_spec_tool(proof: Path, tool: str) -> tuple[int, str]:
    """Run one of the CAD skill's spec checks on the Proof."""

    done = subprocess.run([sys.executable, str(CAD_SCRIPTS / tool), str(proof)], capture_output=True,
                          text=True, cwd=ROOT)
    return done.returncode, done.stdout or done.stderr


def read_contract(contract: Path) -> dict:
    """The Design Contract as the host seals it (``to_dict``)."""

    from workshop.errors import ContractError
    from workshop.wish.design_contract import parse_design_contract

    try:
        return parse_design_contract(contract.read_text(encoding="utf-8")).to_dict()
    except (OSError, UnicodeError, ContractError) as exc:
        raise Refusal("the contract does not parse: %s" % exc) from exc


MOTION_REVIEW = "snap/MOTION-REVIEW.json"
MOTION_EVIDENCE = "snap/MOTION-EVIDENCE.json"
# make_round's carried assembly review names this reviewer; the carried
# motion review must name another (motion_presentation's carried rule).
CARRIED_SIGNATURE_REVIEWER = "the owner (Approved Proof)"


def check_carried_motion_review(proof: Path, product: dict) -> None:
    """Owner decision 1: the Proof Critic's motion review must pass the run's
    carried-review rule as sealed - its own reviewer, 1 to 4 rounds, the
    sealed concept's hash and the sealed motion evidence."""

    from workshop.make.seeded_batch import concept_sha256

    try:
        review = json.loads((proof / MOTION_REVIEW).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal("%s is not JSON: %s" % (MOTION_REVIEW, exc)) from exc
    if not isinstance(review, dict):
        raise Refusal("%s must be a JSON object" % MOTION_REVIEW)
    problems = []
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer == CARRIED_SIGNATURE_REVIEWER:
        problems.append("reviewer must name the Proof Critic, not %r" % (reviewer,))
    rounds = review.get("review_rounds")
    if type(rounds) is not int or rounds not in (1, 2, 3, 4):
        problems.append("review_rounds must be 1 to 4")
    if review.get("concept_sha256") != concept_sha256(product["concept"]):
        problems.append("concept_sha256 is not SEED-PRODUCT.json's concept hash")
    if review.get("evidence_sha256") != sha256(proof / MOTION_EVIDENCE):
        problems.append("evidence_sha256 is not %s's sha256" % MOTION_EVIDENCE)
    if review.get("motion_matches_wish") is not True or review.get("simulation_not_physical_test") is not True:
        problems.append("the review must affirm motion_matches_wish and simulation_not_physical_test")
    if problems:
        raise Refusal("%s cannot be carried into a seeded run: %s" % (MOTION_REVIEW, "; ".join(problems)))


def check_seed_inputs(proof: Path, design_contract: dict) -> dict:
    """ADR 0098 decision 1: every check input the contract needs, present
    and well formed; returns path -> sha256."""

    from workshop.errors import ContractError
    from workshop.wish.seed import (SEED_PRODUCT, check_seed_product, describe_check_inputs,
                                    missing_check_inputs, required_check_inputs)

    missing = missing_check_inputs(proof, design_contract)
    if missing:
        raise Refusal("the Proof lacks check inputs a seeded run needs: %s; run seal_proof.py inputs %s "
                      "--contract CONTRACT.md for the list" % (describe_check_inputs(missing), proof))
    try:
        product = check_seed_product((proof / SEED_PRODUCT).read_bytes())
    except ContractError as exc:
        raise Refusal(str(exc)) from exc
    if any(item.path == MOTION_REVIEW for item in required_check_inputs(design_contract)):
        check_carried_motion_review(proof, product)
    return {item.path: sha256(proof / item.path) for item in required_check_inputs(design_contract)}


def dry_run_batch(proof: Path, contract: Path, design_contract: dict, nozzle: float) -> dict:
    """Owner decision 5: the seeded batch's design plan on the Proof. Refuses
    on any failing step, quoting each in its own words."""

    from workshop.make import seeded_batch
    from workshop.wish.seed import contract_geometry_ids, contract_is_moving, contract_is_powered

    inputs = seeded_batch.PlanInputs(
        project=proof, python=sys.executable, skills_root=MAKE_SKILLS, contract_path=contract,
        roles=contract_geometry_ids(design_contract), nozzle=nozzle,
        coupled_interfaces=seeded_batch.coupled_interface_ids(design_contract),
        powered=contract_is_powered(design_contract), moving=contract_is_moving(design_contract),
        image_derived=bool(design_contract.get("references")))
    path = proof / seeded_batch.RECORD
    record = seeded_batch.run_batch(seeded_batch.design_plan(inputs), proof, runner=batch_runner(),
                                    record_path=path, plan_name="design")
    if record["status"] != seeded_batch.PASS:
        failing = ["%s (%s): %s" % (item["id"], item.get("reason") or "exit %s" % item.get("exit_code"),
                                    (item.get("excerpt") or "").strip()[-400:])
                   for item in record["steps"]
                   if item["status"] in (seeded_batch.CHECK_FAILURE, seeded_batch.HARNESS_FAILURE)]
        raise Refusal("the seeded batch fails on the Proof (%s); see %s:\n%s"
                      % (record["status"], seeded_batch.RECORD, "\n".join(failing)))
    return {"ok": True, "plan": "design", "record_sha256": sha256(path),
            "tool_sha256": seeded_batch.module_sha256()}


def batch_runner():
    """How the batch runs its steps: real processes (a test passes a fake)."""

    from workshop.make import seeded_batch

    return seeded_batch.subprocess_runner


def render_runner():
    """How the seal renders the Approved Proof's assembly: a real
    ``render_review`` process (a test passes a fake). It takes
    ``(argv, cwd)`` and returns ``(exit code, output)``."""

    def run(argv, cwd):
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=RENDER_TIMEOUT_SECONDS)
        return done.returncode, (done.stdout or "") + (done.stderr or "")

    return run


def render_assembly(proof: Path, design_contract: dict) -> list[dict]:
    """ADR 0102's 2026-11-11 amendment: the Approved Proof's assembly,
    rendered by ``render_review`` from the Proof's one assembly entry at each
    assembly Reference Camera of the contract (the view an assembly round
    renders the model at), sealed under ``approved/assembly/``. A seeded
    run's assembly look compares its model beside these, never a Reference
    Image. Empty when the contract has no assembly reference camera."""

    from workshop.wish.seed import APPROVED_ASSEMBLY_DIR, assembly_cameras, assembly_render_name

    cameras = assembly_cameras(design_contract)
    if not cameras:
        return []
    entries = sorted(path.name for path in proof.glob("*.step.py") if not path.name.startswith("part_"))
    if len(entries) != 1:
        raise Refusal("the Proof needs exactly one assembly entry *.step.py to render the approved assembly "
                      "at its Reference Cameras (found %d)" % len(entries))
    holder = Path(tempfile.mkdtemp(prefix=".seal-proof-renders-", dir=proof.parent))
    try:
        argv = [sys.executable, str(CAD_SCRIPTS / "render_review"), entries[0],
                *("--view=%g,%g" % (az, el) for az, el in cameras), "-o", str(holder)]
        code, output = render_runner()(argv, proof)
        if code != 0:
            raise Refusal("render_review could not render the approved assembly (exit %s): %s"
                          % (code, " ".join(str(output).split())[-400:]))
        target = proof / APPROVED_ASSEMBLY_DIR
        target.mkdir(parents=True, exist_ok=True)
        renders = []
        for camera in cameras:
            name = assembly_render_name(camera)
            made = holder / Path(name).name
            if not made.is_file():
                raise Refusal("render_review wrote no %s for the approved assembly" % made.name)
            shutil.copyfile(made, proof / name)
            renders.append({"file": name, "camera": camera, "sha256": sha256(proof / name)})
        return renders
    finally:
        shutil.rmtree(holder, ignore_errors=True)


def inputs_report(args) -> list[str]:
    """The re-seal path: each check input the contract needs, present or not,
    and which design step writes it."""

    from workshop.wish.seed import required_check_inputs

    proof = Path(args.proof).resolve()
    design_contract = read_contract(Path(args.contract).resolve())
    lines = []
    for item in required_check_inputs(design_contract):
        present = (proof / item.path).is_file()
        lines.append("%s %s  (%s; written by %s)" % ("ok     " if present else "MISSING", item.path, item.when,
                                                    item.written_by))
    return lines


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
    design_contract = read_contract(contract)
    check_inputs = check_seed_inputs(proof, design_contract)
    record = identities(proof, contract)
    if record.get("contract_sha256") != sha256(contract):
        raise Refusal("make_round read another contract than %s" % contract)
    check_rules(proof, record)
    check_final_inputs(proof, record["components"], args.nozzle)
    # Issue #241: a re-seal's old approved/ copies are STEP files no
    # Component builds, which the batch's project check refuses as strays.
    # They wait outside the Proof and come back if this seal refuses, so a
    # failed re-seal leaves the previous seal whole.
    held = set_aside(proof / APPROVED_DIR)
    try:
        document = _seal_after_set_aside(args, proof, contract, checklist, verdict, design_contract,
                                         check_inputs, record)
    except BaseException:
        restore(held, proof / APPROVED_DIR)
        raise
    if held is not None:
        shutil.rmtree(held.parent)
    return document


def set_aside(directory: Path):
    """Move ``directory`` into a fresh hidden directory beside the Proof,
    outside it but on its filesystem, so the move is a rename and a seal
    killed midway leaves the copies where the owner can find them; return
    its new path, or None when it does not exist."""

    if not directory.exists():
        return None
    holder = Path(tempfile.mkdtemp(prefix=".seal-proof-approved-", dir=directory.parent.parent))
    return Path(shutil.move(str(directory), str(holder / directory.name)))


def restore(held, directory: Path) -> None:
    """Put a set-aside directory back, replacing whatever the failed seal
    left in its place."""

    if held is None:
        return
    if directory.exists():
        shutil.rmtree(directory)
    shutil.move(str(held), str(directory))
    shutil.rmtree(held.parent, ignore_errors=True)


def _seal_after_set_aside(args, proof, contract, checklist, verdict, design_contract, check_inputs,
                          record) -> dict:
    batch = dry_run_batch(proof, contract, design_contract, args.nozzle)

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
    assembly_renders = render_assembly(proof, design_contract)
    from workshop.wish.seed import seed_contract_sha256

    files = manifest(proof)
    document = {
        "schema_version": SCHEMA_VERSION,
        "tool": "design-a-toy seal_proof",
        # The hash a seeded run binds: without a Bought Parts block, which
        # prices the design and shapes nothing (ADR 0095, 2026-11-07).
        "contract_sha256": seed_contract_sha256(contract.read_text(encoding="utf-8")),
        "components": components,
        "assembly_identity": record["assembly_identity"],
        "assembly_renders": assembly_renders,
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
        "check_inputs": check_inputs,
        "batch": batch,
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
    if document.get("schema_version") not in VERIFIED_SCHEMAS:
        raise Refusal("%s schema_version %r is not %d; a Proof sealed before ADR 0098 is re-sealed: run "
                      "seal_proof.py inputs %s --contract CONTRACT.md, then seal again"
                      % (APPROVAL, document.get("schema_version"), SCHEMA_VERSION, proof))
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
    p = sub.add_parser("inputs")
    p.add_argument("proof")
    p.add_argument("--contract", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inputs":
            lines = inputs_report(args)
            for line in lines:
                print("seal_proof: %s" % line)
            return 1 if any(line.startswith("MISSING") for line in lines) else 0
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
