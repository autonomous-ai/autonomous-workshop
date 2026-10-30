"""A schema 10 Design Contract's Electrical section (ADR 0095).

A powered toy states its circuit in the contract, so Make builds the circuit
the owner approved and the host can hold Make's power report to it. The
section is short on purpose: what design-a-toy grilled (the parts, each
complete path, the supply, the current, the standby drain, the runtime, the
switch logic and who joins the leads), not a schematic. Make still writes
the full ``measure/power.json`` of the vendored
``electromechanical-integration`` skill and passes its ``check_power`` gate;
the host checks that report against this section before Make is accepted
(``workshop.make.power``).

The shape, in brief::

    "electrical": {
      "parts": [{"id": "cells", "bought": "cell-aaa", "count": 2, "role": "source"},
                {"id": "plate", "bought": "contact-aaa-plate", "role": "connector"},
                {"id": "switch", "bought": "microswitch-mini-lever", "role": "switch"},
                {"id": "resistor", "bought": "resistor-75r", "role": "controller"},
                {"id": "led", "bought": "led-5mm-amber-diffused", "role": "load"},
                {"id": "wire", "bought": "wire-28awg", "role": "wire"}],
      "paths": [{"id": "screen-light", "load": "led", "current_ma": 12.7,
                 "sequence": ["cells", "plate", "switch", "resistor", "led", "cells"]}],
      "supply_v": {"min": 2.4, "nominal": 3.0, "max": 3.2},
      "standby_ma": 0,
      "runtime_h": 60,
      "switch_logic": "The floppy fully in presses the NO microswitch: on. Out: off.",
      "assembled_by": "maker",
      "joins": "solder",
      "batteries_included": false
    }

A product powered by the buyer's own charger (ADR 0095 amendment, E1)
carries no source: its source part is ``{"id": "usb-supply", "role":
"source", "external": true}``, which names no Bought Part, and each path
from it passes a carried ``inlet`` part (the USB receptacle). That maps to
``check_power``'s ``external`` boundary: a non-carried source and a carried
inlet. Such a circuit has no cells to run down, so its ``runtime_h`` is null
or absent, and ``batteries_included`` is false.

Roles are ``check_power``'s. A path lists its parts from the source back to
the source, without wires: Make's report may put any wire segment between
them. Every Bought Part the section names is a catalogue entry, sealed beside
the contract with the rest of its catalogue snapshot, so a powered toy that
is not a kit still carries its Bought Parts (ADR 0095 decision 2). A kit's
Assembly Tree and its Electrical section name the same catalogue entries.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from workshop.wish.catalogues import Catalogues

# check_power's component roles (power-manifest.md, schema 3).
ROLES = ("source", "protection", "switch", "controller", "connector", "wire",
         "actuator", "load", "inlet")
LOADS = ("load", "actuator")
# Which roles a catalogue category may play. A resistor is an ``other``
# Bought Part playing ``controller`` (current limiting) or ``protection``.
CATEGORY_ROLES = {
    "power": ("source",),
    "cell": ("source",),
    "contact": ("connector",),
    "switch": ("switch",),
    "lamp": ("load",),
    "wire": ("wire",),
    "other": ("protection", "controller", "connector", "load", "actuator", "inlet"),
}
# Categories a kit's tree holds that belong in its circuit.
ELECTRICAL_CATEGORIES = ("power", "cell", "contact", "switch", "lamp", "wire")
ASSEMBLERS = ("maker", "buyer")
JOINS = ("solder", "solderless")
MAX_PARTS = 40
MAX_PATHS = 12
MAX_COUNT = 99
MAX_TEXT_CHARS = 300
MAX_SUPPLY_V = 24.0
MAX_CURRENT_MA = 5000.0
FIELDS = {"parts", "paths", "supply_v", "standby_ma", "runtime_h", "switch_logic",
          "assembled_by", "joins", "batteries_included"}
# ``runtime_h`` may be absent when every source is external.
EXTERNAL_OPTIONAL = {"runtime_h"}
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ContractElectrical:
    """The validated section, kept as the exact JSON the contract sealed, and
    the catalogue entries it names as they read when the contract was parsed.
    ``unconfirmed`` names the entries the owner has not confirmed."""

    section: Dict[str, Any]
    catalogue: Mapping[str, Any] = field(default_factory=dict)
    unconfirmed: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return self.section

    def catalogue_snapshot(self) -> Dict[str, Any]:
        return copy.deepcopy(dict(self.catalogue))


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_TEXT_CHARS


def parse_electrical(
    value: Any, catalogues: Catalogues, errors: List[str],
    tree_bought: Optional[Mapping[str, str]] = None,
) -> Optional[ContractElectrical]:
    """The section, or None with every failure appended to ``errors``.
    ``tree_bought`` maps a kit's Bought Part ids to their catalogue ids."""

    label = "electrical"
    before = len(errors)
    if not isinstance(value, dict):
        errors.append("%s must be an object" % label)
        return None
    unknown = sorted(set(value) - FIELDS)
    if unknown:
        errors.append("%s has unknown field(s): %s" % (label, ", ".join(unknown)))

    parts: Dict[str, Dict[str, Any]] = {}
    external = set()
    used: Dict[str, Any] = {}
    unconfirmed = set()
    items = value.get("parts")
    if not isinstance(items, list) or not items or len(items) > MAX_PARTS:
        errors.append("%s.parts must list 1 to %d circuit parts" % (label, MAX_PARTS))
        items = []
    for index, item in enumerate(items):
        where = "%s.parts[%d]" % (label, index)
        if isinstance(item, dict) and item.get("external") is not None:
            # The buyer's own supply: no Bought Part, never carried.
            if set(item) != {"id", "role", "external"} or item["external"] is not True:
                errors.append("%s, an external source, must be exactly {id, role: source, external: true}: "
                              "it is no Bought Part" % where)
                continue
            if item["role"] != "source":
                errors.append("%s: only a source is external" % where)
                continue
        elif not isinstance(item, dict) or not {"id", "bought", "role"} <= set(item) or not set(item) <= {
            "id", "bought", "role", "count"
        }:
            errors.append("%s must be {id, bought, role} with an optional count, or an external source "
                          "{id, role, external}" % where)
            continue
        identifier = item["id"]
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            errors.append("%s.id must be a kebab-case mnemonic" % where)
            continue
        if identifier in parts:
            errors.append("%s.id repeats %r" % (where, identifier))
            continue
        if item.get("external") is True:
            external.add(identifier)
            parts[identifier] = item
            continue
        count = item.get("count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_COUNT:
            errors.append("%s.count must be 1 to %d" % (where, MAX_COUNT))
        role = item["role"]
        if role not in ROLES:
            errors.append("%s.role must be one of check_power's roles: %s" % (where, ", ".join(ROLES)))
        entry = catalogues.parts.get(item["bought"]) if isinstance(item["bought"], str) else None
        if entry is None:
            errors.append(
                "%s.bought names %r, which is not in the Bought Part catalogue: one outside it "
                "needs the owner's approval" % (where, item["bought"])
            )
        elif entry.material:
            errors.append("%s.bought names %r, a %s, which is no circuit part" % (where, entry.id, entry.category))
        else:
            allowed = CATEGORY_ROLES.get(entry.category, ())
            if role in ROLES and role not in allowed:
                errors.append(
                    "%s: a %s Bought Part plays %s, not %s"
                    % (where, entry.category, " or ".join(allowed) or "no circuit role", role)
                )
            used[entry.id] = entry
            if not entry.confirmed:
                unconfirmed.add("bought-parts.json:%s" % entry.id)
        parts[identifier] = item

    def role(identifier: Any) -> Optional[str]:
        item = parts.get(identifier) if isinstance(identifier, str) else None
        return None if item is None else item.get("role")

    if parts and not any(role(key) == "source" for key in parts):
        errors.append("%s.parts has no source: a powered toy carries its cells or battery box, or names "
                      "the buyer's supply as an external source" % label)
    carried_sources = [key for key in parts if role(key) == "source" and key not in external]
    if external and carried_sources:
        errors.append("%s.parts mixes external and carried sources (%s): check_power's boundary is "
                      "one or the other" % (label, ", ".join(sorted(carried_sources))))
    if external and not any(role(key) == "inlet" for key in parts):
        errors.append("%s.parts has an external source but no inlet: the toy carries the socket "
                      "its supply plugs into" % label)
    only_external = bool(external) and not carried_sources
    missing = sorted(FIELDS - set(value) - (EXTERNAL_OPTIONAL if only_external else set()))
    if missing:
        errors.append("%s is missing: %s" % (label, ", ".join(missing)))
    on_path = set()
    paths = value.get("paths")
    if not isinstance(paths, list) or not paths or len(paths) > MAX_PATHS:
        errors.append("%s.paths must list 1 to %d complete paths, one per load" % (label, MAX_PATHS))
        paths = []
    path_ids = set()
    for index, item in enumerate(paths):
        where = "%s.paths[%d]" % (label, index)
        if not isinstance(item, dict) or set(item) != {"id", "load", "current_ma", "sequence"}:
            errors.append("%s must be exactly {id, load, current_ma, sequence}" % where)
            continue
        if not isinstance(item["id"], str) or not _ID.fullmatch(item["id"]) or item["id"] in path_ids:
            errors.append("%s.id must be a kebab-case mnemonic used once" % where)
        path_ids.add(item["id"])
        current = item["current_ma"]
        if not _number(current) or not 0 < current <= MAX_CURRENT_MA:
            errors.append("%s.current_ma must be the load's current, above 0 and at most %g mA" % (where, MAX_CURRENT_MA))
        sequence = item["sequence"]
        if not isinstance(sequence, list) or len(sequence) < 3 or not all(isinstance(key, str) for key in sequence):
            errors.append("%s.sequence must name the parts from the source back to it" % where)
            continue
        strangers = [key for key in sequence if key not in parts]
        if strangers:
            errors.append("%s.sequence names %s, which is no electrical part" % (where, ", ".join(sorted(set(strangers)))))
            continue
        on_path.update(sequence)
        source = sequence[0]
        if role(source) != "source" or sequence[-1] != source or sequence.count(source) != 2:
            errors.append("%s.sequence begins and ends at its source, and passes it nowhere else" % where)
        if source in external and not any(role(key) == "inlet" for key in sequence[1:-1]):
            errors.append("%s.sequence leaves the external source %s through no inlet: the path is "
                          "incomplete inside the toy" % (where, source))
        if any(role(key) == "wire" for key in sequence):
            errors.append("%s.sequence leaves wires out: Make's power report places them" % where)
        load = item["load"]
        if role(load) not in LOADS:
            errors.append("%s.load must name a load or actuator part" % where)
        elif sequence.count(load) != 1:
            errors.append("%s.sequence holds its load %s exactly once" % (where, load))
        inline = [key for key in sequence[1:-1] if role(key) in LOADS + ("source",) and key != load]
        if inline:
            errors.append("%s.sequence carries another source or load inline: %s" % (where, ", ".join(inline)))
    for key in sorted(parts):
        if role(key) != "wire" and key not in on_path:
            errors.append("electrical part %s is on no path" % key)

    supply = value.get("supply_v")
    if (
        not isinstance(supply, dict) or set(supply) != {"min", "nominal", "max"}
        or not all(_number(supply[key]) for key in ("min", "nominal", "max"))
        or not 0 < supply["min"] <= supply["nominal"] <= supply["max"] <= MAX_SUPPLY_V
    ):
        errors.append("%s.supply_v must be {min, nominal, max} volts, 0 < min <= nominal <= max <= %g"
                      % (label, MAX_SUPPLY_V))
    standby = value.get("standby_ma")
    if not _number(standby) or not 0 <= standby <= MAX_CURRENT_MA:
        errors.append("%s.standby_ma must be the drain with the toy off, 0 for a mechanical switch" % label)
    runtime = value.get("runtime_h")
    if only_external:
        if runtime is not None:
            errors.append("%s.runtime_h is null or absent: every source is external, so no cells run "
                          "down" % label)
    elif "runtime_h" in value and (not _number(runtime) or runtime <= 0):
        errors.append("%s.runtime_h must be the hours one set of cells lights the load" % label)
    if not _text(value.get("switch_logic")):
        errors.append("%s.switch_logic must say in at most %d characters what turns it on and off"
                      % (label, MAX_TEXT_CHARS))
    if value.get("assembled_by") not in ASSEMBLERS:
        errors.append("%s.assembled_by must be %s: who joins the leads" % (label, " or ".join(ASSEMBLERS)))
    if value.get("joins") not in JOINS:
        errors.append("%s.joins must be %s" % (label, " or ".join(JOINS)))
    if not isinstance(value.get("batteries_included"), bool):
        errors.append("%s.batteries_included must be true or false" % label)
    elif only_external and value["batteries_included"]:
        errors.append("%s.batteries_included is false: every source is external" % label)

    if tree_bought is not None:
        named = {item.get("bought") for item in parts.values() if "bought" in item}
        for part, catalogue_id in sorted(tree_bought.items()):
            entry = catalogues.parts.get(catalogue_id)
            if entry is not None and entry.category in ELECTRICAL_CATEGORIES and catalogue_id not in named:
                errors.append(
                    "the Assembly Tree's %s (%s) is a %s in no electrical part: a kit's circuit "
                    "names every catalogue entry it wires" % (part, catalogue_id, entry.category)
                )
        for key, item in sorted(parts.items()):
            if key not in external and item.get("bought") not in tree_bought.values():
                errors.append("electrical part %s (%s) is no Bought Part of the Assembly Tree" % (key, item.get("bought")))

    if len(errors) != before:
        return None
    snapshot = {
        "bought_parts": {
            entry.id: {"name": entry.name, "category": entry.category,
                       "sizes": copy.deepcopy(list(entry.sizes)), "confirmed": entry.confirmed}
            for entry in sorted(used.values(), key=lambda item: item.id)
        }
    }
    return ContractElectrical(section=value, catalogue=snapshot, unconfirmed=tuple(sorted(unconfirmed)))


__all__ = ["CATEGORY_ROLES", "ContractElectrical", "ROLES", "parse_electrical"]
