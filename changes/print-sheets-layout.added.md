- Add `print_sheets.py` to the print-details skill (ADR 0091 decision 6): a
  deterministic tool that lays a schema 6 contract's Print Pieces out on A4
  sheets, one stock per page, and writes a print-at-100 % PDF with cut and
  fold lines, ids and a scale bar, PNG previews and a JSON report. It fails
  a piece that fits no sheet, a cut edge under 5 mm, and art that is
  missing, mis-shaped or under 300 dpi.
