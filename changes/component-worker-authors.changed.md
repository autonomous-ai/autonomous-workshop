- Spark Make: each Component Worker now writes its Component's first draft as
  well as repairing it, and the Workshop Manager writes only the shared
  parameter and feature files with every joint fixed (ADR 0080). A Workshop
  hook refuses a Component's `make_round` round from any agent but its worker,
  and the host refuses Make output holding a Component round no worker ran.
  When two Design Contract statements cannot both hold, Make now stops with a
  need that quotes both instead of choosing one itself.
