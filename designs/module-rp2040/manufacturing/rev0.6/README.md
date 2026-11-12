# Cleaver rev0.6 manufacturing — Waveshare RP2040-Plus

Use `Cleaver-rev0.6-fabrication.zip` with this revision's `BOM-JLCPCB.csv` and
`CPL-JLCPCB.csv`. There are **479 factory SMD placements, all on the bottom**,
in 13 purchasing groups. The Waveshare module and headers are owner-installed
on top; see `user-installed.csv`.

Changes from rev0.5:

- U1 is **Waveshare RP2040-Plus 4MB**, SKU 20290 / pre-headered 20808.
- Header pin **40 / VBUS** feeds F1 through 0.6 mm carrier copper.
- TP1 is a bare VBUS test pad. **No USB tap wire is required.**
- Controller body is 51 x 21 mm; header holes and key/mounting coordinates match
  rev0.5. Pins 35/37/39 are ADC_VREF/3V3_EN/VSYS, all unconnected on the carrier.
- [Firmware](firmware/README.md) retains the matrix, RGB order and Vial identity.

Fabrication: four copper layers, 1.6 mm carrier, ordinary through-vias, separate
PTH/NPTH drills. Only U1's 40 component holes are plated. All front paste is empty.
TP1–TP6 and fiducials have no paste or fitted components. No via-in-pad process
is required. Position origin is lower-left, +X right / +Y up, top view.

Use the exact BOM, `pad-orientation-reference.csv`, and `assembly-bottom.svg`
for assembly orientation. The reverse-mounted SK6812MINI-E LEDs shine through
117 milled 3.6 x 3.2 mm openings; internal corner radius ≤0.5 mm, preferably
0.4 mm. Socket placement centres in the CPL are socket centres, not key centres.
C5 is a bottom SMD 470µF polymer capacitor: allow **11 mm underside case depth**.

`checks/` contains fresh ERC, DRC, connectivity, model and firmware-map checks.
`SHA256.json` hashes package files with paths relative to the design directory.
Component sourcing evidence remains dated 2026-11-10. Physical assembly, module
USB-plug fit, power measurements and hardware operation require prototype checks;
see [`../../VALIDATION.md`](../../VALIDATION.md).
