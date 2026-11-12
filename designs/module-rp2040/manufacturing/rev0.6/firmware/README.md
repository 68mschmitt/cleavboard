# Cleaver rev0.6 firmware

- **`Cleaver-rev0.6-vial.uf2`**: Vial remapping and VialRGB.
- `Cleaver-rev0.6-default.uf2`: fixed default keymap.

For the module-rp2040 carrier with **Waveshare RP2040-Plus 4MB or 16MB**.
Hold BOOT while plugging in USB, then copy the UF2 to `RPI-RP2`. Alternatively,
hold BOOT, press/release RESET, then release BOOT. The module restarts after
copying. In Vial, unlock using **Esc + main Enter** when requested.

Both builds preserve the 8x16 ROW2COL matrix, 117-key layout, 117-LED RGB chain,
GP27 data, GP28 USB-aware LED supply enable, and 8/255 brightness ceiling.
The board routes USB VBUS pin 40 to the protected LED branch; no wire tap is needed.
EEPROM uses the first 2MB on either flash variant.

`build.json` records the exact vial-qmk commit, submodules, compiler, source
hashes, image hashes and UF2 validation. Build logs are included. These images
have been compiled and format-checked, but not exercised on physical hardware.
Source and build instructions: [`../../../firmware/`](../../../firmware/).
