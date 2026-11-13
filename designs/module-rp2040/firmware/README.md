# Cleaver rev0.8 — Waveshare RP2040-Plus / RGB badge

Copy this directory to `keyboards/cleaver/` in a vial-qmk checkout, then run:

```sh
make cleaver:default -j4
make cleaver:vial -j4
```

Ready-to-flash images and build provenance are in
[`../manufacturing/rev0.8/firmware/`](../manufacturing/rev0.8/firmware/).
Hold BOOT while connecting USB, or hold BOOT, press/release RESET, then release
BOOT. Copy the Vial UF2 to the `RPI-RP2` drive. Open Vial and use **Esc + main
Enter** to unlock when requested.

## Hardware compatibility

| Function | GPIOs | Module header pins |
| --- | --- | --- |
| Rows 0–7 | GP0–GP7 | 1, 2, 4, 5, 6, 7, 9, 10 |
| Columns 0–15 | GP8–GP22, GP26 | 11, 12, 14, 15, 16, 17, 19, 20, 21, 22, 24, 25, 26, 27, 29, 31 |
| RGB data | GP27 | 32 |
| Protected LED power enable | GP28 | 34 |
| Raw USB LED supply | VBUS | 40 |

The 8x16 ROW2COL matrix, 117-key physical layout, first 117 LED indices, Vial UID,
VID/PID and secure unlock combination match earlier revisions. Pin 40 is a power pin;
firmware does not drive it. GP28 still gates the TPS2553 after USB configuration,
and disables it on suspend/RGB-off. The key brightness ceiling stays at 8/255.
The module's GP25 status LED is separate from the keyboard RGB chain.

`BOARD = GENERIC_RP_RP2040` and `BOOTLOADER = rp2040` use QMK's default
W25Q080-compatible boot stage, compatible with the Waveshare W25Q32JV (4MB)
and W25Q128JV (16MB). `WEAR_LEVELING_RP2040_FLASH_SIZE` is explicitly 2MB:
firmware and Vial's persistent settings fit within both variants, with EEPROM
at the same address as the earlier generic-RP2040 builds. The USB device
version is now 0.8.0. A new physical module starts with its own EEPROM contents;
export/import your Vial layout to transfer remaps from another module.

## Illuminated badge

The **121-pixel chain** appends four non-key accent LEDs at **indices 117–120**.
They follow the RGB hue/saturation/brightness controls as a steady logo color,
with a 4× brightness gain capped at **32/255**. Key effects still run on the keys.
Zero brightness gives zero logo output. VialRGB direct mode can set the four
badge pixels individually, with the same gain and cap. Suspend/RGB-off still
removes power to all LEDs. See [badge electronics and current budget](../LOGO.md).

Earlier 117-pixel UF2 files do not drive the badge; flash this revision. The
default and Vial builds use the same control/power logic. The executable host
test also checks callback range limits, zero/excess brightness, direct mode and
USB/RGB/suspend power gating.

Validation checks the schematic/PCB/header/firmware mapping, Vial layout,
VialRGB and unlock configuration, and builds both keymaps. Physical USB,
key scanning, LED operation and persistence still require a prototype.
