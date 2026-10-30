"""The host's check of a Made powered toy's power report (ADR 0095).

A schema 10 Design Contract with an Electrical section states the circuit
the owner approved. Make's final verification runs ``verify_project
--powered``, which refuses without ``measure/power.json`` and runs the
vendored ``electromechanical-integration`` gate ``check_power`` on it. Before
Make is accepted the host checks, on the exact sealed bytes and without
rebuilding any geometry or rerunning the gate (ADR 0061), that

- the Made CAD project declares ``measure/power.json`` and the final
  pipeline record, and the record's newest run passed ``check_power``;
- the report is the contract's circuit: every non-wire electrical part is a
  report component with the same id and role, a wire part has at least one
  wire component, and every contract path is a report path with the same id,
  source and load whose sequence, wires left out, is the contract's;
- each report path is rated for the contract's current, and the source's
  declared voltage covers the contract's supply range;
- a contract whose source is the buyer's own supply (``external``, ADR 0095
  amendment) has a report with ``check_power``'s ``external`` boundary, that
  source not carried; a contract that carries its source has no external
  boundary.

The report's evidence, mounts, wire envelopes and current capacity stay
``check_power``'s and ``check_mount``'s to judge; this check adds only that
the report describes the sealed circuit and not some other one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError

ELECTRICAL_SCHEMA_VERSION = 10
POWER_PATH = "measure/power.json"
PIPELINE_PATH = "measure/verification-pipeline.md"
POWER_GATE = "check_power"
POWER_SCHEMA_VERSIONS = (2, 3)
# A float tolerance only: a report rated at the contract's current passes.
CURRENT_TOLERANCE_A = 1e-9


def has_electrical(contract: Any) -> bool:
    """Whether a sealed Design Contract states a circuit (schema 10)."""

    if not isinstance(contract, Mapping):
        return False
    schema = contract.get("schema_version")
    return (
        type(schema) is int and schema >= ELECTRICAL_SCHEMA_VERSION
        and isinstance(contract.get("electrical"), Mapping)
    )


def external_sources(electrical: Mapping[str, Any]) -> list[str]:
    """The ids of the circuit's external sources: the buyer's own supply,
    which the toy does not carry and no one buys with it."""

    return [item["id"] for item in electrical.get("parts") or () if item.get("external") is True]


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def check_power_report(electrical: Mapping[str, Any], report: Any) -> list[str]:
    """Every way ``report`` (a parsed power.json) is not the circuit
    ``electrical`` states; empty when it is."""

    problems: list[str] = []
    if not isinstance(report, Mapping) or report.get("schema_version") not in POWER_SCHEMA_VERSIONS:
        return ["%s is not a schema 2 or 3 power report" % POWER_PATH]
    components = {
        item.get("id"): item for item in report.get("components") or ()
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    parts = {item["id"]: item for item in electrical.get("parts") or ()}
    external = external_sources(electrical)
    boundary = report.get("boundary")
    if external and boundary != "external":
        problems.append("the contract's source %s is external, but the report's boundary is %s, not "
                        "external" % (", ".join(external), boundary))
    elif not external and boundary == "external":
        problems.append("the contract carries its source, but the report's boundary is external")
    for key in external:
        component = components.get(key)
        if isinstance(component, Mapping) and component.get("carried") is not False:
            problems.append("report source %s is the buyer's external supply, so carried is false, not %s"
                            % (key, component.get("carried")))
    wires = {key for key, item in components.items() if item.get("role") == "wire"}
    for key, item in sorted(parts.items()):
        if item["role"] == "wire":
            if not wires:
                problems.append("the contract buys wire %s, but the report has no wire component" % key)
            continue
        component = components.get(key)
        if component is None:
            problems.append("the contract's %s %s is no report component" % (item["role"], key))
        elif component.get("role") != item["role"]:
            problems.append("report component %s is a %s, not the contract's %s"
                            % (key, component.get("role"), item["role"]))
    paths = {
        item.get("id"): item for item in report.get("paths") or ()
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    for path in electrical.get("paths") or ():
        found = paths.get(path["id"])
        if found is None:
            problems.append("the contract's path %s is no report path" % path["id"])
            continue
        target = found.get("load", found.get("actuator"))
        if found.get("source") != path["sequence"][0] or target != path["load"]:
            problems.append("report path %s runs %s to %s, not the contract's %s to %s"
                            % (path["id"], found.get("source"), target, path["sequence"][0], path["load"]))
        sequence = found.get("sequence")
        bare = [key for key in sequence or () if key not in wires] if isinstance(sequence, list) else None
        if bare != list(path["sequence"]):
            problems.append("report path %s, wires left out, is %s, not the contract's %s"
                            % (path["id"], bare, list(path["sequence"])))
        required = path["current_ma"] / 1000.0
        for field in ("required_continuous_current_a", "required_peak_current_a"):
            rated = found.get(field)
            if not _number(rated) or rated + CURRENT_TOLERANCE_A < required:
                problems.append("report path %s.%s is %s A, below the contract's %g mA"
                                % (path["id"], field, rated, path["current_ma"]))
        source = components.get(path["sequence"][0])
        voltage = source.get("voltage_v") if isinstance(source, Mapping) else None
        supply = electrical.get("supply_v") or {}
        if (
            not isinstance(voltage, Mapping) or not _number(voltage.get("min")) or not _number(voltage.get("max"))
            or voltage["min"] > supply.get("min", 0) or voltage["max"] < supply.get("max", 0)
        ):
            problems.append("report source %s declares %s V, which does not cover the contract's "
                            "supply %g-%g V" % (path["sequence"][0], voltage, supply.get("min", 0),
                                                supply.get("max", 0)))
    return problems


def verify_made_power(run_root: Path, made: Any, contract: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The accepted circuit's account, or None for a contract without one.
    Raises ContractError naming what is wrong."""

    if not has_electrical(contract):
        return None
    electrical = contract["electrical"]
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)

    def content(relative: str, missing: str) -> bytes:
        path = (prefix / relative).as_posix()
        entry = entries.get(path)
        if entry is None:
            raise ContractError(missing)
        data = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(data) != entry.bytes or hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ContractError("the power file %s differs from the Made manifest" % relative)
        return data

    raw = content(POWER_PATH, "the Made CAD project lacks its power report, %s: the contract "
                              "states a circuit (ADR 0095)" % POWER_PATH)
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("%s is not JSON" % POWER_PATH) from exc
    record = content(PIPELINE_PATH, "the Made CAD project lacks its final pipeline record, %s" % PIPELINE_PATH)
    # Read with the release's own reader of the record; imported here, as
    # Release depends on Make.
    from workshop.release.direct_publish import parse_pipeline_record

    try:
        rows = parse_pipeline_record(record.decode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("%s is not text" % PIPELINE_PATH) from exc
    # A NOTE row (a planned fit coupon) is verify_project's non-failing
    # limitation, not a run of the gate.
    gate = [row for row in rows if row["gate"] == POWER_GATE and row["status"] != "note"]
    if not gate or any(row["result"] != "pass" for row in gate):
        raise ContractError("final verification did not pass %s on the power report" % POWER_GATE)
    problems = check_power_report(electrical, report)
    if problems:
        raise ContractError("the power report is not the sealed circuit: %s" % "; ".join(problems)[:600])
    return {
        "report": (prefix / POWER_PATH).as_posix(),
        "report_sha256": hashlib.sha256(raw).hexdigest(),
        # The buyer's own supply is no part of the toy.
        "parts": len([item for item in electrical["parts"] if item.get("external") is not True]),
        "boundary": "external" if external_sources(electrical) else "onboard",
        "paths": [{"id": item["id"], "load": item["load"], "current_ma": item["current_ma"]}
                  for item in electrical["paths"]],
        "supply_v": dict(electrical["supply_v"]),
        "standby_ma": electrical["standby_ma"],
        "runtime_h": electrical.get("runtime_h"),
        "assembled_by": electrical["assembled_by"],
        "joins": electrical["joins"],
    }


__all__ = ["check_power_report", "external_sources", "has_electrical", "verify_made_power"]
