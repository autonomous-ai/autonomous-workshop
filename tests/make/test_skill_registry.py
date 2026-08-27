import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError
import workshop.make.skill_registry as skills_module
from workshop.make.skill_registry import (
    discover_skills,
    fingerprint_skill_tree,
    resolve_skills_root,
)


class SkillFingerprintTest(unittest.TestCase):
    def test_explicit_root_discovers_and_fingerprints_deterministically(self):
        with tempfile.TemporaryDirectory() as temporary:
            skills = Path(temporary).resolve() / "skills"
            skill = skills / "mechanisms"
            scripts = skill / "scripts"
            scripts.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Mechanisms\n", encoding="utf-8")
            tool = scripts / "measure.py"
            tool.write_text("print('one')\n", encoding="utf-8")

            first = discover_skills(skills)
            second = discover_skills(skills)

            self.assertEqual([item.name for item in first], ["mechanisms"])
            self.assertEqual(first[0].sha256, second[0].sha256)
            self.assertEqual(
                [item.path for item in first[0].files],
                ["SKILL.md", "scripts/measure.py"],
            )
            tool.write_text("print('two')\n", encoding="utf-8")
            changed = fingerprint_skill_tree(skill)
            self.assertNotEqual(first[0].sha256, changed.sha256)

    def test_checkout_discovery_finds_canonical_workshop_skills(self):
        observed = {skill.name for skill in discover_skills()}
        self.assertEqual(
            observed,
            {
                "cad",
                "design-reference",
                "image-to-cad",
                "step-parts",
            },
        )

    def test_reviewed_skill_lock_matches_exact_tree_fingerprints(self):
        workshop_root = Path(__file__).resolve().parents[2]
        lock = json.loads(
            (
                workshop_root
                / "src"
                / "workshop"
                / "make"
                / "skills"
                / "LOCK.json"
            ).read_text(encoding="utf-8")
        )
        expected = {
            name: record["sha256"] for name, record in lock["skills"].items()
        }
        observed = {skill.name: skill.sha256 for skill in discover_skills()}
        self.assertEqual(observed, expected)

    def test_explicit_root_must_be_absolute(self):
        with self.assertRaises(ContractError):
            discover_skills(Path("skills"))

    def test_component_package_layout_resolves_owned_skill_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            make_package = target / "workshop" / "make"
            skills_root = make_package / "skills"
            skill = skills_root / "cad"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# CAD\n", encoding="utf-8")
            with mock.patch.object(
                skills_module,
                "__file__",
                str(make_package / "skill_registry.py"),
            ):
                self.assertEqual(resolve_skills_root(), skills_root.resolve())

    def test_cad_command_guidance_does_not_assume_a_repository_root(self):
        cad = resolve_skills_root() / "cad"
        checked = (cad / "SKILL.md", *sorted((cad / "references").glob("*.md")))
        for path in checked:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("python skills/cad/", text)
                self.assertNotIn("python scripts/", text)
        self.assertIn('CAD_SKILL_ROOT="$(workshop skills path)/cad"', checked[0].read_text(encoding="utf-8"))

    def test_step_parts_command_guidance_uses_the_installed_skill_root(self):
        skill_text = (resolve_skills_root() / "step-parts" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("python scripts/", skill_text)
        self.assertIn(
            'STEP_PARTS_SKILL_ROOT="$(workshop skills path)/step-parts"',
            skill_text,
        )
        self.assertIn(
            'python "$STEP_PARTS_SKILL_ROOT/scripts/download_step_part.py"',
            skill_text,
        )

    def test_design_reference_command_guidance_uses_the_installed_skill_root(self):
        skill_text = (
            resolve_skills_root() / "design-reference" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("python skills/design-reference/", skill_text)
        self.assertIn(
            'DESIGN_REFERENCE_SKILL_ROOT="$(workshop skills path)/design-reference"',
            skill_text,
        )

    def test_image_to_cad_command_guidance_uses_the_installed_skill_root(self):
        skill = resolve_skills_root() / "image-to-cad"
        checked = (skill / "SKILL.md", skill / "scripts" / "render_views.py")
        for path in checked:
            with self.subTest(path=path.name):
                self.assertNotIn("python skills/image-to-cad/", path.read_text(encoding="utf-8"))
        self.assertIn(
            'IMAGE_TO_CAD_SKILL_ROOT="$(workshop skills path)/image-to-cad"',
            checked[0].read_text(encoding="utf-8"),
        )

    def test_warm_daemon_fingerprints_the_installed_skill_tree(self):
        cad = resolve_skills_root() / "cad"
        client_path = cad / "scripts" / "cadgen_daemon" / "client.py"
        spec = importlib.util.spec_from_file_location(
            "workshop_test_cadgen_daemon_client", client_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.SKILL_ROOT, cad.resolve())
        self.assertEqual(module._VERSION_TREES, ("scripts",))
        self.assertGreater(module.compute_version_token(), 0)
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            module.subprocess,
            "Popen",
            return_value=object(),
        ) as popen:
            sock_path = Path(temporary).resolve() / "cadgen.sock"
            self.assertIsNotNone(module._spawn_daemon(sock_path))
        self.assertNotIn("start_new_session", popen.call_args.kwargs)

    def test_warm_daemon_uses_a_compact_tree_specific_socket_name(self):
        module = self._load_warm_daemon_client()
        with mock.patch.dict(module.os.environ, {"TMPDIR": "/private/tmp"}, clear=True):
            first = module.socket_path()
            with mock.patch.object(module, "SKILL_ROOT", Path("/different/cad-skill")):
                second = module.socket_path()

        self.assertRegex(first.name, r"^cg-[0-9a-f]{12}\.sock$")
        self.assertNotEqual(first, second)
        self.assertLessEqual(
            len(module.os.fsencode(first)),
            module._PORTABLE_UNIX_SOCKET_PATH_BYTES,
        )

    def test_warm_daemon_skips_overlong_socket_before_connect_or_spawn(self):
        module = self._load_warm_daemon_client()
        overlong_environments = (
            {
                "CADGEN_WARM": "1",
                "TMPDIR": "/" + ("x" * module._PORTABLE_UNIX_SOCKET_PATH_BYTES),
            },
            {
                "CADGEN_WARM": "1",
                "CADGEN_DAEMON_SOCKET": "/" + ("é" * 52),
            },
        )
        for environment in overlong_environments:
            with self.subTest(environment=environment), mock.patch.dict(
                module.os.environ,
                environment,
                clear=True,
            ), mock.patch.object(
                module, "compute_version_token", return_value=1
            ), mock.patch.object(module, "_connect_or_spawn") as connect_or_spawn:
                self.assertIsNone(module.run_via_daemon("gen", ["part.step.py"]))
                connect_or_spawn.assert_not_called()

    def test_warm_daemon_keeps_the_normal_connector_for_a_usable_path(self):
        module = self._load_warm_daemon_client()
        with mock.patch.dict(
            module.os.environ,
            {
                "CADGEN_WARM": "1",
                "CADGEN_DAEMON_SOCKET": "/private/tmp/cg-test.sock",
            },
            clear=True,
        ), mock.patch.object(
            module, "compute_version_token", return_value=1
        ), mock.patch.object(
            module, "_connect_or_spawn", return_value=None
        ) as connect_or_spawn:
            self.assertIsNone(module.run_via_daemon("gen", ["part.step.py"]))
        connect_or_spawn.assert_called_once_with(Path("/private/tmp/cg-test.sock"))

    @staticmethod
    def _load_warm_daemon_client():
        client_path = (
            resolve_skills_root()
            / "cad"
            / "scripts"
            / "cadgen_daemon"
            / "client.py"
        )
        spec = importlib.util.spec_from_file_location(
            "workshop_test_cadgen_daemon_path_client", client_path
        )
        if spec is None or spec.loader is None:
            raise AssertionError("CAD warm-daemon client cannot be imported")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


if __name__ == "__main__":
    unittest.main()
