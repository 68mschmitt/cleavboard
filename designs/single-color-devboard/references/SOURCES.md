# Component and technical sources

Reviewed for `white-0.1` on 2026-11-10. Inventory observations are dated snapshots,
not reservations. Exact purchasing identities and quantities are in `../BOM.csv`.

| Evidence | Source / local copy | Design consequence |
|---|---|---|
| BrtLed BL-HZ333H-L21-TRE | [JLCPCB C5123487](https://jlcpcb.com/partdetail/5717311-BL_HZ333H_L21TRE/C5123487), `BL-HZ333H-L21-TRE.pdf` | Selected reverse white LED; package/tape drawings inspected; low-current brightness still needs a sample |
| LED live inventory | [Dated sourcing record](LED-SOURCING-2026-11-10.md) | Live product data: 1,460 stock / 1,415 presale; inventory not reserved |
| HanElectricity CPG151101S11-16 | [JLCPCB C41430893](https://jlcpcb.com/partdetail/HanElectricity-CPG151101S1116/C41430893), [vendor PDF](https://datasheet.lcsc.com/datasheet/pdf/d953a8b0b623247f3341ebcfbaa2e88f.pdf), `HanElectricity-CPG151101S11-16.pdf` | Socket recommended hole spacing/diameters and land dimensions match PCB |
| YD-RP2040 module | [Repository](https://github.com/initdc/YD-RP2040), [V1.1 circuit PDF](https://raw.githubusercontent.com/initdc/YD-RP2040/master/YD-2040-2022-V1.1-SCH.pdf), `YD-RP2040-V1.1.pdf` | Pin40 is downstream of BAT54C; pin39 is another diode input. This does not establish the exact purchased V1.3 circuit |
| BAT54C reference limits | [Diodes Incorporated datasheet](https://www.diodes.com/datasheet/download/BAT54C.pdf) | Reference part limits only; actual module diode manufacturer remains unidentified. Direct PDF download returned HTTP 403; no local copy is claimed |
| TPS2553DBVR | [TI datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf), `TPS2553.pdf` | ILIM-to-IN mode: 50/75/100mA minimum/typical/maximum; input bypass requirement |
| AO3400A | [AOS datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf), `AO3400A.pdf` | RDS(on) specified at 2.5V gate drive, suitable for 3.3V control |

## Catalog identities

New branch resistor, MOSFET and PTC identities were independently checked against
their catalog pages. Other carrier commodity identities inherit the rev0.4 BOM;
their links are supplied for order-time confirmation. Stock and assembly-service
availability must be confirmed when purchasing.

| Function | Manufacturer part | LCSC catalog |
|---|---|---|
| 117 LED resistors | UNI-ROYAL 0805W8F3901T5E | [C17614](https://www.lcsc.com/product-detail/C17614.html) |
| Low-side MOSFET | AOS AO3400A | [C20917](https://www.lcsc.com/product-detail/C20917.html) |
| 0.20A hold PTC | Littelfuse 1206L020YR | [C207035](https://www.lcsc.com/product-detail/C207035.html) |
| Current limiter | TI TPS2553DBVR | [C55266](https://www.lcsc.com/product-detail/C55266.html) |
| 330Ω gate resistor | UNI-ROYAL 0805W8F3300T5E | [C17630](https://www.lcsc.com/product-detail/C17630.html) |
| 100kΩ pull-downs | UNI-ROYAL 0805W8F1003T5E | [C149504](https://www.lcsc.com/product-detail/C149504.html) |
| 1µF input ceramic | Samsung CL21B105KBFNNNE | [C28323](https://www.lcsc.com/product-detail/C28323.html) |
| 22µF output ceramic | Samsung CL21A226MPQNNNE | [C29277](https://www.lcsc.com/product-detail/C29277.html) |
| Hot-swap socket | HanElectricity CPG151101S11-16 | [C41430893](https://jlcpcb.com/partdetail/HanElectricity-CPG151101S1116/C41430893) |
| Reverse white LED | BrtLed BL-HZ333H-L21-TRE | [C5123487](https://jlcpcb.com/partdetail/5717311-BL_HZ333H_L21TRE/C5123487) |
| Matrix diode | Semtech 1N4148W | [C81598](https://www.lcsc.com/product-detail/C81598.html) |

Both replacements now have exact catalog IDs in the purchasing and KiCad data.
The previous Kingbright datasheet and footprint remain historical references,
not active BOM items. A generic 1206 white LED is not equivalent.

Manufacturer PDFs remain their respective owners' technical documents. Geometric
and electrical interpretations, tolerances and unresolved checks are documented
in `../MECHANICAL.md` and `../POWER.md`.
