# Cleaver rev0.8 — illuminated badge fabrication package

**117 keys, 121 RGB LEDs, 489 underside SMT placements / 14 purchasing groups.**
This revision adds LED118–LED121 and C218–C221 beneath a replaceable square
printed logo between the front trios. H9 moves from `(220,138)` to `(250,138)` mm.

- `Cleaver-rev0.8-fabrication.zip`: Gerber/drill package.
- `BOM-JLCPCB.csv` and `CPL-JLCPCB.csv`: matching purchasing and bottom placement
  files. Existing U2 +90° and switch-socket +180° catalog corrections are included.
- `pad-orientation-reference.csv`, `assembly-bottom.svg`, `fiducials.csv`,
  `mounting-holes.csv`, `controller-pin-map.csv` and `controller-interface.json`:
  orientation, mounting and socket references.
- `user-installed.csv`: module/headers, switches, stabilizers and hardware.
- [`firmware/`](firmware/README.md): default and Vial **121-pixel** UF2 files.
- `checks/`: ERC/DRC/netlist, regeneration, migration and test evidence.
- `SHA256.json`: source/export hashes relative to `designs/module-rp2040/`.

Use the **[rev0.8 plate/base/cover](../../mechanical/rev0.8/README.md)** and
[badge print parts](../../LOGO.md). Earlier base/plate files have H9 in the old
position. The square openings are in the plate and cover; the PCB has four small
reverse-LED apertures under the badge.

The Waveshare module, underside Harwin sockets, long Samtec headers, protection,
fabrication minima and current limiter follow rev0.7. LEDs/capacitors use the
existing qualified part selections, with quantities increased by four each.
See the [controller socket interface](../../references/CONTROLLER-SOCKETS-0.7.md)
and [recorded validation](../../VALIDATION.md). Physical fit/light output and
supplier assembly acceptance remain prototype checks.

Regenerate from the repository root:

```sh
python3 -B designs/module-rp2040/source/export_manufacturing.py
```
