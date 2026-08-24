# Inventors

Each immediate subfolder is one active inventor. It contains `inventor.json`,
`TASTE.md`, a `profile.py` entrypoint, operating guidance, tests, and any
niche-specific implementation the inventor truly owns. `TASTE.md` is the
human-owned creative constitution: agents read it, outcomes may motivate a
proposed revision, and self-improvement code cannot rewrite it. Inventors may
depend on the shared [Workshop root](../README.md); Workshop never imports an
inventor.

| Inventor | Workshop lane | Customization | Status |
|---|---|---|---|
| [Alice](alice/) | classics made yours | taste-only | known rules; customized-object Playtest |
| [Leo](leo/) | invented games | custom Make + Playtest | independent human replay gate; typed adapters pending |
| [Bob](bob/) | moving machines | custom Make | kinetic Make pending; legacy game lab preserved |
| [Ivy](ivy/) | holdable science | taste-only | orreries, pendulums, and mathematical objects |
| [Eve](eve/) | little worlds | taste-only | your dog, rig, or homelab made epic |

Create the next inventor from the repository root:

```bash
python3 -m pip install -e .
workshop new pocket-orreries \
  --name Ada \
  --niche "personalized printable orbit models" \
  --lane holdable-science \
  --level taste-only \
  --root inventors
```

The command writes `inventors/pocket-orreries/`. Give the inventor a Wish
boundary, its own Taste, and only the niche-specific Make or Playtest work it
truly needs. Reuse the Workshop's artifact handling, durable runtime, and
adapters instead of creating
new branded stages for those implementation details. Keep prompts, generators,
evaluators, and the reward hypothesis in the inventor folder.
