# Inventors

Each immediate subfolder is one active inventor. It contains `inventor.json`,
`TASTE.md`, a `profile.py` entrypoint, operating guidance, tests, and any
niche-specific implementation the inventor truly owns. `TASTE.md` is the
human-owned creative constitution: agents read it, outcomes may motivate a
proposed revision, and self-improvement code cannot rewrite it. Inventors may
depend on the shared [Workshop root](../README.md); Workshop never imports an
inventor. Every toy the inventor makes lives under
`inventors/<id>/toys/<toy-name>/`.

| Inventor | Makes | `TASTE.md` | Custom Make | Custom Playtest |
|---|---|:---:|:---:|:---:|
| [Alice](alice/) | classics made yours | ✅ | ⬜ | ⬜ |
| [Leo](leo/) | games that don't exist yet | ✅ | ✅ | ✅ |
| [Bob](bob/) | machines that move | ✅ | ✅ | ⬜ |
| [Ivy](ivy/) | science you can hold | ✅ | ⬜ | ⬜ |
| [Eve](eve/) | little worlds | ✅ | ⬜ | ⬜ |

Every inventor owns a `TASTE.md`. Leo also owns his own Make and Playtest,
because inventing rules and proving a game is fun are his alone; Bob owns his
Make, because a machine that moves is designed differently from anything else.
Leo's and Bob's Make seams are typed and waiting — a run stops and says so
rather than faking a result.

## Five Workshop toys

All five inventors used the shared Workshop Make and Playtest contracts to
create these checked-in digital prototypes. *Playtest rounds* is how many times
that wish paid for Playtest to test the toy and send it back to Make:

| Inventor | Toy | Playtest rounds |
|---|---|---:|
| Alice | [Five-Job Checkers](alice/toys/five-job-checkers/) | 2 |
| Leo | [Counterorbit](leo/toys/counterorbit/) | 10 |
| Bob | [Comet Geneva](bob/toys/comet-geneva/) | 4 |
| Ivy | [Montauk Tide Orrery](ivy/toys/montauk-tide-orrery/) | 3 |
| Eve | [Rackhaven: Night Shift](eve/toys/rackhaven-night-shift/) | 3 |

Open a toy to see its render, STEP/STL files, evidence, and receipt. Every
check a computer can do has passed. None of them has been printed or handed to
a person yet, so Instructions and Deliver stay locked and the receipt says so.

Every creation belongs under `inventors/<id>/toys/<toy-name>/`, whether it is
a tabletop game, a moving machine, holdable science, or a little world. Do not
split an inventor's work into sibling `games/` or `products/` collections.

Create the next inventor from the repository root:

```bash
python3 -m pip install -e .
workshop create inventor pocket-orreries \
  --name Ada \
  --description "Choose Ada for personalized printable orbit models; not kinetic spectacle, tabletop rules, or decorative miniatures." \
  --lane holdable-science \
  --level taste-only \
  --root .
```

The command writes `inventors/pocket-orreries/`. Give the inventor a Wish
boundary, its own Taste, and only the niche-specific Make or Playtest work it
truly needs. Reuse the Workshop's artifact handling, durable runtime, and
adapters instead of creating
new branded stages for those implementation details. Keep prompts, generators,
evaluators, and the reward hypothesis in the inventor folder.
