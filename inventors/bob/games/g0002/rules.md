# Re-Pin

*A printed lock, five hidden pins, and no referee.*

2–4 players · 20–30 minutes · ages 8+

---

## 1. Overview

One player is the **Locksmith**. Behind a hood they load five hidden **pins** into a printed lock. Everyone else is a **Cracker**: on your turn you set the five numbered **sliders** on your key, push it in, and turn the plug. The plug turns exactly as far as your first wrong chamber and stops dead. A printed pointer reports how many chambers you got right, **counting from the front and stopping at the first mistake** — no card to read, no player to trust, no argument possible.

The feeling is held breath: you turn, the plug creeps one more notch than last time, and the table leans in. The Locksmith is not a neutral dealer — they score for every turn the lock survives, and after any failed turn they may **re-pin** one chamber, which costs them points and quietly rots everything the Crackers thought they knew.

The Locksmith seat rotates so nobody plays referee for long. Highest score at the end of the last round wins.

---

## 2. Components bill

Every part is printed. Nothing in this list is an abstraction.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plug_01` | **Staircase-cam plug** ★ | 1 | ⌀34 × 96 | ★ **The load-bearing mechanism.** Five stepped gates around the plug: each chamber only blocks rotation once the plug reaches that chamber's gate angle, so the plug can pass gate 2 only if chamber 1 is already right. Carries the keyway and the pointer. This part is the reason the game exists. |
| `shell_01` | Lock shell | 1 | 118 × 74 × 66 | Body. Holds the plug, the five chamber bores, the protractor face marked `0 1 2 3 4 OPEN`, the latch seat and the foot that keeps the lock upright on the table. |
| `hood_01` | Loading hood | 1 | 122 × 56 × 74 | Clips over the chamber row. Solid on three sides, open only towards the Locksmith's seat. Everything secret happens under it. |
| `latch_01` | Latch bar | 1 | 74 × 12 × 8 | Sits in the shell under tension from its own printed flexure. When the plug reaches OPEN it snaps out — that is the click. |
| `lever_01` | Reset lever | 1 | 60 × 14 × 8 | On the back of the shell. Lifts all five driver slugs clear so a jammed plug can be turned back to 0. |
| `slug_01`–`slug_07` | Driver slug | 7 | ⌀6 × 8 | One plain slug rides on top of each pin (5 in use, 2 spares). Slugs are identical and never secret: they are what falls across the shear line and jams the plug when a slider is set **too low**, just as a pin sticking up jams it when a slider is set **too high**. |
| `pin_r1`–`pin_r8` | Pin, rungs 1–8 | 40 (5 of each rung) | ⌀6 × h, where h = 3.0 / 3.4 / 3.8 / 4.2 / 4.6 / 5.0 / 5.4 / 5.8 by rung | The hidden combination. The rung number is engraved on the top face. One rung per 0.4 mm step — this ladder is the whole game. |
| `case_01` | Pin case | 1 | 96 × 62 × 22 | Eight tubes, one per rung, under a sliding lid. Holds the stock and the Locksmith's hidden reserve. |
| `key_01`–`key_04` | Key blank | 4 (one per player) | 132 × 30 × 14 | Five print-in-place sliders numbered 1–5 along the blade, each detented at settings 1–8. Slider 1 is nearest the bow (the grip) and sits under chamber 1 when the key is home. |
| `rail_01` | Cut rail | 1 | 110 × 26 × 10 | Five print-in-place thumbwheels numbered 1–8. The public record of the five rungs the Locksmith started the round with. |
| `board_01` | Round board | 1 | 180 × 60 × 8 | Two peg lanes: the **time rail** (12 down to 1) and the **Locksmith lane** (0 to 20). |
| `board_02` | Score board | 1 | 220 × 90 × 8 | Four peg lanes, 0 to 70. |
| `grid_01`–`grid_04` | Deduction card | 4 (one per player) | 108 × 152 × 9 | Print-in-place shutter card: 5 columns (chambers) × 8 rows (rungs), 40 sliding shutters. A **closed** shutter means "this chamber is not this rung". Memory aid only — it never forces a play. |
| `peg_01`–`peg_06` | Peg | 6 | ⌀5 × 16 | Two for the round board, four for the score board. |

Everything prints on a 256 mm bed. The lock, four keys and four deduction cards are the bulk of the print.

---

## 3. Setup

1. **Assemble the lock.** Drop the plug into the shell, pointer at `0`. Drop one driver slug into each of the five chambers from the top. Push the latch bar into its seat until it holds. Stand the lock on its foot in the middle of the table with the protractor face towards the players.
2. **Hand out kit.** Each player takes one key blank and one deduction card. Open every shutter on your card (nothing is ruled out yet). Push all five sliders on your key to `1`.
3. **Boards.** Put the round board and the score board where everyone can reach them. Put a peg on `12` of the time rail, a peg on `0` of the Locksmith lane, and one peg per player on `0` of their score lane.
4. **First Locksmith.** The player who most recently locked themselves out of a house, car or phone takes the Locksmith seat. If nobody can remember, the tallest player takes it. *(Machine play or a tournament: choose the first Locksmith at random.)*
5. **Round count.** Play one round per player, so every player is Locksmith exactly once — 4 rounds at 4 players, 3 rounds at 3 players. **At 2 players, play 4 rounds** (called *legs*), so each player is Locksmith twice.
6. **Start the round.** The Locksmith does the **Load** action (section 5). Then the player to the Locksmith's left takes the first turn.

Between rounds: pass the Locksmith seat to the left, return all pins to the case, reset the time rail to `12`, reset the Locksmith lane to `0`, spin the cut rail wheels back to `1`, and open every shutter on every deduction card. Score board pegs stay where they are.

---

## 4. Turn structure

Turns pass clockwise among the **Crackers only**. The Locksmith never takes a turn; they answer turns.

Each turn, in this exact order:

1. **The Cracker acts.** They must choose exactly one: **Probe** or **Hold**. There is no third option and no skipping.
2. **The lock answers.** On a Probe, the pointer stops somewhere. If it stops on `OPEN`, the round ends immediately — go to section 6.
3. **Locksmith income.** If the lock did not open, the Locksmith moves their lane peg **up 1**. This happens on a Hold as well as on a failed Probe.
4. **Re-pin window.** If the turn was a **failed Probe**, the Locksmith may now take the **Re-pin** action, once. After a **Hold** they may not.
5. **Time.** The Locksmith moves the time rail peg **down one space**. If the peg would leave space `1`, the round ends — go to section 6.
6. Turn passes to the next Cracker clockwise.

Nothing else happens in a turn. Crackers may talk, argue and lie to each other at any time; the Locksmith may say anything they like too, because nothing either of them says is evidence — only the pointer is.

---

## 5. Actions

### Load *(Locksmith, once, at the start of a round)*

1. Open the pin case. In the open, pick any five pins — repeats allowed, e.g. two rung-3 pins is legal.
2. Show all five to the table and **dial their rungs onto the cut rail in ascending order**. The table checks the dials against the pins. The rail now publicly says *which five rungs are in the lock*, and says nothing about where they are.
3. Take **three more pins from the case without showing them**. These are your hidden **reserve**. Keep them under the hood or in the case.
4. Clip the hood over the chamber row and, working from your own side where nobody can see, drop the five pins into chambers 1–5 in any order you like, one pin per chamber, each under its driver slug.
5. Say "loaded". Play begins.

The Locksmith may look at the lock's pins any time; nobody else may.

### Probe *(Cracker)*

1. Set your five sliders. Every slider must sit **in a detent** on a number from 1 to 8. Settings are **public** — set them in the open, and anyone may read your key before you insert it. You may reuse a setting you or anyone else has already tried.
2. Push the key all the way home into the keyway until it stops.
3. Turn the plug **clockwise only**, one steady push, until it stops. Do not rock it, jiggle it, or force it.
4. Read the pointer: `0`, `1`, `2`, `3`, `4` or `OPEN`. That number is the **reading**.
5. Turn the plug back to `0` **before** pulling the key out, then pull the key out.

**What the reading means.** The reading is the number of chambers, counted from chamber 1 (nearest the keyway mouth), that are set correctly in an unbroken run. It stops at your first mistake and tells you nothing beyond it.

> Pins in the lock: **3 7 2 5 1**. Your key: **3 7 4 5 1**.
> Chambers 1 and 2 match, chamber 3 does not. **Reading: 2** — even though chambers 4 and 5 also match. The lock cannot report them and does not.

A reading of `5` is not possible: five correct chambers means the plug turns the full 90°, the latch bar snaps out, and the pointer reads `OPEN`.

**Physical rulings for a Probe:**

- **Slider not in a detent** (sitting between numbers): the reading is void. Nobody may act on it. Re-seat the slider, re-insert, and turn again — it is still the same turn and costs nothing extra. If the Cracker still cannot produce a clean turn on their second attempt, the turn becomes a **Hold**.
- **Key not fully home**: same as above — void, re-insert, turn again.
- **Plug forced, rocked, or turned anticlockwise**: the reading is void and the turn becomes a **Hold**. The Locksmith re-seats the plug at `0`.
- **Jam** (the key was pulled out while the plug was off `0`, so slugs dropped across the shear line): the reading already taken stands. The Locksmith closes the hood, works the reset lever until the plug turns back to `0`, and play continues. A jam never repeats or cancels a turn.
- **Pointer reaches OPEN but the latch does not snap**: the lock is open. The pointer is the authority; re-seat the latch bar before the next round.
- **The plug stops between two marks**: read the **lower** mark.

### Hold *(Cracker)*

Say "hold". You do not touch the lock. Nothing is revealed, the Locksmith gains their point, the time rail still drops one, and — importantly — the Locksmith gets **no re-pin window**.

Holding hands the next Cracker the job of buying information with a turn, and hands them the tempo to use it. It is a real move, not a pass: it freezes the lock for one turn while the round's value bleeds away.

### Re-pin *(Locksmith, at most once per failed Probe)*

1. **Announce it out loud: "re-pin."** Reaching under the hood without announcing is not allowed. The table always knows *that* a chamber changed.
2. **Pay 2**: move your Locksmith lane peg **down 2**. A re-pin is **illegal if it would take your lane peg below 0** — so you cannot re-pin until the round has paid you enough.
3. Under the hood, take the pin out of exactly one chamber and put one of your three hidden reserve pins in its place. The pin you removed joins the reserve. Your reserve is always three pins.
4. Which chamber, and which rung went in, are secret. Do not update the cut rail — the rail records the *start* of the round and never changes.

You may re-pin the same chamber on consecutive turns. You may not re-pin twice in one turn, and you may not re-pin after a Hold or after the opening Probe.

---

## 6. End & winning

**A round ends the instant either of these happens:**

- **The lock opens.** A Cracker's Probe reads `OPEN`.
- **Time runs out.** The time rail peg is on `1` and a turn finishes, so the peg has nowhere to go.

Every turn moves the time rail down exactly one space and the rail is 12 spaces long, so **a round is at most 12 turns and always ends.** There is no way to add time, take a turn back, or move the peg up.

**Scoring a round:**

| who | scores |
|---|---|
| The Cracker who opened the lock | the number the time rail peg is **on at that moment** (12 down to 1) |
| Every other Cracker | 0 |
| The Locksmith | whatever their Locksmith lane peg reads at the end of the round (+1 per failed turn, −2 per re-pin) |
| The Locksmith, if the lock never opened | **+5** on top of their lane |
| **Deepest reading bonus**, only in a round that ended unopened | **3** to the Cracker who got the highest reading during the round; ties go to whoever got it on the earlier turn. If no Probe was made all round, nobody gets it. |

Move the score board pegs, reset as in section 3, pass the seat left.

**The game ends after the last round** — one round per player (4 rounds at 2 players). **The highest score on the score board wins.**

### Worked scoring example (4 players: Dee is Locksmith, Ash, Bo and Cy crack)

Cut rail shows **1 2 3 5 7**. Every Cracker immediately closes rows 4, 6 and 8 on all five columns of their deduction card.

| turn | rail | who | action | reading | Locksmith lane |
|---|---|---|---|---|---|
| 1 | 12 | Ash | Probe `1 2 3 5 7` | 0 | 0 → 1 |
| 2 | 11 | Bo | Probe `2 1 3 5 7` | 1 | 1 → 2 |
| 3 | 10 | Cy | Hold | — | 2 → 3 *(no re-pin window)* |
| 4 | 9 | Ash | Probe `2 3 1 5 7` | 3 | 3 → 4, re-pin −2 → 2 |
| 5 | 8 | Bo | Probe `2 3 1 7 5` | 2 | 2 → 3 |
| 6 | 7 | Cy | Probe `2 3 5 7 1` | 1 | 3 → 4, re-pin −2 → 2 |
| 7 | 6 | Ash | Probe `2 7 5 1 3` | 0 | 2 → 3 |
| 8 | 5 | Bo | Probe `2 3 7 5 1` | **OPEN** | stays 3 |

Bo scores **5** (the rail was on 5). Ash and Cy score **0**. Dee scores **3** — six failed turns paid 6, two re-pins cost 4, and the lock opened so no +5. No deepest reading bonus, because the round ended with an open.

Note turn 4: Ash's reading of 3 was the best information anyone had bought, and Bo — not Ash — got the next turn with it. That is the whole Cracker game.

---

## 7. Tiebreak

Apply in order until one player is ahead. This always ends with a single winner; there is no shared victory.

1. Most points.
2. Most locks opened as a Cracker across the whole game.
3. Highest single opening score (the biggest rail number anyone banked).
4. The tied player who sat in the Locksmith seat **most recently** wins.

Step 4 always separates them: each round has exactly one Locksmith, and the seat order is fixed, so no two players sat in it last.

---

## 8. Edge cases

**Supply and legality**

- *The case has no more pins of the rung the Locksmith wants (for the five starting pins or the reserve).* Take a different rung. The case holds five pins of each rung; that is the hard limit, and it is public that it is.
- *The Locksmith cannot afford a re-pin* (lane peg is on 0 or 1). Then they may not re-pin. They may not borrow against future turns and may not go negative.
- *The Locksmith announces "re-pin", pays, and then changes their mind.* Too late — the payment stands and they must swap a chamber. Announcing is the commitment.
- *A Cracker probes a setting already known to be wrong* (a dead probe, to burn a turn without revealing anything new). Fully legal. It still pays the Locksmith 1 and still opens a re-pin window.
- *A Cracker sets sliders to a rung that is not on the cut rail.* Legal — the rail describes the start of the round, and re-pins can bring in any rung.

**Mistakes at the lock**

- *A chamber is found empty, or holding two pins, or missing its driver slug, mid-round.* The round is void. Reset the round board, re-load from scratch, and replay it. The Locksmith scores **0** for the voided round; the replay scores normally.
- *A Cracker sees a pin's rung* during loading or a re-pin, by accident or otherwise. The Locksmith must immediately, under the hood, swap that chamber's pin for a pin of a different rung from the reserve. This costs nothing and is not a re-pin.
- *The Locksmith's dialled cut rail does not match the pins they loaded* and this is discovered later. The round is void, exactly as above, and the Locksmith scores 0 for it.
- *Someone lifts the hood.* Nothing secret is legal to look at. If a Cracker lifts the hood, they take no turn on their next turn (it counts as a Hold) and the Locksmith may re-load the chambers under the hood for free, keeping the same five starting rungs.

**Timing and simultaneity**

- *The lock opens on the last space of the time rail.* The open resolves first: the Cracker scores 1, the round ends as an opened round, and the Locksmith does **not** get the +5.
- *A Probe reads OPEN.* The turn ends there. The Locksmith gets no income for that turn and no re-pin window.
- *The time rail runs out on a turn that was a Hold.* Normal unopened ending: the Locksmith takes their lane +5, and the deepest reading bonus goes to the best reading from earlier in the round.
- *Every Cracker holds every turn.* Legal and terrible: the round ends unopened after 12 turns, the Locksmith scores 12 + 5 = 17, and nobody gets the deepest reading bonus because no Probe was made. This is why holding forever is not a strategy.
- *Two Crackers claim the same deepest reading in an unopened round.* The earlier turn wins. Only one Probe happens per turn, so this always resolves.

**Player counts**

- *2 players (4 legs).* One Cracker, one Locksmith, seat alternating each leg. Everything else is identical. Hold still matters: it costs one point of rail value and denies the Locksmith a re-pin window, which is the sole Cracker's only way to freeze a chamber they are close to reading.
- *3 players (3 rounds).* Two Crackers per round; the tempo fight in section 6 is sharper because a Hold hands the tempo straight back to your only rival.
- *4 players (4 rounds).* Three Crackers per round. Everyone is Locksmith once; the extra Cracker means fewer turns each, so the deepest reading bonus matters more.

**How long this takes.** At most 12 turns per round; a turn is one key setting and one push, about 30 seconds. Loading takes about a minute. So a round is 6–7 minutes at most and typically ends around turn 8. Four rounds ≈ 24–28 minutes of play, plus about 5 minutes to teach.
