from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from alice.adapters import AdapterError, AdapterReceipt
from alice.engine import _validate_action_semantics, _validate_adapter_payload_shape
from alice.loops import OUTPUT_CONTRACTS, validate_output_semantics
from alice.store import DurableStore
from alice.text2game_adapter import (
    AmbiguousText2GameEffect,
    Text2GameAdapterError,
    Text2GamePhysicalAdapter,
)
from alice.text2game_export import canonical_sha256
import alice.text2game_adapter as text2game_adapter_module


PNG_HEX = (
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082"
)
TETRA_STL = """solid tetra
facet normal 0 0 -1
outer loop
vertex 0 0 0
vertex 0 1 0
vertex 1 0 0
endloop
endfacet
facet normal 0 -1 0
outer loop
vertex 0 0 0
vertex 1 0 0
vertex 0 0 1
endloop
endfacet
facet normal -1 0 0
outer loop
vertex 0 0 0
vertex 0 0 1
vertex 0 1 0
endloop
endfacet
facet normal 1 1 1
outer loop
vertex 1 0 0
vertex 0 1 0
vertex 0 0 1
endloop
endfacet
endsolid tetra
"""
CONCEPT = (
    "Players build a shared river network while privately steering boats toward "
    "their own harbors. Every placement changes the useful routes for everyone "
    "at the table, so a generous connection can also become a precise block. "
    "The printed locks make each route change visible without cards or an app."
)


