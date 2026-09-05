from __future__ import annotations

import hashlib
import io
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.native import NativeMade
from workshop.release.manual_design import validate_manual_design_evidence
from workshop.release.renders import (
    HOST_RENDERS_EVIDENCE_NAME,
    HostRenderError,
    HostRenders,
    host_renders_stage_input,
    load_host_renders,
    mesh_volume,
    render_made_product,
    verified_render_bytes,
    verified_render_sources,
)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _binary_cube(scale=1.0, offset=0.0):
    faces = []

    def quad(a, b, c, d):
        faces.append((a, b, c))
        faces.append((a, c, d))

    p = lambda x, y, z: (x * scale + offset, y * scale, z * scale)  # noqa: E731
    quad(p(0, 0, 0), p(0, 1, 0), p(1, 1, 0), p(1, 0, 0))
    quad(p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1))
    quad(p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1))
    quad(p(0, 1, 0), p(0, 1, 1), p(1, 1, 1), p(1, 1, 0))
    quad(p(0, 0, 0), p(0, 0, 1), p(0, 1, 1), p(0, 1, 0))
    quad(p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1))
    out = bytearray(b"\0" * 80 + struct.pack("<I", len(faces)))
    for face in faces:
        out += struct.pack("<3f", 0.0, 0.0, 0.0)
        for vertex in face:
            out += struct.pack("<3f", *vertex)
        out += b"\0\0"
    return bytes(out)


def _png(size, colour):
    image = Image.new("RGB", (size, size), colour)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _package(names):
    return {
        "schemaVersion": 2,
        "entryKind": "assembly",
        "kind": "assembly-package",
        "packageSchemaVersion": 3,
        "rootName": "toy",
        "units": "mm",
        "occurrences": [
            {
                "id": "o1.%d.1" % (index + 1),
                "name": name,
                "component": "c%d" % index,
                "transform": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                "color": colour,
            }
            for index, (name, colour) in enumerate(names)
        ],
        "stats": {"occurrenceCount": len(names)},
    }


class FakeRenderer:
    """Writes one PNG per requested view; can fail or vary state frames."""

    def __init__(self, *, fail=None, distinct_states=True):
        self.calls = []
        self.fail = fail
        self.distinct_states = distinct_states

    def __call__(self, scene_path, out_dir):
        scene = json.loads(scene_path.read_bytes())
        staged = sorted(
            str(path.relative_to(scene_path.parent))
            for path in scene_path.parent.rglob("*")
            if path.is_file()
        )
        self.calls.append((scene, staged))
        if self.fail is not None:
            raise HostRenderError(self.fail)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        for index, view in enumerate(scene["views"]):
            shade = (index * 40) % 255 if self.distinct_states or not view["name"].startswith("state-") else 90
            (out_dir / (view["name"] + ".png")).write_bytes(_png(view["size"], (shade, 120, 200)))
            outputs.append({"name": view["name"], "width": view["size"], "height": view["size"], "triangles": 12})
        return {"ok": True, "outputs": outputs, "three": "0.160.0", "chromium": "149", "node": "v22"}


class HostRendersTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.run_root = base / "run"
        self.host_state = base / "state"
        self.run_root.mkdir()
        self.host_state.mkdir(mode=0o700)
        os.chmod(self.host_state, 0o700)

    def _made(self, *, package=None, parts=(), states=None, step=b"ISO-10303-21;\n"):
        product_root = self.run_root / "artifacts/make/r0001/product"
        project = product_root / "cad/project"
        validation = product_root / "validation"
        project.mkdir(parents=True)
        validation.mkdir()
        product = {"title": "Moon Nook", "summary": "A tiny lunar observatory."}
        if states is not None:
            product["presentation"] = {"states": list(states)}
            (product_root / "states").mkdir()
            for index, path in enumerate(states):
                target = product_root.joinpath(*path.split("/"))
                target.write_bytes(_binary_cube(1.0 + index))
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "assembled.step").write_bytes(step)
        descriptor = json.dumps(package if package is not None else {"assembly": "x"}).encode()
        (product_root / "assembled.step.json").write_bytes(descriptor)
        (product_root / "assembled.stl").write_bytes(_binary_cube(2.0))
        for name, scale in parts:
            (product_root / "parts").mkdir(exist_ok=True)
            (product_root / "parts" / ("%s.stl" % name)).write_bytes(_binary_cube(scale))
        (project / "moon.step.py").write_text("def build():\n    return None\n")
        (project / "moon.step").write_bytes(b"ISO-10303-21;\n")
        (project / "moon.stl").write_bytes(_binary_cube(1.0))
        verification = b'{"ok":true}\n'
        (validation / "cad-build.json").write_bytes(verification)
        manifest = build_artifact_manifest(product_root, created_at="content-addressed")
        return NativeMade(
            round=1,
            wish_sha256="a" * 64,
            assignment_sha256="b" * 64,
            taste_sha256="c" * 64,
            blueprint_sha256="d" * 64,
            invented_sha256="e" * 64,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=manifest,
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(verification),
        )

    def test_mesh_volume_reads_binary_and_ascii_stl(self):
        self.assertAlmostEqual(mesh_volume(_binary_cube(2.0)), 8.0, places=4)
        ascii_tetra = (
            b"solid t\n"
            b" facet normal 0 0 0\n  outer loop\n   vertex 0 0 0\n   vertex 1 0 0\n   vertex 0 1 0\n  endloop\n endfacet\n"
            b" facet normal 0 0 0\n  outer loop\n   vertex 0 0 0\n   vertex 0 0 1\n   vertex 1 0 0\n  endloop\n endfacet\n"
            b" facet normal 0 0 0\n  outer loop\n   vertex 0 0 0\n   vertex 0 1 0\n   vertex 0 0 1\n  endloop\n endfacet\n"
            b" facet normal 0 0 0\n  outer loop\n   vertex 1 0 0\n   vertex 0 0 1\n   vertex 0 1 0\n  endloop\n endfacet\n"
            b"endsolid t\n"
        )
        self.assertAlmostEqual(mesh_volume(ascii_tetra), 1.0 / 6.0, places=6)
        with self.assertRaises(HostRenderError):
            mesh_volume(b"not a mesh at all")

    def test_multipart_scene_carries_sealed_colours_and_part_volumes(self):
        made = self._made(
            package=_package([("owl", [0.82, 0.51, 0.18, 1.0]), ("nest", [0.3, 0.52, 0.62, 1.0])]),
            parts=(("owl", 1.0), ("nest", 3.0)),
        )
        renderer = FakeRenderer()

        record = render_made_product(self.run_root, self.host_state, made, runner=renderer)

        self.assertEqual(record.status, "rendered")
        scene, staged = renderer.calls[0]
        self.assertEqual([view["name"] for view in scene["views"]], ["hero"])
        part = scene["scenes"]["assembly"]["parts"][0]
        self.assertEqual(part["stl"], "assembled.stl")
        self.assertEqual(
            [(item["name"], item["color"], round(item["volume"], 4)) for item in part["shell_colors"]],
            [("owl", "#d1822e", 1.0), ("nest", "#4d859e", 27.0)],
        )
        self.assertEqual(staged, ["assembled.stl", "scene.json"])
        hero = record.output("hero")
        self.assertEqual((hero.width, hero.height, hero.path), (2000, 2000, "renders/hero.png"))
        self.assertEqual(
            [path for path, _ in record.inputs],
            ["assembled.stl", "parts/owl.stl", "parts/nest.stl"],
        )
        renders_dir = self.run_root / "artifacts/make/r0001/renders"
        self.assertEqual(_sha((renders_dir / "hero.png").read_bytes()), hero.sha256)
        private = self.host_state / "evidence/make/r0001-renders.json"
        self.assertEqual(oct(private.stat().st_mode & 0o777), "0o600")
        self.assertEqual(
            json.loads(private.read_bytes()), json.loads((renders_dir / HOST_RENDERS_EVIDENCE_NAME).read_bytes())
        )
        self.assertEqual(load_host_renders(self.host_state, made), record)

    def test_states_render_a_signature_strip_when_frames_differ(self):
        made = self._made(states=["states/a.stl", "states/b.stl", "states/c.stl"])
        renderer = FakeRenderer()

        record = render_made_product(self.run_root, self.host_state, made, runner=renderer)

        self.assertEqual(record.status, "rendered")
        names = {item.name: item for item in record.outputs}
        self.assertEqual(set(names), {"hero", "state-0", "state-1", "state-2", "signature"})
        self.assertEqual((names["signature"].width, names["signature"].height), (3000, 1000))
        self.assertTrue(record.states["presented"])
        self.assertEqual(len(record.states["differences"]), 3)
        sources = verified_render_sources(self.run_root, made, record)
        self.assertIn("renders/signature.png", sources)
        stage_input = host_renders_stage_input(self.run_root, made, record)
        self.assertEqual(stage_input["status"], "rendered")
        self.assertEqual(
            {item["manual_source_path"] for item in stage_input["outputs"]}, set(sources)
        )
        self.assertEqual(
            stage_input["outputs"][0]["workspace_path"], "artifacts/make/r0001/renders/hero.png"
        )

    def test_indistinguishable_states_are_not_presented(self):
        made = self._made(states=["states/a.stl", "states/b.stl"])

        record = render_made_product(
            self.run_root, self.host_state, made, runner=FakeRenderer(distinct_states=False)
        )

        self.assertEqual(record.status, "rendered")
        self.assertEqual([item.name for item in record.outputs], ["hero"])
        self.assertFalse(record.states["presented"])
        self.assertIn("indistinguishable", record.states["reason"])

    def test_malformed_state_declaration_still_renders_the_hero(self):
        made = self._made(states=["states/a.stl"])

        record = render_made_product(self.run_root, self.host_state, made, runner=FakeRenderer())

        self.assertEqual(record.status, "rendered")
        self.assertEqual([item.name for item in record.outputs], ["hero"])
        self.assertIn("2 to 5", record.states["reason"])

    def test_renderer_failure_is_recorded_not_raised(self):
        made = self._made()

        record = render_made_product(
            self.run_root, self.host_state, made, runner=FakeRenderer(fail="chromium exploded")
        )

        self.assertEqual(record.status, "unavailable")
        self.assertIn("chromium exploded", record.reason)
        self.assertEqual(record.outputs, ())
        self.assertEqual(load_host_renders(self.host_state, made), record)
        self.assertEqual(verified_render_sources(self.run_root, made, record), {})
        self.assertIsNone(verified_render_bytes(self.run_root, made, record, "hero"))
        self.assertEqual(host_renders_stage_input(self.run_root, made, record)["status"], "unavailable")

    def test_tampered_workspace_render_is_not_verified(self):
        made = self._made()
        record = render_made_product(self.run_root, self.host_state, made, runner=FakeRenderer())
        target = self.run_root / "artifacts/make/r0001/renders/hero.png"
        self.assertEqual(verified_render_bytes(self.run_root, made, record, "hero"), target.read_bytes())

        target.write_bytes(_png(2000, (1, 2, 3)))

        self.assertEqual(verified_render_sources(self.run_root, made, record), {})
        self.assertIsNone(verified_render_bytes(self.run_root, made, record, "hero"))

    def test_record_for_a_different_made_revision_is_ignored(self):
        made = self._made()
        render_made_product(self.run_root, self.host_state, made, runner=FakeRenderer())
        private = self.host_state / "evidence/make/r0001-renders.json"
        document = json.loads(private.read_bytes())
        document["made_product_sha256"] = "0" * 64
        private.write_bytes(json.dumps(document, sort_keys=True, separators=(",", ":")).encode() + b"\n")

        self.assertIsNone(load_host_renders(self.host_state, made))

    def test_manual_evidence_may_cite_a_bound_host_render(self):
        made = self._made()
        record = render_made_product(self.run_root, self.host_state, made, runner=FakeRenderer())
        sources = verified_render_sources(self.run_root, made, record)
        self.assertEqual(list(sources), ["renders/hero.png"])
        with self.assertRaisesRegex(ContractError, "render sources are invalid"):
            validate_manual_design_evidence(
                self.run_root, manual=b"%PDF", made=made, render_sources={"cad/x.png": "0" * 64}
            )
        with self.assertRaises(ContractError):
            HostRenders.from_mapping({**record.to_dict(), "status": "rendered", "outputs": []})


if __name__ == "__main__":
    unittest.main()
