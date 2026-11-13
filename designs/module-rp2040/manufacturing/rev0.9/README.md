# Cleaver rev0.9 — 2 × 1 inch illuminated badge

**117 keys, 121 RGB LEDs, 489 underside SMT placements / 14 purchasing groups.**
The badge grows to **50.8 × 25.4 mm**. Its four LEDs and bypass capacitors are
spread across the wider area; H9 moves to **(263,138) mm**. The PCB outline and
all key positions are retained. The matching plate and case extend 8 mm forward.

- `Cleaver-rev0.9-fabrication.zip`: Gerber/drill package.
- `BOM-JLCPCB.csv`, `CPL-JLCPCB.csv`: purchasing and underside placement files;
  U2 +90° and switch-socket +180° catalog corrections are retained.
- `pad-orientation-reference.csv`, `assembly-bottom.svg`, `fiducials.csv`,
  `mounting-holes.csv`, `controller-pin-map.csv`, `controller-interface.json`:
  placement, mounting and socket references.
- `user-installed.csv`: module, headers, switches, stabilizers, badge and hardware.
- [`firmware/`](firmware/README.md): default and Vial 121-pixel UF2 files.
- `checks/`: ERC/DRC, tests, migration and complete-copper regeneration evidence.
- `SHA256.json`: source/export hashes relative to `designs/module-rp2040/`.

Use the **[rev0.9 mechanics](../../mechanical/rev0.9/README.md)** and
[badge parts](../../LOGO.md). Earlier base/plate files have H9 in a different
position. PCB emitters use individual small apertures; the large rectangular
opening is in the plate and cover.

Controller sockets, long module headers, protection/current limits and part
selections follow rev0.8. See the
[socket interface](../../references/CONTROLLER-SOCKETS-0.7.md) and
[validation record](../../VALIDATION.md).

```sh
python3 -B designs/module-rp2040/source/export_manufacturing.py
```
