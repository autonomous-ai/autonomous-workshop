#!/usr/bin/env python3
"""Exercise installed all-five orchestration with deterministic external boundaries.

This proves packaging, Taste-based routing, Manager-owned shared execution,
Workshop-owned stage composition, the installed Manager service registry,
release contracts, exact Deliver evidence, resumable Instructions, and
synthetic Factory request/readback state. It does not call a live routing
model, real CAD kernel/slicer, live Factory, or actual physical production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


CASES = {
    "alice": "A personal set that keeps every rule of checkers unchanged, with midnight-blue studio pieces.",
    "bob": "A pocket-size wind-up walking mechanism with one proud, rhythmic step.",
    "eve": "A miniature night market world centered on my fictional violet lantern arch.",
    "ivy": "A hand-held toy that shows coupled periodic motion when I turn one handle.",
    "leo": "A brand-new seven-token strategy game with a complete finite ending.",
}
LANES = {
    "alice": "classics-made-yours",
    "bob": "moving-machines",
    "eve": "little-worlds",
    "ivy": "holdable-science",
    "leo": "invented-games",
}
PROOF_CLASSES = {
    "alice": "classic-rule-conformance-proof",
    "bob": "kinematic-motion-proof",
    "eve": "reference-bound-world-proof",
    "ivy": "source-bound-science-proof",
    "leo": "seeded-game-analysis-proof",
}
EXPECTED_OCCURRENCES = {
    "alice": 3,
    "bob": 3,
    "eve": 3,
    "ivy": 3,
    "leo": 7,
}
ACCEPTANCE_FACTORY_PASSWORD = "installed-acceptance-credential"


def _run(command, *, cwd, environment=None, timeout=300):
    completed = subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "command failed (%d): %s\nstdout:\n%s\nstderr:\n%s"
            % (
                completed.returncode,
                " ".join(str(item) for item in command),
                completed.stdout,
                completed.stderr,
            )
        )
    return completed


def _python(venv):
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _workshop(venv):
    return venv / ("Scripts/workshop.exe" if os.name == "nt" else "bin/workshop")


def _build_wheel(repository, root):
    wheelhouse = root / "wheelhouse"
    wheelhouse.mkdir()
    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            wheelhouse,
            repository,
        ),
        cwd=repository,
    )
    wheels = tuple(wheelhouse.glob("inventor_workshop-*.whl"))
    if len(wheels) != 1:
        raise AssertionError("expected exactly one Workshop wheel")
    return wheels[0]


def _install(wheel, root):
    venv = root / "venv"
    _run((sys.executable, "-m", "venv", venv), cwd=root)
    python = _python(venv)
    _run((python, "-m", "pip", "install", "--no-deps", wheel), cwd=root)
    return python, _workshop(venv)


def _purelib(python, root):
    return Path(
        _run(
            (python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"),
            cwd=root,
        ).stdout.strip()
    )


def _install_boundaries(repository, python, root, log_path):
    purelib = _purelib(python, root)
    support = repository / "tests" / "all_five_cli_acceptance_support.py"
    (purelib / "workshop_all_five_acceptance_support.py").write_bytes(
        support.read_bytes()
    )
    (purelib / "workshop_all_five_acceptance_config.py").write_text(
        "from pathlib import Path\nLOG_PATH = Path(%r)\n" % str(log_path),
        encoding="utf-8",
    )
    (purelib / "workshop_all_five_acceptance.pth").write_text(
        "import workshop_all_five_acceptance_support\n", encoding="utf-8"
    )
    dist_info = (
        purelib / "workshop_all_five_acceptance_provider-1.0.0.dist-info"
    )
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: workshop-all-five-acceptance-provider\n"
        "Version: 1.0.0\n",
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        "[autonomous_workshop.manager_services]\n"
        "installed-acceptance = "
        "workshop_all_five_acceptance_support:manager_services\n",
        encoding="utf-8",
    )


def _fake_codex(path):
    if os.name == "nt":
        path.write_text(
            '@echo off\r\nif "%1"=="--version" (echo codex 1.0.0 & exit /b 0)\r\nexit /b 97\r\n',
            encoding="utf-8",
        )
    else:
        path.write_text(
            "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'codex 1.0.0'; exit 0; fi\nexit 97\n",
            encoding="utf-8",
        )
        path.chmod(0o700)


def _rows(database):
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        events = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM events ORDER BY sequence"
            )
        ]
        product = dict(
            connection.execute("SELECT * FROM products").fetchone()
        )
        intent = dict(
            connection.execute(
                "SELECT * FROM publish_intents ORDER BY created_at DESC, id DESC LIMIT 1"
            ).fetchone()
        )
    finally:
        connection.close()
    return product, events, intent


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _find_evidence(runtime, capability):
    matches = []
    for path in runtime.rglob("results/%s.json" % capability):
        if "/attempts/" in path.as_posix() and path.is_file():
            matches.append(path)
    if not matches:
        raise AssertionError("missing %s evidence" % capability)
    return json.loads(sorted(matches)[-1].read_text(encoding="utf-8"))


def acceptance(repository, wheel):
    with tempfile.TemporaryDirectory(prefix="workshop-all-five-installed-") as temporary:
        root = Path(temporary)
        away = root / "unrelated-cwd"
        away.mkdir()
        home = root / "workshop-home"
        log_path = root / "boundary.jsonl"
        python, workshop = _install(wheel, root)
        _install_boundaries(repository, python, root, log_path)
        codex = root / ("codex.cmd" if os.name == "nt" else "codex")
        _fake_codex(codex)
        environment = {
            name: os.environ[name]
            for name in (
                "HOME",
                "LANG",
                "LC_ALL",
                "LC_CTYPE",
                "PATH",
                "SYSTEMROOT",
                "TMPDIR",
            )
            if os.environ.get(name)
        }
        environment.update(
            {
                "WORKSHOP_CODEX_BIN": str(codex),
                "WORKSHOP_HOME": str(home),
                "WORKSHOP_MANAGER_SERVICES": "installed-acceptance",
            }
        )

        receipts = {}
        for inventor_id, objective in CASES.items():
            try:
                completed = _run(
                    (workshop, "wish", objective, "--json"),
                    cwd=away,
                    environment=environment,
                    timeout=600,
                )
            except AssertionError as exc:
                boundary = (
                    log_path.read_text(encoding="utf-8")
                    if log_path.is_file()
                    else "<no boundary log>"
                )
                raise AssertionError("%s\nboundary log:\n%s" % (exc, boundary)) from exc
            receipt = json.loads(completed.stdout)
            receipts[inventor_id] = receipt
            if receipt["match"]["inventor_id"] != inventor_id:
                raise AssertionError("Wish routed to the wrong Inventor")
            result = receipt["result"]
            if (result["status"], result["job"]) != ("delivered", "deliver"):
                raise AssertionError(
                    "%s did not complete through the registered Deliver service: %s"
                    % (inventor_id, json.dumps(result, sort_keys=True))
                )
            if result["needs"]:
                raise AssertionError("completed registered Deliver retained a Need")
            delivery = result.get("delivery")
            if (
                not isinstance(delivery, dict)
                or delivery.get("status") != "handed-off"
                or delivery.get("product_artifact_sha256")
                != result.get("artifact_sha256")
                or delivery.get("instructions_sha256")
                != result.get("instructions_sha256")
                or set(delivery.get("evidence", {}))
                != {
                    "print_receipt",
                    "qa_receipt",
                    "packing_receipt",
                    "carrier_receipt",
                }
            ):
                raise AssertionError("registered Deliver returned inexact evidence")
            publication = result.get("publication")
            if not isinstance(publication, dict) or publication.get("status") != "public":
                raise AssertionError("synthetic Factory publication was not verified public")
            if publication.get("verified") is not True:
                raise AssertionError("synthetic Factory public readback was not verified")
            product_id = receipt["wish"]["product_id"]
            expected_url = "https://www.autonomous.ai/factory/product/%s" % product_id
            if result.get("page_url") != expected_url or publication.get("page_url") != expected_url:
                raise AssertionError("Factory page URL is not exact")
            binding = result["manager_assignment"]
            if binding.get("schema_version") != 4:
                raise AssertionError("Manager child result used the wrong exact Handoff")
            for name in (
                "handoff_sha256",
                "manifest_sha256",
                "taste_sha256",
                "implementation_sha256",
                "publication_policy_sha256",
            ):
                if not isinstance(binding.get(name), str) or len(binding[name]) != 64:
                    raise AssertionError("exact Handoff lacks %s" % name)
            if inventor_id == "eve":
                for name in ("world_inputs_sha256", "world_evidence_sha256"):
                    if not isinstance(binding.get(name), str) or len(binding[name]) != 64:
                        raise AssertionError("world Handoff lacks %s" % name)

            catalogs = tuple(
                home.glob("bundled-catalogs/*/inventors/%s" % inventor_id)
            )
            if len(catalogs) != 1:
                raise AssertionError(
                    "expected one retained bundled catalog for %s, found %d"
                    % (inventor_id, len(catalogs))
                )
            runtime = catalogs[0] / ".workshop"
            handoffs = tuple((runtime / "manager-assignments").glob("*.json"))
            if len(handoffs) != 1:
                raise AssertionError("expected one saved exact Manager handoff")
            handoff = json.loads(handoffs[0].read_text(encoding="utf-8"))
            if handoff["schema_version"] != 4:
                raise AssertionError(
                    "saved assignment is not publication-bound Handoff v4"
                )
            if (
                handoff.get("world_inputs") is not None
                or handoff.get("world_evidence") is not None
            ):
                raise AssertionError("saved assignment unexpectedly contains service data")
            for name in (
                "inventor_id",
                "wish_sha256",
                "decision_sha256",
                "assignment_sha256",
                "manifest_sha256",
                "taste_sha256",
                "implementation_sha256",
            ):
                if handoff.get(name) != binding.get(name):
                    raise AssertionError("saved assignment identity differs at %s" % name)
            if not isinstance(handoff.get("publication_policy"), dict):
                raise AssertionError("saved Handoff v4 lacks publication policy")
            if (
                inventor_id != "eve"
                and handoff["handoff_sha256"] != binding["handoff_sha256"]
            ):
                raise AssertionError("saved Handoff v4 differs from final binding")

            database = runtime / "workshop.sqlite3"
            product, events, intent = _rows(database)
            metadata = _json(product["metadata_json"])
            if metadata["inventor_id"] != inventor_id or metadata["lane"] != LANES[inventor_id]:
                raise AssertionError("durable run lost selected identity")
            status_receipt = json.loads(
                _run(
                    (workshop, "status", product_id, "--json"),
                    cwd=away,
                    environment=environment,
                ).stdout
            )
            provenance = status_receipt.get("engine_provenance")
            if (
                not isinstance(provenance, dict)
                or provenance != metadata.get("engine_provenance")
                or [item.get("stage") for item in provenance.get("components", [])]
                != ["invent", "make", "playtest", "instructions", "deliver"]
                or not isinstance(
                    provenance.get("informational_engine_sha256"), str
                )
                or len(provenance["informational_engine_sha256"]) != 64
            ):
                raise AssertionError(
                    "installed status lost exact five-stage engine provenance"
                )
            transitions = [event["to_stage"] for event in events]
            for stage in ("wish", "invent", "make", "playtest", "instructions", "deliver"):
                if stage not in transitions:
                    raise AssertionError("durable event chain missed %s" % stage)
            final_event = _json(events[-1]["payload_json"])
            if (
                product.get("stage") != "deliver"
                or final_event.get("status") != "delivered"
                or final_event.get("delivery") != delivery
            ):
                raise AssertionError("durable Deliver evidence differs from the CLI receipt")
            if intent["state"] != "live":
                raise AssertionError("Factory outbox did not record verified public state")
            persisted_receipt = _json(intent["receipt_json"])
            if persisted_receipt["status"] != "public":
                raise AssertionError("Factory durable receipt is not public")
            if persisted_receipt["details"]["page_url"] != expected_url:
                raise AssertionError("Factory durable receipt has a different page URL")

            lane_capability = {
                "alice": "classic-rules-test",
                "bob": "motion-test",
                "eve": "world-test",
                "ivy": "science-test",
                "leo": "game-simulation",
            }[inventor_id]
            evidence = _find_evidence(runtime, lane_capability)
            proof = evidence.get("release_proof")
            if not isinstance(proof, dict) or proof.get("proof_class") != PROOF_CLASSES[inventor_id]:
                raise AssertionError("lane release did not use the typed production proof")
            if inventor_id == "leo":
                if evidence.get("requested_games") != 1_000 or evidence.get("completed_games") != 1_000:
                    raise AssertionError("Leo did not complete 1,000 seeded games")
                traces = runtime / next(
                    path.relative_to(runtime)
                    for path in runtime.rglob("traces/game-simulation.json")
                    if path.is_file()
                )
                games = json.loads(traces.read_text(encoding="utf-8"))["games"]
                if len(games) != 1_000 or len({item["seed"] for item in games}) != 1_000:
                    raise AssertionError("Leo's seeded trace set is incomplete")

        records = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        registry_records = [
            item for item in records if item["event"] == "manager-services-loaded"
        ]
        expected_capabilities = {
            "research",
            "classic_rules",
            "world_reference",
            "world_playtest",
            "factory_credentials",
            "deliver",
        }
        if (
            len(registry_records) != len(CASES)
            or any(
                item.get("configuration_id") != "installed-acceptance"
                or set(item.get("capabilities", ())) != expected_capabilities
                for item in registry_records
            )
        ):
            raise AssertionError("installed Manager service entry point was not exact")
        models = {item["model"] for item in records if item["event"] == "structured-model"}
        if models != {"gpt-5.6-terra", "gpt-5.6-luna"}:
            raise AssertionError("acceptance did not stay on Terra/Luna")
        semantic_records = [
            item for item in records if item["event"] == "semantic-model"
        ]
        manager_pids = {
            item["selected_inventor_id"]: item["pid"]
            for item in records
            if item["event"] == "semantic-model"
            and item["capability"] == "semantic-inventor-retriever"
        }
        if set(manager_pids) != set(CASES):
            raise AssertionError("semantic Manager process identity is incomplete")
        if {item["pid"] for item in registry_records} != set(manager_pids.values()):
            raise AssertionError("Manager services loaded outside the Wish Manager processes")
        for item in registry_records:
            argv = item["argv"]
            if "wish" not in argv or "--assignment-stdin" in argv:
                raise AssertionError(
                    "shared services escaped the authoritative Manager-owned wish path"
                )
        for inventor_id, engine_pid in manager_pids.items():
            cad_commands = {
                record.get("command_id")
                for record in records
                if record["event"] == "cad-command"
                and record["pid"] == engine_pid
            }
            if not {
                "runtime-probe",
                "check_layout",
                "gen",
                "export",
                "inspect",
                "check_fit",
                "check_mesh",
                "check_thickness",
            } <= cad_commands:
                raise AssertionError(
                    "%s did not reach every shared CAD process seam" % inventor_id
                )
            slicers = [
                record
                for record in records
                if record["event"] == "slicer-boundary"
                and record["pid"] == engine_pid
            ]
            if not slicers or any(
                record.get("checker") != "PrusaSlicerPrintCheck"
                or record.get("command_runner") != "_slicer_command_runner"
                for record in slicers
            ):
                raise AssertionError(
                    "%s replaced the shared slicer adapter instead of its process"
                    % inventor_id
                )
        for inventor_id in CASES:
            routed = [
                item
                for item in semantic_records
                if item["selected_inventor_id"] == inventor_id
            ]
            if {item.get("source_kind") for item in routed} != {"description", "taste"}:
                raise AssertionError("routing did not read both actual description and full Taste")
            for item in routed:
                fits = item.get("candidate_fits")
                if (
                    not isinstance(fits, list)
                    or not fits
                    or fits[0].get("inventor_id") != inventor_id
                    or fits[0].get("score", 0) <= 0
                    or (
                        len(fits) > 1
                        and fits[0].get("score") == fits[1].get("score")
                    )
                    or any(
                        not isinstance(candidate.get("content_sha256"), str)
                        or len(candidate["content_sha256"]) != 64
                        for candidate in fits
                    )
                ):
                    raise AssertionError("actual Taste content did not uniquely select the route")
        eve_pid = manager_pids["eve"]
        service_records = [
            item for item in records if item["event"] == "manager-service"
        ]
        research_records = [
            item for item in service_records if item.get("capability") == "research"
        ]
        if (
            len(research_records) != len(CASES)
            or {item["pid"] for item in research_records}
            != set(manager_pids.values())
        ):
            raise AssertionError("Wish-aware research did not use the installed registry")
        classic_records = [
            item for item in service_records if item.get("capability") == "classic_rules"
        ]
        if len(classic_records) != 1 or classic_records[0]["pid"] != manager_pids["alice"]:
            raise AssertionError("classic rules did not use the installed registry")
        deliver_records = [
            item for item in service_records if item.get("capability") == "deliver"
        ]
        if (
            len(deliver_records) != len(CASES)
            or {item["pid"] for item in deliver_records}
            != set(manager_pids.values())
        ):
            raise AssertionError("not every Wish completed registered Deliver")
        credential_records = [
            item
            for item in service_records
            if item.get("capability") == "factory_credentials"
        ]
        if (
            {item.get("inventor_id") for item in credential_records} != set(CASES)
            or any(
                item["pid"] != manager_pids[item["inventor_id"]]
                for item in credential_records
            )
        ):
            raise AssertionError("Factory credentials bypassed the installed broker")
        world_reference_records = [
            item for item in records if item["event"] == "world-reference-service"
        ]
        if (
            {item.get("operation") for item in world_reference_records}
            != {
                "descriptors",
                "verify-admission",
                "authorize-provider-inputs",
                "verify-authorization",
            }
            or any(item["pid"] != eve_pid for item in world_reference_records)
            or any(item.get("reference_id") != "customer-market" for item in world_reference_records)
        ):
            raise AssertionError("world descriptors did not stay in the Eve Manager process")
        world_playtest_records = [
            item for item in records if item["event"] == "world-playtest-service"
        ]
        eve_binding = receipts["eve"]["result"]["manager_assignment"]
        if (
            {item.get("operation") for item in world_playtest_records}
            != {"evaluate", "verify"}
            or any(item["pid"] != eve_pid for item in world_playtest_records)
            or any(
                item.get("evidence_sha256")
                != eve_binding["world_evidence_sha256"]
                for item in world_playtest_records
            )
            or not any(
                item.get("invent_inputs_sha256")
                == eve_binding["world_inputs_sha256"]
                for item in world_playtest_records
            )
        ):
            raise AssertionError("world evidence did not bind the resumed v3 Handoff")
        for inventor_id, receipt in receipts.items():
            product_id = receipt["wish"]["product_id"]
            pid = manager_pids[inventor_id]
            calls = [
                (item["method"], item["path"])
                for item in records
                if item["event"] == "factory-http" and item["pid"] == pid
            ]
            imports = [
                index
                for index, call in enumerate(calls)
                if call == ("POST", "/designs/import")
            ]
            publishes = [
                index
                for index, call in enumerate(calls)
                if call == ("POST", "/designs/%s/publish" % product_id)
            ]
            readbacks = [
                index
                for index, call in enumerate(calls)
                if call == ("GET", "/designs/%s" % product_id)
            ]
            if len(imports) != 1 or len(publishes) != 1:
                raise AssertionError("Factory effect count is not exact for %s" % inventor_id)
            if not any(imports[0] < index < publishes[0] for index in readbacks):
                raise AssertionError("Factory draft was not read back before publication")
            if not any(index > publishes[0] for index in readbacks):
                raise AssertionError("Factory public state was not read back after publication")
            deliver_index = next(
                index
                for index, item in enumerate(records)
                if item["event"] == "manager-service"
                and item.get("capability") == "deliver"
                and item["pid"] == pid
            )
            publish_index = next(
                index
                for index, item in enumerate(records)
                if item["event"] == "factory-http"
                and item["pid"] == pid
                and item.get("method") == "POST"
                and item.get("path") == "/designs/%s/publish" % product_id
            )
            if deliver_index >= publish_index:
                raise AssertionError("Factory publication happened before exact Deliver")
            inventories = [
                item
                for item in records
                if item["event"] == "factory-pack-inventory" and item["pid"] == pid
            ]
            if not inventories:
                raise AssertionError("synthetic Factory did not inspect its exact transport Pack")
            expected_sidecar = product_id + ".step.json"
            for inventory in inventories:
                paths = inventory["paths"]
                sidecars = [path for path in paths if path.endswith(".step.json")]
                if sidecars != [expected_sidecar]:
                    raise AssertionError(
                        "Factory transport did not contain one canonical occurrence sidecar"
                    )
                if product_id + ".step" not in paths:
                    raise AssertionError("Factory transport lacks the canonical STEP sibling")
                occurrences = inventory.get("occurrences")
                if (
                    not isinstance(occurrences, list)
                    or len(occurrences) != EXPECTED_OCCURRENCES[inventor_id]
                    or len({item["name"] for item in occurrences}) != len(occurrences)
                    or any(
                        item.get("order") != index
                        or item.get("path")
                        != "%s_parts/%s.stl" % (product_id, item.get("name"))
                        or item.get("path") not in paths
                        or not isinstance(item.get("sha256"), str)
                        or len(item["sha256"]) != 64
                        for index, item in enumerate(occurrences)
                    )
                    or any(
                        not isinstance(inventory.get(name), str)
                        or len(inventory[name]) != 64
                        for name in (
                            "primary_sha256",
                            "step_sha256",
                            "sidecar_sha256",
                        )
                    )
                ):
                    raise AssertionError("Factory occurrence hashes are incomplete")
            logins = [
                item.get("username")
                for item in records
                if item["event"] == "factory-login" and item["pid"] == pid
            ]
            if not logins or set(logins) != {inventor_id}:
                raise AssertionError("Factory login did not use the selected Inventor identity")
        serialized_records = "\n".join(json.dumps(item, sort_keys=True) for item in records)
        if ACCEPTANCE_FACTORY_PASSWORD in serialized_records:
            raise AssertionError("acceptance log exposed credential material")
        for item in records:
            if {key.casefold() for key in item} & {
                "authorization",
                "factory_password",
                "password",
            }:
                raise AssertionError("acceptance log exposed an authentication field")

        status = json.loads(
            _run((workshop, "status", "--json"), cwd=away, environment=environment).stdout
        )
        if status["count"] != 5:
            raise AssertionError("installed status did not retain all five Wishes")
        if {item["inventor_id"] for item in status["wishes"]} != set(CASES):
            raise AssertionError("installed status lost an Inventor route")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args(argv)
    repository = Path(__file__).resolve().parents[1]
    if args.wheel is None:
        with tempfile.TemporaryDirectory(prefix="workshop-all-five-wheel-") as temporary:
            wheel = _build_wheel(repository, Path(temporary))
            acceptance(repository, wheel)
    else:
        acceptance(repository, args.wheel.resolve(strict=True))
    print("installed-all-five-orchestration: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