FAKE_TEXT2GAME = r'''#!/usr/bin/env python3
import argparse, json, os, shutil
from pathlib import Path

PNG = bytes.fromhex("''' + PNG_HEX + r'''")
STL = ''' + repr(TETRA_STL) + r'''.encode("ascii")

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

parser = argparse.ArgumentParser()
parser.add_argument("--slug", required=True)
parser.add_argument("--phase", choices=["1", "2", "3"], required=True)
parser.add_argument("--max-rounds")
args = parser.parse_args()
root = Path(__file__).resolve().parent / "out" / args.slug
if not (Path.home() / ".codex" / "auth.json").is_file():
    raise SystemExit("fixture mirrors text2game codex_ready preflight")
if os.environ.get("CODEX_FALLBACK") != "0":
    raise SystemExit("Claude fallback must remain disabled")
if os.environ.get("MEASURE_CMD") != "alice-measure":
    raise SystemExit("measure must use the pinned CAD shim")
if not (shutil.which("uv") or "").endswith("/.local/bin/uv"):
    raise SystemExit("uv must resolve to the operation-local deterministic shim")
if not (shutil.which("python") or "").endswith("/.local/bin/python"):
    raise SystemExit("python must resolve to the pinned CAD interpreter shim")
if not (shutil.which("python3") or "").endswith("/.local/bin/python3"):
    raise SystemExit("python3 must resolve to the pinned CAD interpreter shim")
if os.environ.get("MUTATE_GDD") == "1" and args.phase == "1":
    (root / "gdd.md").write_text("changed rules\n", encoding="utf-8")
if os.environ.get("MUTATE_RUNTIME") == "1" and args.phase == "1":
    runtime = Path(__file__).resolve().parent / "phase2.py"
    runtime.chmod(0o600)
    runtime.write_text("raise SystemExit('mutated runtime executed')\n", encoding="utf-8")
if args.phase == "1":
    write_json(root / "phase1.json", {
        "exit": "clean", "priorart": "clear", "consistency_high": 0,
        "critic_high": 0, "referee_clean": True, "referee_missing": False,
    })
    write_json(root / "consistency.json", [])
    write_json(root / "critic.json", [])
    (root / "referee.md").write_text("# Referee\n\nCLEAN\n", encoding="utf-8")
    write_json(root / "priorart.json", {"verdict": "clear", "nearest": []})
elif args.phase == "2":
    components = json.loads((root / "components.json").read_text(encoding="utf-8"))
    ids = [row["id"] for row in components]
    write_json(root / "phase2.json", {
        "groups": [{"group": part, "parts": [part], "high": 0, "issues": []} for part in ids],
        "sculptural": [], "staged": True, "coherence": 8.0, "coherence_fail": False,
    })
    (root / "renders").mkdir(exist_ok=True)
    (root / "renders" / "assembled.png").write_bytes(PNG)
    (root / "assembled.stl").write_bytes(STL)
    (root / "assembled.step").write_text(
        "ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n", encoding="ascii")
    (root / "parts").mkdir(exist_ok=True)
    (root / "fe_parts").mkdir(exist_ok=True)
    for part in ids:
        (root / "parts" / (part + ".py")).write_text(
            "def build():\n    return " + repr(part) + "\n", encoding="utf-8")
        (root / "fe_parts" / (part + ".stl")).write_bytes(STL)
    write_json(root / "part_colors.json", {
        part: ("#555555" if index == 0 else "#ffaa00")
        for index, part in enumerate(ids)
    })
    (root / "art_direction.md").write_text("# River stone and brass\n", encoding="utf-8")
elif args.phase == "3":
    components = json.loads((root / "components.json").read_text(encoding="utf-8"))
    gate_parts = {}
    slice_parts = []
    (root / "gcode").mkdir(exist_ok=True)
    for row in components:
        part = row["id"]
        gate_parts[part + ".stl"] = {
            "watertight": True, "bodies": 1, "volume_mm3": 1.0,
            "bbox_mm": row["target_bbox_mm"], "print_orientation": "as-modelled",
            "overhang_pct": 0.0, "bridge_span_mm": 0.0,
        }
        slice_parts.append({
            "part": part, "qty": row["qty"], "grams_each": 2.0,
            "seconds_each": 60, "grams_total": 2.0 * row["qty"],
            "seconds_total": 60 * row["qty"],
        })
        (root / "gcode" / (part + ".gcode")).write_text("; fixture\nG28\n", encoding="utf-8")
    gate = {"pass": True, "fails": [], "parts": gate_parts}
    sliced = {
        "parts": slice_parts, "failed": [],
        "total_grams": sum(row["grams_total"] for row in slice_parts),
        "total_seconds": sum(row["seconds_total"] for row in slice_parts),
        "total_print_time": "0h10m", "spool_1kg_pct": 1.0,
        "profile": "/profiles/petg.ini", "slicer": "/usr/bin/prusa-slicer",
    }
    write_json(root / "gate.json", gate)
    write_json(root / "slice_report.json", sliced)
    write_json(root / "phase3.json", {
        "gate": gate, "fit_ok": True, "plates": 1, "unplaceable": [],
        "slice": sliced, "howto_spec": True, "open_questions": 0,
    })
    write_json(root / "plates.json", [{"designs": [row["id"] for row in components]}])
    (root / "rulebook.md").write_bytes((root / "gdd.md").read_bytes())
    (root / "print_kit.md").write_text("# Print kit\n\nMeasured.\n", encoding="utf-8")
'''

FAKE_CONSISTENCY = r'''#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

out = Path(sys.argv[1])
gdd = (out / "gdd.md").read_text(encoding="utf-8")
components = json.loads((out / "components.json").read_text(encoding="utf-8"))
mechanisms = json.loads((out / "mechanisms.json").read_text(encoding="utf-8"))
issues = []
for heading in ("First minute", "Components", "Setup", "Turn structure",
                "Action economy", "Win/lose", "Legacy", "Edge cases"):
    if f"## {heading}" not in gdd:
        issues.append({"severity": "high", "code": "missing-heading", "message": heading})
chosen = mechanisms.get("chosen") or []
allowed = {"blocking_claim", "modular_tiles"}
if not 2 <= len(chosen) <= 3 or not set(chosen) <= allowed:
    issues.append({"severity": "high", "code": "mechanisms", "message": "invalid"})
for row in components:
    part = row["id"]
    if f"`{part}`" not in gdd:
        issues.append({"severity": "high", "code": "component", "message": part})
(out / "consistency.json").write_text(json.dumps(issues), encoding="utf-8")
raise SystemExit(1 if any(x["severity"] == "high" for x in issues) else 0)
'''


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    return result.stdout.strip()


