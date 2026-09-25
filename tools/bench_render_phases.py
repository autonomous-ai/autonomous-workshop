#!/usr/bin/env python3
"""Benchmark a render of the Antisol Companion assembly, phase by phase.

Issue #58. This measures the real 222-occurrence Companion assembly
(`toys/ad-astra-antisol-companion`), never a synthetic mesh: the earlier
50 us-per-triangle figure came from a synthetic mesh and had to be walked
back as "the size of the prize, not a promise"
(`docs/BASELINE_CORRECTION_RUN.md`).

It reports wall-clock seconds for three phases -- build, tessellate,
rasterise -- each with the occurrence tessellation cache (`d853a382`,
`render_review.tessellate_occurrences`) cold and warm, plus:

- a multi-camera case: one scene tessellated once, rasterised from several
  cameras, where extra cameras are expected to be nearly free;
- a multi-state case: the three board states `positions.py` defines
  (opening, midgame, endgame), where occurrences that do not move between
  states are expected to be tessellated once.

Run by hand, with a Python that has build123d/OCP/numpy/Pillow installed
(the CAD skill's own interpreter, `$WORKSHOP_PYTHON`):

    "$WORKSHOP_PYTHON" tools/bench_render_phases.py

This script is not run in CI and asserts no timing: it only prints numbers
for a human to read and record.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import runpy
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDERER_PATH = REPO_ROOT / "src/workshop/make/skills/cad/scripts/render_review"
COMPANION_ENTRY = (
    REPO_ROOT / "toys/ad-astra-antisol-companion/make/source/cad/antisol.step.py"
)
CAMERA_VIEWS = ["iso", "front", "top", "rear_iso"]
BOARD_STATES = ["opening", "midgame", "endgame"]


def host_info() -> str:
    """The host's core count and load, since the baseline host was shared
    with other workloads and timings below carry that noise."""
    cpu_count = os.cpu_count()
    try:
        usable = len(os.sched_getaffinity(0))
    except AttributeError:
        usable = cpu_count
    try:
        load1, load5, load15 = os.getloadavg()
        load = f"load1={load1:.2f} load5={load5:.2f} load15={load15:.2f}"
    except OSError:
        load = "load=unavailable"
    return f"cores={cpu_count} usable={usable} {load}"


@contextlib.contextmanager
def timed():
    box = {}
    start = time.perf_counter()
    yield box
    box["seconds"] = time.perf_counter() - start


def load_renderer():
    renderer = runpy.run_path(str(RENDERER_PATH))
    # Toy CAD sources import `cadgen` (the vendored package beside this
    # script), which render_review itself only puts on sys.path lazily, once
    # a tessellation cache is requested. Building the Companion needs it too.
    renderer["_runtime_paths"]()
    return renderer


def load_assemblies():
    cad_dir = str(COMPANION_ENTRY.parent)
    if cad_dir not in sys.path:
        sys.path.insert(0, cad_dir)
    import assemblies  # noqa: PLC0415

    return assemblies


def cache_dir() -> Path:
    return COMPANION_ENTRY.parent / "__cadgen__" / "tessellation-v1"


def clear_cache() -> None:
    shutil.rmtree(cache_dir(), ignore_errors=True)


def build_opening(renderer) -> tuple[float, object]:
    with timed() as box:
        _source, shape = renderer["build_shape"](COMPANION_ENTRY)
    return box["seconds"], shape


def build_state(assemblies, state: str) -> tuple[float, object]:
    with timed() as box:
        shape = assemblies.product_compound(position=state)
    return box["seconds"], shape


def tessellate(renderer, shape, tolerance: float, angular: float | None):
    with timed() as box:
        occurrences = renderer["tessellate_occurrences"](
            shape, tolerance, angular, cache_entry=COMPANION_ENTRY
        )
    return box["seconds"], occurrences


def rasterise_views(renderer, occurrences, views, size: int, pad: float):
    per_view = {}
    with timed() as total:
        for label, azimuth, elevation in views:
            with timed() as box:
                renderer["render"](occurrences, azimuth, elevation, size, pad)
            per_view[label] = box["seconds"]
    return total["seconds"], per_view


def triangle_count(occurrences) -> int:
    return sum(len(faces) for _points, faces, _colour in occurrences)


def single_pass(renderer, tolerance, angular, size, pad, view):
    build_seconds, shape = build_opening(renderer)
    tessellate_seconds, occurrences = tessellate(renderer, shape, tolerance, angular)
    rasterise_seconds, _per_view = rasterise_views(renderer, occurrences, [view], size, pad)
    return {
        "build": build_seconds,
        "tessellate": tessellate_seconds,
        "rasterise": rasterise_seconds,
        "occurrences": len(occurrences),
        "triangles": triangle_count(occurrences),
    }


def report_phase_line(label: str, phases: dict) -> None:
    total = phases["build"] + phases["tessellate"] + phases["rasterise"]
    print(
        f"  {label}: build={phases['build']:.2f}s tessellate={phases['tessellate']:.2f}s "
        f"rasterise={phases['rasterise']:.2f}s total={total:.2f}s "
        f"(occurrences={phases['occurrences']} triangles={phases['triangles']})"
    )


def bench_cold_warm(renderer, tolerance, angular, size, pad, view) -> None:
    print("\n=== phase by phase: single view, tessellation cache cold vs. warm ===")
    clear_cache()
    cold = single_pass(renderer, tolerance, angular, size, pad, view)
    report_phase_line("cold", cold)
    warm = single_pass(renderer, tolerance, angular, size, pad, view)
    report_phase_line("warm", warm)


def bench_multi_camera(renderer, tolerance, angular, size, pad, views) -> None:
    print("\n=== multi-camera: one scene, several cameras, cache warm ===")
    build_seconds, shape = build_opening(renderer)
    tessellate_seconds, occurrences = tessellate(renderer, shape, tolerance, angular)
    total_rasterise, per_view = rasterise_views(renderer, occurrences, views, size, pad)
    print(f"  build={build_seconds:.2f}s tessellate={tessellate_seconds:.2f}s (once)")
    for label, seconds in per_view.items():
        print(f"  rasterise[{label}]={seconds:.2f}s")
    print(f"  rasterise total ({len(views)} cameras)={total_rasterise:.2f}s")


def bench_multi_state(renderer, assemblies, tolerance, angular) -> None:
    print("\n=== multi-state: several board states, cache warm across states ===")
    clear_cache()
    for state in BOARD_STATES:
        build_seconds, shape = build_state(assemblies, state)
        tessellate_seconds, occurrences = tessellate(renderer, shape, tolerance, angular)
        print(
            f"  {state}: build={build_seconds:.2f}s tessellate={tessellate_seconds:.2f}s "
            f"(occurrences={len(occurrences)} triangles={triangle_count(occurrences)})"
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tolerance", type=float, default=0.08)
    parser.add_argument("--angular-tolerance", type=float, default=None)
    parser.add_argument("--size", type=int, default=900)
    parser.add_argument("--pad", type=float, default=0.07)
    parser.add_argument("--view", default="iso", help="named view for the cold/warm phase report")
    parser.add_argument(
        "--cameras", default=",".join(CAMERA_VIEWS), help="comma-separated named views for the multi-camera case"
    )
    parser.add_argument("--skip-multi-camera", action="store_true")
    parser.add_argument("--skip-multi-state", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    print(f"host: {host_info()}")
    print(f"entry: {COMPANION_ENTRY.relative_to(REPO_ROOT)}")
    print(f"tolerance={args.tolerance} angular_tolerance={args.angular_tolerance} size={args.size}")

    renderer = load_renderer()
    view = renderer["parse_view"](args.view)

    bench_cold_warm(renderer, args.tolerance, args.angular_tolerance, args.size, args.pad, view)

    if not args.skip_multi_camera:
        camera_views = [renderer["parse_view"](name) for name in args.cameras.split(",")]
        bench_multi_camera(renderer, args.tolerance, args.angular_tolerance, args.size, args.pad, camera_views)

    if not args.skip_multi_state:
        assemblies = load_assemblies()
        bench_multi_state(renderer, assemblies, args.tolerance, args.angular_tolerance)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
