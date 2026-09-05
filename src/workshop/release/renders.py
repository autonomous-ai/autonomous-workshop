"""Trusted-host product renders from sealed Made bytes.

After a Make proposal passes its CAD gate, the host renders the sealed
``assembled.stl`` (and any exact state meshes Make declares) with a pinned
three.js renderer under headless Chromium.  The inputs are sealed Made bytes
only; the outputs are bound to the Made product hash in ``renders.json``, whose
private copy under the host state is the authority the Release stage trusts
when the manual cites ``renders/<name>.png`` or the Factory cover is shipped.

Colour follows the sealed parts: the shells of a posed mesh are matched to the
production STLs by volume and painted in the colour the STEP (or the sealed
assembly-package) carries for that occurrence.  When the renderer is missing
or fails, the record says ``unavailable`` and every consumer behaves exactly
as it did before host renders existed.  Rendering never blocks a run.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import shutil
import stat
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple

from PIL import Image

from workshop.errors import ContractError
from workshop.make.assembly_package import (
    ASSEMBLY_PACKAGE_PATH,
    AssemblyPackage,
    is_assembly_package,
    read_assembly_package,
)
from workshop.make.cad.step_color import read_step_part_colors
from workshop.make.native import NativeMade
from workshop.make.native_gate import _atomic_private_write
from workshop.runtime.execution import minimal_tool_environment


HOST_RENDERS_KIND = "autonomous-workshop.host-renders"
HOST_RENDERS_SCHEMA_VERSION = 1
HOST_RENDERS_DIRECTORY = "renders"
HOST_RENDERS_EVIDENCE_NAME = "renders.json"
HOST_RENDER_SOURCE_PREFIX = "renders/"
RENDERER_ID = "three-swiftshader-v1"
HERO_VIEW = "hero"
SIGNATURE_VIEW = "signature"
HERO_SIZE = 2000
STATE_SIZE = 1000
TURNAROUND_SIZE = 1200
TURNAROUND_VIEWS: Tuple[Tuple[str, float, float], ...] = (
    ("turnaround-front", 0.0, 18.0),
    ("turnaround-back", 180.0, 18.0),
    ("turnaround-side-l", -90.0, 18.0),
    ("turnaround-side-r", 90.0, 18.0),
    ("turnaround-top", 35.0, 80.0),
)
DEFAULT_BACKGROUND = "#f5f0e6"
NEUTRAL_COLOUR = "#9aa5b1"
MAX_RENDER_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_RENDER_STL_BYTES = 256 * 1024 * 1024
MAX_RENDER_TRIANGLES = 12_000_000
MAX_STATES = 5
MIN_STATES = 2
MIN_STATE_DIFFERENCE = 2.0
RENDER_TIMEOUT_SECONDS = 600.0
SELF_CHECK_TIMEOUT_SECONDS = 180.0
MAX_REASON_CHARS = 500
_HEX = re.compile(r"^#[0-9a-f]{6}$")
_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_ASCII_VERTEX = re.compile(rb"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)")


class HostRenderError(Exception):
    """A bounded, non-fatal reason why the host could not render."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _bounded_reason(value: Any) -> str:
    text = " ".join(str(value).split())
    return text[:MAX_REASON_CHARS] or "unavailable"


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def renderer_script() -> Path:
    return repository_root() / "tools" / "render" / "render_scene.mjs"


def node_executable() -> Optional[str]:
    configured = os.environ.get("WORKSHOP_NODE_BIN")
    if configured:
        return configured if Path(configured).is_file() else None
    return shutil.which("node")


def renderer_command() -> Optional[Tuple[str, ...]]:
    """Return the renderer command when node, the script, and three.js exist."""

    if os.environ.get("WORKSHOP_HOST_RENDERER", "").strip().lower() in ("0", "off", "false", "no"):
        return None
    node = node_executable()
    script = renderer_script()
    three = script.parent / "node_modules" / "three" / "package.json"
    playwright = script.parent / "node_modules" / "playwright" / "package.json"
    if node is None or not script.is_file() or not three.is_file() or not playwright.is_file():
        return None
    return (node, str(script))


