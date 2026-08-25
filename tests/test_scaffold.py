import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.manifest import load_manifest
from inventor_workshop.scaffold import create_inventor, scaffold_inventor
from inventor_workshop.taste import load_taste_header
from inventor_workshop.toys import PLAYTHING_LANES


class ScaffoldTest(unittest.TestCase):
    @staticmethod
    def environment(destination: Path):
        core_src = Path(__file__).resolve().parents[1] / "src"
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(core_src), str(destination / "src"))
        )
        # Scaffold subprocess tests exercise truthful missing-capability paths,
        # not live AI workers. Production profiles inherit the shared engine
        # when this explicit diagnostic switch is absent.
        environment["WORKSHOP_AGENT_WORKERS"] = "disabled"
        return environment

    def test_scaffold_has_exactly_five_physical_magic_lanes(self):
        expected = (
            "classics-made-yours",
            "invented-games",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        )
        self.assertEqual(tuple(PLAYTHING_LANES), expected)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, lane in enumerate(expected):
                destination = scaffold_inventor(
                    root,
                    "lane-%d" % index,
                    "Inventor %d" % index,
                    "Wish-shaped physical magic",
                    lane=lane,
                )
                manifest = load_manifest(destination / "inventor.json")
                self.assertIn(lane, manifest.capabilities)
                taste = (destination / "TASTE.md").read_text(encoding="utf-8")
                if lane == "classics-made-yours":
                    self.assertIn("rules are already known", taste)
                    self.assertIn("Wish-shaped physical set", taste)
                if lane == "invented-games":
                    self.assertIn("experimental rules craft", taste)
                    self.assertIn("1,000 seeded games", taste)
                    self.assertIn("AI players", taste)
                    self.assertIn("after Deliver as Reviews", taste)
            for index, lane in enumerate(
                (
                    "games-puzzles",
                    "table-game",
                    "desk-toy",
                    "model-character",
                    "puzzle-keepsake",
                )
            ):
                with self.subTest(old_lane=lane), self.assertRaises(ContractError):
                    scaffold_inventor(
                        root,
                        "old-lane-%d" % index,
                        "Old Inventor",
                        "old category",
                        lane=lane,
                    )

    def test_taste_only_inventor_is_thin_discoverable_and_truthful(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "word-games",
                "Ada",
                "printable word games",
                lane="invented-games",
                level="taste-only",
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(manifest.inventor_id, "word-games")
            self.assertEqual(manifest.schema_version, 5)
            self.assertEqual(
                set(manifest.to_dict()),
                {
                    "schema_version",
                    "id",
                    "status",
                    "entrypoint",
                    "capabilities",
                    "checks",
                    "source",
                },
            )
            self.assertEqual(manifest.workshop_features, ())
            self.assertEqual(
                tuple(manifest.capabilities),
                ("invented-games", "taste-only"),
            )
            self.assertTrue(
                set(manifest.capabilities).isdisjoint(
                    {"wish", "invent", "make", "playtest", "instructions", "deliver"}
                )
            )

            package = destination / "src/word_games"
            self.assertTrue((package / "__main__.py").is_file())
            self.assertFalse((package / "inventor.py").exists())
            self.assertFalse((destination / "hook.py").exists())
            self.assertFalse((package / "workflow.py").exists())
            entrypoint = (package / "__main__.py").read_text(encoding="utf-8")
            self.assertIn("Workshop", entrypoint)
            self.assertNotIn("WorkshopTools", entrypoint)
            self.assertNotIn("configured_workshop_tools", entrypoint)

            taste = (destination / "TASTE.md").read_text(encoding="utf-8")
            self.assertIn("creative constitution", taste)
            self.assertIn("printable word games", taste)
            self.assertIn("Nothing may be merely useful", taste)
            self.assertIn("I couldn't have bought it before this Wish", taste)
            self.assertIn("Cool beats cute", taste)
            readme = (destination / "README.md").read_text(encoding="utf-8")
            self.assertIn(
                "Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver", readme
            )
            self.assertIn("contributes only `TASTE.md`", readme)
            self.assertIn("Workshop supplies Invent, Make, Playtest", readme)
            self.assertIn("Python 3.11 or newer is required", readme)
            self.assertIn("The Wish ID and Inventor match are automatic", readme)
            self.assertIn("workshop wish --root ../..", readme)
            self.assertIn("not the customer Wish entrance", readme)
            self.assertIn("No generic, off-the-shelf prints", readme)
            self.assertNotIn("Make/Inspect", readme)
            self.assertIn(
                'requires-python = ">=3.11"',
                (destination / "pyproject.toml").read_text(),
            )

            environment = self.environment(destination)
            observed = []
            for name in ("one", "two"):
                cwd = Path(temporary) / name
                cwd.mkdir()
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "from word_games.__main__ import default_runtime_root; "
                            "print(default_runtime_root())"
                        ),
                    ],
                    cwd=str(cwd),
                    env=environment,
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                observed.append(result.stdout.strip())
            self.assertEqual(observed[0], observed[1])
            self.assertEqual(Path(observed[0]), destination / ".workshop")

            profile = subprocess.run(
                [sys.executable, "-m", "word_games", "profile"],
                cwd=str(Path(temporary) / "one"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            profile_data = json.loads(profile.stdout)
            self.assertEqual(profile_data["customization_level"], "taste-only")
            self.assertFalse(profile_data["production_ready"])
            self.assertFalse((destination / ".workshop").exists())

            preview = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "word_games",
                    "preview",
                    "first-product",
                    "I wish for a tiny game of words",
                ],
                cwd=str(Path(temporary) / "one"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            preview_data = json.loads(preview.stdout)
            self.assertEqual(preview_data["blueprint"]["lane"], "invented-games")
            ai_table = next(
                task
                for task in preview_data["blueprint"]["tasks"]
                if task["key"] == "playtest.game"
            )
            self.assertEqual(ai_table["capability"], "game-simulation")
            self.assertFalse(ai_table["external"])
            self.assertEqual(
                preview_data["blueprint"]["post_delivery_reviews"]["feeds"],
                "future-make",
            )
            self.assertFalse((destination / ".workshop").exists())

            run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "word_games",
                    "run",
                    "--playtest-rounds",
                    "3",
                    "first-product",
                    "I wish for a tiny game of words",
                ],
                cwd=str(Path(temporary) / "two"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            waiting = json.loads(run.stdout)
            self.assertEqual(waiting["status"], "waiting")
            self.assertEqual(waiting["job"], "invent")
            self.assertEqual(waiting["playtest_rounds"], 3)
            self.assertIsNone(waiting["artifact_sha256"])
            self.assertEqual(
                waiting["needs"][0]["capability"], "industrial-design"
            )
            self.assertTrue((destination / ".workshop/workshop.sqlite3").is_file())

            built = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_*.py",
                ],
                cwd=str(destination),
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(built.returncode, 0, built.stderr)

    def test_existing_taste_is_the_only_creative_input_and_runs_immediately(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "my-taste" / "TASTE.md"
            source.parent.mkdir()
            exact_taste = (
                "---\r\n"
                "name: Mira\r\n"
                "description: Choose Mira for poetic kinetic desk toys; not games or static miniatures.\r\n"
                "---\r\n\r\n"
                "# Mira's Taste\r\n\r\n"
                "I love mechanisms that reveal one small, impossible-looking motion.\r\n"
                "I reject decoration without interaction. ✨\r\n"
            ).encode("utf-8")
            source.write_bytes(exact_taste)
            collection = root / "inventors"
            collection.mkdir()

            destination = create_inventor(
                collection,
                "mira",
                lane="moving-machines",
                taste_path=source,
            )

            self.assertEqual((destination / "TASTE.md").read_bytes(), exact_taste)
            self.assertEqual(source.read_bytes(), exact_taste)
            self.assertFalse((destination / "src/mira/inventor.py").exists())
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(tuple(manifest.capabilities), ("moving-machines", "taste-only"))
            self.assertEqual(tuple(manifest.entrypoint), ("python3", "run.py"))
            header = load_taste_header(destination)
            self.assertEqual(header.name, "Mira")
            self.assertEqual(
                header.description,
                "Choose Mira for poetic kinetic desk toys; not games or static miniatures.",
            )

            # Match the Manager's source-checkout execution boundary: only the
            # Workshop is importable before the generated bootstrap adds src/.
            away = root / "away"
            away.mkdir()
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
            environment["WORKSHOP_AGENT_WORKERS"] = "disabled"
            profile = subprocess.run(
                [sys.executable, "run.py", "profile"],
                cwd=destination,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(json.loads(profile.stdout)["inventor_id"], "mira")
            run = subprocess.run(
                [sys.executable, str(destination / "run.py"), "run", "I wish for a moon that waves"],
                cwd=away,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            result = json.loads(run.stdout)
            self.assertEqual(result["status"], "waiting")
            self.assertEqual(result["job"], "invent")
            self.assertEqual(result["needs"][0]["capability"], "industrial-design")

    def test_existing_taste_conflicts_and_unsafe_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            collection = root / "inventors"
            collection.mkdir()
            source = root / "source" / "TASTE.md"
            source.parent.mkdir()
            source.write_text(
                "---\n"
                "name: Mira\n"
                "description: Choose Mira for moving poetry; not static miniatures.\n"
                "---\n\n"
                "# Taste\n\nMotion should carry the idea.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "name conflicts"):
                create_inventor(
                    collection,
                    "wrong-name",
                    "Someone Else",
                    lane="moving-machines",
                    taste_path=source,
                )
            self.assertFalse((collection / "wrong-name").exists())

            alias = root / "alias" / "TASTE.md"
            alias.parent.mkdir()
            alias.symlink_to(source)
            with self.assertRaisesRegex(ContractError, "regular file named TASTE.md"):
                create_inventor(
                    collection,
                    "linked-taste",
                    lane="moving-machines",
                    taste_path=alias,
                )
            self.assertFalse((collection / "linked-taste").exists())

    def test_existing_taste_cannot_change_during_atomic_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            collection = root / "inventors"
            collection.mkdir()
            source = root / "source" / "TASTE.md"
            source.parent.mkdir()
            source.write_text(
                "---\n"
                "name: Mira\n"
                "description: Choose Mira for moving poetry; not static miniatures.\n"
                "---\n\n"
                "# Taste\n\nMotion should carry the idea.\n",
                encoding="utf-8",
            )

            def mutate_after_generated_checks(manifest):
                del manifest
                source.write_text(
                    source.read_text(encoding="utf-8") + "Taste changed.\n",
                    encoding="utf-8",
                )
                return []

            with mock.patch(
                "inventor_workshop.contribution.run_declared_checks",
                side_effect=mutate_after_generated_checks,
            ), self.assertRaisesRegex(ContractError, "changed during Inventor creation"):
                create_inventor(
                    collection,
                    "changing-taste",
                    lane="moving-machines",
                    taste_path=source,
                )
            self.assertFalse((collection / "changing-taste").exists())
            self.assertEqual(tuple(collection.glob(".changing-taste.*")), ())

    def test_generated_package_layout_contains_a_runnable_exact_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source" / "TASTE.md"
            source.parent.mkdir()
            exact_taste = (
                "---\n"
                "name: Nori\n"
                "description: Choose Nori for surprising tiny worlds; not games or mechanisms.\n"
                "---\n\n"
                "# Nori's Taste\n\nMake every scene reveal a private joke.\n"
            ).encode("utf-8")
            source.write_bytes(exact_taste)
            collection = root / "inventors"
            collection.mkdir()
            destination = create_inventor(
                collection,
                "nori",
                lane="little-worlds",
                taste_path=source,
                run_checks=False,
            )
            target = root / "installed"
            package = target / "nori"
            shutil.copytree(destination / "src/nori", package)
            identity = package / "_identity/nori"
            identity.mkdir(parents=True)
            for filename in ("inventor.json", "TASTE.md", "run.py"):
                shutil.copy2(destination / filename, identity / filename)
            self.assertEqual((identity / "TASTE.md").read_bytes(), exact_taste)
            packaged_manifest = load_manifest(identity / "inventor.json")
            self.assertEqual(
                tuple(packaged_manifest.entrypoint), ("python3", "run.py")
            )
            self.assertIn(
                'for filename in ("inventor.json", "TASTE.md", "run.py")',
                (destination / "setup.py").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (destination / "MANIFEST.in").read_text(encoding="utf-8"),
                "include inventor.json TASTE.md run.py\n",
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join(
                (str(target), str(Path(__file__).resolve().parents[1] / "src"))
            )
            environment["WORKSHOP_AGENT_WORKERS"] = "disabled"
            profile = subprocess.run(
                [sys.executable, str(identity / "run.py"), "profile"],
                cwd=root,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(json.loads(profile.stdout)["inventor_id"], "nori")

    def test_three_levels_generate_only_the_declared_creative_seams(self):
        cases = (
            ("taste-only", False, False),
            ("custom-make", True, False),
            ("custom-playtest", True, True),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for index, (level, has_make, has_playtest) in enumerate(cases):
                inventor_id = "level-%d" % index
                with self.subTest(level=level):
                    destination = scaffold_inventor(
                        Path(temporary),
                        inventor_id,
                        "Inventor %d" % index,
                        "small desk surprises",
                        lane="moving-machines",
                        level=level,
                    )
                    manifest = load_manifest(destination / "inventor.json")
                    self.assertEqual(
                        tuple(manifest.capabilities), ("moving-machines", level)
                    )
                    self.assertNotIn("wish", manifest.capabilities)
                    hook = destination / "src" / inventor_id.replace("-", "_") / "inventor.py"
                    self.assertEqual(hook.exists(), has_make)
                    rpc_hook = destination / "hook.py"
                    self.assertEqual(rpc_hook.exists(), has_make)
                    if hook.exists():
                        source = hook.read_text(encoding="utf-8")
                        self.assertIn("def make(", source)
                        self.assertEqual("def playtest(" in source, has_playtest)
                        self.assertIn("WaitingFor", source)
                        self.assertIn("context.playtest_rounds", source)
                        rpc_source = rpc_hook.read_text(encoding="utf-8")
                        self.assertIn("contribution_hook_main", rpc_source)
                        self.assertIn("make=make", rpc_source)
                        self.assertEqual(
                            "playtest=playtest" in rpc_source, has_playtest
                        )
                        self.assertNotIn("Workshop(", rpc_source)
                        self.assertIn(
                            "hook.py",
                            (destination / "MANIFEST.in").read_text(encoding="utf-8"),
                        )
                        setup = (destination / "setup.py").read_text(encoding="utf-8")
                        self.assertIn('destination / "contribution_src"', setup)
                        self.assertIn('"hook.py"', setup)
                    for source in sorted(destination.rglob("*.py")):
                        compile(source.read_text(encoding="utf-8"), str(source), "exec")

                    package = inventor_id.replace("-", "_")
                    environment = self.environment(destination)
                    observed = subprocess.run(
                        [sys.executable, "-m", package, "profile"],
                        cwd=str(destination),
                        env=environment,
                        check=True,
                        stdout=subprocess.PIPE,
                        text=True,
                    )
                    self.assertEqual(
                        json.loads(observed.stdout)["customization_level"], level
                    )
                    run = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            package,
                            "run",
                            "waiting-product",
                            "I wish for a playful desk companion",
                        ],
                        cwd=str(destination),
                        env=environment,
                        check=True,
                        stdout=subprocess.PIPE,
                        text=True,
                    )
                    need = json.loads(run.stdout)["needs"][0]["capability"]
                    self.assertEqual(need, "industrial-design")

    def test_custom_package_identity_carries_the_bounded_hook_and_exact_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            destination = scaffold_inventor(
                root / "source",
                "packed-custom",
                "Packed Custom",
                "custom playful motion",
                lane="moving-machines",
                level="custom-playtest",
            )
            build_lib = root / "build-lib"
            identity = build_lib / "packed_custom/_identity/packed-custom"
            identity.mkdir(parents=True)
            for filename in ("inventor.json", "TASTE.md", "run.py", "hook.py"):
                shutil.copy2(destination / filename, identity / filename)
            shutil.copytree(
                destination / "src/packed_custom",
                identity / "contribution_src/packed_custom",
            )
            setup_source = (destination / "setup.py").read_text(encoding="utf-8")
            compile(setup_source, str(destination / "setup.py"), "exec")
            self.assertIn(
                'for filename in ("inventor.json", "TASTE.md", "run.py", "hook.py")',
                setup_source,
            )
            self.assertIn('destination / "contribution_src"', setup_source)
            self.assertTrue((identity / "hook.py").is_file())
            self.assertEqual(
                (identity / "hook.py").read_bytes(),
                (destination / "hook.py").read_bytes(),
            )
            packaged_source = (
                identity / "contribution_src/packed_custom/inventor.py"
            )
            self.assertTrue(packaged_source.is_file())
            self.assertEqual(
                packaged_source.read_bytes(),
                (destination / "src/packed_custom/inventor.py").read_bytes(),
            )
            self.assertEqual(
                tuple(load_manifest(identity / "inventor.json").capabilities),
                ("moving-machines", "custom-playtest"),
            )

    def test_scaffold_rejects_unknown_scope_and_unsafe_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for inventor_id in (
                "a",
                "class",
                "inventor-workshop",
                "tests",
                "json",
                "foo--bar",
                "foo-",
            ):
                with self.subTest(inventor_id=inventor_id), self.assertRaises(ContractError):
                    scaffold_inventor(
                        root,
                        inventor_id,
                        "Ada",
                        "word games",
                        lane="invented-games",
                    )
            with self.assertRaises(ContractError):
                scaffold_inventor(
                    root,
                    "safe-id",
                    "Ada\nInjected",
                    "word games",
                    lane="invented-games",
                )
            with self.assertRaisesRegex(ContractError, "lane"):
                scaffold_inventor(root, "no-lane", "Ada", "word games")
            with self.assertRaisesRegex(ContractError, "lane"):
                scaffold_inventor(
                    root, "bad-lane", "Ada", "word games", lane="organizer"
                )
            with self.assertRaisesRegex(ContractError, "level"):
                scaffold_inventor(
                    root,
                    "bad-level",
                    "Ada",
                    "word games",
                    lane="invented-games",
                    level="everything",
                )
            with self.assertRaisesRegex(ContractError, "conflicts"):
                scaffold_inventor(
                    root,
                    "conflict",
                    "Ada",
                    "word games",
                    lane="moving-machines",
                    template="board-game",
                )
            destination = scaffold_inventor(
                root, "existing", "Ada", "word games", lane="invented-games"
            )
            self.assertTrue(destination.is_dir())
            with self.assertRaises(StateConflict):
                scaffold_inventor(
                    root, "existing", "Ada", "word games", lane="invented-games"
                )

    def test_legacy_template_maps_to_a_toy_lane_without_entering_help_surface(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "legacy-game",
                "Ada",
                "word games",
                template="board-game",
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertIn("invented-games", manifest.capabilities)
            self.assertIn("taste-only", manifest.capabilities)

    def test_scaffold_quotes_display_text_and_person_wish_stays_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "quote-toys",
                'Ada "The Inventor"',
                'tiny "word" toys with \\ paths',
                lane="little-worlds",
            )
            for source in sorted(destination.rglob("*.py")):
                compile(source.read_text(encoding="utf-8"), str(source), "exec")
            manifest = load_manifest(destination / "inventor.json")
            header = load_taste_header(destination)
            self.assertEqual(header.name, 'Ada "The Inventor"')
            self.assertIn('tiny "word" toys with \\ paths', header.description)
            self.assertIn('tiny "word" toys', (destination / "TASTE.md").read_text())

            environment = self.environment(destination)
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from quote_toys.__main__ import create_wish; "
                        "print(create_wish('quoted', 'My exact wish').objective)"
                    ),
                ],
                cwd=temporary,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(observed.stdout.strip(), "My exact wish")

    def test_manifested_taste_only_profile_cannot_inject_shared_stage_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "hostile-tools",
                "Hostile Tools",
                "attempted shared-stage substitution",
                lane="moving-machines",
                level="taste-only",
            )
            marker = destination / "invent-ran"
            hostile = destination / "hostile_profile.py"
            hostile.write_text(
                "from pathlib import Path\n"
                "from inventor_workshop import Workshop, WorkshopTools\n"
                "root = Path(__file__).resolve().parent\n"
                "def stolen_invent(context):\n"
                "    del context\n"
                "    (root / 'invent-ran').write_text('bad', encoding='utf-8')\n"
                "Workshop(root, 'moving-machines', "
                "tools=WorkshopTools(invent=stolen_invent), "
                "runtime_root=root / '.workshop')\n",
                encoding="utf-8",
            )
            observed = subprocess.run(
                [sys.executable, str(hostile)],
                cwd=destination,
                env=self.environment(destination),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotEqual(observed.returncode, 0)
            self.assertIn(
                "manifested Inventors cannot supply raw WorkshopTools",
                observed.stderr,
            )
            self.assertFalse(marker.exists())

    def test_manifest_contribution_level_is_the_only_custom_seam_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            taste_only = scaffold_inventor(
                root,
                "hostile-hooks",
                "Hostile Hooks",
                "attempted undeclared hooks",
                lane="moving-machines",
                level="taste-only",
            )
            from inventor_workshop.workshop import Workshop

            forbidden = mock.Mock(name="undeclared-make")
            with self.assertRaisesRegex(
                ContractError, "do not match its declared taste-only level"
            ):
                Workshop(
                    taste_only,
                    "moving-machines",
                    make=forbidden,
                    runtime_root=taste_only / ".workshop-hostile",
                )
            forbidden.assert_not_called()

            custom_make = scaffold_inventor(
                root,
                "declared-make",
                "Declared Make",
                "one declared Make seam",
                lane="moving-machines",
                level="custom-make",
            )
            with self.assertRaisesRegex(
                ContractError, "do not match its declared custom-make level"
            ):
                Workshop(
                    custom_make,
                    "moving-machines",
                    runtime_root=custom_make / ".workshop-missing-hook",
                )
            with self.assertRaisesRegex(
                ContractError, "custom Playtest requires custom Make"
            ):
                Workshop(
                    custom_make,
                    "moving-machines",
                    playtest=forbidden,
                    runtime_root=custom_make / ".workshop-playtest-only",
                )

    def test_generated_profile_supports_the_structured_manager_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "handoff-toys",
                "Ada",
                "small exact toys",
                lane="little-worlds",
            )
            source = (
                destination / "src/handoff_toys/__main__.py"
            ).read_text(encoding="utf-8")
            self.assertIn("--assignment-stdin", source)
            self.assertIn("read_manager_assignment", source)
            self.assertIn("bind_manager_assignment_result", source)
            self.assertEqual(source.count("handoff.assert_inventor_current"), 2)
            self.assertIn("expected_inventor_id=INVENTOR_ID", source)
            self.assertNotIn("INVENTOR_ROOT", source)
            self.assertIn("identity = inventor_root()", source)
            self.assertIn("world_inputs=handoff.world_inputs", source)
            self.assertIn("world_evidence=handoff.world_evidence", source)
            self.assertIn('workshop.resume(handoff.wish)', source)
            self.assertIn("resume is an internal Manager-only action", source)
            compile(source, str(destination / "src/handoff_toys/__main__.py"), "exec")

            module_path = destination / "src/handoff_toys/__main__.py"
            spec = importlib.util.spec_from_file_location(
                "generated_handoff_toys", module_path
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            generated = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generated)
            handoff = mock.Mock(unsafe=True)
            handoff.wish = mock.sentinel.wish
            handoff.playtest_rounds = 7
            handoff.world_inputs = mock.sentinel.world_inputs
            handoff.world_evidence = mock.sentinel.world_evidence
            workshop = mock.Mock()
            workshop.run.return_value.to_dict.return_value = {"stage": "invent"}
            with (
                mock.patch.object(
                    generated, "read_manager_assignment", return_value=handoff
                ),
                mock.patch.object(
                    generated, "build_workshop", return_value=workshop
                ) as build_workshop,
                mock.patch.object(
                    generated,
                    "bind_manager_assignment_result",
                    return_value={"stage": "invent", "manager_assignment": {}},
                ),
                mock.patch("builtins.print"),
            ):
                self.assertEqual(
                    generated.main(["run", "--assignment-stdin"]), 0
                )
            build_workshop.assert_called_once_with(
                world_inputs=mock.sentinel.world_inputs,
                world_evidence=mock.sentinel.world_evidence,
            )
            workshop.run.assert_called_once_with(
                mock.sentinel.wish, playtest_rounds=7
            )
            self.assertEqual(handoff.assert_inventor_current.call_count, 2)

    def test_generated_identity_resolves_from_target_like_package_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = scaffold_inventor(
                root / "source",
                "target-games",
                "Ada",
                "word games",
                lane="invented-games",
            )
            target = root / "target"
            package = target / "target_games"
            shutil.copytree(destination / "src/target_games", package)
            identity = package / "_identity/target-games"
            identity.mkdir(parents=True)
            shutil.copy2(destination / "inventor.json", identity / "inventor.json")
            shutil.copy2(destination / "TASTE.md", identity / "TASTE.md")
            away = root / "away"
            away.mkdir()
            core_src = Path(__file__).resolve().parents[1] / "src"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join((str(target), str(core_src)))
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from target_games.__main__ import inventor_root; print(inventor_root())",
                ],
                cwd=away,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(Path(observed.stdout.strip()), identity.resolve())


if __name__ == "__main__":
    unittest.main()
