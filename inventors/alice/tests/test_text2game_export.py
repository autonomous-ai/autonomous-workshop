from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from alice.page_builder import snapshot_project
from alice.text2game_export import (
    REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT,
    REQUIRED_RULES_ARCHIVE_CONTRACT,
    TEXT2GAME_REPOSITORY,
    Text2GameExportConflict,
    Text2GameExportError,
    Text2GameExportRequest,
    canonical_sha256,
    export_text2game_to_vibe,
)


PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082"
)
STL = (
    b"solid fixture\n"
    b"facet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\n"
    b"vertex 0 1 0\nendloop\nendfacet\nendsolid fixture\n"
)
CONCEPT = (
    "Players build a shared river network while privately steering boats toward "
    "their own harbors. Every placement changes the useful routes for everyone "
    "at the table, so a generous connection can also become a precise block. "
    "The printed locks make each route change visible without cards or an app."
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


class Text2GameExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "text2game-output"
        self.workspace = self.root / "vibe-ideas"
        (self.workspace / "board-game" / "ideas").mkdir(parents=True)
        operator = self.workspace / "board-game" / "tools" / "publish.py"
        operator.parent.mkdir(parents=True)
        operator.write_text("# existing rich-draft operator\n", encoding="utf-8")
        write_json(self.workspace / "board-game" / "QUEUE.json", {"ideas": {}})

        setup_text = (
            "Set both docks and all four locks beside the empty river, give each "
            "player a matching harbor marker, then rotate the starting dock toward "
            "the first open channel so every player can see the route that is legal "
            "before the first placement."
        )
        turn_text = "On a turn, place exactly one lock in an open channel."
        end_text = "The game ends after four turns."
        scoring_text = "Score one point per connected dock; the highest score wins."
        ties_text = "Ties go to the player whose dock used fewer locks."
        self.rules_markdown = (
            "# River Locks\n\n"
            f"{setup_text}\n\n{turn_text}\n\n{end_text}\n\n"
            f"{scoring_text}\n\n{ties_text}\n"
        )
        self.rules = {
            "setup": [
                {
                    "text": setup_text,
                    "uses": ["dock", "lock"],
                }
            ],
            "turn": [
                {
                    "text": "On a turn, place exactly one lock in an open channel.",
                    "uses": ["lock"],
                }
            ],
            "legal_actions": [
                {
                    "text": "On a turn, place exactly one lock in an open channel.",
                    "uses": ["lock"],
                }
            ],
            "end": [
                {
                    "text": end_text,
                    "uses": [],
                }
            ],
            "scoring": {
                "text": scoring_text,
                "uses": ["dock"],
            },
            "ties": {
                "text": ties_text,
                "uses": ["dock", "lock"],
            },
            "rules_markdown": self.rules_markdown,
        }
        self.game = {
            "title": "River Locks",
            "concept": CONCEPT,
            "players": {"min": 2, "max": 4},
            "playtime_min": 25,
            "components": [
                {"name": "dock", "qty": 2, "desc": "A player harbor and score marker."},
                {"name": "lock", "qty": 4, "desc": "A channel piece that redirects boats."},
            ],
        }
        self._make_source()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _make_source(self) -> None:
        self.source.mkdir()
        (self.source / "gdd.md").write_text(self.rules_markdown, encoding="utf-8")
        components = [
            {
                "id": "dock",
                "qty": 2,
                "target_bbox_mm": [40, 30, 8],
                "tolerance_mm": 0.3,
            },
            {
                "id": "lock",
                "qty": 4,
                "target_bbox_mm": [30, 20, 6],
                "tolerance_mm": 0.3,
            },
        ]
        write_json(self.source / "components.json", {"components": components})
        write_json(
            self.source / "phase1.json",
            {
                "exit": "clean",
                "priorart": "clear",
                "consistency_high": 0,
                "critic_high": 0,
                "referee_clean": True,
                "referee_missing": False,
            },
        )
        write_json(self.source / "consistency.json", [])
        write_json(self.source / "critic.json", [])
        (self.source / "referee.md").write_text("# Referee\n\nCLEAN\n", encoding="utf-8")
        write_json(self.source / "priorart.json", {"verdict": "clear", "nearest": []})
        write_json(
            self.source / "phase2.json",
            {
                "groups": [
                    {"group": "docks", "parts": ["dock"], "high": 0, "issues": []},
                    {"group": "locks", "parts": ["lock"], "high": 0, "issues": []},
                ],
                "sculptural": [],
                "staged": True,
                "coherence": 8.0,
                "coherence_fail": False,
            },
        )
        gate = {
            "pass": True,
            "fails": [],
            "parts": {
                "dock.stl": {
                    "watertight": True,
                    "bodies": 1,
                    "volume_mm3": 2000.0,
                    "bbox_mm": [40.0, 30.0, 8.0],
                    "print_orientation": "as-modelled",
                    "overhang_pct": 4.0,
                    "bridge_span_mm": 0.0,
                },
                "lock.stl": {
                    "watertight": True,
                    "bodies": 1,
                    "volume_mm3": 900.0,
                    "bbox_mm": [30.0, 20.0, 6.0],
                    "print_orientation": "as-modelled",
                    "overhang_pct": 3.0,
                    "bridge_span_mm": 0.0,
                },
            },
        }
        slice_report = {
            "parts": [
                {
                    "part": "dock",
                    "qty": 2,
                    "grams_each": 20.0,
                    "seconds_each": 1800,
                    "grams_total": 40.0,
                    "seconds_total": 3600,
                },
                {
                    "part": "lock",
                    "qty": 4,
                    "grams_each": 10.0,
                    "seconds_each": 900,
                    "grams_total": 40.0,
                    "seconds_total": 3600,
                },
            ],
            "failed": [],
            "total_grams": 80.0,
            "total_seconds": 7200,
            "total_print_time": "2h00m",
            "spool_1kg_pct": 8.0,
            "profile": "/profiles/petg.ini",
            "slicer": "/usr/bin/prusa-slicer",
        }
        write_json(self.source / "gate.json", gate)
        write_json(self.source / "slice_report.json", slice_report)
        write_json(
            self.source / "phase3.json",
            {
                "gate": gate,
                "fit_ok": True,
                "plates": 2,
                "unplaceable": [],
                "slice": slice_report,
                "howto_spec": True,
                "open_questions": 0,
            },
        )
        write_json(self.source / "plates.json", [{"designs": ["dock"]}, {"designs": ["lock"]}])
        (self.source / "rulebook.md").write_text(self.rules_markdown, encoding="utf-8")
        (self.source / "print_kit.md").write_text("# Print kit\n\nMeasured.\n", encoding="utf-8")
        (self.source / "art_direction.md").write_text(
            "# River stone and brass\n", encoding="utf-8"
        )
        write_json(self.source / "part_colors.json", {"dock": "#555555", "lock": "#ffaa00"})
        renders = self.source / "renders"
        renders.mkdir()
        (renders / "assembled.png").write_bytes(PNG)
        (self.source / "assembled.stl").write_bytes(STL)
        (self.source / "assembled.step").write_text(
            "ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n", encoding="ascii"
        )
        parts = self.source / "parts"
        meshes = self.source / "fe_parts"
        gcode = self.source / "gcode"
        parts.mkdir()
        meshes.mkdir()
        gcode.mkdir()
        (parts / "__init__.py").write_text("", encoding="utf-8")
        for part in ("dock", "lock"):
            (parts / f"{part}.py").write_text(
                f"def build():\n    return {part!r}\n", encoding="utf-8"
            )
            (meshes / f"{part}.stl").write_bytes(STL)
            (gcode / f"{part}.gcode").write_text("; generated by fixture\nG28\n", encoding="utf-8")

    def request(self) -> Text2GameExportRequest:
        hashes = file_hashes(self.source)
        return Text2GameExportRequest(
            source_dir=self.source,
            vibe_workspace=self.workspace,
            production_slug="river-locks",
            candidate_id="candidate-river-locks",
            candidate_version=3,
            candidate_content_sha256="c" * 64,
            accepted_game=self.game,
            accepted_rules=self.rules,
            accepted_rules_sha256=canonical_sha256(self.rules),
            cad_artifact_hashes=hashes,
            dfm_artifact_hashes=hashes,
            source_repo_url=TEXT2GAME_REPOSITORY,
            source_repo_commit="a" * 40,
        )

    def test_exports_exact_vibe_workspace_without_queue_or_publish_effect(self) -> None:
        queue = self.workspace / "board-game" / "QUEUE.json"
        queue_before = queue.read_bytes()

        receipt = export_text2game_to_vibe(self.request())

        destination = self.workspace / "board-game" / "ideas" / "river-locks"
        project = destination / "project"
        self.assertEqual(receipt.destination, destination.resolve())
        self.assertEqual(queue.read_bytes(), queue_before)
        self.assertFalse((destination / "published.json").exists())
        self.assertEqual((project / "RULES.md").read_bytes(), self.rules_markdown.encode())
        self.assertEqual((project / "river-locks.stl").read_bytes(), STL)
        self.assertTrue((project / "river-locks.step").is_file())
        self.assertTrue((project / "_text2game" / "source" / "parts" / "dock.py").is_file())
        self.assertTrue((project / "part_colors.json").is_file())
        self.assertFalse((project / "gcode").exists())
        self.assertTrue((project / "river-locks_review" / "_assembled.png").is_file())
        self.assertFalse((project / "river-locks_review" / "_qa.png").exists())

        idea = json.loads((destination / "idea.json").read_text(encoding="utf-8"))
        self.assertEqual(
            (destination / "idea.json").read_bytes(),
            (project / "_text2game" / "vibe-idea.json").read_bytes(),
        )
        self.assertEqual(idea["slug"], "river-locks")
        self.assertEqual(idea["rules"]["turn"][0]["text"], self.rules["turn"][0]["text"])
        self.assertEqual(
            idea["components"],
            [
                {"name": "dock", "qty": 2, "desc": "A player harbor and score marker."},
                {"name": "lock", "qty": 4, "desc": "A channel piece that redirects boats."},
            ],
        )
        gate = json.loads((project / "gate.json").read_text(encoding="utf-8"))
        self.assertTrue(gate["pass"])
        self.assertEqual(gate["part_count"], 6)
        self.assertEqual(gate["slice"]["total_grams"], 80.0)

        snapshot = snapshot_project(project)
        self.assertEqual(receipt.project_sha256, snapshot.project_sha256)
        self.assertEqual(
            receipt.artifact_hashes,
            {item["path"]: item["sha256"] for item in snapshot.files},
        )
        lineage = receipt.page_builder_lineage()
        self.assertEqual(lineage["project_sha256"], snapshot.project_sha256)
        self.assertEqual(lineage["artifact_hashes"], receipt.artifact_hashes)
        self.assertEqual(lineage["candidate_id"], "candidate-river-locks")
        self.assertEqual(lineage["candidate_version"], 3)
        self.assertEqual(lineage["candidate_content_sha256"], "c" * 64)
        self.assertEqual(
            lineage["vibe_idea_sha256"],
            hashlib.sha256((destination / "idea.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            lineage["text2game_source_artifact_hashes"],
            receipt.source_artifact_hashes,
        )
        self.assertEqual(
            receipt.source_artifact_hashes_sha256,
            canonical_sha256(dict(receipt.source_artifact_hashes)),
        )
        with self.assertRaises(TypeError):
            receipt.artifact_hashes["forged.stl"] = "f" * 64  # type: ignore[index]
        receipt_file = json.loads(
            (destination / ".alice-text2game-export.json").read_text(encoding="utf-8")
        )
        self.assertFalse(receipt_file["handoff"]["vibe_queue_transition_performed"])
        self.assertFalse(receipt_file["handoff"]["vibe_queue_transition_required"])
        self.assertTrue(
            receipt_file["handoff"]["publisher_exact_rules_passthrough_required"]
        )
        self.assertEqual(
            receipt_file["handoff"]["publisher_rules_archive_contract"],
            REQUIRED_RULES_ARCHIVE_CONTRACT,
        )
        self.assertEqual(
            receipt_file["handoff"]["publisher_alice_draft_handoff_contract"],
            REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT,
        )
        provenance = json.loads(
            (project / "alice-text2game-provenance.json").read_text(encoding="utf-8")
        )
        self.assertFalse(provenance["effects"]["publisher_invoked"])
        self.assertFalse(provenance["effects"]["queue_mutated"])

    def test_identical_rerun_is_a_noop_but_mismatched_destination_conflicts(self) -> None:
        first = export_text2game_to_vibe(self.request())
        snapshot_before = file_hashes(first.destination)
        second = export_text2game_to_vibe(self.request())
        self.assertEqual(second.project_sha256, first.project_sha256)
        self.assertEqual(file_hashes(first.destination), snapshot_before)

        (first.destination / "idea.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(Text2GameExportConflict, "different export"):
            export_text2game_to_vibe(self.request())

    def test_uses_real_hero_as_cover_and_assembled_sheet_as_qa(self) -> None:
        hero = self.source / "renders" / "hero.png"
        hero.write_bytes(PNG + b"-hero")
        receipt = export_text2game_to_vibe(self.request())
        review = receipt.destination / "project" / "river-locks_review"
        self.assertEqual((review / "_assembled.png").read_bytes(), PNG + b"-hero")
        self.assertEqual((review / "_qa.png").read_bytes(), PNG)

    def test_rejects_rule_hash_or_unstructured_authority(self) -> None:
        with self.assertRaisesRegex(Text2GameExportError, "rules_sha256"):
            export_text2game_to_vibe(
                replace(self.request(), accepted_rules_sha256="d" * 64)
            )
        bad = dict(self.rules)
        bad["setup"] = "put it together"
        with self.assertRaisesRegex(Text2GameExportError, "setup"):
            export_text2game_to_vibe(
                replace(
                    self.request(),
                    accepted_rules=bad,
                    accepted_rules_sha256=canonical_sha256(bad),
                )
            )

    def test_rejects_gdd_drift_from_exact_accepted_rules(self) -> None:
        (self.source / "gdd.md").write_text(self.rules_markdown + "Changed.\n", encoding="utf-8")
        with self.assertRaisesRegex(Text2GameExportError, "byte-for-byte"):
            export_text2game_to_vibe(self.request())

    def test_rejects_cad_dfm_disagreement_and_source_hash_mismatch(self) -> None:
        request = self.request()
        dfm = dict(request.dfm_artifact_hashes)
        dfm["assembled.stl"] = "f" * 64
        with self.assertRaisesRegex(Text2GameExportError, "did not accept"):
            export_text2game_to_vibe(replace(request, dfm_artifact_hashes=dfm))

        cad = dict(request.cad_artifact_hashes)
        cad["assembled.stl"] = "e" * 64
        with self.assertRaisesRegex(Text2GameExportError, "hash mismatch"):
            export_text2game_to_vibe(
                replace(request, cad_artifact_hashes=cad, dfm_artifact_hashes=cad)
            )

    def test_rejects_failed_or_ambiguous_upstream_gates(self) -> None:
        cases = [
            ("phase1.json", "exit", "rounds-exhausted", "phase1"),
            ("phase2.json", "coherence_fail", True, "coherence"),
            ("gate.json", "pass", None, "gate.json"),
            ("phase3.json", "fit_ok", None, "fit"),
            ("slice_report.json", "failed", [{"part": "lock"}], "slice"),
        ]
        for index, (filename, key, value, message) in enumerate(cases):
            with self.subTest(filename=filename):
                if index:
                    self.tearDown()
                    self.setUp()
                path = self.source / filename
                data = json.loads(path.read_text(encoding="utf-8"))
                data[key] = value
                write_json(path, data)
                with self.assertRaisesRegex(Text2GameExportError, message):
                    export_text2game_to_vibe(self.request())

    def test_rejects_symlinks_and_unsafe_hash_paths(self) -> None:
        target = self.source / "outside.txt"
        target.write_text("outside\n", encoding="utf-8")
        (self.source / "linked.txt").symlink_to(target)
        with self.assertRaisesRegex(Text2GameExportError, "symlink"):
            export_text2game_to_vibe(self.request())

        (self.source / "linked.txt").unlink()
        request = self.request()
        unsafe = dict(request.cad_artifact_hashes)
        unsafe["../outside"] = "a" * 64
        with self.assertRaisesRegex(Text2GameExportError, "unsafe"):
            export_text2game_to_vibe(
                replace(request, cad_artifact_hashes=unsafe, dfm_artifact_hashes=unsafe)
            )

    def test_rejects_credential_like_artifacts_and_unrich_page_rules(self) -> None:
        request = self.request()
        sensitive = dict(request.cad_artifact_hashes)
        sensitive[".env"] = "a" * 64
        with self.assertRaisesRegex(Text2GameExportError, "credential-like"):
            export_text2game_to_vibe(
                replace(request, cad_artifact_hashes=sensitive, dfm_artifact_hashes=sensitive)
            )

        short = dict(self.rules)
        short_setup = {"text": "Set the docks beside the river.", "uses": ["dock"]}
        short["setup"] = [short_setup]
        short["rules_markdown"] = (
            "# River Locks\n\nSet the docks beside the river.\n\n"
            f"{short['turn'][0]['text']}\n\n{short['end'][0]['text']}\n\n"
            f"{short['scoring']['text']}\n\n{short['ties']['text']}\n"
        )
        (self.source / "gdd.md").write_text(short["rules_markdown"], encoding="utf-8")
        with self.assertRaisesRegex(Text2GameExportError, "story block"):
            export_text2game_to_vibe(
                replace(
                    self.request(),
                    accepted_rules=short,
                    accepted_rules_sha256=canonical_sha256(short),
                )
            )

    def test_does_not_require_text2game_to_invent_a_root_main_file(self) -> None:
        self.assertFalse((self.source / "main.py").exists())
        receipt = export_text2game_to_vibe(self.request())
        project = receipt.destination / "project"
        bridge = (project / "main.py").read_text(encoding="utf-8")
        self.assertIn("def gen_step", bridge)
        self.assertIn("importStep", bridge)
        manifest = json.loads((project / "cad_project.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["entrypoint"], {"path": "main.py", "callable": "gen_step"})
        self.assertEqual(
            manifest["model"]["parts"][0]["source"],
            "_text2game/source/parts/dock.py",
        )


if __name__ == "__main__":
    unittest.main()
