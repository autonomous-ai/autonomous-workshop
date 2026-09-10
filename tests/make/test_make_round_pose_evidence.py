"""Preserve each reference's exact camera between measured Make rounds."""
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.make.test_make_round import _gate_output, fake_visual_render, load_module, record_fixture_visual_pass


class MakeRoundPoseEvidenceTest(unittest.TestCase):
    @contextmanager
    def fixture(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "product"
            project.mkdir()
            (project / "toy.step.py").write_text("# fake source\n")
            skills = root / "skills"
            cad = skills / "cad/scripts"
            cad.mkdir(parents=True)
            (cad / "gen").write_text("# fake generator\n")
            (skills / "image-to-cad/scripts").mkdir(parents=True)
            refs = []
            for label in ("hero", "side"):
                ref = project / (label + ".png")
                ref.write_bytes(b"fake reference")
                refs.append(label + "=" + str(ref))
            args = SimpleNamespace(
                project=str(project), entry=None, out=None, all_parts=False,
                refs=refs, min=0.9, nozzle=0.4, overhang_angle=45.0,
                no_motion=True, full=False, json=True, record_visual=None,
                component=None, require_component_passes=False,
            )
            cameras = {"hero": {"az": 10.0, "el": 5.0}, "side": {"az": 100.0, "el": 15.0}}
            control = {"replay_iou": 0.95, "search_iou": 0.95}
            calls = []

            def run(command, *, cwd, log, **kwargs):
                tool = Path(command[1]).name
                code = 0
                if tool == "gen":
                    source = Path(command[2])
                    source.with_name(source.name[:-len(".py")]).write_bytes(b"same solid")
                    stdout = '{"ok":true}\n'
                elif tool == "render_review":
                    return fake_visual_render(command)
                elif tool == "render_views.py":
                    label = command[command.index("--label") + 1]
                    stored = {}
                    if "--poses-from" in command:
                        source = Path(command[command.index("--poses-from") + 1])
                        stored = json.loads(source.read_text())["poses"]
                    replayed = label in stored
                    pose = dict(stored[label] if replayed else cameras[label])
                    if any(arg.startswith("--search-az=") for arg in command):
                        pose["az"] += 20.0
                    calls.append({"label": label, "replayed": replayed, "pose": dict(pose)})
                    # Real render_views writes its match and unclaimed stored
                    # poses to the requested output on every invocation.
                    poses = {label: pose, **{k: v for k, v in stored.items() if k != label}}
                    out = Path(command[command.index("-o") + 1])
                    out.mkdir(parents=True, exist_ok=True)
                    (out / "poses.json").write_text(json.dumps({"poses": poses}))
                    iou = control["replay_iou" if replayed else "search_iou"]
                    ok = iou >= args.min
                    code = 0 if ok else 1
                    stdout = json.dumps({
                        "ok": ok, "views": [{"label": label, "iou": iou, "ok": ok, **pose}],
                    }, indent=2)
                elif tool in ("check_thickness", "check_overhang"):
                    # These fixtures are about camera replay; keep the print
                    # gates green so the pose is the only variable.
                    stdout, code = _gate_output(tool, fails=False)
                else:
                    raise AssertionError(tool)
                log.write_text(stdout)
                return subprocess.CompletedProcess(command, code, stdout, "")

            with (
                patch.object(module, "skills_root", return_value=skills),
                patch.object(module, "run", run),
            ):
                yield module, args, control, calls, cameras

    def round(self, module, args):
        output = io.StringIO()
        with redirect_stdout(output):
            code = module.make_round(args)
        self.assertEqual(code, 1)
        pending = json.loads(output.getvalue())
        self.assertFalse(pending["ok"])
        self.assertEqual(pending["visual"]["status"], "pending")
        summary = record_fixture_visual_pass(module, args.project, pending)
        return (0 if summary["ok"] else 1), summary

    def pose_path(self, result, args):
        # The old global path lets the same test expose the pre-fix wrong
        # camera, rather than failing only because the new field is absent.
        state = json.loads((Path(args.project) / "measure/make-round-state.json").read_text())
        return Path(result.get("poses_path") or state["poses_path"])

    def test_two_references_replay_their_own_previous_camera(self):
        with self.fixture() as (module, args, control, calls, cameras):
            for _ in range(2):
                self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual([c["replayed"] for c in calls], [False, False, True, True])
            self.assertEqual([c["pose"] for c in calls[2:]], [cameras["hero"], cameras["side"]])

    def test_reordering_references_preserves_each_camera(self):
        with self.fixture() as (module, args, control, calls, cameras):
            self.assertEqual(self.round(module, args)[0], 0)
            args.refs.reverse()
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual([c["replayed"] for c in calls[2:]], [True, True])
            self.assertEqual([c["pose"] for c in calls[2:]], [cameras["side"], cameras["hero"]])

    def test_missing_one_pose_does_not_discard_the_other_camera(self):
        with self.fixture() as (module, args, control, calls, cameras):
            code, summary = self.round(module, args)
            self.assertEqual(code, 0)
            self.pose_path(summary["likeness"][0], args).unlink()
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual([c["replayed"] for c in calls[2:]], [False, True])

    def test_worse_search_keeps_the_replayed_camera_and_evidence(self):
        with self.fixture() as (module, args, control, calls, cameras):
            args.refs = args.refs[:1]
            self.assertEqual(self.round(module, args)[0], 0)
            control.update(replay_iou=0.85, search_iou=0.80)
            code, summary = self.round(module, args)
            self.assertEqual(code, 1)
            result = summary["likeness"][0]
            self.assertEqual(result["iou"], 0.85)
            self.assertFalse(result["searched"])
            pose = json.loads(self.pose_path(result, args).read_text())["poses"]["hero"]
            self.assertEqual(pose, cameras["hero"])
            control["replay_iou"] = 0.95
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual(calls[-1]["pose"], cameras["hero"])

    def test_better_search_becomes_the_next_replayed_camera(self):
        with self.fixture() as (module, args, control, calls, cameras):
            args.refs = args.refs[:1]
            self.assertEqual(self.round(module, args)[0], 0)
            control.update(replay_iou=0.85, search_iou=0.94)
            code, summary = self.round(module, args)
            self.assertEqual(code, 0)
            result = summary["likeness"][0]
            self.assertEqual(result["iou"], 0.94)
            self.assertTrue(result["searched"])
            pose = json.loads(self.pose_path(result, args).read_text())["poses"]["hero"]
            self.assertEqual(pose["az"], cameras["hero"]["az"] + 20.0)
            control["replay_iou"] = 0.95
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual(calls[-1]["pose"], pose)

    def test_legacy_global_pose_state_migrates_to_per_reference_replay(self):
        with self.fixture() as (module, args, control, calls, cameras):
            self.assertEqual(self.round(module, args)[0], 0)
            state_path = Path(args.project) / "measure" / module.STATE_NAME
            state = json.loads(state_path.read_text())
            state.pop("pose_paths", None)
            state_path.write_text(json.dumps(state))
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual(self.round(module, args)[0], 0)
            self.assertEqual([c["replayed"] for c in calls[-2:]], [True, True])


if __name__ == "__main__":
    unittest.main()

