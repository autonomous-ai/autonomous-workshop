"""Local-only export in text2game's historical payload format.

Dee (2026-08-22): "here's the repo for automating the publishing pipeline —
github.com/nohope88/text2game." That pipeline's publish.py is the PROVEN
draft-import path (admindash uploads -> bin/importdesign -> GCS project
upload -> fe_colors keying -> Telegram), and it is box-bound by design: it
needs the panda-social-backend checkout, the Mongo URI, the GCS service
account, and admindash — none of which live on this Mac, and none of which
Bob should carry (the import API doc's own division: the client holds no
infrastructure secrets).

Bob's autonomous send path never invokes this module. Workshop's canonical
pack, durable Sender intent, Shop Door adapter, and validated Stamp are the
only send authority. This module remains so an operator can assemble and
inspect the exact ``out/<slug>/`` payload text2game's publish.py once consumed.
It cannot rsync, SSH, invoke that publisher, write send.json, advance Bob's
queue, or turn box stdout/a design id into a Stamp. Contract mirrored from
text2game/publish.py @ 2026-08-22:

    out/<slug>/
      discover.md            WINNER: <slug> / pitch line   (title + desc source)
      seed.md                fallback description
      assembled.stl          required for the 3D viewer upload
      fe_parts/*.stl         per-part meshes, bare ids
      part_colors.json       {part_id: "#hex"} — publish suffixes .stl
      renders/assembled.png  thumb #1 (colored assembly, NEVER origin-pose)
      concept.png            thumb #2, optional
      slice_report.json      measured print facts, optional — NEVER fabricated

Two rules baked in:

- The AI-disclosure sentence LEADS the pitch. text2game's fit_desc() trims
  the tail on a word boundary (facts get their budget first), so a trailing
  disclosure could be truncated away; a leading one survives every cut.
- slice_report.json is copied only if a real slicer wrote one. Its numbers
  are "the only sentence nobody can reconstruct" (text2game publish.py) —
  a fabricated one would put invented grams on a storefront.
"""

import json
import os
import shutil

#: Dee 2026-08-24, verbatim: the listing byline is exactly "By Bob." — the
#: same shape Alice used on Blindcap. AI authorship rides on the byline and
#: the ai-created tag, never a paragraph of explanation.
DISCLOSURE_LINE = "By Bob."

def _home():
    from harness import queue
    return queue.bob_home()


def _game_dir(slug):
    return os.path.join(_home(), "toys", slug)


