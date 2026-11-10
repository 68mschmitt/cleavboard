# Cleaver White firmware

Both `default` and `vial` built successfully against
[`vial-kb/vial-qmk`](https://github.com/vial-kb/vial-qmk) commit
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344`, using ARM GCC 16.2.0.
`build/` contains UF2s, build logs and `provenance.json` with source and binary
SHA-256 hashes. These are compile-verified; no hardware was available to flash.

## Controls and pin mapping

- 117 keys, 8×16 ROW2COL matrix: rows GP0–GP7, columns GP8–GP22 and GP26.
  `key_matrix.csv` records every switch coordinate and matrix cell.
- Hold the final macro key **SW117 / M11** for Fn. Fn+F1 toggles white lighting;
  Fn+F2 decreases and Fn+F3 increases brightness. Five nonzero PWM levels.
- GP27 drives PWM slice 5 channel B at approximately 1kHz. GP26 remains a
  matrix GPIO. GP28 enables the TPS2553 lighting supply.
- Lighting defaults off on fresh EEPROM. QMK can retain the user's backlight
  setting; even a restored nonzero setting waits for USB configuration.
- Supply enable precedes PWM by a nonblocking 20ms settling interval. Loss of
  configuration and suspend disable the supply/PWM; resume repeats the checks.
- GP25 status output and unused GP23 RGB data output initialize low. No RGB
  matrix/WS2812 driver is included. The module's fixed power LED stays powered.
- USB declares 200mA. This does not establish actual consumption or suspend
  compliance; see `../POWER.md`. Flash size is configured for the 4MB module.
- Vial unlock combination: **Esc + Enter** (matrix `[0,0]` and `[4,9]`).
  Vial layout and UID are in `keymaps/vial/`.

## Rebuild

Install the upstream QMK build prerequisites (ARM toolchain, Make, Python/QMK
dependencies), then use a dedicated checkout. Set `WHITE_FW` to this directory's
absolute path before changing directories:

```sh
WHITE_FW=/absolute/path/to/designs/single-color-devboard/firmware
git clone https://github.com/vial-kb/vial-qmk.git cleaver-vial
cd cleaver-vial
git checkout dd43959ae5c08d8a28d38a1acf7b04e86b14a344
git submodule update --init --recursive
mkdir -p keyboards/cleaver_white
cp "$WHITE_FW"/*.{c,h,json,mk} keyboards/cleaver_white/
cp -R "$WHITE_FW/keymaps" keyboards/cleaver_white/
make cleaver_white:default -j4
make cleaver_white:vial -j4
```

Outputs are `cleaver_white_default.uf2` and `cleaver_white_vial.uf2`. The supplied
builds both use the pinned Vial-QMK checkout, including the plain default keymap;
an independent build against QMK master is not claimed.

## Flash and check

For Vial, flash [`build/cleaver_white_vial.uf2`](build/cleaver_white_vial.uf2).
This image was rebuilt from the pinned checkout and its RP2040 UF2 block headers
and all 117 layout/matrix positions were checked.

1. Hold **BOOTSEL** on the YD-RP2040 while plugging in USB, then release it.
2. Copy `cleaver_white_vial.uf2` to the **RPI-RP2** drive. The controller reboots
   automatically when the copy completes.
3. Open the Vial application and select **Cleaver White YD-RP2040**. Its layout
   is embedded in the firmware; no JSON import is needed. When prompted to unlock,
   hold **Esc + main Enter** until Vial completes its countdown.

After restart, test all keys/chords and Fn
controls, re-enumeration, disconnect/reconnect and suspend/resume. Scope GP27 and
measure the actual module/lighting current and diode temperature before accepting
the electrical budget. The full prototype checks are in `../POWER.md`.

The custom driver is GPL-2.0-or-later; linked QMK/Vial and ChibiOS components retain
their upstream licenses. Preserve the upstream source at the recorded commit
together with this keyboard directory when distributing the built firmware.
