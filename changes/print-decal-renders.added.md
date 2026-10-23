- Draw each Print Piece's art on the review renders (ADR 0091 decision 8).
  print-details tags a decal for every piece it places (its frame in the
  tag's name, so a round's kept B-rep keeps it); `render_review` paints the
  decals of a part entry with their art from `print/art/`, depth-tested,
  flat, oval, standing-card, block-cover and gore-sphere alike, and the
  Display Pose entry moves them with the part. An assembly render shows
  none. The Component Reviewer judges a printed area's place, size and
  outline against the reference, never the drawing inside it.
