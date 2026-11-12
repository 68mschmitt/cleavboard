# Revision 0.6 validation — Waveshare RP2040-Plus

Recorded **2026-11-11**, KiCad **10.0.8**. Electrical/layout checks and both
firmware builds pass. Physical hardware operation and mechanical fit remain
unverified.

## Results

| Check | Result |
| --- | --- |
| Unit tests, including Shapely routing checks | **31 passed, none skipped** |
| Schematic ERC, all severities | **0 violations** |
| PCB DRC, all track errors, refilled zones | **0 violations** |
| Unconnected copper / schematic parity issues | **0 / 0** |
| U1 pin 40 → RAW_USB_5V → F1 → U3 → LED_5V | Pass; routed copper |
| Waveshare header mapping, including pins 35–40 | Pass |
| Independent firmware GPIO-to-Waveshare-header check | Pass |
| 8x16 ROW2COL matrix / unique keys / RGB LEDs | 8x16 / 117 / 117 |
| Vial layout, UID, VID/PID, secure unlock, VialRGB | Pass |
| Complete-copper archive regeneration | Exact match, **4,067 tracks + 670 vias** |
| Factory assembly | 479 bottom SMD placements, 13 purchasing groups |
| Through-hole component pads / front paste pads | 40 U1 pads / 0 |
| SMD via holes outside exposed solder lands | Pass |
| Local 3D coverage | 597 instances across 480 populated footprints |
| Updated populated top/bottom previews | Exported |
| Default / Vial firmware builds | **Pass / pass** |
| UF2 format, RP2040 family, flash/EEPROM bounds | Pass |

Revision 0.6 adds two 0.6 mm front-copper segments from U1.40 to the existing
RAW_USB_5V branch. All 4,735 prior tracks/vias remain. The schematic, symbol,
footprint, nominal 51 x 21 mm module model, BOM, silkscreen and assembly
instructions now identify Waveshare RP2040-Plus. TP1 remains as a VBUS test
pad. No tap wire is needed.

The header positions, 117 switch centres, matrix GPIOs, GP27 RGB data, GP28
LED enable, and RGB chain are retained. Vial identity/unlock are retained;
firmware explicitly keeps EEPROM within the first 2MB, suitable for both 4MB
and 16MB RP2040-Plus variants. The USB device version is 0.6.0.

## Firmware build

Built in a fresh checkout of **vial-qmk
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344`**, with its pinned submodules and
**arm-none-eabi-gcc 16.2.0**:

```sh
make cleaver:default -j4
make cleaver:vial -j4
```

Both UF2 images start at `0x10000000`; the Vial image ends at `0x1000da00`,
well below the EEPROM region. The builds include GP28 USB-aware power control,
the 8/255 brightness ceiling, lock-key indicators and secure Esc + main Enter
unlock. Logs, images, exact input hashes and provenance are in
[`manufacturing/rev0.6/firmware/`](manufacturing/rev0.6/firmware/).

## Evidence and reproduction

- [`validation/`](validation/): ERC/DRC, fresh netlist, integration result and
  SHA-256 manifest for the active design.
- [`manufacturing/rev0.6/`](manufacturing/rev0.6/): fabrication ZIP, BOM/CPL,
  assembly drawing, orientation reference, drills, checks and firmware.
- [`routing/Cleaver.ses`](routing/Cleaver.ses): checked complete-copper archive.
- [`references/RP2040-Plus.md`](references/RP2040-Plus.md): vendor pinout,
  VBUS circuit and nominal geometry review with archived source documents.
- [`previews/`](previews/): populated KiCad renderings. Module connector/package
  details are approximations; see the local model README.

From the repository root, with KiCad Python and Shapely >=2:

```sh
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
python3 -B designs/module-rp2040/source/check_kicad.py
```

To regenerate intentionally, import the matching revision 0.6 archive:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --ses designs/module-rp2040/routing/Cleaver.ses
python3 -B designs/module-rp2040/source/check_kicad.py
```

The fresh generated board and in-place migrated board were compared by their
deterministic complete-copper archives and matched exactly. All project
fabrication minima, DRC/ERC severities and exclusions are retained.

## Prototype checks

Confirm the actual module/header stack and USB plug/case access against a 1:1
print. The smaller module fits inside the existing controller plate opening;
its USB-side PCB edge is 1.17 mm inside the carrier edge. Leave the battery
connector unused for USB-only operation. Allow 11 mm free depth below C5.

Test all keys/chords, RGB chain, lock indicators, Vial unlock/remapping and
persistence, suspend/resume and USB-A-to-C/C-to-C enumeration. Measure USB
startup/suspend/full-white current and LED rail ripple at the retained 8/255
ceiling. The TPS2553 branch limit remains approximately 353 mA nominal
(311–401 mA calculated bounds), plus module consumption. No physical prototype
has been tested as part of this change.
