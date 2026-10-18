You transcribe numbers. You do not judge the design.

Read the Design Contract at `<CONTRACT>`: the prose above the
`design-contract` block, every requirement row's `text` and every Interface's
`text`. Write `<OUT>/claims.json`: a JSON list with one entry for every
statement below. Copy each number exactly as written, never compute one, and
quote the words you read it from (at most 120 characters).

- **move**: the text says a Component turns by some angle in a move:
  `{"kind": "move", "component": "<geometry id or id#n>", "deg": 60, "quote": "..."}`.
  An angle a move passes through, such as "the toe points down", is not a move.
- **range**: the text places a Component's own material from one coordinate
  to another on one axis:
  `{"kind": "range", "component": "shin", "axis": "x", "from": 7.5, "to": 25.5, "quote": "..."}`.
  Record only the Component's own solid (a block, a plate, a boss, a lug),
  never a cavity, slot, bore, gap or another part's position.
- **size**: the text gives the width or thickness of a thin solid feature of a
  Component (a finger, a thumb, a rib, a blade, a plate, a wall, a lug, a
  tongue):
  `{"kind": "size", "component": "forearm", "feature": "thumb", "value": 2.8, "quote": "..."}`.
  Add `"exception": true` when the contract names that size as an exception to
  its floors ("The exceptions, which the joints size: ...").
- **envelope**: the text gives the whole toy's size on one axis in the Display
  Pose: `{"kind": "envelope", "axis": "y", "value": 83.25, "quote": "..."}`.

The frame is the contract's own: X, Y and Z as its Frame section defines
them. Component ids are the `geometries[].id` values; use `id#n` only where the
text names one instance. Leave out anything you are unsure of rather than
guess. Reply with the number of entries of each kind.
