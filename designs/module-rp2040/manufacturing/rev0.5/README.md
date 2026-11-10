# Cleaver revision 0.5 manufacturing

Use this package with `designs/module-rp2040/Cleaver.kicad_pcb` revision **0.5**.

- **479 bottom-only SMT placements, 13 exact purchasing groups**: `BOM-JLCPCB.csv`
  and `CPL-JLCPCB.csv`.
- Fabrication: `Cleaver-rev0.5-fabrication.zip`, or `fabrication/` (four copper
  layers, masks, silkscreens, paste, outline and separate PTH/NPTH drills).
- `pad-orientation-reference.csv` gives the actual copper/net coordinates for
  assembler orientation checking. CPL XY is PCB top view, lower-left origin,
  +X right / +Y up. Bottom rotations use KiCad's convention. Socket XY is the
  two-land midpoint, **not the switch centre**.
- `user-installed.csv` lists the top YD-RP2040 module/headers, USB tap wire and
  mechanical assembly items. C5 is factory fitted underneath.
- `checks/` contains fresh ERC/DRC/connectivity and parity results; `SHA256.json`
  identifies the source files and this export.
- [`firmware/`](firmware/) contains freshly built default and Vial UF2 images,
  flashing instructions, build logs and provenance for this module-based board.

Purchasing evidence and per-component review:
[`references/COMPONENT-REVIEW.md`](../../references/COMPONENT-REVIEW.md).
All selected exact parts had positive JLCPCB SMT stock on 2026-11-10. Stock is
not reserved; C5 was the lowest-stock part at 103 pieces.

## Assembly details

- SW001–SW117: **HanElectricity CPG151101S11-16 / C41430893**.
- C5: **Nichicon PCF1A471MCL1GS / C3275369**, 470 µF/10 V polymer. `+`/pad 1
  is LED_5V; pad 2 is GND. **11 mm clear case depth is needed under C5.**
- TP1: bottom bare SMD wire land, no stencil aperture. Owner solders the raw USB
  VBUS tap from the top module to it; route around the edge and strain-relieve.
- The only plated through-hole component pads are U1's 40 header pins. Switch
  positioning/contact apertures and M2 mounts are non-plated mechanical holes.
- LEDs remain **OPSCO SK6812MINI-E / C5149201**, reverse-mounted into 3.6 × 3.2 mm
  apertures. Internal milling corner radius must be ≤0.5 mm (prefer 0.4 mm).
  Bottom soldering is followed by switch insertion from the top.
- No front-side paste or front-side factory placements. Ordinary off-pad vias;
  no filled/capped via-in-pad process required.
- Use the exact-part tape/pad orientation reference during JLCPCB placement
  review, especially polarized LEDs, diodes, C5 and the asymmetrical sockets.

Generated with `python3 -B designs/module-rp2040/source/export_manufacturing.py`,
which runs the integration checker before exporting. `SHA256.json` paths are
relative to `designs/module-rp2040/`. Older `rev0.4`, `archive/` and Taviana
artwork packages are historical, not this manufacturing set.
