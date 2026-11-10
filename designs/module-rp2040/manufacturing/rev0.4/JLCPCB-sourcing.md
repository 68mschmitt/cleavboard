# JLCPCB sourcing evidence — checked 2026-11-08

**Confirmed: JLCPCB has manufacturer-specific catalog entries offering SMT
assembly for both unusual components.** This is stronger evidence than a generic
keyboard blog, but is not a binding promise of stock or acceptance of this order.

| Component | Exact purchasing entry | Published assembly support |
| --- | --- | --- |
| Kailh MX hot-swap socket | [CPG151101S11 — C2803348](https://jlcpcb.com/partdetail/Kailh-CPG151101S11/C2803348) | Manufacturer Kailh; source JLCPCB; SMT Assembly; **Standard Only** |
| Reverse-mount RGB LED | [OPSCO SK6812MINI-E — C5149201](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK6812MINIE/C5149201) | Manufacturer OPSCO; source JLCPCB; SMT Assembly; **Standard Only**, difficulty **High**, **MSL 5a** |

Both entries explain the pre-order-parts → place-PCBA-order → manufacture/assemble
workflow. These are sourcing/assembly listings, not bare-board-only capabilities.
The [LCSC LED page](https://www.lcsc.com/product-detail/C5149201.html) also showed
stock at the time of research; LCSC stock is not reserved JLC assembly stock.

Do not use generic **“JLCPCB Assembly” C990…** entries as evidence of available
manufacturer inventory. For example, C9900001298 is an assembly-service listing
for SK6812MINI-E which showed zero stock / unavailable for purchase, and is not
the manufacturer purchasing code used in this BOM.

## Pinout/source review

The catalog-linked OPSCO document is SK6812MINI-E-012, cover version B/2 dated
2025-11-22 (some page headers still say B/1). Pages 4–5 specify:
**1 GND, 2 DIN, 3 VDD, 4 DOUT**. The emitter-view geometry is VDD upper-left,
DIN upper-right, DOUT lower-left and GND/chamfer lower-right. This matches the
existing physical net arrangement; revision 0.4 aligns the pin numbers as well.

Document URL:
<https://datasheet.lcsc.com/datasheet/pdf/0907a34a701b4aef568078003f6e9eae.pdf>

The drawn LED is 3.2 × 2.8 × 1.78 mm, 5.88 mm overall lead span. Our window is
3.6 × 3.2 mm; copper lands retain nominal 0.59 mm lead overlap at the outer
lead ends and the board's copper-to-milled-edge clearance. Exact production
tolerances and mounting process still require the assembler's DFM review.

## Other purchasing references

Each code can also be looked up directly in JLCPCB's order BOM matcher.

| MPN | Code | Function |
| --- | --- | --- |
| 1N4148W (Semtech) | C81598 | SOD-123 matrix diode |
| CC0805KRX7R9BB104 (YAGEO) | C49678 | 100 nF, 50 V, X7R, 0805 |
| CL21B105KBFNNNE (Samsung) | C28323 | 1 µF, 50 V, X7R, 0805 |
| CL21A226MPQNNNE (Samsung) | C29277 | 22 µF, 10 V, X5R, 0805 |
| 0805W8F3300T5E (UNI-ROYAL) | C17630 | 330 Ω, 1%, 0805 |
| 0805W8F1003T5E (UNI-ROYAL) | C149504 | 100 kΩ, 1%, 0805 |
| 0805W8F7502T5E (UNI-ROYAL) | C17819 | 75 kΩ, 1%, 0805 |
| [1206L050YR](https://jlcpcb.com/partdetail/Littelfuse-1206L050YR/C163512) | C163512 | Littelfuse 0.5 A PTC |
| [SN74LV1T125DBVR](https://jlcpcb.com/partdetail/TexasInstruments-SN74LV1T125DBVR/C473338) | C473338 | TI logic translator |
| [TPS2553DBVR](https://jlcpcb.com/partdetail/TexasInstruments-TPS2553DBVR/C55266) | C55266 | TI adjustable current limiter |

## Quote / engineering message to send with the package

> Please quote two assembled Cleaver revision 0.4 PCBs (optionally three).
> Finished size 452.4375 × 147.6375 mm, four layers, 1.6 mm FR4, ENIG, all 478
> populated SMD parts on bottom only. Owner installs all through-hole parts.
> Please source 117 × Kailh C2803348 and 117 × OPSCO C5149201 per board, plus
> attrition. Confirm current stock/preorder lead time and required excess.
> LEDs must be reverse-mounted with their lenses facing through 3.6 × 3.2 mm
> milled windows toward the top; maximum internal corner radius 0.5 mm.
> Please confirm this placement/reflow process, MSL 5a handling, and the socket
> placement against the assembly drawing and physical pad-coordinate table.
> Please add suitable sacrificial tooling rails/holes, preserve the finished
> board outline, and return depanelized boards. Please include the large-board
> assembly surcharge, tooling/fixture charges, and shipping in the quote.

No message has been sent and no order has been placed by the assistant.
