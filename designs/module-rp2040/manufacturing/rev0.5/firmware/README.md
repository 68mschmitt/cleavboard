# Cleaver revision 0.5 firmware

Fresh clean builds for the **module-based YD-RP2040 board in `designs/module-rp2040/`**:

- **`Cleaver-rev0.5-vial.uf2`** — Vial remapping and VialRGB; recommended for normal use.
- `Cleaver-rev0.5-default.uf2` — fixed default keymap without Vial.

Hold the module's **BOOT** button while connecting USB, then copy one UF2 onto
the **RPI-RP2** drive. The module reboots when copying finishes. For Vial unlock,
hold **Esc + main Enter** when requested by Vial.

Both builds retain the 117-key matrix/RGB mapping, 8/255 brightness cap, lock-key
indicators and USB-aware LED power control. PCB revision 0.5 does not change the
firmware source or its USB `device_version` (0.3.0). These images target the
module-based RGB design; other hardware variants have separate firmware.

## Rebuild and provenance

Source: [`firmware/`](../../../firmware/).
Use vial-qmk commit `dd43959ae5c08d8a28d38a1acf7b04e86b14a344` with its
recorded submodules and `arm-none-eabi-gcc 16.2.0`. Copy the source directory to
`keyboards/cleaver/` in that checkout, then run:

```sh
make cleaver:default:clean
make cleaver:default -j4
make cleaver:vial:clean
make cleaver:vial -j4
```

`build.json` records the source hash, toolchain, submodule commits, output hashes
and UF2 format checks. Full build output is in `build-default.log` and
`build-vial.log`. Builds and image validation passed; physical hardware operation
has not been tested.