def _renderer_environment() -> dict[str, str]:
    environment = dict(minimal_tool_environment())
    node = node_executable()
    if node is not None:
        environment["PATH"] = os.pathsep.join(
            [str(Path(node).resolve().parent), environment["PATH"]]
        )
    for name in ("HOME", "PLAYWRIGHT_BROWSERS_PATH"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def _parse_summary(stdout: str) -> Mapping[str, Any]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise HostRenderError("renderer produced no summary")
    try:
        summary = json.loads(lines[-1])
    except ValueError as exc:
        raise HostRenderError("renderer summary is not JSON") from exc
    if not isinstance(summary, Mapping):
        raise HostRenderError("renderer summary is malformed")
    if summary.get("ok") is not True:
        raise HostRenderError("renderer failed: %s" % summary.get("error", "unknown"))
    return summary


def run_renderer(scene_path: Path, out_dir: Path, *, timeout: float = RENDER_TIMEOUT_SECONDS) -> Mapping[str, Any]:
    """Run the pinned renderer on one scene file and return its summary."""

    command = renderer_command()
    if command is None:
        raise HostRenderError("host renderer is not installed (node, tools/render/node_modules)")
    try:
        completed = subprocess.run(
            [*command, str(scene_path), str(out_dir)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=_renderer_environment(),
            cwd=str(scene_path.parent),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostRenderError("renderer could not run: %s" % type(exc).__name__) from exc
    if completed.returncode != 0:
        summary_error = None
        try:
            summary_error = _parse_summary(completed.stdout)
        except HostRenderError as exc:
            summary_error = exc
        raise HostRenderError(
            "renderer exited %d: %s" % (completed.returncode, summary_error)
        )
    return _parse_summary(completed.stdout)


def renderer_self_check(*, timeout: float = SELF_CHECK_TIMEOUT_SECONDS) -> Mapping[str, Any]:
    """Render a built-in cube; the doctor's proof that the renderer works."""

    command = renderer_command()
    if command is None:
        return {"available": False, "detail": "node, tools/render/render_scene.mjs, or its node_modules are missing"}
    with tempfile.TemporaryDirectory(prefix="workshop-render-check-") as temporary:
        try:
            completed = subprocess.run(
                [*command, "--self-check", temporary],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=_renderer_environment(),
            )
            summary = _parse_summary(completed.stdout)
            output = Path(temporary) / "self-check.png"
            _validate_png(output.read_bytes(), 256, 256)
        except (OSError, subprocess.SubprocessError, HostRenderError, ValueError) as exc:
            return {"available": False, "detail": _bounded_reason(exc)}
    return {
        "available": True,
        "detail": "three.js %s under Chromium %s (node %s)"
        % (summary.get("three"), summary.get("chromium"), summary.get("node")),
        "three": summary.get("three"),
        "chromium": summary.get("chromium"),
        "node": summary.get("node"),
    }


# --- sealed mesh helpers -------------------------------------------------


def stl_triangles(content: bytes):
    """Yield (a, b, c) vertex triples from binary or ASCII STL bytes."""

    if len(content) > MAX_RENDER_STL_BYTES:
        raise HostRenderError("mesh exceeds the render size bound")
    if len(content) >= 84:
        count = struct.unpack("<I", content[80:84])[0]
        if len(content) == 84 + count * 50:
            if count > MAX_RENDER_TRIANGLES:
                raise HostRenderError("mesh exceeds the render triangle bound")
            for record in struct.iter_unpack("<12x9fH", content[84 : 84 + count * 50]):
                yield record[0:3], record[3:6], record[6:9]
            return
    head = content[:512].lstrip()
    if not head.startswith(b"solid"):
        raise HostRenderError("mesh is neither binary nor ASCII STL")
    vertices = [tuple(float(item) for item in match) for match in _ASCII_VERTEX.findall(content)]
    if len(vertices) // 3 > MAX_RENDER_TRIANGLES:
        raise HostRenderError("mesh exceeds the render triangle bound")
    for index in range(0, len(vertices) - len(vertices) % 3, 3):
        yield vertices[index], vertices[index + 1], vertices[index + 2]


def mesh_volume(content: bytes) -> float:
    """Absolute enclosed volume of one STL, in cubic model units."""

    total = 0.0
    for a, b, c in stl_triangles(content):
        total += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    if not math.isfinite(total):
        raise HostRenderError("mesh volume is not finite")
    return abs(total)


def _validate_png(content: bytes, width: int, height: int) -> None:
    if not content.startswith(_PNG_SIGNATURE) or len(content) > MAX_RENDER_OUTPUT_BYTES:
        raise HostRenderError("render output is not a bounded PNG")
    with Image.open(io.BytesIO(content)) as image:
        if image.format != "PNG" or image.size != (width, height):
            raise HostRenderError("render output has unexpected format or size")


def _frame_difference(left: bytes, right: bytes) -> float:
    with Image.open(io.BytesIO(left)) as a, Image.open(io.BytesIO(right)) as b:
        pixels_a = list(a.convert("RGB").resize((96, 96)).getdata())
        pixels_b = list(b.convert("RGB").resize((96, 96)).getdata())
    total = 0
    for pa, pb in zip(pixels_a, pixels_b):
        total += abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2])
    return total / (96 * 96 * 3)


def _composite_strip(frames: Sequence[bytes], background: str) -> bytes:
    images = [Image.open(io.BytesIO(frame)).convert("RGB") for frame in frames]
    try:
        size = images[0].size[0]
        colour = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
        sheet = Image.new("RGB", (size * len(images), size), colour)
        for index, image in enumerate(images):
            sheet.paste(image, (index * size, 0))
        output = io.BytesIO()
        sheet.save(output, format="PNG", optimize=True)
        return output.getvalue()
    finally:
        for image in images:
            image.close()


# --- records ------------------------------------------------------------


@dataclass(frozen=True)
class HostRenderOutput:
    name: str
    kind: str
    path: str
    sha256: str
    bytes: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if _SAFE_NAME.fullmatch(self.name) is None:
            raise ContractError("host render output name is unsafe")
        if self.kind not in ("hero", "state", "signature", "turnaround"):
            raise ContractError("host render output kind is invalid")
        if self.path != HOST_RENDER_SOURCE_PREFIX + self.name + ".png":
            raise ContractError("host render output path is not canonical")
        if re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            raise ContractError("host render output sha256 is invalid")
        for value in (self.bytes, self.width, self.height):
            if type(value) is not int or value <= 0:
                raise ContractError("host render output dimensions are invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class HostRenders:
    """The host's record of one render pass, bound to the Made product hash."""

    round: int
    made_product_sha256: str
    status: str
    reason: Optional[str]
    renderer: Mapping[str, Any]
    inputs: Tuple[Tuple[str, str], ...]
    outputs: Tuple[HostRenderOutput, ...]
    states: Mapping[str, Any]
    schema_version: int = HOST_RENDERS_SCHEMA_VERSION
    kind: str = HOST_RENDERS_KIND

    def __post_init__(self) -> None:
        if self.schema_version != HOST_RENDERS_SCHEMA_VERSION or self.kind != HOST_RENDERS_KIND:
            raise ContractError("host renders record identity is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("host renders round is invalid")
        if re.fullmatch(r"[0-9a-f]{64}", self.made_product_sha256) is None:
            raise ContractError("host renders Made product sha256 is invalid")
        if self.status not in ("rendered", "unavailable"):
            raise ContractError("host renders status is invalid")
        if self.status == "rendered" and not self.outputs:
            raise ContractError("rendered host renders must list outputs")
        if self.status == "unavailable" and self.outputs:
            raise ContractError("unavailable host renders cannot list outputs")
        names = [item.name for item in self.outputs]
        if len(set(names)) != len(names):
            raise ContractError("host render output names must be unique")
        object.__setattr__(self, "renderer", dict(self.renderer))
        object.__setattr__(self, "states", dict(self.states))
        object.__setattr__(self, "inputs", tuple((str(a), str(b)) for a, b in self.inputs))

    @property
    def rendered(self) -> bool:
        return self.status == "rendered"

    def output(self, kind: str) -> Optional[HostRenderOutput]:
        for item in self.outputs:
            if item.kind == kind:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "round": self.round,
            "made_product_sha256": self.made_product_sha256,
            "status": self.status,
            "reason": self.reason,
            "renderer": dict(self.renderer),
            "inputs": [{"path": path, "sha256": sha256} for path, sha256 in self.inputs],
            "outputs": [item.to_dict() for item in self.outputs],
            "states": dict(self.states),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "HostRenders":
        expected = {
            "schema_version", "kind", "round", "made_product_sha256", "status",
            "reason", "renderer", "inputs", "outputs", "states",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("host renders record fields are invalid")
        inputs = value["inputs"]
        outputs = value["outputs"]
        if not isinstance(inputs, list) or not isinstance(outputs, list):
            raise ContractError("host renders record lists are invalid")
        try:
            parsed_outputs = tuple(
                HostRenderOutput(
                    name=item["name"], kind=item["kind"], path=item["path"],
                    sha256=item["sha256"], bytes=item["bytes"],
                    width=item["width"], height=item["height"],
                )
                for item in outputs
            )
            parsed_inputs = tuple((item["path"], item["sha256"]) for item in inputs)
        except (KeyError, TypeError) as exc:
            raise ContractError("host renders record entries are invalid") from exc
        if not isinstance(value["renderer"], Mapping) or not isinstance(value["states"], Mapping):
            raise ContractError("host renders record objects are invalid")
        if value["reason"] is not None and not isinstance(value["reason"], str):
            raise ContractError("host renders reason is invalid")
        record = cls(
            round=value["round"],
            made_product_sha256=value["made_product_sha256"],
            status=value["status"],
            reason=value["reason"],
            renderer=value["renderer"],
            inputs=parsed_inputs,
            outputs=parsed_outputs,
            states=value["states"],
            schema_version=value["schema_version"],
            kind=value["kind"],
        )
        if record.to_dict() != dict(value):
            raise ContractError("host renders record is not canonical")
        return record


# --- locations ----------------------------------------------------------


def renders_directory(run_root: Path, made: NativeMade) -> Path:
    return Path(run_root).joinpath(*made.product_root.split("/")[:-1], HOST_RENDERS_DIRECTORY)


def _private_evidence_path(host_state_root: Path, round_index: int) -> Path:
    current = Path(host_state_root)
    for part in ("evidence", "make"):
        candidate = current / part
        try:
            identity = candidate.lstat()
        except FileNotFoundError:
            candidate.mkdir(mode=0o700)
            identity = candidate.lstat()
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
            raise ContractError("host render evidence directory is unsafe")
        os.chmod(candidate, 0o700)
        current = candidate
    return current / ("r%04d-renders.json" % round_index)


# --- the render pass ------------------------------------------------------


def _read_entry(product_root: Path, made: NativeMade, path: str) -> bytes:
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    entry = entries.get(path)
    if entry is None:
        raise HostRenderError("sealed Made lacks %s" % path)
    target = product_root.joinpath(*path.split("/"))
    if target.is_symlink() or not target.is_file():
        raise HostRenderError("sealed Made %s is not a regular file" % path)
    content = target.read_bytes()
    if len(content) != entry.bytes or _sha256(content) != entry.sha256:
        raise HostRenderError("sealed Made %s changed after sealing" % path)
    return content


def _package(product_root: Path, made: NativeMade) -> Optional[AssemblyPackage]:
    entries = {entry.path for entry in made.product_manifest.entries}
    if ASSEMBLY_PACKAGE_PATH not in entries:
        return None
    content = _read_entry(product_root, made, ASSEMBLY_PACKAGE_PATH)
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError):
        return None
    if not is_assembly_package(document):
        return None
    try:
        return read_assembly_package(content)
    except ContractError:
        return None


def _sealed_colours(product_root: Path, made: NativeMade, package: Optional[AssemblyPackage]) -> dict[str, str]:
    colours: dict[str, str] = {}
    entries = {entry.path for entry in made.product_manifest.entries}
    if "assembled.step" in entries:
        try:
            content = _read_entry(product_root, made, "assembled.step")
            colours = {
                name: value.hex
                for name, value in read_step_part_colors(content).items()
                if _HEX.fullmatch(value.hex)
            }
        except HostRenderError:
            colours = {}
    if not colours and package is not None:
        colours = dict(package.part_colors())
    return colours


def _declared_states(made: NativeMade) -> Tuple[str, ...]:
    presentation = made.product.get("presentation")
    if not isinstance(presentation, Mapping):
        return ()
    states = presentation.get("states")
    if isinstance(states, (str, bytes)) or not isinstance(states, Sequence):
        raise HostRenderError("product.json presentation.states must be a list")
    if not MIN_STATES <= len(states) <= MAX_STATES:
        raise HostRenderError(
            "product.json presentation.states must name %d to %d sealed STL paths"
            % (MIN_STATES, MAX_STATES)
        )
    entries = {entry.path for entry in made.product_manifest.entries}
    result = []
    for item in states:
        pure = PurePosixPath(item) if isinstance(item, str) else PurePosixPath(".")
        if (
            not isinstance(item, str)
            or pure.is_absolute()
            or ".." in pure.parts
            or pure.as_posix() != item
            or pure.suffix.casefold() != ".stl"
            or item not in entries
            or item in result
        ):
            raise HostRenderError("presentation state %r is not a sealed STL path" % item)
        result.append(item)
    return tuple(result)


def _view(name: str, azimuth: float, elevation: float, size: int, scene: str) -> dict[str, Any]:
    return {"name": name, "azimuth": azimuth, "elevation": elevation, "size": size, "scene": scene}


def _render_pass(
    product_root: Path,
    made: NativeMade,
    *,
    runner: Callable[[Path, Path], Mapping[str, Any]],
    turnaround: bool,
) -> Tuple[dict[str, bytes], dict[str, Any], list[Tuple[str, str]], dict[str, Any], Optional[str]]:
    """Return rendered frames by view name plus bookkeeping for the record."""

    package = _package(product_root, made)
    colours = _sealed_colours(product_root, made, package)
    inputs: list[Tuple[str, str]] = []

    def sealed(path: str) -> bytes:
        content = _read_entry(product_root, made, path)
        inputs.append((path, _sha256(content)))
        return content

    assembled = sealed("assembled.stl")
    shell_colors: list[dict[str, Any]] = []
    base_colour = NEUTRAL_COLOUR
    if package is not None and package.is_multipart:
        for occurrence in package.occurrences:
            colour = colours.get(occurrence.name)
            if colour is None:
                continue
            try:
                volume = mesh_volume(sealed(occurrence.production_stl_path))
            except HostRenderError:
                continue
            if volume > 0:
                shell_colors.append(
                    {"name": occurrence.name, "volume": volume, "color": colour}
                )
    elif len(set(colours.values())) == 1:
        base_colour = next(iter(colours.values()))

    def part_entry(path: str) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "stl": path,
            "color": base_colour,
            "transform": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        }
        if shell_colors:
            entry["shell_colors"] = list(shell_colors)
        return entry

    states_note: dict[str, Any] = {"declared": [], "differences": [], "presented": False}
    state_reason: Optional[str] = None
    try:
        declared = _declared_states(made)
    except HostRenderError as exc:
        declared = ()
        state_reason = _bounded_reason(exc)
    state_bytes = [sealed(path) for path in declared]
    states_note["declared"] = list(declared)

    views = [_view(HERO_VIEW, 35.0, 26.0, HERO_SIZE, "assembly")]
    scenes: dict[str, Any] = {"assembly": {"parts": [part_entry("assembled.stl")]}}
    if turnaround:
        for name, azimuth, elevation in TURNAROUND_VIEWS:
            views.append(_view(name, azimuth, elevation, TURNAROUND_SIZE, "assembly"))
    for index, _ in enumerate(declared):
        scene_name = "state-%d" % index
        scenes[scene_name] = {"parts": [part_entry("states/%s.stl" % scene_name)]}
        views.append(_view(scene_name, 35.0, 22.0, STATE_SIZE, scene_name))

    with tempfile.TemporaryDirectory(prefix="workshop-host-render-") as temporary:
        stage = Path(temporary) / "scene"
        out = Path(temporary) / "out"
        stage.mkdir()
        (stage / "assembled.stl").write_bytes(assembled)
        if declared:
            (stage / "states").mkdir()
            for index, content in enumerate(state_bytes):
                (stage / "states" / ("state-%d.stl" % index)).write_bytes(content)
        scene = {
            "schema_version": 1,
            "background": DEFAULT_BACKGROUND,
            "views": views,
            "scenes": scenes,
        }
        scene_path = stage / "scene.json"
        scene_path.write_bytes(_canonical_json(scene))
        summary = runner(scene_path, out)
        outputs = summary.get("outputs") if isinstance(summary, Mapping) else None
        if not isinstance(outputs, list):
            raise HostRenderError("renderer summary lists no outputs")
        by_name: dict[str, Mapping[str, Any]] = {}
        for item in outputs:
            if isinstance(item, Mapping) and isinstance(item.get("name"), str):
                by_name[item["name"]] = item
        frames: dict[str, bytes] = {}
        for view in views:
            item = by_name.get(view["name"])
            if item is None:
                raise HostRenderError("renderer omitted view %s" % view["name"])
            target = out / (view["name"] + ".png")
            if target.is_symlink() or not target.is_file():
                raise HostRenderError("renderer wrote no file for %s" % view["name"])
            content = target.read_bytes()
            _validate_png(content, view["size"], view["size"])
            frames[view["name"]] = content
        renderer_info = {
            "id": RENDERER_ID,
            "three": summary.get("three"),
            "chromium": summary.get("chromium"),
            "node": summary.get("node"),
            "shells": [
                {"view": item.get("name"), "shells": item.get("shells")}
                for item in outputs
                if isinstance(item, Mapping) and item.get("shells")
            ],
        }

    if declared:
        state_frames = [frames.pop("state-%d" % index) for index in range(len(declared))]
        differences = [
            _frame_difference(state_frames[left], state_frames[right])
            for left in range(len(state_frames))
            for right in range(left + 1, len(state_frames))
        ]
        states_note["differences"] = [round(value, 3) for value in differences]
        if any(value < MIN_STATE_DIFFERENCE for value in differences):
            state_reason = (
                "declared states are visually indistinguishable (minimum mean RGB "
                "difference %.3f, required %.3f)" % (min(differences), MIN_STATE_DIFFERENCE)
            )
        else:
            for index, frame in enumerate(state_frames):
                frames["state-%d" % index] = frame
            frames[SIGNATURE_VIEW] = _composite_strip(state_frames, DEFAULT_BACKGROUND)
            states_note["presented"] = True
    if state_reason is not None:
        states_note["reason"] = state_reason
    return frames, renderer_info, inputs, states_note, state_reason


def _output_kind(name: str) -> str:
    if name == HERO_VIEW:
        return "hero"
    if name == SIGNATURE_VIEW:
        return "signature"
    if name.startswith("state-"):
        return "state"
    return "turnaround"


def _clear_renders_directory(directory: Path) -> None:
    if directory.is_symlink():
        raise HostRenderError("renders directory is a symlink")
    if directory.exists():
        for child in directory.iterdir():
            if child.is_symlink() or not child.is_file():
                raise HostRenderError("renders directory contains an unexpected entry")
            if child.suffix == ".png" or child.name == HOST_RENDERS_EVIDENCE_NAME:
                child.unlink()
    else:
        directory.mkdir(mode=0o755)


def _persist(
    run_root: Path,
    host_state_root: Path,
    made: NativeMade,
    record: HostRenders,
    frames: Mapping[str, bytes],
) -> HostRenders:
    directory = renders_directory(run_root, made)
    _clear_renders_directory(directory)
    for output in record.outputs:
        target = directory / (output.name + ".png")
        target.write_bytes(frames[output.name])
        target.chmod(0o644)
    content = _canonical_json(record.to_dict()) + b"\n"
    (directory / HOST_RENDERS_EVIDENCE_NAME).write_bytes(content)
    (directory / HOST_RENDERS_EVIDENCE_NAME).chmod(0o644)
    _atomic_private_write(_private_evidence_path(host_state_root, made.round), content)
    return record


def render_made_product(
    run_root: Path,
    host_state_root: Path,
    made: NativeMade,
    *,
    runner: Optional[Callable[[Path, Path], Mapping[str, Any]]] = None,
    turnaround: bool = False,
) -> HostRenders:
    """Render one sealed Make revision and persist the bound record.

    Never raises for renderer trouble: an unavailable or failing renderer
    yields a record with ``status: unavailable`` and a bounded reason.
    """

    if not isinstance(made, NativeMade):
        raise ContractError("host renders require NativeMade")
    run_root = Path(run_root).resolve(strict=True)
    host_state_root = Path(host_state_root).resolve(strict=True)
    product_root = run_root.joinpath(*made.product_root.split("/"))
    made_sha256 = made.product_manifest.artifact_sha256
    active_runner = runner if runner is not None else run_renderer
    try:
        if runner is None and renderer_command() is None:
            raise HostRenderError(
                "host renderer is not installed; run `workshop doctor` for the render check"
            )
        frames, renderer_info, inputs, states_note, unused_reason = _render_pass(
            product_root, made, runner=active_runner, turnaround=turnaround
        )
        del unused_reason
        outputs = []
        for name in sorted(frames, key=lambda item: (item != HERO_VIEW, item)):
            content = frames[name]
            with Image.open(io.BytesIO(content)) as image:
                width, height = image.size
            outputs.append(
                HostRenderOutput(
                    name=name,
                    kind=_output_kind(name),
                    path=HOST_RENDER_SOURCE_PREFIX + name + ".png",
                    sha256=_sha256(content),
                    bytes=len(content),
                    width=width,
                    height=height,
                )
            )
        record = HostRenders(
            round=made.round,
            made_product_sha256=made_sha256,
            status="rendered",
            reason=None,
            renderer=renderer_info,
            inputs=tuple(inputs),
            outputs=tuple(outputs),
            states=states_note,
        )
        return _persist(run_root, host_state_root, made, record, frames)
    except Exception as exc:  # noqa: BLE001 - rendering must never fail a run
        record = HostRenders(
            round=made.round,
            made_product_sha256=made_sha256,
            status="unavailable",
            reason=_bounded_reason("%s: %s" % (type(exc).__name__, exc)),
            renderer={"id": RENDERER_ID},
            inputs=(),
            outputs=(),
            states={},
        )
        try:
            return _persist(run_root, host_state_root, made, record, {})
        except Exception:  # noqa: BLE001 - even persistence trouble stays non-fatal
            return record


# --- consumers ----------------------------------------------------------


def load_host_renders(host_state_root: Path, made: NativeMade) -> Optional[HostRenders]:
    """Read the private render record for this exact Made revision, if any."""

    path = Path(host_state_root) / "evidence" / "make" / ("r%04d-renders.json" % made.round)
    try:
        if path.is_symlink() or not path.is_file():
            return None
        content = path.read_bytes()
    except OSError:
        return None
    try:
        record = HostRenders.from_mapping(json.loads(content.decode("utf-8")))
    except (UnicodeError, ValueError, ContractError):
        return None
    if record.round != made.round or record.made_product_sha256 != made.product_manifest.artifact_sha256:
        return None
    return record


def verified_render_sources(
    run_root: Path, made: NativeMade, renders: Optional[HostRenders]
) -> dict[str, str]:
    """Map ``renders/<name>.png`` to its sha256 for outputs still exact on disk."""

    if renders is None or not renders.rendered:
        return {}
    directory = renders_directory(run_root, made)
    sources: dict[str, str] = {}
    for output in renders.outputs:
        target = directory / (output.name + ".png")
        try:
            if target.is_symlink() or not target.is_file():
                continue
            content = target.read_bytes()
        except OSError:
            continue
        if len(content) == output.bytes and _sha256(content) == output.sha256:
            sources[output.path] = output.sha256
    return sources


def verified_render_bytes(
    run_root: Path, made: NativeMade, renders: Optional[HostRenders], kind: str
) -> Optional[bytes]:
    """Return the exact bytes of one rendered output kind, or ``None``."""

    if renders is None or not renders.rendered:
        return None
    output = renders.output(kind)
    if output is None:
        return None
    target = renders_directory(run_root, made) / (output.name + ".png")
    try:
        if target.is_symlink() or not target.is_file():
            return None
        content = target.read_bytes()
    except OSError:
        return None
    if len(content) != output.bytes or _sha256(content) != output.sha256:
        return None
    return content


def host_renders_stage_input(
    run_root: Path, made: NativeMade, renders: Optional[HostRenders]
) -> dict[str, Any]:
    """The bounded description of host renders a Release Goal may cite."""

    if renders is None:
        return {"status": "unavailable", "reason": "no host render record", "outputs": []}
    verified = verified_render_sources(run_root, made, renders)
    directory = "/".join(made.product_root.split("/")[:-1] + [HOST_RENDERS_DIRECTORY])
    return {
        "status": renders.status,
        "reason": renders.reason,
        "outputs": [
            {
                "kind": item.kind,
                "workspace_path": "%s/%s.png" % (directory, item.name),
                "manual_source_path": item.path,
                "sha256": item.sha256,
                "width": item.width,
                "height": item.height,
            }
            for item in renders.outputs
            if item.path in verified
        ],
        "states": dict(renders.states),
    }


__all__ = [
    "HOST_RENDERS_DIRECTORY",
    "HOST_RENDERS_EVIDENCE_NAME",
    "HOST_RENDERS_KIND",
    "HOST_RENDER_SOURCE_PREFIX",
    "HostRenderError",
    "HostRenderOutput",
    "HostRenders",
    "host_renders_stage_input",
    "load_host_renders",
    "mesh_volume",
    "render_made_product",
    "renderer_command",
    "renderer_self_check",
    "run_renderer",
    "verified_render_bytes",
    "verified_render_sources",
]