class Text2GameAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "text2game"
        self.repo.mkdir()
        entrypoint = self.repo / "text2game"
        entrypoint.write_text(FAKE_TEXT2GAME, encoding="utf-8")
        entrypoint.chmod(0o755)
        (self.repo / "consistency.py").write_text(
            FAKE_CONSISTENCY, encoding="utf-8"
        )
        (self.repo / "mechanisms.md").write_text(
            "## Vocabulary\n| `blocking_claim` | blocks |\n"
            "| `modular_tiles` | tiles |\n## Permanent change\n",
            encoding="utf-8",
        )
        for name in ("phase2.py", "phase3.py", "slice_parts.py"):
            (self.repo / name).write_text("# pinned fixture\n", encoding="utf-8")
        (self.repo / "harness.py").write_text(
            "HERE = None\n"
            "def _codex_cmd(out_dir):\n"
            "    return [\n"
            "            \"-C\", str(out_dir), \"--add-dir\", str(HERE),\n"
            "            \"--skip-git-repo-check\",\n"
            "    ]\n",
            encoding="utf-8",
        )
        for name in (
            "discover.py", "fit.py", "harvest.py", "plates.py", "prompts.py",
            "render_assembly.py", "scaffold.py", "stage.py", "storyboard.py",
            "taste_boardgame.md", "trace_log.py", "trends.py",
        ):
            (self.repo / name).write_text("# pinned fixture\n", encoding="utf-8")
        (self.repo / "catalog.json").write_text("{}\n", encoding="utf-8")
        (self.repo / "publish.py").write_text(
            "raise SystemExit('legacy publisher must never be copied')\n",
            encoding="utf-8",
        )
        (self.repo / "priorart").mkdir()
        (self.repo / "priorart" / "__init__.py").write_text(
            "# pinned fixture\n", encoding="utf-8"
        )
        (self.repo / "priorart" / "bgg_index.py").write_text(
            "# pinned fixture\n", encoding="utf-8"
        )
        (self.repo / "profiles").mkdir()
        (self.repo / "profiles" / "petg.ini").write_text(
            "# pinned slicer profile\n", encoding="utf-8"
        )
        run_git(self.repo, "init", "-q")
        run_git(self.repo, "config", "user.email", "alice@example.invalid")
        run_git(self.repo, "config", "user.name", "Alice Test")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-qm", "fixture")
        self.commit = run_git(self.repo, "rev-parse", "HEAD")
        self.text2cad = self.root / "text2cad"
        self.text2cad.mkdir()
        for relative in (
            "gate.py",
            "concept_image.py",
            "skills/cadcode/SKILL.md",
            "skills/cadcode/scripts/measure/cli.py",
            "skills/cadcode/scripts/cad/cli.py",
            "gen_howto_video.py",
        ):
            target = self.text2cad / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# pinned text2cad fixture\n", encoding="utf-8")
        (self.text2cad / ".env.bak-fixture").write_text(
            "ADMIN_TOKEN=must-not-be-copied\n", encoding="utf-8"
        )
        run_git(self.text2cad, "init", "-q")
        run_git(self.text2cad, "config", "user.email", "alice@example.invalid")
        run_git(self.text2cad, "config", "user.name", "Alice Test")
        run_git(self.text2cad, "add", ".")
        run_git(self.text2cad, "commit", "-qm", "fixture")
        self.text2cad_commit = run_git(self.text2cad, "rev-parse", "HEAD")

        tools = self.root / "tools"
        tools.mkdir()
        self.interpreter = tools / "python"
        self.interpreter.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = '-I' ] && [ \"${2:-}\" = '-c' ]; then exit 0; fi\n"
            f"exec {sys.executable!r} \"$@\"\n",
            encoding="utf-8",
        )
        self.interpreter.chmod(0o755)
        self.slicer = tools / "prusa-slicer"
        self.codex = tools / "codex"
        for executable in (self.slicer,):
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
        self.codex.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = exec ] && [ \"${2:-}\" = --help ]; then\n"
            "  printf '%s\\n' --ephemeral --ignore-user-config --ignore-rules --strict-config\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        self.codex.chmod(0o755)
        system_git = Path(shutil.which("git") or "")
        self.assertTrue(system_git.is_absolute())
        self.git = tools / "git"
        self.git.write_text(
            f"#!/bin/sh\nexec {str(system_git)!r} \"$@\"\n", encoding="utf-8"
        )
        self.git.chmod(0o755)
        self.slicer_profile = self.root / "petg.ini"
        self.slicer_profile.write_text("# test profile\n", encoding="utf-8")
        self.codex_home = self.root / "codex-home"
        self.codex_home.mkdir(mode=0o700)
        (self.codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
        (self.codex_home / "auth.json").chmod(0o600)
        self.workspace = self.root / "vibe"
        (self.workspace / "board-game" / "ideas").mkdir(parents=True)
        (self.workspace / "board-game" / "tools").mkdir(parents=True)
        (self.workspace / "board-game" / "QUEUE.json").write_text(
            json.dumps({"ideas": {}}), encoding="utf-8"
        )
        (self.workspace / "board-game" / "tools" / "publish.py").write_text(
            "# existing private draft operator\n", encoding="utf-8"
        )
        self.work = self.root / "runs"
        self.work.mkdir(mode=0o700)
        self.store = DurableStore(self.root / "alice.sqlite3")
        self.rules = self._rules()
        self.design = self._design()

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def _rules(self) -> dict[str, object]:
        setup = (
            "Set both docks and all four locks beside the empty river, give each "
            "player a matching harbor marker, then rotate the starting dock toward "
            "the first open channel so every player can see the route that is legal "
            "before the first placement."
        )
        turn = "On a turn, place exactly one lock in an open channel."
        end = "The game ends after four turns."
        scoring = "Score one point per connected dock; the highest score wins."
        ties = "Ties go to the player whose dock used fewer locks."
        markdown = (
            "# River Locks\n\n"
            "## First minute\n\nPlace one `lock` beside a `dock`; each choice closes "
            "one route and opens another.\n\n"
            "## Components\n\n- Two `dock` pieces.\n- Four `lock` pieces.\n\n"
            f"## Setup\n\n- {setup}\n\n"
            f"## Turn structure\n\n{turn} The `lock` must connect to a `dock`.\n\n"
            "## Action economy\n\nChoose one open channel, then place one `lock` at one "
            "`dock`; take no second action.\n\n"
            f"## Win/lose\n\n{end} {scoring} {ties}\n\n"
            "## Legacy\n\nThe `dock` and `lock` positions reset after scoring; no "
            "state persists between games.\n\n"
            "## Edge cases\n\nIf no channel is open, pass; if one is open, place the "
            "`lock` beside that `dock`.\n"
        )
        document = {
            "setup": [{"text": setup, "uses": ["dock", "lock"]}],
            "turn": [{"text": turn, "uses": ["lock"]}],
            "legal_actions": [{"text": turn, "uses": ["lock"]}],
            "end": [{"text": end, "uses": []}],
            "scoring": {"text": scoring, "uses": ["dock"]},
            "ties": {"text": ties, "uses": ["dock", "lock"]},
            "rules_markdown": markdown,
        }
        return {**document, "rules_sha256": canonical_sha256(document)}

    def _design(self) -> dict[str, object]:
        candidate_hash = "c" * 64
        components = [
            {
                "id": "dock", "qty": 2, "role": "harbor", "class": "functional",
                "duty": "holds a marker", "tolerance_mm": 0.3,
                "target_bbox_mm": [40, 30, 8], "mates_with": ["lock"],
                "stores_in": "self", "rules_carrier": True, "signature": True,
            },
            {
                "id": "lock", "qty": 4, "role": "channel", "class": "functional",
                "duty": "redirects a route", "tolerance_mm": 0.3,
                "target_bbox_mm": [30, 20, 6], "mates_with": ["dock"],
                "stores_in": "dock", "rules_carrier": False, "signature": False,
            },
        ]
        return {
            "schema_version": "alice.physical-design.v1",
            "candidate_id": "candidate-river",
            "candidate_version": 3,
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": self.rules["rules_sha256"],
            "production_slug": "river-locks-" + candidate_hash[:12],
            "accepted_game": {
                "title": "River Locks", "concept": CONCEPT,
                "players": {"min": 2, "max": 4}, "playtime_min": 25,
                "components": [
                    {"name": "dock", "qty": 2, "desc": "A player harbor and marker."},
                    {"name": "lock", "qty": 4, "desc": "A channel that redirects boats."},
                ],
            },
            "text2game": {
                "mechanisms": {
                    "chosen": ["blocking_claim", "modular_tiles"],
                    "interaction": "Each lock occupies a route another player needs.",
                    "notes": "",
                },
                "components": components,
            },
            "fit_requirements": [
                {"id": "dock-lock", "kind": "assembled", "parts": ["dock", "lock"],
                 "fit_class": "sliding", "owned_side": "male", "owned_dimension_mm": 8.0}
            ],
            "topology_expectations": [
                {"part_id": "dock", "expected_shell_count": 1},
                {"part_id": "lock", "expected_shell_count": 1},
            ],
            "motion_conditions": [],
            "open_items": [],
        }

    def _profile(self) -> dict[str, object]:
        return {
            "profile_id": "profile-1", "revision": 1, "printer_id": "printer-1",
            "nozzle_diameter_mm": 0.4, "layer_height_mm": 0.2, "material": "PETG",
            "calibration_evidence_sha256": "a" * 64,
            "assembled_fits": [{"name": "sliding", "per_side_clearance_mm": 0.2}],
            "print_in_place_fits": [
                {"name": "hinge", "xy_gap_mm": 0.3, "z_gap_mm": 0.4, "bottom_relief_mm": 0.2}
            ],
        }

    def _target(self) -> dict[str, object]:
        return {
            "profile_id": "profile-1", "profile_revision": 1, "printer_id": "printer-1",
            "nozzle_diameter_mm": 0.4, "layer_height_mm": 0.2, "material": "PETG",
        }

    def adapter(self, *, environment: dict[str, str] | None = None) -> Text2GamePhysicalAdapter:
        return Text2GamePhysicalAdapter(
            self.repo, self.commit, self.work, self.workspace, [str(self.interpreter)],
            self._profile(), self._target(), self.store,
            text2cad_repo=self.text2cad,
            text2cad_commit=self.text2cad_commit,
            cad_python=self.interpreter,
            slicer_binary=self.slicer,
            slicer_profile=self.slicer_profile,
            codex_binary=self.codex,
            codex_home=self.codex_home,
            git_binary=self.git,
            environment={"PATH": os.environ.get("PATH", "")} | (environment or {}),
        )

    def cad_payload(self) -> dict[str, object]:
        return {
            "candidate_id": "candidate-river",
            "candidate_version": 3,
            "candidate_content_sha256": "c" * 64,
            "effect_operation_key": "alice:physical-effect:v1:fixture",
            "task_input_sha256": "d" * 64,
            "dependencies": {
                "physical.design": {
                    "result": {"executor": "agent", "response": {"content": self.design}}
                }
            },
            "accepted_artifacts": [
                {"action": "candidate.rules", "content": self.rules}
            ],
        }

    def test_full_cad_dfm_export_is_isolated_and_reconcilable(self) -> None:
        adapter = self.adapter()
        payload = self.cad_payload()
        original = text2game_adapter_module.run_bounded_process
        phase_homes: list[str] = []
        phase_text2cad_dirs: list[str] = []

        def capture_home(command, **kwargs):
            if len(command) > 1 and str(command[1]).endswith("/text2game"):
                phase_homes.append(kwargs["env"]["HOME"])
                phase_text2cad_dirs.append(kwargs["env"]["TEXT2CAD_DIR"])
            return original(command, **kwargs)

        with patch(
            "alice.text2game_adapter.run_bounded_process", side_effect=capture_home
        ):
            cad = adapter.invoke("physical.cad", payload)

        self.assertIsInstance(cad, AdapterReceipt)
        self.assertEqual(cad.status, "passed")
        self.assertEqual(cad.payload["rules_sha256"], self.rules["rules_sha256"])
        self.assertFalse((self.repo / "out").exists())
        operation_id = hashlib.sha256(
            b"alice:physical-effect:v1:fixture"
        ).hexdigest()[:32]
        copied_skill = (
            self.work
            / operation_id
            / "home"
            / ".claude"
            / "skills"
            / "cadcode"
            / "SKILL.md"
        )
        self.assertEqual(
            copied_skill.read_bytes(),
            (self.text2cad / "skills" / "cadcode" / "SKILL.md").read_bytes(),
        )
        self.assertEqual(copied_skill.stat().st_mode & 0o777, 0o400)
        self.assertEqual(phase_homes, [str(copied_skill.parents[3])] * 3)
        preflight_marker = copied_skill.parents[3] / ".codex" / "auth.json"
        self.assertEqual(
            json.loads(preflight_marker.read_text(encoding="utf-8")),
            {
                "schema_version": "alice.codex-preflight-marker.v1",
                "credential_source": "CODEX_HOME",
            },
        )
        self.assertNotEqual(
            preflight_marker.read_bytes(),
            (self.codex_home / "auth.json").read_bytes(),
        )
        self.assertEqual(preflight_marker.stat().st_mode & 0o777, 0o600)
        operation_text2cad = self.work / operation_id / "toolchain" / "text2cad"
        self.assertEqual(
            phase_text2cad_dirs,
            [str(operation_text2cad)] * 3,
        )
        self.assertEqual(
            (operation_text2cad / "gate.py").read_bytes(),
            (self.text2cad / "gate.py").read_bytes(),
        )
        operation_repo = self.work / operation_id / "repo"
        self.assertFalse((operation_repo / "publish.py").exists())
        self.assertFalse((operation_text2cad / ".env.bak-fixture").exists())
        hardened_harness = (operation_repo / "harness.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('"--add-dir", str(HERE)', hardened_harness)
        for flag in ("--ephemeral", "--ignore-user-config", "--ignore-rules"):
            self.assertIn(flag, hardened_harness)
        project = self.workspace / "board-game" / "ideas" / self.design["production_slug"] / "project"
        self.assertEqual((project / "RULES.md").read_text(), self.rules["rules_markdown"])
        self.assertEqual(json.loads((self.workspace / "board-game" / "QUEUE.json").read_text()), {"ideas": {}})

        reconcile = dict(payload)
        reconcile["reconcile_only"] = True
        cached = adapter.invoke("physical.reconcile_cad", reconcile)
        self.assertEqual(cached.payload, cad.payload)

        dfm_payload = {
            "dependencies": {
                "physical.design": {
                    "result": {"executor": "agent", "response": {"content": self.design}}
                },
                "physical.cad": {
                    "result": {
                        "executor": "adapter",
                        "receipt": {"status": "passed", "payload": cad.payload},
                    }
                },
            }
        }
        dfm = adapter.invoke("physical.dfm", dfm_payload)
        self.assertTrue(dfm.payload["fit"])
        self.assertEqual(dfm.payload["artifact_hashes"], cad.payload["artifact_hashes"])
        self.assertEqual(dfm.payload["print_yield"], 1.0)
        _validate_adapter_payload_shape(
            "physical.cad", cad.payload, OUTPUT_CONTRACTS["physical.cad"]
        )
        _validate_action_semantics("physical.cad", cad.payload)
        _validate_adapter_payload_shape(
            "physical.dfm", dfm.payload, OUTPUT_CONTRACTS["physical.dfm"]
        )
        _validate_action_semantics("physical.dfm", dfm.payload)

    def test_physical_design_contract_requires_candidate_unique_slug(self) -> None:
        validate_output_semantics("physical.design", self.design)
        changed = dict(self.design)
        changed["production_slug"] = "river-locks"

        with self.assertRaisesRegex(ValueError, "candidate hash prefix"):
            validate_output_semantics("physical.design", changed)

    def test_rules_mutation_is_never_adopted_or_blindly_retried(self) -> None:
        adapter = self.adapter(environment={"MUTATE_GDD": "1"})
        payload = self.cad_payload()

        with self.assertRaises(Text2GameAdapterError):
            adapter.invoke("physical.cad", payload)
        reconcile = dict(payload)
        reconcile["reconcile_only"] = True
        with self.assertRaises(AmbiguousText2GameEffect):
            adapter.invoke("physical.reconcile_cad", reconcile)

    def test_model_cannot_mutate_trusted_runtime_for_a_later_host_phase(self) -> None:
        adapter = self.adapter(environment={"MUTATE_RUNTIME": "1"})
        payload = self.cad_payload()

        with self.assertRaisesRegex(Text2GameAdapterError, "trusted text2game runtime"):
            adapter.invoke("physical.cad", payload)
        operation_id = hashlib.sha256(
            b"alice:physical-effect:v1:fixture"
        ).hexdigest()[:32]
        self.assertEqual(
            self.store.get_state(f"alice.text2game:v1:{operation_id}").value["status"],
            "phase1_sending",
        )
        reconcile = dict(payload)
        reconcile["reconcile_only"] = True
        with self.assertRaises(AmbiguousText2GameEffect):
            adapter.invoke("physical.reconcile_cad", reconcile)

    def test_dirty_source_and_unconfigured_kernel_or_motion_fail_closed(self) -> None:
        (self.repo / "untracked.txt").write_text("drift", encoding="utf-8")
        with self.assertRaisesRegex(Text2GameAdapterError, "clean"):
            self.adapter().invoke("physical.cad", self.cad_payload())
        (self.repo / "untracked.txt").unlink()

        design = dict(self.design)
        topology = [dict(item) for item in design["topology_expectations"]]
        topology[0]["expected_body_count"] = 1
        design["topology_expectations"] = topology
        with self.assertRaisesRegex(ValueError, "undocumented fields"):
            validate_output_semantics("physical.design", design)

        design = dict(self.design)
        design["motion_conditions"] = [
            {
                "id": "dock-slide",
                "check": "linear_travel",
                "expect": "clear",
                "description": "Dock must slide.",
                "inputs": {},
                "thresholds": {},
            }
        ]
        with self.assertRaisesRegex(ValueError, "must remain empty"):
            validate_output_semantics("physical.design", design)

    def test_diagnostics_require_every_pinned_runtime_dependency(self) -> None:
        adapter = self.adapter()
        diagnostics = adapter.diagnostics()
        self.assertTrue(diagnostics["ready"], diagnostics)
        self.assertTrue(diagnostics["authenticated"])
        self.assertEqual(
            set(diagnostics["capabilities"]), set(adapter.capabilities)
        )

        self.slicer.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
        self.slicer.chmod(0o755)
        diagnostics = adapter.diagnostics()
        self.assertFalse(diagnostics["ready"])
        self.assertEqual(diagnostics["capabilities"], [])
        self.assertIn("pinned_file:slicer_binary", diagnostics["failures"])

    def test_diagnostics_require_hardened_codex_flags_and_pinned_git(self) -> None:
        self.codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.codex.chmod(0o755)
        adapter = self.adapter()
        diagnostics = adapter.diagnostics()
        self.assertFalse(diagnostics["ready"])
        self.assertIn("model_authentication", diagnostics["failures"])

        self.codex.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = exec ] && [ \"${2:-}\" = --help ]; then\n"
            "  printf '%s\\n' --ephemeral --ignore-user-config --ignore-rules --strict-config\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        self.codex.chmod(0o755)
        adapter = self.adapter()
        self.git.write_text(
            self.git.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8"
        )
        self.git.chmod(0o755)
        diagnostics = adapter.diagnostics()
        self.assertFalse(diagnostics["ready"])
        self.assertIn("source:Text2GameAdapterError", diagnostics["failures"])
        self.assertIn("pinned_file:git_binary", diagnostics["failures"])

    def test_commit_blob_and_interpreter_bytes_are_pinned(self) -> None:
        adapter = self.adapter()
        run_git(self.repo, "update-index", "--assume-unchanged", "text2game")
        (self.repo / "text2game").write_text(
            FAKE_TEXT2GAME + "\n# hidden drift\n", encoding="utf-8"
        )
        self.assertEqual(run_git(self.repo, "status", "--porcelain"), "")
        with self.assertRaisesRegex(Text2GameAdapterError, "pinned commit"):
            adapter._repo_snapshot()

        self.interpreter.write_text(
            self.interpreter.read_text(encoding="utf-8") + "# replacement\n",
            encoding="utf-8",
        )
        self.interpreter.chmod(0o755)
        with self.assertRaisesRegex(Text2GameAdapterError, "bytes changed"):
            adapter._verify_interpreter()

    def test_git_replacement_objects_cannot_substitute_the_pinned_tree(self) -> None:
        adapter = self.adapter()
        original = self.commit
        branch = run_git(self.repo, "symbolic-ref", "--short", "HEAD")
        (self.repo / "text2game").write_text(
            FAKE_TEXT2GAME + "\n# replacement-tree drift\n", encoding="utf-8"
        )
        run_git(self.repo, "add", "text2game")
        run_git(self.repo, "commit", "-qm", "replacement tree")
        replacement = run_git(self.repo, "rev-parse", "HEAD")
        run_git(self.repo, "update-ref", f"refs/heads/{branch}", original)
        run_git(self.repo, "replace", original, replacement)

        self.assertEqual(run_git(self.repo, "status", "--porcelain"), "")
        with self.assertRaisesRegex(Text2GameAdapterError, "clean|pinned commit"):
            adapter._text2game_snapshot()

    def test_seed_must_pass_the_pinned_deterministic_consistency_check(self) -> None:
        payload = self.cad_payload()
        rules = dict(self.rules)
        rules["rules_markdown"] = "# River Locks\n\nMissing required sections.\n"
        rule_document = {
            key: rules[key]
            for key in (
                "setup", "turn", "legal_actions", "end", "scoring", "ties",
                "rules_markdown",
            )
        }
        rules["rules_sha256"] = canonical_sha256(rule_document)
        design = dict(self.design)
        design["rules_sha256"] = rules["rules_sha256"]
        payload["accepted_artifacts"] = [
            {"action": "candidate.rules", "content": rules}
        ]
        payload["dependencies"]["physical.design"]["result"]["response"][
            "content"
        ] = design

        with self.assertRaisesRegex(Text2GameAdapterError, "not text2game-compatible"):
            self.adapter().invoke("physical.cad", payload)
        self.assertEqual(self.store.list_tasks(), [])
        self.assertFalse(any(self.work.iterdir()))

    def test_pre_spawn_failure_rolls_back_and_a_retry_can_start(self) -> None:
        adapter = self.adapter()
        original = text2game_adapter_module.run_bounded_process
        phase_spawns = 0

        def flaky(command, **kwargs):
            nonlocal phase_spawns
            if len(command) > 1 and str(command[1]).endswith("/text2game"):
                phase_spawns += 1
                if phase_spawns == 1:
                    raise text2game_adapter_module.BoundedProcessSpawnError(
                        "fixture spawn failure"
                    )
            return original(command, **kwargs)

        with patch(
            "alice.text2game_adapter.run_bounded_process", side_effect=flaky
        ):
            with self.assertRaises(Text2GameAdapterError):
                adapter.invoke("physical.cad", self.cad_payload())
            operation_id = hashlib.sha256(
                b"alice:physical-effect:v1:fixture"
            ).hexdigest()[:32]
            state = self.store.get_state(f"alice.text2game:v1:{operation_id}")
            self.assertIsNotNone(state)
            self.assertEqual(state.value["status"], "prepared")
            reconcile_payload = self.cad_payload()
            reconcile_payload["reconcile_only"] = True
            receipt = adapter.invoke(
                "physical.reconcile_cad", reconcile_payload
            )

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(phase_spawns, 4)

    def test_ambiguous_effects_are_retryable_only_for_reconciliation(self) -> None:
        self.assertTrue(issubclass(AmbiguousText2GameEffect, AdapterError))
        adapter = self.adapter()
        self.assertEqual(adapter.environment["CODEX_JOBS"], "all")
        self.assertEqual(adapter.environment["CODEX_SANDBOX"], "workspace-write")
        self.assertEqual(adapter.environment["CODEX_FALLBACK"], "0")
        self.assertEqual(adapter.environment["VAULT_INGEST"], "off")
        with self.assertRaisesRegex(ValueError, "process-injection"):
            self.adapter(environment={"GIT_CONFIG_GLOBAL": "/tmp/host-config"})


if __name__ == "__main__":
    unittest.main()
