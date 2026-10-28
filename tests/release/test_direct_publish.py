"""Direct publication of an outside CAD project through the unchanged adapter."""

import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from tests.integrations.test_factory import RootSelectingFactoryTransport, multipart_parts
from workshop.errors import ContractError
from workshop.release.direct_publish import (
    load_cad_project,
    load_public_toy_archive,
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
    return root


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
        self.assertIn("cad/part_arm.step (one STEP crosses: the primary)", out)
        self.assertIn("Playtest (recorded as not-run)", out)
        self.assertNotIn("public:", out)
        self.assertEqual(NoNetwork.calls, 0)
        self.assertFalse((self.home / "direct-publish").exists())

    def test_live_publishes_the_dry_run_bytes_and_reads_them_back(self):
        _, dry, _ = self.run_tool()
        self.store_credential()
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
        self.store_credential()
        transport = RootSelectingFactoryTransport()
        self.assertEqual(self.run_tool("--live", transport=transport)[0], 0)
        code, out, _ = self.run_tool("--live", transport=transport)
        self.assertEqual(code, 0)
        self.assertIn("public: https://www.autonomous.ai/toys/product/verified-toy", out)
        self.assertEqual(transport.imports, 1)

    def test_changed_bytes_for_a_published_product_are_refused(self):
        self.store_credential()
        transport = RootSelectingFactoryTransport()
        self.assertEqual(self.run_tool("--live", transport=transport)[0], 0)
        (self.project / "widget_lib.py").write_text("SIZE = 21\n")
        code, _, err = self.run_tool("--live", transport=transport)
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("different durable factory-import intent", err)
        self.assertEqual(transport.imports, 1)

    def test_lost_import_response_is_reconciled_not_resent(self):
        self.store_credential()
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
        self.assertIn("--live is refused", out)

    def test_workshop_run_archive_is_refused(self):
        archive = pack_archive(self.project, self.root / ("%s-widget" % INVENTOR))
        (archive / "release").mkdir()
        (archive / "release" / "release.json").write_text("{}")
        reseal(archive)
        with self.assertRaisesRegex(ContractError, "workshop publish"):
            load_public_toy_archive(archive)

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
