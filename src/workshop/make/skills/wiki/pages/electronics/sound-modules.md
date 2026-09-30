---
title: Sound in toys and gadgets
tags: [sound, piezo, buzzer, speaker, dfplayer, audio, mp3]
aliases: [beeper, sounder, mini speaker, mp3 module, audio player, sound effects]
sources:
  - https://www.adafruit.com/product/160
  - https://www.adafruit.com/product/1890
  - https://wiki.dfrobot.com/DFPlayer_Mini_SKU_DFR0299
related: [microcontroller-boards, power-path-design, electronics-enclosure-design, logic-level-interfacing]
updated: 2026-09-23
---

# Sound in toys and gadgets

Pick the simplest thing that makes the sound the object needs: a beep from a
piezo, tones or speech from a speaker, recorded clips from an MP3 module.
Then give the sound a way out of the housing.

## Options

| part | example | size | drive | notes |
|---|---|---|---|---|
| **passive piezo buzzer** | PS1240 (Adafruit 160) | Ø11.9 × 6.53 mm, 0.7 g | 3–30 V p-p square wave from a pin | loudest around 4 kHz, usable 2–10 kHz; driving both pins differentially doubles the volume |
| **mini speaker** | 8 Ω 0.5 W metal (Adafruit 1890) | Ø28 × 4.5 mm, 6 g | needs an amplifier or a player module | 0.25 W rated, 0.5 W max; ~600 Hz–10 kHz; resonance 680 Hz ±20 % |
| **MP3 player module** | DFPlayer Mini | 20 × 20 mm | 3.2–5 V supply; drives a speaker < 3 W directly from SPK1/SPK2 | microSD up to 32 GB (FAT16/32), 100 folders × 255 tracks; UART at 9,600 bps with a 1 kΩ resistor in series with its RX from the microcontroller's TX; 30 volume steps, 6 EQ presets |

A passive piezo needs a tone signal (PWM or a timer). An "active" buzzer has
its own oscillator and just needs power, but it plays only one pitch. The
PS1240 is passive.

## Letting the sound out

- A speaker needs an **open grille in front** of the cone and ideally a
  closed volume behind it. A small speaker in an open box sounds thin
  because the back wave cancels the front. Clamp its rim on a gasket or
  shoulder, not its cone.
- The grille is a pattern of holes or slots in the wall. Keep openings small
  enough to keep fingers and parts out, and print the grille flat on the bed
  so the holes stay round.
- A piezo can radiate through a thin wall section or a small port. It is loud
  at resonance and quiet elsewhere.
- Vibration from motors couples into the housing and sounds louder than the
  speaker. Isolate mounts where quiet matters.

## Power and wiring

- An amplifier driving a speaker is a real load: the DFPlayer at full volume
  into a speaker can pull enough current to brown out a shared 5 V rail.
  Give it the battery rail or bulk capacitance, and share ground
  ([[power-path-design]]).
- DFRobot recommends a 1 kΩ resistor between the microcontroller's TX and
  the DFPlayer's RX; check the module's input level against the board's
  logic level ([[logic-level-interfacing]]).
- Keep audio wires away from motor leads and PWM lines ([[small-dc-motors#electrical-noise]]).
- Leave access to the microSD slot if the sounds are meant to be changed.
