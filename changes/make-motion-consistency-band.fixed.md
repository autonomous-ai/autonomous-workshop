- Make motion checks judge Boolean volume agreement within a band that scales
  with the operand volumes instead of a fixed 0.000001 mm3, and fall back to
  both differences when the union is unavailable, so accepted parts of
  thousands of mm3 are no longer reported inconclusive; gross disagreement
  still fails closed.
