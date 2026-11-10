# Cleaver-Embedded firmware

Both default and Vial configurations have passed independent compilation and
ELF linkage checks; see [build evidence](../validation/firmware/README.md).

The retained keyboard hook source is GPL-2.0-or-later; the GPL v2 text is bundled
as `LICENSE-GPL-2.0.txt` (GNU's unmodified license text). QMK/Vial dependencies
retain their own license notices in the build checkout.

Copy this directory to `keyboards/cleaver_embedded/` in vial-qmk. The filename
`cleaver_embedded.c` must match the keyboard directory so QMK compiles its USB-aware
LED power hooks. Build `make cleaver_embedded:default` or
`make cleaver_embedded:vial`. Use the Vial build for runtime remapping and VialRGB.

The board is `GENERIC_RP_RP2040`, with the default W25Q080-compatible second-stage
loader for the Winbond W25Q32JV family. `PICO_FLASH_SIZE_BYTES` explicitly selects
4 MiB. Standard RP2040 EEPROM wear leveling reserves the final 8 KiB at 0x3FE000;
the logical EEPROM is 4 KiB. Do not transplant the older module firmware image.

VID/PID FEED:C1EB and Vial UID C1 EA E0 01 20 40 11 09 distinguish this hardware
from the original Cleaver. These development identifiers are not a USB-IF allocation.
The 8/255 RGB cap, 117 LED chain, 8x16 ROW2COL mapping, and Esc + main Enter secure
unlock are retained. GP28 remains low until USB configuration and during suspend.
USB-C does not imply a higher current allowance or enable USB Power Delivery.

Hold BOOTSEL and press RESET to enter ROM USB boot mode, or hold BOOTSEL while
connecting USB. Drag the resulting UF2 onto RPI-RP2. SWDIO, SWCLK, GND and 3V3
reference are available at TP11, TP10, TP12 and TP13 respectively.

Documentation consulted: vial-qmk `docs/platformdev_rp2040.md` and
`docs/drivers/eeprom.md` via Context7 on 2026-11-09. Independent build provenance
is recorded separately in validation artifacts when available.
