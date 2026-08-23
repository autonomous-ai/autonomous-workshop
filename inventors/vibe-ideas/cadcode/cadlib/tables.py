"""Canonical hardware dimension tables — single source of truth.

All values in millimetres. Pulled from the reference pattern docs and
manufacturer specs. Updating a value here updates every helper that uses it.
"""

from __future__ import annotations


# ISO 4762 socket-head cap screws (clearance hole, self-tap pilot, cap head).
SCREW_TABLE: dict[str, dict[str, float]] = {
    "M2":   {"clearance": 2.4, "self_tap": 1.7, "cap_head_dia": 3.8, "cap_head_h": 2.0},
    "M2.5": {"clearance": 2.9, "self_tap": 2.2, "cap_head_dia": 4.5, "cap_head_h": 2.5},
    "M3":   {"clearance": 3.4, "self_tap": 2.5, "cap_head_dia": 5.5, "cap_head_h": 3.0},
    "M4":   {"clearance": 4.5, "self_tap": 3.3, "cap_head_dia": 7.0, "cap_head_h": 4.0},
    "M5":   {"clearance": 5.5, "self_tap": 4.2, "cap_head_dia": 8.5, "cap_head_h": 5.0},
}


# ISO 4032 hex nuts (flat-to-flat + thickness). pocket_flat adds 0.2 mm
# FDM clearance over the nominal flat-to-flat.
NUT_TABLE: dict[str, dict[str, float]] = {
    "M2":   {"flat": 4.0,  "thick": 1.6, "pocket_flat": 4.2,  "pocket_h": 1.8, "screw_clear": 2.4},
    "M2.5": {"flat": 5.0,  "thick": 2.0, "pocket_flat": 5.2,  "pocket_h": 2.2, "screw_clear": 2.9},
    "M3":   {"flat": 5.5,  "thick": 2.4, "pocket_flat": 5.7,  "pocket_h": 2.6, "screw_clear": 3.4},
    "M4":   {"flat": 7.0,  "thick": 3.2, "pocket_flat": 7.2,  "pocket_h": 3.4, "screw_clear": 4.5},
    "M5":   {"flat": 8.0,  "thick": 4.0, "pocket_flat": 8.2,  "pocket_h": 4.2, "screw_clear": 5.5},
    "M6":   {"flat": 10.0, "thick": 5.0, "pocket_flat": 10.2, "pocket_h": 5.2, "screw_clear": 6.5},
}


# Ruthex (and equivalent) heat-set inserts. pocket_d is the *body* OD between
# knurls — NOT the max-knurl OD. The knurls bite INTO plastic.
HEATSET_TABLE: dict[str, dict[str, float]] = {
    "M2":   {"pocket_d": 3.2, "insert_len": 4.0, "relief_d": 4.0, "relief_h": 0.6},
    "M2.5": {"pocket_d": 3.7, "insert_len": 4.0, "relief_d": 4.5, "relief_h": 0.6},
    "M3":   {"pocket_d": 4.0, "insert_len": 5.7, "relief_d": 5.0, "relief_h": 0.6},
    "M4":   {"pocket_d": 5.6, "insert_len": 8.1, "relief_d": 6.5, "relief_h": 0.6},
    "M5":   {"pocket_d": 6.4, "insert_len": 9.5, "relief_d": 7.5, "relief_h": 0.6},
}


# Standard radial ball bearings. Pocket is sized for an FDM press-fit on a
# stock-calibration printer; shoulder_id keeps the inner race spinning free.
BEARING_TABLE: dict[str, dict[str, float]] = {
    # name    OD,   ID,   H,   pocket_d, shoulder_id, shoulder_h
    "608":    {"od": 22.0, "id":  8.0, "h": 7.0, "pocket": 21.95, "shoulder_id": 12.0, "shoulder_h": 1.0},
    "608ZZ":  {"od": 22.0, "id":  8.0, "h": 7.0, "pocket": 21.95, "shoulder_id": 12.0, "shoulder_h": 1.0},
    "624":    {"od": 13.0, "id":  4.0, "h": 5.0, "pocket": 12.95, "shoulder_id":  7.0, "shoulder_h": 0.8},
    "625":    {"od": 16.0, "id":  5.0, "h": 5.0, "pocket": 15.95, "shoulder_id":  9.0, "shoulder_h": 0.8},
    "688":    {"od": 16.0, "id":  8.0, "h": 5.0, "pocket": 15.95, "shoulder_id": 11.0, "shoulder_h": 0.8},
    "6800":   {"od": 19.0, "id": 10.0, "h": 5.0, "pocket": 18.95, "shoulder_id": 13.5, "shoulder_h": 0.8},
    "6803":   {"od": 26.0, "id": 17.0, "h": 5.0, "pocket": 25.95, "shoulder_id": 20.0, "shoulder_h": 0.8},
    "6900":   {"od": 22.0, "id": 10.0, "h": 6.0, "pocket": 21.95, "shoulder_id": 14.0, "shoulder_h": 1.0},
    "6901":   {"od": 24.0, "id": 12.0, "h": 6.0, "pocket": 23.95, "shoulder_id": 16.0, "shoulder_h": 1.0},
}


# Stock neodymium disc magnets (diameter x thickness, mm).
MAGNET_TABLE: dict[str, dict[str, float]] = {
    "6x3":   {"d": 6.0,  "h": 3.0},
    "6x2":   {"d": 6.0,  "h": 2.0},
    "8x3":   {"d": 8.0,  "h": 3.0},
    "10x3":  {"d": 10.0, "h": 3.0},
    "10x2":  {"d": 10.0, "h": 2.0},
    "12x5":  {"d": 12.0, "h": 5.0},
    "15x3":  {"d": 15.0, "h": 3.0},
    "20x5":  {"d": 20.0, "h": 5.0},
}


# Common cable / wire jacket diameters. Connectors are RECTANGULAR — when
# routing the connector through the channel, size for ``*_connector``;
# when routing the jacket only, use ``*_cable``.
CABLE_TABLE: dict[str, float] = {
    "JST-XH-2":        2.5,
    "JST-XH-4":        3.5,
    "ribbon-flat":     3.0,
    "dupont":          1.0,
    "USB-A-cable":     4.5,
    "USB-A-connector": 4.5,
    "USB-C-cable":     4.0,
    "USB-C-connector": 3.0,
    "micro-USB-cable": 3.5,
    "DC-barrel":       3.5,
    "ethernet-cable":  6.0,
    "ethernet-boot":   9.0,
    "mains-2c":        6.0,
}
