"""Deterministic inspection progress and content-bound reusable measurements.

This is geometry-tool infrastructure, not an agent or lifecycle scheduler.
Only completed measurements are cached. The supervising CLI owns cancellation.
"""
from __future__ import annotations

import contextlib
from contextvars import ContextVar
import functools
import hashlib
import json
import os
from pathlib import Path
import sys
import stat
import uuid
from typing import Any, Callable, Iterator


PROGRESS_ENV = "WORKSHOP_GEOMETRY_PROGRESS_FD"
_SCENES: ContextVar[dict | None] = ContextVar("inspection_scenes", default=None)
_IGNORED = {"__cadgen__", "__pycache__", ".git", ".venv", "node_modules"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def emit(event: str, **values: Any) -> None:
    raw = os.environ.get(PROGRESS_ENV)
    if raw is None:
        return
    try:
        data = canonical({"event": event, "request": os.environ.get("WORKSHOP_GEOMETRY_REQUEST_ID"), **values}) + b"\n"
        # Small atomic control messages use a dedicated pipe, never JSON stdout.
        if len(data) <= 4096:
            os.write(int(raw), data)
    except (OSError, ValueError):
        pass


@contextlib.contextmanager
def reuse_scenes():
    token = _SCENES.set({})
    try:
        yield
    finally:
        _SCENES.reset(token)


def _inputs(script: Path, extra: tuple[str, ...] = ()) -> str | None:
    """Byte hashes, including directory membership; never trust size/mtime alone."""
    root = script.parent
    files: set[Path] = {script}
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORED)
        if any((Path(folder) / d).is_symlink() for d in dirs):
            return None
        for name in names:
            path = Path(folder) / name
            files.add(path)
    for relative in extra:
        files.add((root / relative).resolve())
    digest = hashlib.sha256()
    total = 0
    if len(files) > 4096:
        return None
    try:
        for path in sorted(files):
            total += path.stat().st_size
            if total > 256 * 1024 * 1024:
                return None
            if path.is_symlink() or not path.is_file():
                return None
            digest.update(str(path).encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    except OSError:
        return None
    return digest.hexdigest()


def cached_scene(script: Path, generator: str):
    cache = _SCENES.get()
    if cache is None:
        return None
    key = (str(script.resolve()), generator)
    previous = cache.get(key)
    if previous is None:
        return None
    fingerprint, dependencies, scene = previous
    if fingerprint is not None and _inputs(script, dependencies) == fingerprint:
        emit("scene-reused", label=script.name)
        return scene
    cache.pop(key, None)
    return None


def remember_scene(script: Path, generator: str, scene: Any) -> None:
    cache = _SCENES.get()
    if cache is None or scene is None:
        return
    dependencies = tuple(getattr(scene, "source_closure_files", ()))
    fingerprint = _inputs(script, dependencies)
    # One entry at a time bounds native shape retention. The verifier groups
    # each entry's requests together, including assembly interference.
    cache.clear()
    cache[(str(script.resolve()), generator)] = (fingerprint, dependencies, scene)


@functools.lru_cache(maxsize=1)
def tool_identity() -> str:
    import OCP

    digest = hashlib.sha256(canonical({
        "schema": 1, "python": sys.version, "ocp": getattr(OCP, "__version__", "unknown"),
    }))
    package = Path(__file__).resolve().parent
    for path in sorted(package.rglob("*.py")):
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


_IDENTITY_EDGE_SAMPLES = 5
_IDENTITY_FACE_SAMPLES = 3


def shape_identity(shape: Any, *, rigid_placement_invariant: bool = False) -> str:
    """A content hash of `shape`'s geometry, stable across repeated builds.

    `OCP.BinTools.BinTools.Write_s` (this function's predecessor) dumps OCCT's
    internal B-rep container order along with the geometry: a boolean result's
    edge/curve representation lists are populated in an allocation-dependent
    order (observed to vary run to run, including within one process, for
    `part_belt_cell` -- see ADR 0073's amendment), so two builds of the
    identical script produced different bytes for bit-identical geometry. This
    hashes exact sampled points from each face's/edge's own analytic geometry
    instead of OCCT's serialized container bytes, sorted by content rather
    than by traversal order, so it does not depend on that internal order.
    Two genuinely different shapes still hash differently: this is exact
    content, not a tolerance-rounded approximation.
    """
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS

    candidate = shape
    if rigid_placement_invariant:
        transform = shape.Location().Transformation()
        # Translation/proper rotation preserve validity and signed volume.
        # Scaled/mirrored placements retain their exact identity instead.
        if abs(transform.ScaleFactor() - 1.0) < 1e-12 and not transform.IsNegative():
            candidate = shape.Located(TopLoc_Location())

    def point(p: Any) -> tuple[float, float, float]:
        return (p.X(), p.Y(), p.Z())

    def subshapes(kind: Any) -> Iterator[Any]:
        explorer = TopExp_Explorer(candidate, kind)
        while explorer.More():
            yield explorer.Current()
            explorer.Next()

    vertices = [point(BRep_Tool.Pnt_s(TopoDS.Vertex_s(raw))) for raw in subshapes(TopAbs_VERTEX)]

    edges = []
    for raw in subshapes(TopAbs_EDGE):
        adaptor = BRepAdaptor_Curve(TopoDS.Edge_s(raw))
        first, last = adaptor.FirstParameter(), adaptor.LastParameter()
        samples = tuple(
            point(adaptor.Value(first + (last - first) * i / (_IDENTITY_EDGE_SAMPLES - 1)))
            for i in range(_IDENTITY_EDGE_SAMPLES)
        )
        edges.append((int(adaptor.GetType()), int(raw.Orientation()), samples))

    faces = []
    for raw in subshapes(TopAbs_FACE):
        adaptor = BRepAdaptor_Surface(TopoDS.Face_s(raw))
        u0, u1 = adaptor.FirstUParameter(), adaptor.LastUParameter()
        v0, v1 = adaptor.FirstVParameter(), adaptor.LastVParameter()
        # Sorted, not grid-ordered: face content, not sampling-grid traversal order.
        samples = tuple(sorted(
            point(adaptor.Value(
                u0 + (u1 - u0) * i / (_IDENTITY_FACE_SAMPLES - 1),
                v0 + (v1 - v0) * j / (_IDENTITY_FACE_SAMPLES - 1),
            ))
            for i in range(_IDENTITY_FACE_SAMPLES) for j in range(_IDENTITY_FACE_SAMPLES)
        ))
        faces.append((int(adaptor.GetType()), int(raw.Orientation()), samples))

    payload = {
        "shapeType": int(candidate.ShapeType()),
        "vertices": sorted(vertices),
        "edges": sorted(edges),
        "faces": sorted(faces),
    }
    return hashlib.sha256(canonical(payload)).hexdigest()


class Measurements:
    """Resume completed exact-shape checks; an absent/invalid cache is a miss."""

    def __init__(self, entry: Path):
        self.root = entry.parent / "__cadgen__" / "inspection-v2"
        self.enabled = os.environ.get("WORKSHOP_GEOMETRY_CACHE", "1") != "0"
        self.memory: dict[str, Any] = {}
        self.completed = 0
        self.reused = 0
        self.failed = 0

    def run(self, kind: str, label: str, inputs: Callable[[], Any], operation: Callable[[], Any], *, failed: Callable[[Any], bool]) -> Any:
        emit("operation-start", kind=kind, label=label, completed=self.completed, failures=self.failed)
        key = hashlib.sha256(canonical([tool_identity(), kind, inputs()])).hexdigest()
        value = self.memory.get(key)
        reused = value is not None
        path = self.root / (key + ".json")
        if value is None and self.enabled:
            try:
                with self._directory() as directory:
                    fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                    with os.fdopen(fd, "rb") as stream:
                        identity = os.fstat(stream.fileno())
                        if stat.S_ISREG(identity.st_mode) and identity.st_size <= 1_000_000:
                            document = json.loads(stream.read(1_000_001))
                            candidate = document["result"]
                            if (isinstance(candidate, dict) and not candidate.get("unverified")
                                    and document["key"] == key
                                    and document["sha256"] == hashlib.sha256(canonical(candidate)).hexdigest()):
                                failed(candidate)  # reject a malformed measurement as a cache miss
                                value = candidate
                                reused = True
            except (OSError, ValueError, KeyError, TypeError):
                pass
        if value is None:
            value = operation()
        # Unknown results are never reusable evidence. Each caller preserves
        # that status and reports it rather than manufacturing a successful test.
        if isinstance(value, dict) and not value.get("unverified"):
            self.memory[key] = value
            if self.enabled and not reused:
                document = {"key": key, "result": value, "sha256": hashlib.sha256(canonical(value)).hexdigest()}
                try:
                    with self._directory() as directory:
                        temporary = "." + uuid.uuid4().hex + ".tmp"
                        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
                        try:
                            with os.fdopen(fd, "wb") as stream:
                                stream.write(canonical(document))
                            os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
                        finally:
                            try:
                                os.unlink(temporary, dir_fd=directory)
                            except FileNotFoundError:
                                pass
                except OSError:
                    pass  # Cache availability never changes a verdict.
        self.completed += 1
        self.reused += int(reused)
        self.failed += int(failed(value))
        emit("operation-done", kind=kind, label=label, completed=self.completed, failures=self.failed, reused=self.reused)
        return value

    @contextlib.contextmanager
    def _directory(self):
        # Walk writable cache components through descriptors. A concurrent
        # rename/symlink swap cannot redirect cache IO outside the opened tree.
        project = self.root.parent.parent
        if project.absolute() != project.resolve():
            raise OSError("cache project path contains a symlink")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(project, flags)
        try:
            for name in ("__cadgen__", "inspection-v2"):
                try:
                    os.mkdir(name, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(name, flags, dir_fd=fd)
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)
