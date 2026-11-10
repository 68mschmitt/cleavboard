# Live JLCPCB reverse-white LED sourcing — 2026-11-10

## Recommendation

**BrtLed BL-HZ333H-L21-TRE — C5123487** is the preferred replacement candidate
for the 117 Kingbright LEDs. JLCPCB lists it for SMT assembly, Economic and
Standard PCBA, as an Extended component. This is a sourcing recommendation;
at the time of this search the schematic, PCB and manufacturing BOM still
specified the Kingbright. **Implementation update:** the KiCad project and BOM
now use C5123487 and HanElectricity C41430893. The comparison below records the
pre-change evaluation; see `../MECHANICAL.md` and `../validation/replacements.json`
for the implemented geometry and completed CAD checks. Physical qualification
remains outstanding.

- Live part: https://jlcpcb.com/partdetail/5717311-BL_HZ333H_L21TRE/C5123487
- Local datasheet: [BL-HZ333H-L21-TRE.pdf](BL-HZ333H-L21-TRE.pdf)
- Datasheet retrieved from:
  https://file.icallin.com/static/lcsc/documents/2026-01-22/5d6a0760351b74f3569f378dbec90b4b.pdf
- JLCPCB's linked datasheet:
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2208051800_BrtLed-Bright-LED-Elec-BL-HZ333H-L21-TRE_C5123487.pdf

## Live inventory evidence

Fetched JLCPCB's product-page HTML directly over HTTPS and decoded its embedded
Next.js data. Matched the `componentCode` in both `componentInfo` and the separate
purchase/inventory object; related-product counts were excluded. These are live
page-response values, not search-engine snippets. Availability can change and
has not been reserved in an account or validated by an assembly order.

| Part | `overseasStockCount` | `canPresaleNumber` | `preMinPurchaseNum` | `needAuditFlag` |
|---|---:|---:|---:|---|
| C5123487 / BL-HZ333H-L21-TRE | 1,460 | 1,415 | 199 | false |
| C3646935 / XL-3216UWC-FB | 106,623 | 105,549 | 705 | true |
| C7433005 / DY-S321608/UWT-T5-3A | 601 | 501 | 931 | false |

All three returned `assemblyMode: smtWeld`, `componentLibraryType: expand`,
`isBuyComponent: "1"` and `noBuyReason: null`. The stock and presale fields are
distinct; the latter is not a second stock pool. The prepurchase minimum is
not established here as an assembly-order minimum.

C5123487 prices returned in USD: 1–99 $0.0568; 100–299 $0.0454; 300–2,999
$0.0396. At the 100–299 tier, 117 fitted LEDs cost about **$5.31**, excluding
attrition, Extended-part and assembly fees. The inventory is enough for five
117-LED boards (585 fitted LEDs) with substantial attrition allowance. Its
purchase record also reports `lossNumber: 4`, `leastPatchNumber: 5`, and a
3,000-piece full reel; final order quantities are set by the quotation.

## Datasheet comparison with the actual design

Inspected the package and tape drawings, not only the catalog's “1206” label.
The BrtLed drawing shows metallized ends on the lens side and a raised central
lens; the tape drawing shows the flat marked back presented for pickup. This
supports underside placement with the lens directed into the PCB aperture.

| Feature | BrtLed datasheet | Existing Kingbright implementation |
|---|---|---|
| Carrier envelope | 3.20 ±0.10 × 1.60 ±0.10 mm | 3.2 × 1.6 mm nominal |
| Total height | 1.10 ±0.10 mm | 1.05 mm nominal |
| Lens length | 1.40 ±0.05 mm | 1.4 mm nominal |
| Suggested lands | 1.5 × 1.6 mm, 2.0 mm inner gap | 1.35 × 1.6 mm, 2.4 mm inner gap |
| PCB aperture | No dimensioned routed aperture in BrtLed drawing | 2.10 × 2.30 mm |
| Polarity | Green cathode dot/triangle | Pad 1 cathode, pad 2 anode |

The existing aperture is promising: even using the full maximum carrier width
as a conservative lens-width bound gives a 1.45 × 1.70 mm lens envelope, smaller
than the 2.05 × 2.25 mm minimum opening specified in MECHANICAL.md. At ±0.10 mm
placement offset there is at least 0.20/0.175 mm straight-edge margin, before
aperture registration error. Nominal carrier-to-land overlap is 0.40 mm/end;
minimum carrier length and ±0.10 mm placement reduce the limiting end to 0.25 mm.
These are envelope checks, not terminal-wetting or production qualification.

The existing lands differ from the vendor's suggested pattern. Adoption requires
an exact BrtLed footprint/terminal and stencil review, polarity/rotation mapping,
and updated BOM/schematic/model identity. It may retain the present aperture,
but is **not yet a qualified drop-in substitution**. The current precision
aperture/copper-edge constraints in MECHANICAL.md still apply.

Electrically it is a two-terminal white LED, 20 mA maximum continuous current,
with Vf typical 2.8 V / maximum 3.2 V and intensity minimum 63 / typical 120 mcd
at 5 mA. The existing resistor/PWM topology is suitable; 3.9 kΩ remains a
reasonable initial value under the existing current limiter. The design runs
roughly 0.4–0.6 mA per LED, so the 5 mA brightness specification does not guarantee
keycap brightness at the actual operating current. Do not target 5 mA per key:
117 × 5 mA = 585 mA, outside the header-powered design budget.

## Other candidates

- [XINGLIGHT C3646935](https://jlcpcb.com/partdetail/XINGLIGHT-XL_3216UWCFB/C3646935):
  plentiful live stock, but JLCPCB marks assembly difficulty High and returns
  `needAuditFlag: true`. Manufacturer drawing page 8 shows a 1.86 mm lens with
  a general ±0.25 mm tolerance: 2.11 mm maximum exceeds the existing 2.05 mm
  minimum aperture length even before placement error. Requires an aperture/land
  redesign. Catalog color is very cold white (12,000–27,000 K).
  Drawing inspected: https://www.xinglight.cn/uploadfile/202511/f07621b4df781fc.pdf
- [TONYU C7433005](https://jlcpcb.com/partdetail/TONYU-DY_S321608_UWT_T53A/C7433005):
  lower available quantities and prepurchase minimum greater than reported
  presale availability. Its linked PDF could not be retrieved as a valid PDF
  during this check; mechanical suitability is unverified. Not preferred.
