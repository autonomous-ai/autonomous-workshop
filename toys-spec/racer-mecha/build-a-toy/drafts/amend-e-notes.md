# amend-e: shin prints upside down with no overhang (v02 attempt, wish-20261014-100904-1ee4c488)

Need (Blocked Report 3, shin r0011): in the sealed stance (upside down on the post's
top, Z 96) (a) the knee guard, free-standing 3.5 in front of the post because the
thigh's front wall slides there, starts 6.5 above the bed as an island; (b) the
block is wider than the post on every side, so its top is a 354 mm2 overhang.

No stance avoids both: the post is inset from the block on all four sides, so on
the back, front or a side the post or the tongue is a cantilever 1.25 to 5.5 above
the bed. Supports are forbidden and check_overhang has no support allowance.

Fix (smallest found):
- Knee guard rises to the post's top (Z 96) instead of Z 89.5, so it prints from
  the bed. Robot: it laps 6 over the thigh's foot, 0.5 in front (same red, same
  column ref-01 draws). Car: it reaches Z 112, under the thigh's step at 112.5 and
  5 under the torso.
- Block top slopes down at 52 degrees beside and behind the post (to Z 67.1 at the
  inner side, 65.2 outer, 69.7 back); flat only between guard and post, which is a
  3.5 bridge. Outer slope is behind the rear wheel (Z 46 to 80); inner one is 2
  wide beside the guard, between the legs; back one faces the back.
- Thigh row R18 loses "two of them standing proud on the front": the guard now
  covers the thigh's front to Z 112 in the car at 0.5, where the contract's own
  2 mm rule forbids proud blocks.
- knee-slide-1 text and R01 updated to match; landmark line updated.
- Folded in-run amendment 1 (head-slide post Y 0.5 to 8.5, bore Y 0 to 9) and
  matched the head and torso prose to it.
- Intro paragraph shortened (it repeated the geometry table) to keep the file
  under 40,000 characters.

Visibility: judged invisible at the references' scale. ref-01 draws the leg as one
red column with no black post showing, which the taller guard keeps; ref-08 shows
square shoulders where the slopes sit under the guard's sides and behind the wheel.
Resumed as an owner amendment so locked Components keep their locks.
