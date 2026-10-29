"""Direct publication of an outside CAD project through the unchanged adapter."""

import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from tests.integrations.test_factory import RootSelectingFactoryTransport, multipart_parts
from workshop.errors import ContractError
from workshop.release.direct_publish import (
    EVIDENCE_PATH,
    build_evidence,
    load_cad_project,
    load_public_toy_archive,
    parse_pipeline_record,
    stage_direct_publication,
)
from workshop.release.native import direct_release_claims, playtest_omission_sha256
from workshop.release.public_archive import build_public_archive_manifest
from workshop.runtime import EffectLedger


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "publish_direct.py"
SPEC = importlib.util.spec_from_file_location("workshop_publish_direct", TOOL_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("cannot load tools/publish_direct.py")
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)

INVENTOR = "mira-fold"
# The shared Factory fake answers with this title, description and slug.
TITLE = "Verified Toy"
SUMMARY = "An exact toy page authored before Factory import."
PRODUCT_ID = "verified-toy"
STEP = b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"
ENTRY = "PRINTABLE = {flag}\n\n\ndef gen_step():\n    return None\n"


def png(shaded=True):
    image = Image.new("RGB", (64, 64), (234, 240, 246) if shaded else (255, 255, 255))
    ImageDraw.Draw(image).polygon(
        [(8, 56), (32, 8), (56, 56)], fill=(186, 14, 14) if shaded else (0, 0, 0)
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def write_project(root):
    root.mkdir(parents=True)
    (root / "README.md").write_text("# %s\n\n%s\n\n## Files\n\nMore.\n" % (TITLE, SUMMARY))
    for stem, flag in (("widget", "True"), ("part_arm", "False")):
        (root / (stem + ".step.py")).write_text(ENTRY.format(flag=flag))
        (root / (stem + ".step")).write_bytes(STEP + stem.encode())
    (root / "widget_lib.py").write_text("SIZE = 20\n")
    (root / "snap").mkdir()
    (root / "snap" / "iso.png").write_bytes(png())
    (root / "snap" / "top.png").write_bytes(png())
    (root / "measure").mkdir()
    (root / "measure" / "check.md").write_text("print gates: not recorded here\n")
    (root / "ref").mkdir()
    (root / "ref" / "concept.png").write_bytes(png())
    (root / "inputs").mkdir()
    (root / "inputs" / "request.md").write_text("the owner's private request\n")
    return root


def pipeline_record(thickness="rc=0", gates=("check_mesh", "check_overhang", "check_thickness")):
    rows = ["| 1 | `/v/bin/python /r/skills/cad/scripts/gen widget/widget.step.py --write --json` | rc=0 | 1.00 |",
            "| 2 | `check_motion  # NOT RUN: no moving joint is declared` | skipped | 0.00 |",
            "| 3 | `/v/bin/python widget/measure/check_fit.py` | rc=0 | 1.00 |"]
    for index, gate in enumerate(gates, 4):
        status = thickness if gate == "check_thickness" else "rc=0"
        rows.append("| %d | `/v/bin/python /r/skills/cad/scripts/%s widget/widget.step.py --nozzle 0.4` | %s | 1.00 |"
                    % (index, gate, status))
    return ("# Verification pipeline record\n\n- Mode: `final`\n\n| # | command | result | seconds |\n"
            "|---:|---|---:|---:|\n" + "\n".join(rows) + "\n\n---\n\n## Previous pipeline record (preserved)\n\n"
            "| 1 | `/v/bin/python /r/skills/cad/scripts/check_mesh widget/widget.step.py` | rc=1 | 1.00 |\n")


def write_evidence(project, *, thickness="rc=0", arguments=("--fresh", "--print-gates"), **record):
    text = pipeline_record(thickness, **record)
    (project / "measure" / "verification-pipeline.md").write_text(text)
    evidence = build_evidence(
        load_cad_project(project), record=text.encode(),
        exit_code=0 if thickness == "rc=0" else 1,
        arguments=[*arguments, "--assembly", "widget.step.py"],
        verifier_sha256="0" * 64, recorded_at="2026-10-28T00:00:00+00:00",
    )
    (project / EVIDENCE_PATH).write_text(json.dumps(evidence))


def pack_archive(project, destination):
    """Lay a project out as toy_archive packs it, with its manifest."""

    for path in sorted(project.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(project).as_posix()
        head = relative.split("/", 1)[0]
        if head == "measure":
            target = "make/verification/reports/" + relative.split("/", 1)[1]
        elif head == "snap":
            target = "make/verification/renders/" + relative.split("/", 1)[1]
        elif relative.endswith(".step") and head != "ref":
            target = "make/models/cad/" + relative
        else:
            target = "make/source/cad/" + relative
        (destination / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination / target)
    (destination / "README.md").write_text(
        "# %s\n\n![%s](make/verification/renders/iso.png)\n\n%s\n" % (TITLE, TITLE, SUMMARY)
    )
    reseal(destination)
    return destination


def reseal(archive):
    (archive / "MANIFEST.json").write_text(json.dumps({
        "schema_version": 4,
        "kind": "autonomous-workshop.public-toy-archive",
        "scope": "all files except MANIFEST.json and README.md",
        "artifact_manifest": build_public_archive_manifest(archive).to_dict(),
    }))


class NoNetwork:
    calls = 0

    def __call__(self, *args):
        NoNetwork.calls += 1
        raise AssertionError("the network was used")


class DirectPublishTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = write_project(self.root / "widget")
        self.home = self.root / "home"
        self.environment = {"WORKSHOP_HOME": str(self.home)}

    def store_credential(self):
        folder = self.home / "credentials" / "inventors"
        folder.mkdir(parents=True)
        os.chmod(folder, 0o700)
        path = folder / (INVENTOR + ".env")
        path.write_text(
            "FACTORY_USERNAME=alice\nFACTORY_PASSWORD=test-secret\nFACTORY_INVENTOR_ID=%s\n" % INVENTOR
        )
        os.chmod(path, 0o600)

    def ready(self, **evidence):
        self.store_credential()
        write_evidence(self.project, **evidence)

    def run_tool(self, *arguments, transport=None, source=None):
        out, err = io.StringIO(), io.StringIO()
        transports = {} if transport is None else {"transport": transport}
        code = TOOL.main(
            [*(source or ["--cad-dir", str(self.project)]), "--inventor", INVENTOR,
             "--product-id", PRODUCT_ID, *arguments],
            environment=self.environment, transports=transports, out=out, err=err,
        )
        return code, out.getvalue(), err.getvalue()

    def uploaded(self, transport):
        call = next(call for call in transport.calls if call[1].endswith("/designs/import"))
        return multipart_parts(call[2], call[3])["file"][0]

    def test_dry_run_reads_no_credential_and_sends_nothing(self):
        self.store_credential()
        with mock.patch.object(TOOL, "factory_credential_environment", side_effect=AssertionError("read")):
            code, out, err = self.run_tool(transport=NoNetwork())
        self.assertEqual((code, err), (0, ""))
        self.assertIn("dry run, nothing is read from the credential store or sent", out)
        self.assertIn("title:         %s" % TITLE, out)
        self.assertIn("ref/concept.png (reference material is not published)", out)
        self.assertIn("inputs/request.md (working material is not published)", out)
        self.assertIn("cad/part_arm.step (one STEP crosses: the primary)", out)
        self.assertIn("Playtest (recorded as not-run)", out)
        self.assertNotIn("public:", out)
        self.assertEqual(NoNetwork.calls, 0)
        self.assertFalse((self.home / "direct-publish").exists())

    def test_live_publishes_the_dry_run_bytes_and_reads_them_back(self):
        self.ready()
        _, dry, _ = self.run_tool()
        transport = RootSelectingFactoryTransport()
        code, out, err = self.run_tool("--live", transport=transport)
        self.assertEqual((code, err), (0, ""), out)
        self.assertRegex(out, r"(?m)^public: https://www\.autonomous\.ai/toys/product/verified-toy$")
        self.assertEqual(transport.imports, 1)
        self.assertTrue(transport.public)
        content = self.uploaded(transport)
        pack = re.search(r"pack sha256 ([0-9a-f]{64})", dry).group(1)
        self.assertEqual(hashlib.sha256(content).hexdigest(), pack)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            facts = json.loads(archive.read("workshop-product-facts.json"))
            page = json.loads(archive.read("workshop-release-page.json"))
            self.assertEqual(archive.read("assembled.step"), STEP + b"widget")
            self.assertEqual(archive.read("assembled_review/_assembled.png"), png())
        self.assertEqual([name for name in names if name.endswith(".step")], ["assembled.step"])
        self.assertFalse(any(name.startswith("cad/ref/") for name in names))
        self.assertEqual(facts["wish"]["kind"], "workshop.direct-publish")
        self.assertIsNone(facts["wish"]["wish"])
        self.assertEqual(facts["wish"]["workshop_lifecycle"], "not-run")
        self.assertEqual(facts["inventor"], {"name": "Mira Fold"})
        self.assertEqual(page["playtest_status"], "not-run")
        self.assertEqual(page["claims"], direct_release_claims())
        self.assertEqual(page["playtest_evidence_artifact_sha256"], playtest_omission_sha256())
        self.assertEqual(page["source_document"]["source_path"], "cad/README.md")
        self.assertNotIn("test-secret", out + err)

    def test_rerun_of_the_same_bytes_reconciles_without_a_second_design(self):
        self.ready()
        transport = RootSelectingFactoryTransport()
        self.assertEqual(self.run_tool("--live", transport=transport)[0], 0)
        code, out, _ = self.run_tool("--live", transport=transport)
        self.assertEqual(code, 0)
        self.assertIn("public: https://www.autonomous.ai/toys/product/verified-toy", out)
        self.assertEqual(transport.imports, 1)

    def test_changed_bytes_for_a_published_product_are_refused(self):
        self.ready()
        transport = RootSelectingFactoryTransport()
        self.assertEqual(self.run_tool("--live", transport=transport)[0], 0)
        # A report is not gate evidence, so the evidence stays fresh and the
        # ledger is what refuses the different bytes.
        (self.project / "measure" / "check.md").write_text("a later note\n")
        code, _, err = self.run_tool("--live", transport=transport)
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("different durable factory-import intent", err)
        self.assertEqual(transport.imports, 1)

    def test_lost_import_response_is_reconciled_not_resent(self):
        self.ready()
        transport = RootSelectingFactoryTransport()
        original = transport.__call__

        def lose_import(method, url, headers, body, timeout):
            response = original(method, url, headers, body, timeout)
            if url.endswith("/designs/import") and transport.imports == 1:
                raise TimeoutError("connection reset")
            return response

        code, _, err = self.run_tool("--live", transport=lose_import)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("AmbiguousEffectError", err)
        ledger = EffectLedger(TOOL.ledger_path(PRODUCT_ID, self.environment))
        self.assertEqual(ledger.latest(PRODUCT_ID, "factory-import").state, "unknown")
        code, out, _ = self.run_tool("--live", transport=lose_import)
        self.assertEqual(code, 0, out)
        self.assertEqual(transport.imports, 1)
        self.assertTrue(transport.public)

    def test_dry_run_warns_about_unsanitized_home_paths(self):
        (self.project / "measure" / "check.md").write_text("ran in /home/someone/work/x\n")
        code, out, _ = self.run_tool()
        self.assertEqual(code, 0)
        self.assertIn("would publish it: measure/check.md", out)

    def test_live_needs_the_inventors_own_credential(self):
        write_evidence(self.project)
        code, _, err = self.run_tool("--live", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("workshop login %s" % INVENTOR, err)
        self.assertEqual(NoNetwork.calls, 0)

    def test_reimport_is_refused_before_any_effect(self):
        self.store_credential()
        code, _, err = self.run_tool("--live", "--reimport-slug", "verified-toy", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("--reimport-slug is not supported", err)
        self.assertEqual(NoNetwork.calls, 0)

    def test_unknown_inventor_is_refused(self):
        out, err = io.StringIO(), io.StringIO()
        code = TOOL.main(["--cad-dir", str(self.project), "--inventor", "nobody-here"],
                         environment=self.environment, out=out, err=err)
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("no Inventor 'nobody-here'", err.getvalue())

    def test_archive_and_project_stage_the_same_made_bytes(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        staged = []
        for source in (load_cad_project(self.project), load_public_toy_archive(archive)):
            workspace = self.root / ("stage-" + source.kind)
            workspace.mkdir()
            staged.append(stage_direct_publication(
                source, workspace, product_id=PRODUCT_ID, inventor_display_name="Mira Fold",
                primary_step="widget.step", title=TITLE, summary=SUMMARY,
            ))
        self.assertEqual(
            staged[0].context.made.artifact_sha256, staged[1].context.made.artifact_sha256
        )
        code, out, _ = self.run_tool(source=["--archive", str(archive)])
        self.assertEqual(code, 0)
        self.assertIn("MANIFEST.json verified", out)
        self.assertIn("primary model: assembled.step <- widget.step", out)

    def test_archive_defaults_product_id_title_and_primary(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        out, err = io.StringIO(), io.StringIO()
        code = TOOL.main(["--archive", str(archive), "--inventor", INVENTOR],
                         environment=self.environment, out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("product id:    widget", out.getvalue())
        self.assertIn("title:         %s" % TITLE, out.getvalue())

    def test_tampered_archive_names_the_changed_file(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        (archive / "make" / "source" / "cad" / "widget_lib.py").write_text("SIZE = 99\n")
        code, _, err = self.run_tool(source=["--archive", str(archive)])
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("make/source/cad/widget_lib.py", err)

    def test_archive_with_a_publication_record_is_never_published_again(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        (archive / "publication").mkdir()
        (archive / "publication" / "PUBLICATION.json").write_text(json.dumps(
            {"publication": {"page_url": "https://www.autonomous.ai/toys/product/widget"}}
        ))
        reseal(archive)
        self.store_credential()
        code, _, err = self.run_tool("--live", source=["--archive", str(archive)], transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("already records a publication", err)
        code, out, _ = self.run_tool(source=["--archive", str(archive)])
        self.assertEqual(code, 0)
        self.assertIn("live:          refused", out)
        self.assertIn("already records a publication", out)

    def test_workshop_run_archive_is_refused(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        (archive / "release").mkdir()
        (archive / "release" / "release.json").write_text("{}")
        reseal(archive)
        with self.assertRaisesRegex(ContractError, "workshop publish"):
            load_public_toy_archive(archive)

    def test_publication_records_evidence_and_receipt_identities(self):
        self.ready()
        transport = RootSelectingFactoryTransport()
        code, out, _ = self.run_tool("--live", transport=transport)
        self.assertEqual(code, 0, out)
        line = next(line for line in out.splitlines() if line.startswith("publication-record: "))
        record = json.loads(line[len("publication-record: "):])
        content = self.uploaded(transport)
        self.assertEqual(record["identities"]["pack_sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(record["identities"]["publication_anchor_path"], "workshop-release-page.json")
        self.assertEqual(record["primary_model"]["path"], "make/models/cad/widget.step")
        self.assertEqual(record["publication"]["page_url"],
                         "https://www.autonomous.ai/toys/product/verified-toy")
        evidence = record["direct_publish"]["evidence"]
        self.assertEqual(evidence["known_gate_failures"], [])
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertIn("cad/" + EVIDENCE_PATH, archive.namelist())
        self.assertEqual(facts["wish"]["evidence"], evidence)

    def test_a_verifier_cache_with_lock_files_stays_local(self):
        cache = self.project / "__cadgen__" / "models"
        cache.mkdir(parents=True)
        (cache / ".widget.step.generation.lock").write_text("")
        (cache / "widget.glb").write_bytes(b"glTF")
        write_evidence(self.project)
        code, out, err = self.run_tool()
        self.assertEqual(code, 0, err)
        self.assertNotIn("cad/__cadgen__", out)
        self.assertIn("__cadgen__/models/widget.glb (derived cache)", out)
        self.assertIn("evidence:      pass", out)

    def test_live_refuses_without_evidence(self):
        self.store_credential()
        code, out, _ = self.run_tool()
        self.assertEqual(code, 0)
        self.assertIn("evidence:      missing", out)
        self.assertIn("live:          refused", out)
        code, _, err = self.run_tool("--live", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("gate evidence is missing", err)
        self.assertEqual(NoNetwork.calls, 0)

    def test_stale_evidence_names_the_changed_source(self):
        self.ready()
        (self.project / "widget_lib.py").write_text("SIZE = 21\n")
        code, _, err = self.run_tool("--live", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("gate evidence is stale", err)
        self.assertIn("widget_lib.py", err)
        self.assertEqual(NoNetwork.calls, 0)

    def test_undeclared_gate_failure_refuses(self):
        self.ready(thickness="rc=1")
        code, out, _ = self.run_tool()
        self.assertIn("failed: check_thickness on widget.step.py (rc=1)", out)
        self.assertIn("undeclared gate failure: check_thickness", out)
        code, _, err = self.run_tool("--live", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("undeclared gate failure: check_thickness", err)
        self.assertEqual(NoNetwork.calls, 0)

    def test_declared_gate_failure_is_printed_and_recorded(self):
        self.ready(thickness="rc=1")
        reason = "only the designed 0.2 mm breakaway ties"
        declared = ("--known-gate-failure", "check_thickness:" + reason)
        _, dry, _ = self.run_tool(*declared)
        self.assertIn("known gate failure declared: check_thickness: " + reason, dry)
        self.assertIn("live:          ready", dry)
        transport = RootSelectingFactoryTransport()
        code, out, _ = self.run_tool("--live", *declared, transport=transport)
        self.assertEqual(code, 0, out)
        record = json.loads(out.split("publication-record: ", 1)[1].splitlines()[0])
        self.assertEqual(record["direct_publish"]["evidence"]["known_gate_failures"],
                         [{"gate": "check_thickness", "reason": reason}])
        with zipfile.ZipFile(io.BytesIO(self.uploaded(transport))) as archive:
            facts = json.loads(archive.read("workshop-product-facts.json"))
        self.assertEqual(facts["wish"]["evidence"]["known_gate_failures"],
                         [{"gate": "check_thickness", "reason": reason}])

    def test_evidence_must_be_exact(self):
        cases = {
            "a declaration that did not fail": (
                {}, ("--known-gate-failure", "check_thickness:just in case"),
                "declared failure check_thickness did not fail"),
            "a run without --print-gates": (
                {"arguments": ("--fresh",)}, (), "verification ran without --print-gates"),
            "a print gate that never ran": (
                {"gates": ("check_mesh", "check_overhang")}, (), "print gate check_thickness did not run"),
        }
        for label, (evidence, arguments, message) in cases.items():
            with self.subTest(label):
                write_evidence(self.project, **evidence)
                code, out, _ = self.run_tool(*arguments)
                self.assertEqual(code, 0)
                self.assertIn(message, out)
                self.assertIn("live:          refused", out)

    def test_record_parser_reads_only_the_newest_run(self):
        rows = parse_pipeline_record(pipeline_record("rc=1"))
        self.assertEqual([row["gate"] for row in rows], [
            "gen", "check_motion", "measure/check_fit.py",
            "check_mesh", "check_overhang", "check_thickness"])
        self.assertEqual(rows[-1], {"gate": "check_thickness", "target": "widget.step.py",
                                    "status": "rc=1", "result": "fail"})
        refused = parse_pipeline_record(
            "| 1 | `preflight  # ERROR: final verification refused` | refused | 0.00 |\n")
        self.assertEqual(refused[0]["gate"], "preflight")
        self.assertEqual(refused[0]["result"], "fail")

    def test_verify_runs_the_verifier_in_place_and_binds_its_output(self):
        repository = self.root / "product-to-cad"
        script = repository / "skills" / "cad" / "scripts" / "verify_project"
        script.parent.mkdir(parents=True)
        script.write_text(
            "import sys, pathlib\n"
            "project = pathlib.Path(sys.argv[1])\n"
            "assert sys.argv[2:] == ['--fresh', '--print-gates', '--assembly', 'widget/widget.step.py'], sys.argv\n"
            "(project / 'widget.step').write_bytes(b'ISO-10303-21;\\nregenerated')\n"
            "(project / 'measure' / 'verification-pipeline.md').write_text(%r)\n"
            "sys.exit(1)\n" % pipeline_record("rc=1")
        )
        self.store_credential()
        verify = ("--verify", "--verifier-repo", str(repository), "--verifier-python", sys.executable)
        code, out, err = self.run_tool(*verify)
        self.assertEqual(code, 0, err)
        self.assertIn("running skills/cad/scripts/verify_project", err)
        evidence = json.loads((self.project / EVIDENCE_PATH).read_text())
        self.assertEqual(evidence["exit_code"], 1)
        self.assertIn({"path": "widget.step", "sha256": hashlib.sha256(
            b"ISO-10303-21;\nregenerated").hexdigest()}, evidence["subject"]["files"])
        self.assertIn("undeclared gate failure: check_thickness", out)
        code, out, _ = self.run_tool("--known-gate-failure", "check_thickness:ties")
        self.assertIn("evidence:      pass", out)
        self.assertIn("live:          ready", out)

    def test_verify_is_refused_for_an_archive(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        code, _, err = self.run_tool("--verify", source=["--archive", str(archive)])
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("re-pack the archive", err)

    def test_archive_carries_its_evidence(self):
        write_evidence(self.project, thickness="rc=1")
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        self.store_credential()
        code, out, _ = self.run_tool("--known-gate-failure", "check_thickness:ties",
                                     source=["--archive", str(archive)])
        self.assertEqual(code, 0)
        self.assertIn("evidence:      pass", out)
        self.assertIn("live:          ready", out)

    def test_archive_packed_for_another_inventor_must_be_repacked(self):
        write_evidence(self.project)
        archive = pack_archive(self.project, self.root / "rowan-vale-widget")
        self.store_credential()
        out, err = io.StringIO(), io.StringIO()
        code = TOOL.main(["--archive", str(archive), "--inventor", INVENTOR],
                         environment=self.environment, out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("product id:    widget", out.getvalue())
        self.assertIn("archive was packed for Inventor rowan-vale; re-pack it with "
                      "`toy_archive pack --inventor mira-fold`", out.getvalue())
        code = TOOL.main(["--archive", str(archive), "--inventor", INVENTOR, "--live"],
                         environment=self.environment, transports={"transport": NoNetwork()},
                         out=io.StringIO(), err=err)
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertEqual(NoNetwork.calls, 0)

    def test_unpublishable_projects_are_refused(self):
        cases = {
            "a mesh": (lambda: (self.project / "widget.stl").write_bytes(b"solid"), "STEP only"),
            "a hidden file": (lambda: (self.project / ".env").write_text("X=1"), "hidden file"),
            "a likeness-mask cover": (
                lambda: (self.project / "snap" / "iso.png").write_bytes(png(shaded=False)),
                "likeness mask"),
            "no cover": (lambda: (self.project / "snap" / "iso.png").unlink(), "snap/iso.png"),
            "a second cover": (
                lambda: (self.project / "measure" / "snap").mkdir() or
                (self.project / "measure" / "snap" / "iso.png").write_bytes(png()),
                "exactly one snap/iso.png"),
            "a non-STEP primary": (
                lambda: (self.project / "widget.step").write_bytes(b"solid widget"),
                "not a STEP file"),
            "two printable entries": (
                lambda: (self.project / "part_arm.step.py").write_text(ENTRY.format(flag="True")),
                "2 top-level entries declare PRINTABLE"),
        }
        for label, (change, message) in cases.items():
            with self.subTest(label):
                shutil.rmtree(self.project)
                write_project(self.project)
                change()
                out, err = io.StringIO(), io.StringIO()
                code = TOOL.main(["--cad-dir", str(self.project), "--inventor", INVENTOR],
                                 environment=self.environment, out=out, err=err)
                self.assertEqual(code, TOOL.EXIT_INPUT)
                self.assertIn(message, err.getvalue())


if __name__ == "__main__":
    unittest.main()
