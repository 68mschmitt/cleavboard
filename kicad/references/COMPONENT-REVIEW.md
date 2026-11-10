# Revision 0.5 component review — 2026-11-10

All **13 factory purchasing groups / 479 placements** have an exact, purchasable
JLCPCB SMT listing with positive stock. Every factory schematic/PCB component has
its manufacturer, MPN and LCSC/JLCPCB code embedded; switch legends use `Key`.

Evidence: [live page records](JLCPCB-2026-11-10.json), captured with
`scripts/review_jlcpcb.py`. The script decodes JLCPCB's embedded page data and
matches **both** component and inventory objects to the exact catalog code.
It does not use search snippets or related-product stock. All selected records
report `assemblyMode: smtWeld`, `isBuyComponent: "1"`, `noBuyReason: null` and
`needAuditFlag: false`. “Available” below means this dated catalog observation;
stock is not reserved. JLCPCB does not supply a manufacturer lifecycle field in
these records, so purchase availability is not presented as lifecycle certification.

## Complete factory BOM cross-reference

| References | Qty | Manufacturer / exact MPN | JLCPCB | Library | Stock | Available presale | Package / review |
|---|---:|---|---|---|---:|---:|---|
| SW001–SW117 | 117 | HanElectricity CPG151101S11-16 | [C41430893](https://jlcpcb.com/partdetail/C41430893) | Extended | 216,697 | 183,820 | SMD MX socket; replaces unavailable Kailh |
| D001–D117 | 117 | ST(Semtech) 1N4148W | [C81598](https://jlcpcb.com/partdetail/C81598) | Basic | 3,471,971 | 3,075,331 | SOD-123; 1=K, 2=A, ROW2COL retained |
| LED001–LED117 | 117 | OPSCO SK6812MINI-E | [C5149201](https://jlcpcb.com/partdetail/C5149201) | Extended | 210,937 | 198,869 | Reverse RGB; 1=GND, 2=DIN, 3=VDD, 4=DOUT; aperture/pinout retained |
| C3, C101–C217 | 118 | YAGEO CC0805KRX7R9BB104 | [C49678](https://jlcpcb.com/partdetail/C49678) | Basic | 25,830,632 | 22,369,344 | 0805, 100 nF, 50 V, X7R; bypassing retained |
| C1 | 1 | Samsung CL21B105KBFNNNE | [C28323](https://jlcpcb.com/partdetail/C28323) | Basic | 3,902,934 | 2,949,602 | 0805, 1 µF, 50 V, X7R; U3 input bypass |
| C2 | 1 | Samsung CL21A226MPQNNNE | [C29277](https://jlcpcb.com/partdetail/C29277) | Extended | 420,883 | 353,276 | 0805, 22 µF, 10 V, X5R; output bypass, in parallel with C5 |
| C5 | 1 | Nichicon PCF1A471MCL1GS | [C3275369](https://jlcpcb.com/partdetail/C3275369) | Extended | 103 | 103 | 470 µF, 10 V polymer, D10 × 10 mm; new bottom SMD footprint |
| R1 | 1 | UNI-ROYAL 0805W8F3300T5E | [C17630](https://jlcpcb.com/partdetail/C17630) | Basic | 1,617,055 | 1,390,718 | 0805, 330 Ω, 1%; RGB series damping |
| R2, R3 | 2 | UNI-ROYAL 0805W8F1003T5E | [C149504](https://jlcpcb.com/partdetail/C149504) | Basic | 2,551,803 | 2,056,385 | 0805, 100 kΩ, 1%; default-off/data pull-downs |
| R4 | 1 | UNI-ROYAL 0805W8F7502T5E | [C17819](https://jlcpcb.com/partdetail/C17819) | Extended | 645,650 | 610,144 | 0805, 75 kΩ, 1%; retains approximately 353 mA nominal limit |
| F1 | 1 | Littelfuse 1206L050YR | [C163512](https://jlcpcb.com/partdetail/C163512) | Extended | 10,488 | 10,275 | 1206, 0.50 A hold; existing raw-VBUS protection |
| U2 | 1 | Texas Instruments SN74LV1T125DBVR | [C473338](https://jlcpcb.com/partdetail/C473338) | Extended | 89,109 | 88,572 | SOT-23-5; threshold-translating buffer; no generic HC/LVC substitution |
| U3 | 1 | Texas Instruments TPS2553DBVR | [C55266](https://jlcpcb.com/partdetail/C55266) | Extended | 56,875 | 55,916 | SOT-23-6; pinout, enable and ILIM circuit retained |

Presale availability and stock are distinct fields, not additive pools. C5 has
the smallest inventory: 103 pieces, enough for 103 fitted boards before any
order-specific allowance. The page's pre-purchase minimum is four; it is not
assumed to be an assembly-order minimum. Check the actual quotation quantities.

## Socket replacement and physical compatibility

The original Kailh CPG151101S11 / **C2803348 has zero stock and zero presale**.
The selected HanElectricity socket is the same exact part used in
`designs/single-color-devboard/`. Its [drawing](HanElectricity-CPG151101S11-16.pdf)
specifies 6.35 mm horizontal / 2.54 mm vertical contact-hole separation, Ø3 mm
holes, and 2.55 × 2.50 mm lands. These match the actual retained geometry:

- Top-view pad 1: `(switch X + 6.29, switch Y − 5.08)`.
- Top-view pad 2: `(switch X − 7.56, switch Y − 2.54)`.
- Socket holes: `(X + 2.54, Y − 5.08)` and `(X − 3.81, Y − 2.54)`.
- Placement centroid: `(switch X − 0.635, switch Y − 3.81)`.

All 117 footprints are now genuinely **B.Cu / SMD**, with their original switch
centres, pad nets, lands and non-plated switch holes. The local library is
normalized for the normal bottom-side flip; flipping the old footprint directly
would have moved its holes and solder lands. The CPL uses the socket centroid,
not the switch origin. The 3D socket envelope is explicitly an approximation.

## Bulk capacitor replacement

The radial Panasonic EEU-FR1A471 is replaced by **Nichicon PCF1A471MCL1GS**.
The [manufacturer page](https://www.nichicon.com/en-us/part/pcf1a471mcl1gs/432/)
lists **Mass Production**. The [PCF datasheet](Nichicon-PCF.pdf) establishes
470 µF ±20%, 10 V, 16 mΩ maximum ESR at 100 kHz, 4.6 A rated ripple at
105°C/100 kHz, 940 µA maximum rated-voltage leakage, and 2,000 h at 105°C.
Ripple limits at other frequencies use the datasheet's frequency coefficients.
It preserves the reservoir capacitance and voltage rating, with low ESR for
coincident RGB PWM pulses. It remains **after** U3, never directly across USB.
The existing brightness cap and current limiter remain in force.

The [manufacturer land recommendation](Nichicon-SMD-land-pattern.pdf), polymer
Ø10 row, is **two 4 × 2 mm lands with a 4 mm inner gap**, implemented at X=±4 mm.
Pad 1 is positive/LED_5V (left in PCB top view), pad 2 negative/GND (right).
The body is Ø10 ±0.5 mm, platform 10.3 ±0.2 mm, maximum height 10.0 mm.
C5 remains centred at `(377, 6)` mm, now underneath. Reserve at least **11 mm
case depth beneath C5** including assembly clearance. Its maximum body/platform
fits within the new courtyard; the nearby R2 body starts 0.75 mm beyond the
maximum platform envelope. Power/ground use off-pad vias. Follow the PCF reflow
limits, including one cycle maximum at 260°C, or two at 250°C.

Rejected catalog checks are also recorded: Panasonic C494797/C497581 had only
three pieces each; C344072 had zero. The chosen Nichicon avoids those stock limits.

## Every non-factory item

| Items | Disposition |
|---|---|
| U1 YD-RP2040 4 MB USB-C module and its two 1×20 headers | Owner-installed on top; exact module not located in JLCPCB search. A bare RP2040 or XIAO is not a footprint-compatible replacement. These are the only 40 plated through-hole component pins. |
| TP1 | Bare **bottom SMD** 2.4 mm circular wire pad, no paste or fitted component; raw USB tap wire still required. Route around the board edge and strain-relieve to the case. |
| TP2–TP6 | Bare bottom SMD probe lands, no purchased part, no paste. |
| H1–H11 | Mechanical NPTH mounting holes; no PCBA component. |
| FID1–FID3 | Bare bottom copper fiducials; no PCBA component. |
| LOGO1 | Top silkscreen artwork; excluded from BOM/CPL. |
| 117 MX switches, keycaps, plate stabilizers and case hardware | Mechanical/owner assembly; switches plug into the underside sockets from above. No soldered through-hole switch terminals. |

Manufacturer PDFs remain their respective owners' documents. Catalog stock and
CAD checks do not establish physical fit, reverse-LED reflow or hardware operation.
