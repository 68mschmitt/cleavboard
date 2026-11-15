# PCB revision 0.11 — removable cartridge mounting

Use **`Cleaver-rev0.11-fabrication.zip`** for this PCB. Match the
[rev0.11 base, switch plate and cover](../../mechanical/rev0.11/README.md).

## Changes from rev0.9

- Remove the old eleven mounting holes and their keepouts.
- Add **12 Ø7.0 mm NPTH pass-through holes** for Ø6 mm case posts: H1–H12.
- Add **12 Ø2.2 mm NPTH PCB-to-plate screw holes**: H13–H24.
- All-layer hardware keepouts are Ø8.0 mm and Ø6.4 mm respectively.
- All **5,528 routed track/via items** and electrical component placement/pad
  mapping are retained. Zones are refilled around the new hardware keepouts.

See [`mounting-holes.csv`](mounting-holes.csv) for coordinates, roles and diameters,
and [`checks/mounting-migration.json`](checks/mounting-migration.json) for the
baseline hash and measured copper/component clearances.

## Deliverables

- [`Cleaver-rev0.11-fabrication.zip`](Cleaver-rev0.11-fabrication.zip):
  four copper layers, masks, silkscreens, paste, outline, drill files and maps.
- [`BOM-JLCPCB.csv`](BOM-JLCPCB.csv) / [`CPL-JLCPCB.csv`](CPL-JLCPCB.csv):
  489 bottom-SMT placements, using the existing electrical BOM.
- [`assembly-bottom.svg`](assembly-bottom.svg) and
  [`pad-orientation-reference.csv`](pad-orientation-reference.csv).
- [`user-installed.csv`](user-installed.csv): module, switches, stabilizers and
  updated cartridge hardware.
- [`controller-interface.json`](controller-interface.json) /
  [`controller-pin-map.csv`](controller-pin-map.csv).
- [`checks/erc.json`](checks/erc.json), [`checks/drc.json`](checks/drc.json),
  [`checks/validation.json`](checks/validation.json) and
  [`checks/roundtrip/roundtrip.json`](checks/roundtrip/roundtrip.json).
- [`SHA256.json`](SHA256.json): paths relative to the module design directory.

The **[rev0.9 firmware builds](../rev0.9/firmware/README.md)** remain compatible:
GPIOs, matrix, 121-LED chain, USB identity and Vial configuration are unchanged.
No new firmware build is required for these mechanical changes.

Electrical checks are recorded separately from the printed-part trial.
Test the new mounting and USB coupons before full assembly; the final USB bezel
opening is intentionally fitted after measuring the actual PCB/MCU stack.
