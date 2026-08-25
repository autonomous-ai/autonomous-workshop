# Instructions

Owns in-box instructions, evidence-bound product facts, attribution, and the
authenticated private Factory handoff after Playtest passes.

Public API: `workshop.instructions`.

Instructions owns the `LaunchPort` used to import and publish its sealed
product result. Factory adapters implement that port downstream.
