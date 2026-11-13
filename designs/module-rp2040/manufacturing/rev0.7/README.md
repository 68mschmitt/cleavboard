# Cleaver rev0.7 — bottom-entry SMT controller sockets

**Engineering-quote/prototype handoff, not production-approved.** Read the
[socket qualification and remaining gates](../../references/CONTROLLER-SOCKETS-0.7.md).

Use **`Cleaver-rev0.7-fabrication.zip`**, **`BOM-JLCPCB.csv`** and
**`CPL-JLCPCB.csv`** together. Do not mix these with rev0.6 Gerbers or placement.

## Changes from rev0.6

- **J1/J2: 2 × Harwin M20-7862042 / C5379059**, assembled underneath.
- **481 bottom SMT placements / 14 purchasing groups**, no top factory parts.
- 40 **NPTH** module-entry holes replace 40 plated U1 solder holes. Socket
  contacts and nearby escape vias now carry the signals and VBUS.
- `controller-pin-map.csv` explicitly maps J1/J2 contacts to module pins.
  **J2.1 is module pin 40 / USB VBUS**; the second row runs in reverse order.
- `controller-interface.json` records land/hole checks, pin depth and unconfirmed
  physical/supplier approvals. `pad-orientation-reference.csv` gives actual
  bottom solder-land coordinates in top view, +Y up from the lower-left origin.
- Board dimensions, 117 switch positions, matrix, RGB chain, power protection,
  module location and USB direction are unchanged. Existing rev0.6 firmware is
  compatible: use its [default/Vial UF2 files](../rev0.6/firmware/README.md).

## Pick-and-place rotation corrections

`CPL-JLCPCB.csv` includes the placement-review corrections below. Positive
angle offsets are counterclockwise, normalized to 0–360°.

| Parts | JLCPCB part | Correction | Exported rotation |
| --- | --- | --- | --- |
| U2, SN74LV1T125DBVR | C473338 | **90° counterclockwise** | **90°** |
| SW001–SW117, CPG151101S11-16 switch sockets | C41430893 | **180°** | **180°** |

These are catalog-model zero-angle corrections, **not changes to the PCB
footprints**. They are already applied in the CPL; do not apply them again in
the placement preview. Coordinates, bottom side and physical pad orientation
remain unchanged. All other rotations, including controller sockets J1/J2,
are unchanged. The exporter retains these corrections on regeneration.

## Owner installation

Use **bare Waveshare RP2040-Plus 4MB SKU 20290** and **two Samtec
TSW-120-14-G-S** strips. Solder their **2.79 mm tails to the module only**;
the **8.13 mm gold posts point downward**. Plastic insulators seat on the
carrier top. Plug U1 in from above, USB facing right. **Do not solder or fill
the carrier's 40 entry holes.** The stock pre-headered SKU 20808 is not qualified.

Use the [rev0.7 case base with socket backstops](../../mechanical/rev0.7/case/README.md).
Print the USB/seat coupons first and support the sockets during insertion.
The old rev0.6 base lacks these load supports. C5 still requires 11 mm clear
depth below the carrier. All other mechanical assembly is unchanged.

## Message for JLCPCB engineering

> Please quote single-side bottom SMT assembly, including two Harwin
> M20-7862042 / C5379059 single-row bottom-entry sockets at J1/J2. The owner
> installs U1 later; U1 and its male headers are excluded from your BOM/CPL.
> The 40 Ø1.00 mm controller holes must be **non-plated, open and solder-free**;
> please confirm ±0.05 mm drill/registration tolerance. The socket lands are
> 1.02 × 1.80 mm, trimmed 0.10 mm on the hole-facing edge relative to Harwin's
> recommendation, retaining the outer toe and 0.30 mm nominal hole clearance.
> Please approve this land/stencil adaptation and confirm pickup/placement of
> these 51 mm long tube-packed parts. Confirm every alternating solder tail
> against pad-orientation-reference.csv; KiCad CPL rotation is not a validated
> mapping to your component model. Both sockets are on the bottom and mate
> through the PCB from the top. Do not substitute top-entry-only sockets.
> All 117 SK6812MINI-E LEDs remain reverse-mounted. Confirm the 3.6 × 3.2 mm
> milled apertures, internal radius ≤0.5 mm (prefer 0.4 mm), tolerance/placement
> stack and LED direction before release. Please retain parts-placement review.

Catalog stock is dated evidence, not reserved material or approval. Do not
release a batch until the engineering response and actual preview are checked.
