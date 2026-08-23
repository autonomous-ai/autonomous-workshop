"""``python scripts/review <project_dir | .step | .step.json>`` — QA review pass.

Renders the assembled model and every named part to multi-view PNGs (the
missing per-part visual the build loop needs to actually *look* at), and
re-surfaces the deterministic geometry warnings cadpy recorded in the
``.step.json`` sidecar.

Prints a single JSON line on stdout::

  {
    "ok": true,
    "stem": "ladybug_robot",
    "warnings": [ { "part", "kind", "detail", "severity" }, ... ],
    "assembled_png": "<abs path>",          // multi-view QA grid (_qa.png); null on fail
    "cover_png": "<abs path>",              // single-iso hero cover (_assembled.png)
    "renders": [ { "part", "stl_path", "png_path" }, ... ],
    "section_png": "<abs path>",            // first cross-section, back-compat
    "section_pngs": [ { "axis", "part", "png_path" }, ... ]
  }

Each per-part PNG is a grid of the part seen from every direction (a 3/4 iso plus
all six axis-aligned faces), so a defect that hides behind the body on one view
shows on another.

By default the assembly is cut through its x, y, and z center planes so INTERIOR
engagement always reads — a peg seated in a socket, a tooth on solid material, a
lip inside its groove — which exterior views hide. Pass ``--section
<x|y|z>[@offset]`` (optionally ``--part <name>``) to target a single plane (e.g.
to hit an interface the center cuts miss), or ``--no-sections`` to skip them.

The PNGs are QA artifacts (the viewer renders the STL); they land in
``<stem>_review/`` next to the model. Rendering never raises — a failed render
yields a null path, not an error.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections.abc import Sequence
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
for _p in (SCRIPTS_DIR, SCRIPTS_DIR / "packages"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


# ---------------------------------------------------------------------------
# Card cover ("hero") look for the web/social publish.
#
# The publish flow zips the workspace and the panda-social import API resolves
# the design cover from the `<stem>_review/` PNGs by name — the render called
# `_assembled.png` is the one it treats as THE cover. So the cover takes the
# `_assembled.png` slot: a single unlabeled iso "hero" in a per-project filament
# color over a soft color-matched gradient. The multi-view slate-blue QA grid the
# build's review-fix loop actually inspects for defects is written alongside as
# `_qa.png` (and surfaced as `assembled_png` in the JSON). Keeping "assembled" out
# of the QA grid's name is deliberate — it must not outscore the cover.
# ---------------------------------------------------------------------------
_COVER_VIEWS = (("", 24.0, -58.0),)  # one iso panel, no title
_COVER_SIZE = 900
_COVER_ZOOM = 1.5  # single hero panel → fill the frame (mplot3d's default reads small)

# Curated filament palette (fully-lit base RGB, 0..1): a per-project color keeps
# the feed varied without the muddy / near-white / near-black misfires raw random
# RGB hits; all read well over the light gradient backdrop.
_COVER_PALETTE = [
    (0.910, 0.475, 0.169),  # orange
    (0.839, 0.271, 0.271),  # red
    (0.910, 0.725, 0.231),  # amber
    (0.243, 0.557, 0.353),  # green
    (0.184, 0.651, 0.604),  # teal
    (0.204, 0.702, 0.831),  # cyan
    (0.298, 0.494, 0.941),  # blue
    (0.486, 0.361, 0.839),  # violet
    (0.851, 0.373, 0.627),  # pink
]


def _cover_color(seed: str) -> tuple[float, float, float]:
    """Pick a palette color deterministically from ``seed`` (the project stem), so a
    given project always renders the same cover color while the feed stays varied.
    Seeding a local RNG keeps it stable across re-renders."""
    return random.Random(seed or "").choice(_COVER_PALETTE)


def _cover_bg(color: tuple[float, float, float]) -> tuple:
    """Soft vertical gradient from the part color: near-white at the top fading to a
    light tint of the color at the bottom, so the backdrop matches the hue."""
    top = tuple(c * 0.06 + 0.94 for c in color)
    bot = tuple(c * 0.30 + 0.70 for c in color)
    return (top, bot)


def render_cover(render_fn, stl_path: Path, out_png: Path, seed: str) -> Path | None:
    """Render the single-iso hero cover for ``stl_path`` into ``out_png`` via the
    shared renderer ``render_fn`` (``render_stl_to_png``). Never raises — a failed
    cover just leaves the QA grid as the publish fallback."""
    color = _cover_color(seed)
    return render_fn(
        str(stl_path),
        str(out_png),
        views=_COVER_VIEWS,
        base_color=color,
        bg=_cover_bg(color),
        size=_COVER_SIZE,
        zoom=_COVER_ZOOM,
    )


# Two isos, front-left and front-right, so the colored sheet shows both sides of
# the assembly. A `camera.json` next to the model ({"elev": E, "azim": A}, written
# by the build agent to match the approved concept's viewpoint) is PREPENDED to
# these, never substituted for one: the concept camera is eyeballed fresh every
# run, so a sheet made only of it has no frame two runs share, and a likeness
# score then carries the build's aim as well as its geometry. Keeping both fixed
# isos costs one panel and leaves every run comparable to every other.
_COLORED_VIEWS = (("iso", 24.0, -58.0), ("iso-mirror", 24.0, 122.0))
_COLORED_SIZE = 900
_COLORED_ZOOM = 1.4


def _concept_view(base_dir: Path) -> tuple[str, float, float] | None:
    """The build's concept-matching camera from `camera.json`, validated.

    Unchecked values reach mplot3d as written: a NaN, an inf or an elevation of
    400 renders an empty or nonsense panel, and the likeness lens then scores
    the renderer instead of the model — which at the build milestone can abort a
    whole cycle. Out-of-range angles are clamped/wrapped to the equivalent legal
    view rather than dropped, since the build's intent is still readable.
    """
    cam_file = base_dir / "camera.json"
    if not cam_file.is_file():
        return None
    try:
        cam = json.loads(cam_file.read_text(encoding="utf-8"))
        elev, azim = float(cam["elev"]), float(cam["azim"])
    except Exception:
        return None
    if not (math.isfinite(elev) and math.isfinite(azim)):
        return None
    return ("concept-cam", max(-89.0, min(89.0, elev)), (azim + 180.0) % 360.0 - 180.0)


def _hex_to_rgb01(value: str) -> tuple[float, float, float] | None:
    value = str(value or "").strip().lstrip("#")
    if len(value) != 6:
        return None
    try:
        return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None


def render_parts_colored(render_fn, base_dir: Path, meta: dict, out_png: Path) -> Path | None:
    """Render the assembled-pose per-part STLs from the sidecar composed in one
    scene, each part in its `part_colors.json` color (fallback: palette cycle).
    Skipped (returns None) when there is no part_colors.json or no parts[] —
    single-part projects already read fine from the plain renders."""
    colors_file = base_dir / "part_colors.json"
    parts = meta.get("parts", []) or []
    if not colors_file.is_file() or not parts:
        return None
    try:
        cmap = json.loads(colors_file.read_text(encoding="utf-8"))
    except Exception:
        cmap = {}
    items = []
    for i, part in enumerate(parts):
        name = str(part.get("name", "")) or "part"
        stl_path = (base_dir / part.get("stlPath", "")).resolve()
        if not stl_path.is_file():
            continue
        # part_colors.json keys instance families by their base name
        # (side_panel.stl covers side_panel_1/_2), so retry with the numeric
        # suffix stripped before falling back to the palette cycle.
        base = re.sub(r"_\d+$", "", name)
        color = _hex_to_rgb01(
            cmap.get(f"{name}.stl") or cmap.get(name) or cmap.get(f"{base}.stl", ""))
        color = color or _COVER_PALETTE[i % len(_COVER_PALETTE)]
        # This sheet is a diagnostic, not the product shot: near-black brief
        # palettes (gunmetal props) shade to mud under Lambert, so scale very
        # dark colors up (hue preserved) until every part stays tellable-apart.
        mx = max(color)
        if 0 < mx < 0.45:
            color = tuple(c * 0.45 / mx for c in color)
        elif mx == 0:
            color = (0.45, 0.45, 0.45)
        items.append((stl_path, color))
    if not items:
        return None
    concept = _concept_view(base_dir)
    views = ((concept,) + _COLORED_VIEWS) if concept else _COLORED_VIEWS
    return render_fn(
        items, out_png, views=views, size=_COLORED_SIZE, zoom=_COLORED_ZOOM)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scripts/review",
        description=(
            "Render the assembled model + each named part to QA PNGs and "
            "re-surface cadpy's deterministic geometry warnings."
        ),
    )
    p.add_argument(
        "input",
        type=Path,
        help=(
            "A generated project dir (containing <stem>.step.json), or a path "
            "to a .step / .step.json file directly."
        ),
    )
    p.add_argument(
        "--stem",
        default=None,
        help="Disambiguate when a directory holds multiple .step.json files.",
    )
    p.add_argument(
        "--section",
        default=None,
        metavar="<x|y|z>[@offset_mm]",
        help=(
            "Also render an INTERIOR cross-section through the given axis-aligned "
            "plane (offset defaults to the bbox center) so mating interiors read — "
            "a peg seated in a socket, a tooth on solid material, a lip in its "
            "groove. Sections the assembled model unless --part is given."
        ),
    )
    p.add_argument(
        "--part",
        default=None,
        help="With --section, cut this named part instead of the assembled model.",
    )
    p.add_argument(
        "--no-sections",
        action="store_true",
        help=(
            "Skip the automatic interior cross-sections. By default (when "
            "--section is not given) the assembly is cut through its x, y, and z "
            "center planes so interior engagement is always visible."
        ),
    )
    return p


def _parse_section(spec: str) -> tuple[str, float | None]:
    """Parse a ``--section`` value like ``z`` or ``z@10.5`` → ``(axis, offset)``."""
    axis, _, off = spec.partition("@")
    axis = axis.strip().lower()
    if axis not in ("x", "y", "z"):
        raise ValueError(f"section axis must be x, y, or z (got {axis!r})")
    offset = float(off.strip()) if off.strip() else None
    return axis, offset


def _resolve_sidecar(input_path: Path, stem: str | None) -> Path | None:
    """Find the ``<stem>.step.json`` sidecar for the given input.

    Raises ``ValueError`` when a directory holds several sidecars and no
    ``--stem`` was given — silently picking one would review the wrong model.
    """
    input_path = input_path.resolve()
    if input_path.is_file():
        if input_path.name.endswith(".step.json"):
            return input_path
        if input_path.suffix == ".step":
            cand = input_path.with_suffix(".step.json")
            return cand if cand.is_file() else None
        return None
    if input_path.is_dir():
        if stem:
            cand = input_path / f"{stem}.step.json"
            return cand if cand.is_file() else None
        sidecars = sorted(input_path.glob("*.step.json"))
        if len(sidecars) > 1:
            names = ", ".join(s.name[: -len(".step.json")] for s in sidecars)
            raise ValueError(
                f"{input_path} holds {len(sidecars)} .step.json sidecars "
                f"({names}) — pass --stem to pick one"
            )
        return sidecars[0] if sidecars else None
    return None


def _err(message: str, code: str = "VALIDATION_FAILED") -> int:
    print(json.dumps({"ok": False, "error": {"code": code, "message": message}}))
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if not args.input.exists():
        return _err(f"input not found: {args.input}")

    try:
        sidecar = _resolve_sidecar(args.input, args.stem)
    except ValueError as exc:
        return _err(str(exc))
    if sidecar is None:
        return _err(
            f"no .step.json sidecar found for {args.input} — generate the model "
            "first with scripts/cad"
        )

    try:
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception as exc:
        return _err(f"failed to read sidecar {sidecar.name}: {exc}")

    base_dir = sidecar.parent
    stem = sidecar.name[: -len(".step.json")]
    warnings = meta.get("validation", {}).get("warnings", []) or []

    from cadpy.render_part import (
        render_stl_section_to_png,
        render_stl_to_png,
        render_stls_to_png,
    )

    review_dir = base_dir / f"{stem}_review"

    # Assembled model (always written by cadpy as <stem>.stl). Two renders:
    #   _qa.png        — multi-view slate-blue QA grid; the render-fix loop reads it
    #                    (surfaced as `assembled_png`) to spot geometry defects.
    #   _assembled.png — single-iso "hero" cover in a per-project filament color;
    #                    the publish API resolves the design cover from this name.
    assembled_stl = base_dir / f"{stem}.stl"
    assembled_png = None
    cover_png = None
    if assembled_stl.is_file():
        rendered = render_stl_to_png(assembled_stl, review_dir / "_qa.png")
        assembled_png = str(rendered) if rendered else None
        cover = render_cover(render_stl_to_png, assembled_stl, review_dir / "_assembled.png", stem)
        cover_png = str(cover) if cover else None

    # Assembled per-part color sheet: the likeness/fidelity lenses read this one
    # next to the approved concept — a missing part is a missing COLOR, which a
    # vision judge can name ("the red grip is absent") instead of describing.
    parts_colored = render_parts_colored(
        render_stls_to_png, base_dir, meta, review_dir / "_parts_colored.png")
    parts_colored_png = str(parts_colored) if parts_colored else None

    # Per-part renders. For single-part projects there is no parts[] list; the
    # assembled render is the part.
    renders: list[dict] = []
    for part in meta.get("parts", []) or []:
        name = str(part.get("name", "")) or "part"
        rel = part.get("stlPath", "")
        stl_path = (base_dir / rel).resolve()
        if not stl_path.is_file():
            renders.append({"part": name, "stl_path": str(stl_path), "png_path": None})
            continue
        rendered = render_stl_to_png(stl_path, review_dir / f"{name}.png")
        renders.append(
            {
                "part": name,
                "stl_path": str(stl_path),
                "png_path": str(rendered) if rendered else None,
            }
        )

    # Interior cross-sections so mating interiors read — a peg seated in a socket,
    # a tooth on solid material, a lip inside its groove — which exterior views
    # hide. An explicit `--section` cuts one targeted plane (assembly or --part);
    # otherwise we auto-cut the assembly through its x, y, and z centers so
    # interior engagement is ALWAYS visible without the reviewer having to ask.
    # `--no-sections` opts out for speed.
    section_pngs: list[dict] = []
    if args.section:
        try:
            axis, offset = _parse_section(args.section)
        except ValueError as exc:
            return _err(str(exc))
        if args.part:
            match = next(
                (p for p in (meta.get("parts") or []) if str(p.get("name")) == args.part),
                None,
            )
            if match is None:
                return _err(f"--part {args.part!r} not found in {sidecar.name}")
            sec_stl = (base_dir / match.get("stlPath", "")).resolve()
            sec_name = args.part
        else:
            sec_stl = assembled_stl
            sec_name = stem
        if sec_stl.is_file():
            out = render_stl_section_to_png(
                sec_stl,
                review_dir / f"{sec_name}_section_{axis}.png",
                axis=axis,
                offset=offset,
            )
            section_pngs.append(
                {"axis": axis, "part": sec_name, "png_path": str(out) if out else None}
            )
    elif not args.no_sections and assembled_stl.is_file():
        for axis in ("x", "y", "z"):
            out = render_stl_section_to_png(
                assembled_stl,
                review_dir / f"{stem}_section_{axis}.png",
                axis=axis,
                offset=None,
            )
            section_pngs.append(
                {"axis": axis, "part": stem, "png_path": str(out) if out else None}
            )

    print(
        json.dumps(
            {
                "ok": True,
                "stem": stem,
                "warnings": warnings,
                "assembled_png": assembled_png,
                "cover_png": cover_png,
                "parts_colored_png": parts_colored_png,
                "renders": renders,
                # First cross-section path, kept for back-compat with callers that
                # read a single `section_png`; `section_pngs` carries all of them.
                "section_png": next(
                    (s["png_path"] for s in section_pngs if s["png_path"]), None
                ),
                "section_pngs": section_pngs,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
