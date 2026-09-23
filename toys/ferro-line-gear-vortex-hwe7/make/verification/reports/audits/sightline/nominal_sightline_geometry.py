"""Exact STEP-derived witness geometry; no pass/fail grading."""
import hashlib
from math import atan2, hypot
from pathlib import Path
from build123d import Align, CenterOf, Color, Compound, Cylinder, Face, GeomType, Location, Pos, Rot, Solid, import_step

ROOT = Path(__file__).resolve().parent
PRODUCT = ROOT.parent / 'product' / 'gear_vortex'


def pinned_step(filename, expected_hash):
    path = PRODUCT / filename
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f'Probe source STEP changed: {filename}')
    return import_step(path)


def sightline(expected_hash):
    original = pinned_step('gear_vortex.step', expected_hash)
    leaves = []

    def walk(node, parent_pose):
        pose = parent_pose * node.location
        children = list(node.children)
        if children:
            for child in children:
                walk(child, pose)
        else:
            if len(node.solids()) != 1:
                raise ValueError('Expected one solid in each imported product occurrence')
            # Fresh wrapper avoids copying any parent ownership graph.
            body = Solid(node.wrapped)
            body.location = pose
            body.parent = None
            leaves.append(body)

    walk(original, Location())
    if len(leaves) != 40:
        raise ValueError(f'Expected all 40 product occurrences, found {len(leaves)}')
    product = Compound(leaves)
    product.label = 'all_40_product_solids'
    product.color = Color(0.25, 0.25, 0.25)
    if product.children or len(product.solids()) != 40:
        raise ValueError('Witness product must be one compound leaf retaining all 40 solids')
    probe = Pos(0, 200, 120) * Rot(90, 0, 0) * Cylinder(
        7.0, 400, align=(Align.CENTER, Align.CENTER, Align.MIN))
    probe.label = 'sightline_radius_7_00'
    probe.color = Color(1, 0, 0)
    return Compound(label='sightline_witness', children=[product, probe])

