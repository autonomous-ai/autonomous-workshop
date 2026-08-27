---
type: rule-pattern
name: "Printed Fit Clearance"
created: 2026-08-25
source: agent
status: seeded
---

# Printed Fit Clearance

## Definition
Declare mate clearances by FIT CLASS, not one number: drop-in/gravity fits (a figure in a saddle, a hull in a dock slot) want 0.5-1.0mm so parts lift with zero resistance; sliding fits (a bar in a channel) want ~0.3mm; press/snap fits want 0.10-0.15mm and a lead-in chamfer. On FDM the printed hole is always smaller and the printed peg always fatter than modelled, so a contract written at nominal CAD dimensions reads 10x too tight against measured reality.

## Relations

## Notes
- [yt:XKrDUnZCmQQ] medium: Round corners, chamfer the bottom, hollow solid infill into thin walls, and use a 0.3mm gap for flex fingers so lid/base fits stay consistent across printers, materials, and colors. (Slant 3D 2025)
