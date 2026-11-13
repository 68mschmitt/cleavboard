# Revision 0.8 firmware

- **`Cleaver-rev0.8-vial.uf2`**: remapping, macros and VialRGB controls.
- **`Cleaver-rev0.8-default.uf2`**: default QMK keymap and RGB controls.

Both drive **117 key LEDs + 4 logo LEDs** on the Waveshare RP2040-Plus.
Key brightness is capped at 8/255; badge brightness at 32/255. RGB/Vial controls
change its color and brightness, and VialRGB direct mode can address its four
pixels independently. USB configuration, suspend and RGB-off gate LED power.

Hold BOOT while connecting USB (or hold BOOT and tap RESET). Copy the desired
UF2 to `RPI-RP2`. Vial unlock is **Esc + main Enter**. Existing Vial UID/matrix
mapping and the first 117 RGB indices are retained. Old 117-pixel builds do not
drive the new badge.

Build logs, input/output hashes, pinned vial-qmk commit and UF2 format checks
are in `build.json`. [Source and build commands](../../../firmware/README.md).
Physical hardware operation has not yet been tested.
