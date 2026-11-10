# Prototype fabrication / underside assembly package

**Engineering prototype, not a fabrication-qualified release.** First read
`../MECHANICAL.md` for the precise LED aperture process and `../POWER.md` for
actual-module qualification. Files are generated from the checked KiCad board.

## Ordering data

- `BOM-JLCPCB.csv`: 476 bottom SMD placements in exact purchasing groups.
- `CPL-JLCPCB.csv`: all rows marked `bottom`; owner module/headers excluded.
- `pad-orientation-reference.csv`: every SMD pad and net, absolute position and
  displacement from its component placement centre.
- `owner-installed.csv`: module/header and mechanical installation list.
- `fabrication/`: four copper layers, both masks/silks/paste, Edge.Cuts, separate
  plated and non-plated drill files and a drill map/report.
- `Cleaver-White-white-0.1-prototype.zip`: those fabrication files only.
- `SHA256.json`: exact source/export identity.

**CPL origin:** lower-left of board, X right, Y up, coordinates in mm viewed from
the top. Bottom parts are not pre-mirrored in the CSV. Rotations follow the KiCad
footprint orientation convention; the bottom-side flag and pad-reference file
disambiguate polarity when matching a supplier's placement model.

For **SW001–SW117**, the placement is the **socket body centre**, computed from
the two bottom solder-land centres: switch origin **X−0.635, Y−3.81 mm** in the
PCB's top-view/down-Y frame. It is not the composite footprint's MX switch
origin. The footprint is nominally front-side because it also includes switch
holes, but every factory socket pad and all CPL entries are bottom-side.

## Exact replacement parts and placement

- **SW001–SW117:** HanElectricity **CPG151101S11-16 / C41430893**, underside SMT.
- **LED001–LED117:** BrtLed **BL-HZ333H-L21-TRE / C5123487**, underside reverse SMT.

The purchasing BOM, schematic and PCB all carry these exact identities. The
LED is an Extended catalog part; the old blank-code/consignment route is retired.
Live sourcing evidence is in `../references/LED-SOURCING-2026-11-10.md`.

For LEDs, **flat marked back faces away from the PCB**, raised lens faces into
the aperture and emits toward the switches. Pad 1 is cathode/LED_RETURN; pad 2 is
anode/individual resistor. In PCB **top view**, cathode is the left land; when
viewing the underside directly it is on the right. The green cathode mark must
agree with the B.Silkscreen cathode bar and pad-reference CSV.

For sockets the two 3 mm locating holes and stepped pad positions define the
orientation. Their CPL centres are socket centres, not switch centres. The CPL
uses KiCad rotations; JLCPCB's per-part zero-angle mapping has **not** been
confirmed in an uploaded order. Match its assembly preview against
`pad-orientation-reference.csv` and the actual bottom-assembly plot for these
new catalog IDs before approving placement. Do not reuse the former parts'
supplier rotation offsets without checking.

The LED footprint retains custom 1.35 × 1.60 mm lands outside a 2.10 × 2.30 mm
optical aperture; these differ from the vendor's suggested 1.50 × 1.60 mm lands
with 2.0 mm inner gap. Copper/fit checks pass under the precision requirements
in `../MECHANICAL.md`; reverse placement, stencil/reflow wetting and low-current
brightness remain physical qualification items. The geometry is not qualified
for ordinary coarse aperture routing merely because the LED is catalog-listed.

No components are owner-soldered on the underside. All SMD support, including
both capacitors and the MOSFET, is bottom factory assembly. U1 is the top owner
module with two 1×20 headers; it is not an SMT assembly item. Test points and
fiducials are bare pads, not purchasing entries.

Stack: four layers, nominal 1.6 mm FR4; F.Cu LED supply and matrix routes,
In1.Cu GND, In2.Cu switched LED return plus matrix routes, B.Cu SMD/signal routes.
General minima: 0.2 mm track and net clearance, 0.3 mm via drill, 0.5 mm copper to
edge except the specifically documented reverse-LED lands. No via-in-pad,
blind/buried vias, filled/capped holes or owner power wire is required.
