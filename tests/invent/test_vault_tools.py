"""The run-local vault_tools.py answers exactly what workshop.invent.vault answers."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.invent.test_vault import FIXTURE, write_vault
from workshop.invent.vault import Vault, assert_concept_compatible, bundled_vault_root
from workshop.invent.vault import VaultError

TOOL = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "workshop"
    / "invent"
    / "skills"
    / "design-vault"
    / "vault_tools.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location("vault_tools_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VaultToolParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.fixture_root = write_vault(cls.temporary.name)
        cls.fixture_packed = Path(cls.temporary.name) / "fixture.json"
        cls.fixture_packed.write_bytes(Vault.from_directory(cls.fixture_root).packed_bytes())
        cls.seed_packed = Path(cls.temporary.name) / "seed.json"
        cls.seed_packed.write_bytes(Vault.from_directory(bundled_vault_root()).packed_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def pair(self, packed):
        host = Vault.from_packed_bytes(packed.read_bytes())
        run = self.tool.PackedVault.load(packed)
        self.assertEqual(run.sha256, host.sha256)
        return host, run

    def test_seed_queries_agree_for_every_mechanism(self):
        host, run = self.pair(self.seed_packed)
        constraints = list(host.constraints())
        self.assertEqual(run.constraints(), host.constraints())
        for path in host.paths("mechanisms"):
            with self.subTest(path=path):
                name = path.split("/", 1)[1].replace("-", " ")
                self.assertEqual(run.resolve(name), host.resolve(name))
                self.assertEqual(run.follow_links(path, depth=2), host.follow_links(path, depth=2))
                self.assertEqual(
                    run.follow_links(path, reverse=True), host.follow_links(path, reverse=True)
                )
                self.assertEqual(
                    run.check_compatibility([path] + constraints),
                    host.check_compatibility([path] + constraints),
                )
                self.assertEqual(run.guidance([path]), host.guidance([path]))
                concept = {"mechanisms": [path.split("/", 1)[1]]}
                self.assertEqual(run.leads_for_concept(concept), host.leads_for_concept(concept))
        node = "mechanisms/hand-management"
        self.assertEqual(run.read_node(node), dict(host.read_node(node)) | {"frontmatter": dict(host.read_node(node)["frontmatter"]), "relations": {k: list(v) for k, v in host.read_node(node)["relations"].items()}})

    def test_fixture_refusals_agree(self):
        host, run = self.pair(self.fixture_packed)
        concepts = (
            {"mechanisms": ["hand off", "single-token"]},
            {"mechanisms": ["rotating-drum"]},
            {"mechanisms": ["card-hand"]},
            {"mechanisms": ["hand-off"]},
            {"mechanisms": ["hand-off"], "novel_mechanisms": "no"},
            {"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "x"}]},
            {"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "other", "definition": "x" * 30}]},
            {
                "mechanisms": ["a", "single-token"],
                "novel_mechanisms": [{"id": "a", "definition": "x" * 30}, {"id": "a", "definition": "y" * 30}],
            },
            {"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "hand-off", "definition": "x" * 30}]},
            {"mechanisms": ["a", "single-token"], "novel_mechanisms": [{"id": "a", "definition": "short"}]},
            {"mechanisms": ["a", "single-token"], "novel_mechanisms": [{"id": "a", "definition": "x" * 30}]},
            {"mechanisms": "hand-off"},
        )
        for concept in concepts:
            with self.subTest(concept=concept):
                try:
                    expected = ("ok", assert_concept_compatible(host, concept))
                except VaultError as exc:
                    expected = ("refused", str(exc))
                try:
                    observed = ("ok", self.tool.assert_concept_compatible(run, concept))
                except self.tool.VaultToolError as exc:
                    observed = ("refused", str(exc))
                self.assertEqual(observed, expected)
        with self.assertRaisesRegex(self.tool.VaultToolError, "no vault node"):
            run.read_node("mechanisms/nothing-here")
        with self.assertRaisesRegex(self.tool.VaultToolError, "Close matches"):
            run.read_node("mechanisms/hand-of")
        self.assertEqual(run.resolve("   "), None)
        self.assertEqual(run.resolve("pass the baton"), "mechanisms/hand-off")
        self.assertEqual(run.paths(), host.paths())
        self.assertEqual(self.tool.normalize_path("./mechanisms/a.md"), "mechanisms/a")
        with self.assertRaisesRegex(self.tool.VaultToolError, "at most 16"):
            self.tool.assert_concept_compatible(
                run,
                {"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "n%d" % i, "definition": "x" * 30} for i in range(17)]},
            )
        dangling = dict(FIXTURE)
        dangling["mechanisms/dangling"] = FIXTURE["mechanisms/lonely"].replace(
            "## Relations", "## Relations\n- risks:: [[anti-patterns/ghost]]"
        ).replace("Lonely", "Dangling")
        with tempfile.TemporaryDirectory() as temporary:
            packed = Path(temporary) / "dangling.json"
            packed.write_bytes(Vault.from_directory(write_vault(temporary, dangling)).packed_bytes())
            host_d, run_d = self.pair(packed)
            self.assertEqual(
                run_d.check_compatibility(["mechanisms/dangling"]),
                host_d.check_compatibility(["mechanisms/dangling"]),
            )
            self.assertEqual(run_d.guidance(["mechanisms/dangling"]), host_d.guidance(["mechanisms/dangling"]))
            self.assertEqual(run_d.guidance(["mechanisms/dangling"])[0]["risks"], [])
        self.assertEqual(run.follow_links("mechanisms/card-hand", depth=3), host.follow_links("mechanisms/card-hand", depth=3))
        self.assertEqual(run.follow_links("mechanisms/hand-off", link_type="risks"), host.follow_links("mechanisms/hand-off", link_type="risks"))

    def test_packed_document_is_validated(self):
        document = json.loads(self.fixture_packed.read_bytes())
        for broken, pattern in (
            ({**document, "extra": 1}, "fields are invalid"),
            ({**document, "kind": "other"}, "schema or kind"),
            ({**document, "sha256": "0" * 64}, "sha256 does not match"),
        ):
            with self.assertRaisesRegex(self.tool.VaultToolError, pattern):
                self.tool.PackedVault(broken)
        with self.assertRaisesRegex(self.tool.VaultToolError, "cannot read"):
            self.tool.PackedVault.load(Path(self.temporary.name) / "missing.json")
        self.assertEqual(self.tool.default_vault_path(), TOOL.parent / "vault.json")

    def run_cli(self, *argv, expected=0):
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--vault", str(self.fixture_packed), *argv],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(completed.returncode, expected, completed.stderr)
        return completed

    def test_command_line_surface(self):
        node = json.loads(self.run_cli("node", "mechanisms/hand-off").stdout)
        self.assertEqual(node["name"], "Hand Off")
        links = json.loads(self.run_cli("links", "anti-patterns/idle-player", "--reverse", "--type", "risks").stdout)
        self.assertEqual(list(links), ["mechanisms/hand-off"])
        resolved = json.loads(self.run_cli("resolve", "pass the baton").stdout)
        self.assertEqual(resolved, {"name": "pass the baton", "node": "mechanisms/hand-off"})
        unresolved = json.loads(self.run_cli("resolve", "fdm only", "--folder", "constraints").stdout)
        self.assertEqual(unresolved["node"], "constraints/fdm-only")
        check = json.loads(self.run_cli("check", "mechanisms/card-hand", "--with-constraints").stdout)
        self.assertEqual(check[0]["kind"], "conflict")
        self.assertEqual(len(check[0]["id"]), 16)
        plain = json.loads(self.run_cli("check", "mechanisms/hand-off").stdout)
        self.assertEqual([item["kind"] for item in plain], ["risk", "unmet-requirement"])
        guidance = json.loads(self.run_cli("guidance", "mechanisms/hand-off").stdout)
        self.assertEqual(guidance[0]["exemplars"], ["games/relay"])
        failed = self.run_cli("node", "mechanisms/nothing", expected=2)
        self.assertIn("vault-tools: no vault node", failed.stderr)
        missing = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--vault", str(Path(self.temporary.name) / "nope.json"), "node", "x"],
            capture_output=True, text=True, check=False, timeout=60,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("cannot read packed vault", missing.stderr)

    def test_main_runs_in_process_for_every_command(self):
        def run_main(*argv):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = self.tool.main(["--vault", str(self.fixture_packed), *argv])
            return code, out.getvalue(), err.getvalue()

        code, out, _ = run_main("node", "mechanisms/hand-off")
        self.assertEqual((code, json.loads(out)["name"]), (0, "Hand Off"))
        code, out, _ = run_main("links", "mechanisms/hand-off", "--depth", "2")
        self.assertEqual(code, 0)
        self.assertIn("anti-patterns/idle-player", json.loads(out))
        code, out, _ = run_main("resolve", "single tokens")
        self.assertEqual(json.loads(out)["node"], "mechanisms/single-token")
        code, out, _ = run_main("check", "mechanisms/hand-off", "mechanisms/single-token")
        self.assertEqual([item["kind"] for item in json.loads(out)], ["risk"])
        code, out, _ = run_main("check", "mechanisms/card-hand", "--with-constraints")
        self.assertEqual(json.loads(out)[0]["kind"], "conflict")
        code, out, _ = run_main("guidance", "mechanisms/single-token")
        self.assertEqual(json.loads(out)[0]["node"], "mechanisms/single-token")
        code, _, err = run_main("node", "mechanisms/absent")
        self.assertEqual(code, 2)
        self.assertIn("vault-tools:", err)


if __name__ == "__main__":
    unittest.main()
