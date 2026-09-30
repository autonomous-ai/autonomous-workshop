---
title: Microcontroller boards in enclosures
tags: [microcontroller, arduino, uno, nano, pico, esp32, xiao, qt-py, board, gpio]
aliases: [dev board, arduino nano, raspberry pi pico, rp2040, esp32 devkit, seeed xiao, controller board]
sources:
  - https://docs.arduino.cc/resources/datasheets/A000066-datasheet.pdf
  - https://store.arduino.cc/products/arduino-nano
  - https://docs.arduino.cc/hardware/nano/
  - https://www.adafruit.com/product/4864
  - https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html
  - https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/
  - https://www.adafruit.com/product/4900
related: [logic-level-interfacing, power-path-design, electronics-enclosure-design, led-sizing, hobby-servos]
updated: 2026-09-23
---

# Microcontroller boards in enclosures

Pick the board for its logic voltage, its size and how it is powered. Then
seat it from its STEP (mounting holes, USB position, component heights on
both sides), never from the outline in this table.

## Common boards

| board | size | logic | power in | per-pin current | mounting / USB |
|---|---|---|---|---|---|
| **Arduino Uno R3** | 68.6 × 53.3 mm, ~25 g | 5 V | 7–12 V recommended (6–20 V limits) on the barrel / VIN | 40 mA max per I/O pin | 4 holes near the corners (take the pattern from the STEP); USB-B |
| **Arduino Nano** (classic) | 18 × 45 mm, 7 g | 5 V | 7–12 V on VIN | 20 mA per I/O pin (store spec) | no holes on the classic board, so it rides on headers or a carrier; Mini-B USB |
| **Raspberry Pi Pico** (RP2040) | 51.3 × 21 × 3.9 mm | 3.3 V, **not 5 V tolerant** | USB 5 V through an onboard converter | see datasheet | castellated edge pads (mounting holes: take them from the STEP); micro-USB |
| **ESP32-DevKitC V4** | see Espressif dimension drawing | 3.3 V | micro-USB **or** 5V pin **or** 3V3 pin, exactly one | see datasheet | 2 × 19-pin headers |
| **Seeed XIAO ESP32C3** | 21 × 17.8 mm | 3.3 V | 5 V USB-C, or 3.7 V LiPo on battery pads (onboard charger 380 mA / 40 mA) | 3V3 out up to 500–700 mA | single-sided SMD, castellations |
| **Adafruit QT Py RP2040** | 21.8 × 17.8 × 5.8 mm, 2.2 g | 3.3 V | USB-C; 600 mA peak regulator | — | castellated pads; STEMMA QT I²C connector |

## Power rules that decide the layout

- **One power source at a time** unless the board says otherwise. Espressif:
  "The power supply must be provided using one and only one of the options
  above, otherwise the board and/or the power supply source can be damaged."
  A USB cable plugged in while a battery feeds 5V is exactly that. Put a
  diode or a power-path switch in, or document that USB must not be used
  while the battery is connected ([[power-path-design]]).
- **The board's regulator is not a motor supply.** Servos, motors and pixel
  strips run from the battery or a separate regulator. Share only ground
  ([[hobby-servos]], [[motor-drivers-and-flyback]]).
- **GPIO pins drive signals, not loads.** An LED on a pin is sized to the pin
  limit ([[led-sizing]]). Anything larger goes through a driver.
- **3.3 V boards and 5 V parts** need level care ([[logic-level-interfacing]]).
  The Pico's datasheet warns that 5 V on a GPIO can shorten its life even
  when it survives.

## Mechanical integration

- **Seat on standoffs**, not flat on the floor: through-hole pins and
  components on the underside need clearance
  ([[electronics-enclosure-design#standoffs-and-board-mounting]]).
- **The USB connector sets the board position.** Place the board so its USB
  port sits at the wall with the cable clearance, then derive everything else
  from that datum.
- **Boards without holes** (classic Nano, XIAO, QT Py) go in a printed
  cradle with a lip or clip over the PCB edge, or are soldered to a carrier
  PCB that has holes. Do not clamp on components.
- **Reset and boot buttons** need access holes or a printed plunger, and so do
  status LEDs if they are useful: a light pipe or a thin window.
- **Radio boards (ESP32, Pico W)** want the antenna end away from metal and
  motor wiring.
