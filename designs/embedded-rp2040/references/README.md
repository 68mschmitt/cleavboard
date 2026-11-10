# Pin, package and circuit evidence

Reviewed 2026-11-09. Manufacturer documents are authoritative; distributor mirrors
below reproduce those documents. Downloaded PDFs are unmodified reference copies.

- Raspberry Pi **Hardware design with RP2040**, sections 2.1–2.7:
  https://pip-assets.raspberrypi.com/categories/814-rp2040/documents/RP-008279-DS-2-hardware-design-with-rp2040.pdf
  The primary server rejected binary download in this environment; the bundled
  earlier manufacturer document came from
  https://github.com/janelia-kicad/RP2040_minimal/blob/main/hardware-design-with-rp2040.pdf
  It confirms 15 pF / 15 pF with ABM8-272-T3, 1 kΩ XOUT damping, 27 Ω USB series
  resistors, supply decoupling and machine assembly guidance.
- Raspberry Pi **RP2040 product datasheet**, bundled manufacturer pinout/package
  drawing: https://www.welectron.com/mediafiles/datasheets/raspberrypi/Raspberry-Pi_RP2040_Datasheet.pdf
  Pins 23/50 DVDD, 44 VREG_VIN, 45 VREG_VOUT, 46 DM, 47 DP, 57 exposed GND.
  QFN 7×7 mm, 0.4 mm pitch, exposed pad nominal 3.1 mm / maximum 3.2 mm.
- Winbond **W25Q32JV**, revision I 2021-05-04, sections 3.1, 3.3, 10.2 and 11:
  https://media.digikey.com/pdf/Data%20Sheets/Winbond%20PDFs/W25Q32JV_RevI_5-4-21.pdf
  **SS** is SOIC **208 mil**, not the 150-mil SN package. Pin order is CS, IO1,
  IO2, GND, IO0, CLK, IO3, VCC. Selected part is W25Q32JVSSIQ, 4 MiB, 2.7–3.6 V.
- Diodes Inc. **AP2112**, SOT-23-5 K package:
  https://cdn-shop.adafruit.com/product-files/2471/AP2112.pdf
  Pin 1 VIN, 2 GND, 3 EN, 4 NC for fixed output, 5 VOUT. Use the Diodes Inc.
  AP2112K-3.3TRG1, not an unspecified same-marking compatible regulator.
- Abracon **ABM8-272-T3**:
  https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6387/ABM8_272_T3-3392615-pages.pdf
  12 MHz, 10 pF load, 3.2×2.5 mm; pins 1/3 crystal, 2/4 grounded case.
- HRO **TYPE-C-31-M-12**, base M-12 variant:
  https://en.krhro.com/Product-Details/726.html
  https://omo-oss-file110.thefastfile.com/portal-saas/new2023011311465136174/cms/file/type-c-31-m-12&12a&12b&12c.pdf
  The downloaded KiCad footprint records the original HRO drawing URL. The
  drawing's 0.30 mm signals at 0.5 mm pitch, 0.60 mm shared power pads, four shell
  slots and locating holes match the vendored footprint. A1/B12 and A12/B1 are
  GND; A4/B9 and A9/B4 are VBUS; A5/B5 are independent CC1/CC2. A6/B6 are D+;
  A7/B7 D−; SBU1/2 unused. Buy the exact HRO variant; clone dimensions vary.
- ST **USBLC6-2**, SOT-23-6:
  https://www.st.com/resource/en/datasheet/usblc6-2.pdf
  Figure 1: pins 1/6 IO1, 3/4 IO2, 2 GND, 5 VBUS. USBLC6-2SC6 is selected.
- C&K **PTS636**, bundled 2022-11-14 drawing, page 3, SMT G leads 2.5 mm:
  https://static.chipdip.ru/lib/080/DOC029080813.pdf
  PTS636 SK25 SMTR LFS has **two**, not four, terminals. Land pattern outer
  width 9 mm / inner separation 6.5 mm, two 1 mm-tall lands; thus centres ±3.875
  mm and 1.25×1 mm pads. Body is 6.1×3.7 mm, height 2.5 mm.

Vendored USB-C, SOT-23-5, SOIC-8W and crystal footprints came from the KiCad
`kicad-footprints` GitHub repository. Its libraries are CC BY-SA 4.0 with the
KiCad libraries exception: https://www.kicad.org/libraries/license/
USB-C silkscreen was moved to F.Fab to avoid printing beyond the unchanged PCB
edge. External model references were removed from these new footprint copies.
The active libs include only project-relative model paths or no model.

These references validate design pin assignments and nominal footprints; they
do not establish stock availability, assembly acceptance, USB compliance,
controlled impedance, worst-case fit, or successful operation of a prototype.
