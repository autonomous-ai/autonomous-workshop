- Spark Make in Contract Mode: `make_round --shared-helpers` now checks the
  Shared Helper rules of ADR 0082 before it builds a sample. Every design value
  cites an existing wiki page with `# wiki: <slug>` and appears in an
  `assert`, a standard element comes from `bd_warehouse` or `py_gearworks`,
  and no helper writes an involute. The installed `features/print_details.py`
  is a Shared Helper, exempt from the citation rule only while its bytes are
  the library's.
