# What reference images have taught

Stage 3 of [LESSONS.md](LESSONS.md), moved here when that file passed 250
lines. The same rules apply: one `###` heading per rule, then **Why:** and
**How to apply:**; extend an entry before adding a near-duplicate; keep this
file under 250 lines.

## Stage 3 - Reference images

### Draw a part's extra views in one turnaround image, never one view per call
- **Why:** each separate AI edit of a reference into a back or side view
  redesigned the part. In one toy, five of eleven parts drifted: a band
  wrapped onto the open back, a solid block grew a window, and a fist's back
  was drawn as its front. Views cut from one image that shows all three
  views agreed with each other.
- **How to apply:** make one generation per part: LEFT copies the reference,
  MIDDLE and RIGHT are the new cameras, at one scale on one ground line.
  Spell out the part's construction and, for a profile, its proportions in
  units. Cut the views apart by empty columns. Compose each row at the
  sheet's single scale, with the reference matched to the LEFT view's height.

### Fix a wrong detail by editing the image, on two models, and pick
- **Why:** regenerating to fix one detail redraws everything around it. In
  one round of six fixes `openai/gpt-image-2.5-sunburst` kept the source
  intact best (won four), `openai/gpt-5.4-image-2` placed parts where the
  prompt said they sit (won two), `google/gemini-3-pro-image` won none.
- **How to apply:** pass the current image as IMAGE 1, name only the change
  and say "keep everything else exactly"; run sunburst and gpt-5.4
  ([`scripts/gen_image.py`](scripts/gen_image.py); sunburst is image-only,
  via `/images`) and compare. For a turnaround set `IMAGE_ASPECT=3:2`. State
  a spatial fact one way only: "the post's back face is flush with the
  helmet's back face; the front half of the helmet overhangs it".

### Draw what the camera can see, and pick a camera that shows the defining profile
- **Why:** the owner caught a slot open on top invisible from 15 degrees
  above, an L-shaped wing read as a flat bar head-on, and a post and guard
  contracted level drawn at different heights.
- **How to apply:** for each feature the contract places, edit it in if the
  camera can see it. Give a profile part (L, T, U) a three-quarter camera
  showing the profile at one end. Say "ends at exactly the same height as"
  for level things, and give widths as a percentage of the height, because
  the models draw parts too slim.

### Draw transformation steps as one chain of edits, one move per edit
- **Why:** step panels made as separate edits each redrew the toy, so parts
  changed between steps and the owner rejected the whole sheet.
- **How to apply:** start from the approved robot (or end) image. Make
  each step one edit of the previous step's image that names only that
  move, and keep the camera. Give the moved part's new size relative to a
  part in the image, such as "the nose above the chest is 1.2 times the
  chest's height", because the models shorten long parts. Lay the vehicle
  down from the last stood-up step, and pass the old vehicle view only as
  a camera example.

### Show a colour layer hidden inside a fold with a cutaway; fix one defect by editing

- **Why:** views looking into a narrow fold came out as a cup on every model,
  and edge-on profiles of a thick bent part came out as a bent pipe. A cutaway
  showed the hidden layer as one unbroken line round the fold. When one small
  defect was left (a flared foot), regenerating would have lost the rest, but
  an edit of the chosen image fixed only that spot.
- **How to apply:** prompt "sliced in half down its middle, look square at the
  cut face" and name the layer's start, path and end. Fix a leftover defect by
  editing (see above). Check the drawn thickness against the contract, since a
  model can draw a thick part as a blade or a pipe.

### Edits drop objects nobody asked to remove
- **Why:** each "change only X" edit lost one or two unrelated objects (an
  inkwell, a framed picture, a sill plant) in four of seven rounds.
- **How to apply:** name every object to keep in each edit prompt, compare
  object lists after, and restore a lost one in one edit with the earlier
  image passed and the object described as it looked there; a generic noun
  brings back a different object.

### When the models keep moving a part, change the composition, not the prompt
- **Why:** a cabinet "under the stair" landed on the dais in seven tries,
  and an open door lay flat beside its cabinet or hung on its far edge in
  four of six; a niche in the stair's side and "the open door continues the
  side panel forward" were drawn right at once.
- **How to apply:** after three generations put a part in the same wrong
  spot, build it into a neighbour the model already draws; amend the contract.

### Redraw fresh after about four chained edits, counting the whole lineage
- **Why:** editing an edit accumulates blur; the owner saw it after five,
  including an assembly fixed back and forth across rounds with no single
  round making four edits. A text-only redraw lost the box proportions; one
  with the last image as a layout guide kept them.
- **How to apply:** count every edit since the last fresh generation. At
  four, regenerate with the last image as the only reference, labelled "a
  LAYOUT GUIDE: do not copy its pixels", describing every object as it is
  drawn there (shape, colour, count, position) at the same camera; then
  compare object by object and fix any difference with one edit.

### Extract a component by removing, not by redrawing
- **Why:** "redraw this as the empty case" reflowed the layout; "remove the
  chair, the desk ... keep everything else" kept every position.
- **How to apply:** edit the assembly and name every part to remove and
  what shows behind it. For a top view pass a clean earlier top view first
  (camera) and the assembly second; text alone returns a three-quarter view.

### Ask for proportion changes as relative edits
- **Why:** "N times taller than wide" was ignored for thin parts (a ladder
  asked at 9:1 came back 4:1; a window asked at 2.6:1 came back far
  slimmer than asked); "make it half as wide" landed within the 20% resize
  allowance.
- **How to apply:** generate, measure the aspect, then edit with a
  relative instruction ("half as wide", "move the left end to 52% of the
  width") and close the rest with the allowed resize. Side profiles: pass
  an existing side-profile image as a second reference.
