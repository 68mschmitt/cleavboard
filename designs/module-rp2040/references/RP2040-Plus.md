# Waveshare RP2040-Plus review — 2026-11-11

Sources:

- https://docs.waveshare.com/RP2040-Plus
- https://docs.waveshare.com/RP2040-Plus/Resources-And-Documents
- https://files.waveshare.com/wiki/RP2040-Plus/RP2040_Plus.pdf
  (archived as `RP2040-Plus-schematic.pdf`)
- https://docs.waveshare.com/assets/images/RP2040-Plus-details-size-6c1430864c01e95cbf22c9d4c128e82c.webp
  (archived as `RP2040-Plus-dimensions.webp`)

The published schematic explicitly connects header U5.40 / Vbus to USB-C
A4/B9 and A9/B4, upstream of D1 (MBR230LSFT1G). Header 39 is VSYS on the
other side of D1. Thus carrier U1.40 supplies RAW_USB_5V without passing the
keyboard LED current through the module's VSYS diode or 3.3V regulator.

Pins 1–34 and 38 retain the previous carrier's GPIO/GND mapping. Pins 35, 36,
37, 39 are ADC_VREF, 3V3_OUT, 3V3_EN and VSYS respectively; all remain NC on
the carrier. GP23/24/25/29 are module-internal functions, not keyboard GPIOs.
The status LED is GP25. BOOT uses QSPI_SS_N; RESET uses RUN.

The dimension drawing gives a 51 x 21 mm PCB, 17.78 mm row spacing, 2.54 mm
pitch, 1.37 mm from the USB-end board edge to pins 1/40, and 1.61 mm from
the long edge to each header centre. This gives the same ±8.89 / ±24.13 mm
header centres as the previous footprint. Keeping the carrier placement puts
the module's USB-side PCB edge 1.17 mm inboard of the carrier edge. The existing
plate opening covers the smaller module; actual USB-plug/case fit still needs
checking. The drawing specifies 8.95 mm USB width, but not shell projection
or height; those dimensions in the visualization model are approximate.

Target purchase: RP2040-Plus 4MB, SKU 20290, or RP2040-Plus-M, SKU 20808.
The optional 16MB versions have the same documented header interface.
Waveshare lists W25Q32JVSSIQ / W25Q128JVSIQ flash respectively; both use the
Winbond-compatible QMK boot stage. Firmware uses only the first 2MB.

The current web page describes MP28164 regulation while the linked schematic
labels TPS63000. The carrier relies on the documented VBUS/header interface,
not that regulator identity. The battery connector is unused in this design.
