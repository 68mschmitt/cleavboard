# Cleaver KiCad starter project

This project is generated from the supplied KLE JSON and plate DXF. It contains **117 MX switch positions**, one Kailh MX hotswap socket footprint and one 1N4148W diode per key, and **117 SK6812MINI-E addressable RGB pixels**. The three lock-indicator graphics in the KLE are decals, not switch/LED footprints.

## Controller and matrix

The proposed controller is a soldered Raspberry Pi Pico (RP2040) module on a 2x20, 2.54 mm header footprint. QMK supports RP2040; Vial-QMK lists RP2040 as a compatible MCU. The board uses a **13 x 11** diode matrix plus one RGB data pin, which consumes 25 of the Pico's 26 exposed GPIOs.

| Signal | Pico GPIOs |
|---|---|
| Matrix rows R00–R12 | GP0–GP12 |
| Matrix columns C00–C10 | GP13–GP22, GP26 |
| RGB data | GP27 |
| Spare | GP28 |

`firmware/key_matrix.csv` is the generated physical-key to electrical-matrix map. `firmware/config.h`, `rules.mk`, and `keyboard.json` are starting points to copy into a Vial-QMK keyboard definition, not a complete Vial keyboard directory/keymap.

## RGB and USB power limitation

The RGB chain is SK6812MINI-E (not SK6812MINI; verify the exact suffix and pinout when purchasing). The 74AHCT1G125 translates the Pico's 3.3 V data to a solid 5 V LED data level; R1 is a 330 ohm data resistor. F1 is a resettable fuse specified as 0.5 A hold, and C1 is a 470 uF bulk capacitor.

Full-white current for 117 pixels is far beyond USB capability. The supplied QMK starting configuration caps `RGB_MATRIX_MAXIMUM_BRIGHTNESS` at **12/255** and declares 500 mA USB maximum. This is only a conservative initial estimate: LED vendor current varies, so measure current on the assembled board and lower the cap if needed. Do not raise it or enable full-white until power is upgraded. The Pico's onboard USB connector supplies both controller and LED power through VBUS.

## Important status

The PCB file is a **placement and net-assignment starter, not a finished manufacturing design**. It has no copper routing, ground plane, USB connector footprint (the Pico's own connector is used), case, mounting holes, or verified fabrication clearances. The Pico sits in the open gap between M8 and M9; make a case opening/cable path for its USB port. The top-side RGB LED position is a first-pass placement and must be checked against the specific switch housing/LED window and case stack-up. Verify the 14 mm plate cutouts and stabilizer clearance against the DXF before fabrication.

The key apertures and 16 plate stabilizer slots are shown on `Dwgs.User` for reference only; the board edge follows the plate's 452.438 x 147.638 mm envelope. Keep `Dwgs.User` out of fabrication Gerbers.

## Validation snapshot

Checked with KiCad CLI 10.0.8: schematic ERC reports **0 errors and 0 warnings**; PCB DRC with schematic parity reports **0 violations and 0 parity errors**. DRC still reports **499 unconnected pads** because no copper has been routed; this is expected for this placement prototype and must be resolved by routing before fabrication.

Before ordering: complete routing, add mounting features/connector access, confirm the chosen SK6812MINI-E and switch/socket datasheets, run ERC/DRC, and inspect the board against a 1:1 plate print.

## Regeneration

From the repository root, run `python scripts/generate_kicad.py`. It reads the layout JSON and DXF under `plate-2026-11-07T22_24_25.197Z/` and writes the KiCad files under `kicad/`.
