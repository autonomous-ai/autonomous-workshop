- Add Design Contract schema 6 (ADR 0091): a `print` section declares the
  stocks, the sealed print art and every Print Piece (flat, sticker, wrap,
  sphere, fold or stand), each on one Unique Geometry with its sizes in mm.
  The parser refuses unknown stocks and ways, a stock a way cannot use,
  non-CC0 stock art, unused stocks or art, missing hosts and edges under the
  scissors limits. `workshop wish|fix --print-art IMAGE` seals the art as
  `print-NN` after every guide, sharing the image budget; Guide Images become
  optional at schema 6. Nothing compares print art with the model.
