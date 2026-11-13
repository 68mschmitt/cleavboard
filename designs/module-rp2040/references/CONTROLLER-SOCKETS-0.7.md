# Revision 0.7 controller socket qualification

## Selected interface

- Factory: **2 × Harwin M20-7862042**, JLCPCB **C5379059**, J1/J2 on **B.Cu**.
- Owner: **Waveshare RP2040-Plus 4MB, bare SKU 20290**, with
  **2 × Samtec TSW-120-14-G-S** soldered to the module, not the carrier.
- The **8.13 mm gold mating posts point down** through the carrier. The
  **2.79 mm tails** are soldered through the module. Insulators seat on the
  carrier's top surface. Never solder the male posts into the entry holes.
- Row pitch remains **17.78 mm**, contact pitch **2.54 mm**, 20 contacts/row.
  USB-C still faces right. J1.1 = module 1; J2.1 = module **40**, not 21.

The socket is low-profile **above** the carrier, not an ultra-thin connector:
it needs **7.5 mm nominal below the carrier underside**. The module's nominal
top envelope remains 7.64 mm. The case checks an 8.2 mm top envelope below its
8.4 mm cover. Actual package/USB dimensions still need a physical coupon test.

## Source confirmations

1. [Harwin product page](https://www.harwin.com/products/M20-7862042):
   20-position single-row SMT, **dual/top/bottom entry**, 0.64 mm square mating
   pin, 3 A/contact, 260 °C/10 s soldering data.
2. [Harwin drawing](https://content.harwin.com/asset/4f071921-5993-4233-a5de-13dea609e278/DRG-00389-Technical-Drawing-Datasheet-M20-786-pdf.pdf),
   archived as [`Harwin-M20-786.pdf`](Harwin-M20-786.pdf), issue 10:
   M20-7862042 is explicitly on the **active** list, despite other sizes being
   obsolete. Length 51.0 ±0.3, body width 2.50 ±0.15, total height 7.50,
   alternating 0.60 mm tails, 4.00 ±0.25 mm tail span, Ø1.00 entry holes.
   **7.5 mm total height has no individual tolerance: use the drawing's
   general X.X ±0.50 mm tolerance**, not a guessed ±0.10 mm.
3. [Samtec exact part](https://www.samtec.com/products/tsw-120-14-g-s):
   20 positions, one row, **0.320 inch / 8.13 mm post**, 0.530 inch overall.
   [`Samtec-TSW.pdf`](Samtec-TSW.pdf), style 14: 8.13 mm post, 2.79 mm tail,
   2.54 mm insulator. Install inverted relative to a usual upright PCB header.
   Samtec listed 784 pieces available during the review; not reserved.
4. [JLCPCB exact part](https://jlcpcb.com/partdetail/C5379059): captured in
   [`JLCPCB-2026-11-12.json`](JLCPCB-2026-11-12.json), timestamp preserved in UTC
   (2026-11-13 UTC / November 12 local). **28 in stock and 28 available for
   presale**, `smtWeld`, Extended, no component-specific fixture/audit flag.
   Two per board: at most 14 boards before assembly attrition/stock changes.
   Other parts retain November 10 evidence where the refresh hit HTTP 429;
   failed refreshes are explicitly recorded, not presented as fresh stock.
5. [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities):
   Economic supports single-sided placement. All **481 factory parts are
   bottom SMT**; the owner plugs the module in later. This establishes a
   compatible assembly architecture, **not acceptance of this order**.

## Carrier land pattern

The old 40 plated U1 solder pads are removed. J1/J2 each have 20 numbered SMT
lands and 20 **unnumbered, net-free NPTH entry holes** at the original module
pin positions. Off-pad plated escape vias provide electrical layer changes;
none is shared with a pin-entry hole or placed in an exposed solder land.
U1 is an off-board schematic symbol plus an excluded, pad-free PCB visual model.

The vendor layout uses 1.02 × 1.90 mm lands at ±1.65 mm from the hole row.
Its nominal hole-to-land gap is only **0.20 mm**, below this project's existing
**0.25 mm hole clearance**. Revision 0.7 trims **0.10 mm from the hole-facing
edge only**: lands are **1.02 × 1.80 mm at ±1.70 mm**. The outer toe stays at
±2.60 mm, and the nominal hole-to-copper gap becomes **0.30 mm**. Lead overlap
is retained. This deliberate stencil/land adaptation needs JLC engineering
approval; design rules and exclusions have not been weakened.

Require Ø1.00 ±0.05 mm NPTHs, hole/land registration within ±0.05 mm, and
accurate 17.78 mm row spacing. There must be **no plating, solder or solder
paste in the entry holes**. Check actual 40-pin insertion alignment on samples;
the depth calculation below does not establish XY tolerance compatibility.

## Pin depth and case load path

`source/socket_interface.py` records a conservative depth calculation:

- Minimum post: 8.13 −0.13 = **8.00 mm**.
- Maximum carrier: 1.60 +0.16 = **1.76 mm**; allowed seating gap **0.20 mm**.
- Minimum socket insertion: **6.04 mm**.
- Worst contact depth from PCB-facing entry: (7.50 +0.50) − (3.66 −0.10)
  = **4.44 mm**, leaving **1.60 mm past the contact point**.
- Maximum insertion: (8.13 +0.13) − (1.60 −0.16) = **6.82 mm**.
- Minimum socket height 7.00 mm leaves **0.18 mm** before the far end.

The seating gap and carrier tolerance are explicit engineering assumptions;
socket height/contact tolerances use the drawing's general tolerance block.
This budget is not a vendor-qualified mixed-manufacturer pair.
The pre-headered **SKU 20808 is not qualified**: its post length is not established
by the module's board-outline drawing. Do not substitute it without measuring.

Harwin specifies maximum insertion force 2 N/contact: **80 N over 40 contacts**.
The rev0.7 base adds **two floor-connected backstop ribs**, nominally 0.70 mm
below the socket bottoms (0.20 mm below the 8.00 mm maximum-height envelope).
Printed **0.2 / 0.4 / 0.6 / 0.8 / 1.0 mm shims** are supplied. Measure each
actual gap, select and secure a shim per rib as needed for **0.1–0.3 mm
clearance without preload**. Include adhesive thickness in the measurement;
never leave a loose shim that could slide onto contacts. The unshimmed gap is
0.2–1.2 mm over the full socket height range. Fit the carrier in this base
before inserting U1; support both sockets directly outside the case. Check
ribs and shims on the USB/seat coupon. Never press hard on an unsupported socket or lever the
module out by its USB connector. Withdraw it straight and evenly, unplugged.

## Production gates — not yet confirmed

- JLC engineering: adapted land/stencil, NPTH tolerances, pickup of the long
  tube-packed sockets, and all existing reverse-LED milling requirements.
- Actual BOM/CPL preview: both socket bodies and **all 40 alternating tails**
  must align with the supplied pad coordinates; JLC's zero-angle model mapping
  is not inferred from KiCad's angle.
- Physical sample: insertion alignment/contact retention, USB-A/C cable access,
  seating height, rib gap, module removal and firmware/hardware bring-up.

No supplier was contacted and no order or inventory reservation was placed.
