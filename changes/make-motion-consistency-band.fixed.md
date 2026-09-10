- Make motion checks judge Boolean volume agreement within a band that scales
  with the operand volumes instead of a fixed 0.000001 mm3, arbitrate a
  disagreeing or unavailable union with both differences, and otherwise accept
  a pose only when every formulation agrees on the collision verdict, so
  accepted parts of thousands of mm3 and interpenetrating thin shells are no
  longer reported inconclusive; split verdicts still fail closed.
