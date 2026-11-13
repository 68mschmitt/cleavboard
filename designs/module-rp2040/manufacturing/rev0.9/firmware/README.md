# Revision 0.9 firmware

- **`Cleaver-rev0.9-vial.uf2`**: remapping, macros and VialRGB controls.
- **`Cleaver-rev0.9-default.uf2`**: default QMK keymap and RGB controls.

Both drive **117 key LEDs + four badge LEDs** on the Waveshare RP2040-Plus, with
the wider badge's updated LED coordinates and USB device version **0.9.0**.
Key brightness remains capped at 8/255 and badge brightness at 32/255. RGB/Vial
controls set the badge's color; VialRGB direct mode addresses pixels individually.
USB configuration, suspend and RGB-off gate LED power.

Hold BOOT while connecting USB (or hold BOOT and tap RESET), then copy the UF2
to `RPI-RP2`. Vial unlock is **Esc + main Enter**. The Vial UID, matrix and first
117 RGB indices are retained. Rev0.8 builds also drive the four badge pixels,
but retain the previous pixel coordinates and USB device version.

`build.json` records build logs, source/output hashes, pinned vial-qmk revision
and UF2 format checks. [Source/build commands](../../../firmware/README.md).
Physical hardware operation has not yet been tested.
