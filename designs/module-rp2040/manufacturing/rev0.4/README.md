# Cleaver revision 0.4 — manufacturing handoff

This package and its hashes record revision 0.4. The commands below refer to the
historical source checkout. Current generation tools produce revision 0.5; see
[the current handoff](../rev0.5/README.md) and the
[path migration guide](../../../../docs/REPOSITORY.md#path-migration).

## Files to submit

1. `Cleaver-rev0.4-fabrication.zip`: four copper layers, masks, silkscreen,
   paste, outline, **separate PTH/NPTH drills**, drill map/report.
2. `BOM-JLCPCB.csv`: **478 components, 12 purchasing groups**, with exact MPNs
   and JLCPCB/LCSC part codes. Quantities are **per board**.
3. `CPL-JLCPCB.csv`: all **478 placements on bottom**, including socket centres.
4. `assembly-bottom.svg`, `pad-orientation-reference.csv`, `fiducials.csv`, and
   these instructions for engineering review.

Do not use the older loose Gerbers or `Cleaver-gerbers.zip` elsewhere in the
repository. Those predate this revision. The PCB/schematic and exported files
are identified by `SHA256.json`.

## Fabrication / assembly specification

- Four-layer FR4, **1.6 mm finished thickness**, standard stackup, 1 oz outer
  copper, standard inner copper; no controlled impedance requirement.
- F.Cu / In1.Cu / In2.Cu / B.Cu. In1 is ground; F.Cu carries the switched LED
  supply pour as well as signals. Do not reorder the copper files.
- Lead-free ENIG finish; green soldermask; white silkscreen; tent signal vias.
- Finished board **452.4375 × 147.6375 mm**. 11 × 2.2 mm NPTH mounting holes.
- 117 internal **3.6 × 3.2 mm** LED windows. Internal corner radius **≤0.5 mm**,
  preferably 0.4 mm. The windows are Edge.Cuts features, not drill holes.
- **JLCPCB Standard PCBA, bottom side only**. Both unusual purchasing codes
  are listed as Standard Only. No top-side component placement or paste pass.
- Manufacturer to add sacrificial **5 mm tooling rails along top/bottom edges**
  and their required tooling holes for conveyor/fixture handling. Preserve the
  finished outline and component coordinates; return depanelized boards. There
  are three global bottom fiducials on the product board. Factory panelization
  details belong to their process; the submitted Gerbers describe the product.
- No components or paste on TP1–TP6, fiducials or mounting holes. No solder fill
  in the user's header/capacitor holes. No through-hole assembly or programming.

## Placement coordinates and orientation

Gerbers, drill files and CPL share the **lower-left PCB datum**. CPL X increases
right and Y increases up in **top view**, even for bottom components. **Do not
mirror X again.** The SVG assembly drawing is a true bottom view (X mirrored),
with readable text. Mechanical CSVs use an upper-left/Y-down datum instead.

All library placement rotations are currently 0 degrees. These angles describe
this design's geometry; confirm catalog-model registration against the supplied
pad table when JLC imports the order. The table provides each physical pad's
net, absolute coordinates and offset from the exported component centre; it is
authoritative if a catalog library uses a different zero-angle convention.

**Sockets:** SW001–SW117 mean *Kailh CPG151101S11 sockets*, not MX switches.
The KiCad footprint combines a top switch and bottom socket, so its nominal
front-side origin must not be used directly. CPL centres are corrected by
**X −0.635 mm, PCB Y −3.81 mm** relative to the switch centres. In top view,
socket pad 1 is right/up and pad 2 left/down relative to this centre. Populate
the underside socket only; its plastic switch-contact openings register with
the two 3 mm NPTHs. The factory sets its nozzle pickup point for this housing.

**LEDs:** OPSCO **SK6812MINI-E / C5149201**, not MINI or MINI-EA. The lens faces
through the window **toward the top-mounted switch**; the LED rear faces the
underside. Follow OPSCO's catalog-linked B/2 document numbering:

| View from keyboard TOP / emitter | Left | Right |
| --- | --- | --- |
| Upper lead row | 3 = VDD | 2 = DIN |
| Lower lead row | 4 = DOUT | **1 = GND, chamfered lead** |

In the bottom assembly view the left/right columns swap. The board corner mark
identifies the GND corner. This revision renumbers the older schematic's LED
pins to match the orderable part; the physical signal positions are unchanged.
The factory must use a reverse-mount placement/retention process appropriate
for the through-window body, and the part's MSL 5a handling/reflow requirements.

**Diodes:** 1N4148W **SOD-123**, cathode pad 1. In top view cathode is left;
in the bottom assembly drawing cathode is right. Match the cathode stripe to
the local silkscreen mark. Do not substitute the smaller SOD-323 1N4148WS.

**ICs:** exact SN74LV1T125DBVR and TPS2553DBVR; do not substitute a similarly
named buffer or the TPS2553 latch-off `-1` version. R4 is **75 kΩ, 1%**.

## User-installed parts

See `user-installed.csv`. MCU, headers and C5 remain **on top**, installed by
the owner after factory assembly. The raw USB tap wire is also owner-installed.
Switches/stabilizers/keycaps are not part of the PCBA order.

Underside test pads: TP2 GND, TP3 raw USB 5V, TP4 switched LED 5V, TP5 LED enable,
TP6 buffered RGB data. Use TP2 as the scope/meter reference. The protected LED
branch is off until USB configuration and firmware enable it; a dark LED rail
before that is expected.

## Ordering status and regeneration

Catalog evidence is in `JLCPCB-sourcing.md`. Files are prepared for submission;
**no order-specific stock reservation, quotation, or factory DFM acceptance has
been obtained**. JLC's engineering review must confirm tooling rails, the LED
window/reverse-mount process, and catalog rotation registration. These cannot
be established by a local electrical DRC.

```sh
python3 -B scripts/generate_kicad.py --ses kicad/routing/Cleaver.ses
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/export_manufacturing.py
```

The exporter runs fresh ERC/DRC/parity/model checks before exporting. Allow for
the manufacturer's component attrition quantity in addition to 117 sockets and
117 LEDs per board. Two assembled boards require 234 of each before attrition.
