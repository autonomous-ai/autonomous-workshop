# Harness Square hardware inputs

| File | What it is |
|---|---|
| `TXW395039B0-HYE_SPEC.pdf` | Display: 3.95" 720x720 IPS, MIPI DSI (ST7703I), GT911 capacitive touch. Cover glass 84.37 x 84.37 mm, visible area 72.33 mm, active area 71.93 mm, stack 3.23 mm, 30-pin FPC. |
| `SCH_Schematic_LCD_ESP32P4_2026-09-23.pdf` | Main board schematic: WT01P4C5-S1 module, USB-C, CH343P USB-UART, IP5306 charger and battery, ES8311/ES7210 audio, 2 MEMS mics, NS4150B amp, WS2812 LED, vibration motor, TF card, camera FPC, 3 tactile switches. |
| `WT01P4C5-S1_datasheet_V1.3.pdf` | Core module: ESP32-P4 (2 x RISC-V at 360 MHz, MIPI DSI/CSI) + ESP32-C5 (Wi-Fi 6 2.4/5 GHz, BLE 5.3), 16 MB flash, 16/32 MB PSRAM, 35 x 35 x 3.7 mm, 5 V. |
| `PCB_Harness_pro_v1.step` | PCB assembly model, about 80.7 x 35.2 x 22.3 mm. Gitignored (184 MB), so copy it from the main checkout. |

Open points: the P4 has a 2-lane DSI and the panel spec says 4-lane, so confirm the 2-lane
mode. The 3 tactile switches conflict with the no-button exterior.
