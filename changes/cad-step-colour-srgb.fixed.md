- Report sealed STEP part colours as the sRGB hex the shop viewer shows.
  build123d writes the channels a designer passes to `Color` unchanged and
  the cadgen GLB exporter converts them from sRGB to linear for glTF, so
  `read_step_part_colors` no longer applies a second transfer; the sealed
  assembly-package supplies occurrence colours when the STEP is unstyled.