def _read_json_or_none(path):
    try:
        with open(path) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _find_first(gdir, candidates):
    for rel in candidates:
        path = os.path.join(gdir, rel)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def export_text2game(slug):
    """Write toys/<slug>/export_text2game/<slug>/ per the contract above.

    Returns a manifest dict {export_dir, complete, missing, copied} and
    writes it next to the payload as export_manifest.json. Never raises on
    a missing artifact — an incomplete export is a to-do list, not a crash.
    """
    gdir = _game_dir(slug)
    if not os.path.isdir(gdir):
        raise FileNotFoundError("no game dir for %r" % slug)
    listing = _read_json_or_none(os.path.join(gdir, "listing.json")) or {}
    idea = _read_json_or_none(os.path.join(gdir, "idea.json")) or {}

    out = os.path.join(gdir, "export_text2game", slug)
    os.makedirs(os.path.join(out, "fe_parts"), exist_ok=True)
    os.makedirs(os.path.join(out, "renders"), exist_ok=True)
    copied, missing = [], []

    # --- discover.md: title/desc source; disclosure leads (survives fit_desc)
    pitch = (listing.get("description") or idea.get("pitch")
             or idea.get("concept") or "A 3D-printed board game.")
    pitch = " ".join(str(pitch).split())
    if DISCLOSURE_LINE in pitch:  # avoid doubling; we re-lead with it below
        pitch = pitch.replace(DISCLOSURE_LINE, "").strip()
    mechanism = str(idea.get("mechanism") or idea.get("physical_hook") or "")
    discover = "WINNER: %s\n\n%s %s\n" % (slug, DISCLOSURE_LINE, pitch)
    if mechanism:
        discover += "Mechanism: %s\n" % " ".join(mechanism.split())
    with open(os.path.join(out, "discover.md"), "w") as handle:
        handle.write(discover)
    with open(os.path.join(out, "seed.md"), "w") as handle:
        handle.write("%s %s\n" % (DISCLOSURE_LINE, pitch))
    copied += ["discover.md", "seed.md"]

    parts_dir = os.path.join(gdir, "parts")
    part_stls = sorted(
        f for f in (os.listdir(parts_dir) if os.path.isdir(parts_dir) else [])
        if f.lower().endswith(".stl") and not f.startswith("."))

    # --- assembled.stl: explicit name wins; else the largest mesh, noted.
    assembled = _find_first(gdir, [
        "parts/assembled.stl", "parts/%s.stl" % slug, "assembled.stl"])
    if assembled is None and part_stls:
        largest = max(part_stls, key=lambda f: os.path.getsize(
            os.path.join(parts_dir, f)))
        assembled = os.path.join(parts_dir, largest)
        copied.append("assembled.stl (from largest part %s — check it IS the "
                      "assembly)" % largest)
    if assembled:
        shutil.copyfile(assembled, os.path.join(out, "assembled.stl"))
        if "assembled.stl" not in " ".join(copied):
            copied.append("assembled.stl")
    else:
        missing.append("assembled.stl — the viewer upload needs the "
                       "assembled mesh; the build stage must export it")

    # --- fe_parts/: every part mesh except the assembly itself
    for name in part_stls:
        if os.path.join(parts_dir, name) == assembled:
            continue
        shutil.copyfile(os.path.join(parts_dir, name),
                        os.path.join(out, "fe_parts", name))
    if part_stls:
        copied.append("fe_parts/ (%d meshes)" % len(part_stls))

    # --- part_colors.json (bare ids fine; publish.py suffixes .stl itself)
    colors = _find_first(gdir, ["parts/part_colors.json", "part_colors.json"])
    if colors:
        shutil.copyfile(colors, os.path.join(out, "part_colors.json"))
        copied.append("part_colors.json")

    # --- renders: colored assembly hero; NEVER the origin-pose review sheets
    hero = _find_first(gdir, [
        "parts/renders/assembled.png", "renders/assembled.png",
        "parts/render/assembled.png", "review/assembled.png"])
    if hero:
        shutil.copyfile(hero, os.path.join(out, "renders", "assembled.png"))
        copied.append("renders/assembled.png")
    else:
        missing.append("renders/assembled.png — a colored assembly render; "
                       "origin-pose review sheets must never reach a storefront")
    concept = _find_first(gdir, ["concept.png", "review/concept.png"])
    if concept:
        shutil.copyfile(concept, os.path.join(out, "concept.png"))
        copied.append("concept.png")

    # --- slice_report.json: measured or absent. Never fabricated.
    slice_report = _find_first(gdir, ["parts/slice_report.json",
                                      "slice_report.json"])
    if slice_report:
        shutil.copyfile(slice_report, os.path.join(out, "slice_report.json"))
        copied.append("slice_report.json (measured)")

    # --- the rulebook travels in the bundle even though publish.py skips it
    rules = _find_first(gdir, ["RULES.md", "rules.md"])
    if rules:
        shutil.copyfile(rules, os.path.join(out, "rulebook.md"))
        copied.append("rulebook.md (print-bundle only; page content skips it "
                      "per Tam's 2026-08-20 call)")

    complete = not missing
    manifest = {
        "slug": slug,
        "export_dir": out,
        "complete": complete,
        "missing": missing,
        "copied": copied,
        "instructions": [
            "Local compatibility export only; inspect these files in place.",
            "Use the shared Workshop model-only Shop path for any draft.",
        ],
    }
    with open(os.path.join(os.path.dirname(out), "export_manifest.json"),
              "w") as handle:
        json.dump(manifest, handle, indent=2)
    return manifest


def push_box(slug, timeout_s=900):
    """Refuse the retired rsync/SSH publisher before any local or remote I/O."""
    del slug, timeout_s
    raise RuntimeError(
        "push_box is retired: bob export is local inspection only; send the "
        "inspected model through the shared Workshop model-only Shop path"
    )
