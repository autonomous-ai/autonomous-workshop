- The image-to-cad likeness gate and measurement tool read a cut-out
  reference's silhouette from its alpha channel (`alpha > 127` is the
  subject) instead of converting to RGB first, which had admitted transparent
  pixels as subject and scored a reference at 0.655 against its own outline.
  Photographs and opaque images are unchanged; the 0.90 floor is unchanged.
  Skill lock re-sealed. See ADR 0056.
