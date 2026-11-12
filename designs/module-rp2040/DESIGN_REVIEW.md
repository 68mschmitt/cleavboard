# Electrical, Vial-QMK, and assembly review

Source paths and commands in this historical review refer to the original
checkout. See the [path migration guide](../../docs/REPOSITORY.md#path-migration)
and [current design documentation](README.md) for revision 0.6.

> **Historical review of revision 0.2.** The user subsequently selected the
> DWEII/VCC-GND YD-RP2040, removed the power-switch requirement, and approved a
> raw-USB-VBUS tap for RGB power. Revision 0.3 replaces the matrix, schematic,
> footprints, power circuit, and routing. See [README.md](README.md) and the latest
> validation results for its actual status; the old counts below are not its DRC.

Reviewed 2026-11-08 against commit `fc0b76922d99575eb1e385c6a7414a17272c5096`,
using KiCad CLI 10.0.8, the exported schematic netlist, the saved PCB, the generator,
and the firmware files. **Do not fabricate or populate this revision. It will not
work as intended.** This report records findings and proposed corrections; it does
not implement a new circuit or placement.

## Verification results

| Check | Result |
| --- | --- |
| Schematic ERC | 0 errors / 0 warnings, but all library pins are typed passive |
| Schematic/PCB netlist parity | 0 issues; agreement does not establish correctness |
| PCB DRC, latest run | 665 violations: 513 errors and 152 warnings |
| Unconnected items (reported separately by KiCad) | 251 additional errors |
| Switches / diodes / RGB LEDs | 117 / 117 / 117 |
| Independently addressable matrix positions | **95**, not 117 |
| Logical LED chain | All 117 DINs and 116 inter-LED DOUTs correctly assigned |
| Complete, build-tested Vial keyboard definition | Missing; not compiled |
| Physical power switch | Missing from both schematic and PCB |

The DRC includes 199 net shorts, 66 crossing-track errors, 85 clearance errors,
90 hole-clearance errors, 48 board-edge errors, 25 solder-mask bridges, 96 dangling
vias, 45 dangling tracks, 6 co-located holes, and 5 hole-spacing warnings. These
are functional and manufacturing problems, not cosmetic warnings.

Repeated DRC runs on the unchanged files reported 665–671 violations, differing by
six clearance reports. The latest run is tabulated above; both runs found the same
199 shorts and 251 unconnected items.

## Blocking findings, in correction order

### 1. MCU footprint and power pin definitions are wrong

`scripts/generate_kicad.py:pico_footprint()` numbers the two header rows as
odd/even pairs. A Pico instead has **1–20 down one side and 40–21 down the other**.
Its physical copper therefore does not match the GPIO names used by the schematic
and firmware. For example, pads 1 and 2 are opposite each other in this PCB, but
the actual module's pins 1 and 2 are adjacent on the same side.

There is a separate schematic error: `PICO_NAMES`, `GND_PINS`, and `UNUSED_PINS`
declare pin 36 to be GND and pin 38 to be 3V3_OUT. The actual Pico has **pin 36 =
3V3_OUT and pin 38 = GND**. Fixing only the header geometry would consequently
connect the module's 3.3 V output to ground. Correct both the symbol and footprint,
then reassign and reroute every MCU connection. Do not plug a module into this PCB.

The stock Pico is micro-USB, not USB-C. Select one exact USB-C module and verify
its manufacturer's pinout, header spacing, connector overhang, and underside
components. A generic claim of “Pico compatible” is not sufficient. The
[Waveshare RP2040-Plus](https://www.waveshare.com/wiki/RP2040-Plus) is one candidate
with USB-C and 26 GPIOs, not an approved drop-in replacement for this footprint.

### 2. Twenty-two pairs of keys share matrix addresses

`read_keys()` clusters physical x coordinates into 17 columns without checking
whether two switches in a row use the same column. The exported schematic confirms
22 duplicated cells: 44 physical keys are affected. They cannot be distinguished
by QMK or Vial, even after every routing error is repaired. RGB reactive effects
also cannot map both keys independently through the same matrix address.

Examples: grave and `1` share `(1, 1)`, `W` and `E` share `(2, 3)`, and numpad
`9` and `+` share `(2, 16)`. The two 22-key physical rows cannot fit on 17 columns
while retaining one electrical row per physical row.

Use a deliberately assigned, unique logical matrix rather than proximity-based
clustering. **8×16 is a reasonable candidate**: 128 positions, 24 matrix GPIOs,
one RGB GPIO, and one spare of the module's 26 exposed GPIOs. Some physical rows
must be divided between logical rows. Vial can still show the original physical
layout. This requires a new verified mapping and corresponding schematic, copper,
keymap, unlock combo, and RGB layout; changing only firmware is not a repair.

### 3. LED and buffer footprints do not fit the specified packages

`Cleaver.pretty/SK6812MINI-E.kicad_mod` places four square pads at `(±1, ±1)`.
The MINI-E is a gull-wing, reverse-mount package with an approximately 5.88 mm
overall lead span. In the cited Rev. 02 recommended land pattern, VDD/DOUT are on
one side and DIN/GND on the other; the current pads instead put VDD/DOUT together
along the top. Rotation alone does not fix the dimensions or pad ordering.
There is also no LED body opening on Edge.Cuts. These are not solderable,
verified MINI-E land patterns for per-key backlighting.

Choose the exact purchased LED and revision, use its recommended footprint and
orientation, add the required body openings, and verify its location against the
switch's LED window. MINI-E variants and newer datasheets may use different pin
number conventions: verify functions against the physical leads, not just names.

`AHCT1G125_SOT23-5` also has incorrect geometry: its three-pad side uses 0.65 mm
pitch rather than the standard SOT-23-5's 0.95 mm pitch, and the pad banks are too
far apart. The diode footprint uses 2.30 mm pad-centre spacing instead of the
3.30 mm spacing in the standard KiCad SOD-123 footprint. Replace these with
datasheet-verified land patterns. Keep the diode's cathode stripe visibly marked;
the custom symbol's 1=A / 2=K numbering is opposite the usual KiCad diode symbol.

### 4. LED power, ground, and matrix copper are incomplete or shorted

The schematic's ROW → switch → diode anode → cathode → COL topology is consistent
with QMK **ROW2COL**. The intended GPIO allocation and logical RGB chain are also
internally consistent with the current (incorrect) symbol definitions. Those
logical checks do **not** validate the copper or the actual parts.

Specific PCB failures include:

- LED VDD pads have vias but no connecting stubs to the row power rails. For
  LED001, VDD is at `(34.7875, 15.025)` while its rail is at `y=12.325`.
- U1 ground pads remain unconnected to the board's ground network.
- Row buses assume a common y coordinate, but the tall numpad `+` and Enter
  switches have different centres; DRC reports open connections on ROW2 and ROW4.
- RGB-chain tracks cross other nets' through-vias on inner layers, including
  ground vias. A through-via occupies all copper layers, not just the pad layer.
- Tracks cross switch mounting holes and approach the board edge too closely.

Rebuild routing after correcting the matrix, components, and placement. Do not
try to preserve this copper merely because it looks routed. Use a continuous
ground return, appropriately sized 5 V distribution, ordinary vias outside solder
pads, and explicit connections to every power pin. Four layers do not make hand
assembly harder; two layers are preferable only if they can be routed cleanly.

### 5. LED power needs decoupling, inrush control, and a measured budget

Only C1 (470 µF) exists. Add a local ceramic bypass capacitor at each LED supply
and at the logic buffer (normally 100 nF, subject to the exact datasheets). A
distant bulk capacitor does not replace them. Prefer 0805 parts for hand assembly.

117 LEDs at 12 mA per colour would draw about **4.21 A at full white**, excluding
idle current and the controller. The current 12/255 firmware brightness cap lowers
the nominal colour-channel average to about 198 mA, but this is not a worst-case
current guarantee. Include LED idle current, module consumption, tolerances,
startup, and suspend behavior. Measure before permitting higher brightness.

F1 protects only the LED branch, not the whole keyboard. A 500 mA-hold PTC is not
a precise USB current limiter, and `USB_MAX_POWER_CONSUMPTION` only declares a
descriptor value. C1 plus the local bypass capacitors also presents a large USB
attachment load. Use controlled inrush/soft-start or a validated smaller bulk
capacitance; do not attach 470 µF directly to USB through a PTC and assume that is
USB-compliant. Validate both USB-A-to-C and C-to-C operation with the chosen module.

### 6. Power-switch behavior must be chosen before placement is finalized

There is no power switch to review. Do not confuse the 117 key switches with a
dedicated supply switch.

- **RGB-only off:** the simplest option. Switch the LED power branch while keeping
  the MCU and keys operating. Ensure the data buffer is disabled or has suitable
  powered-off input protection so GP27 cannot back-power the unpowered LED rail.
  Never switch ground. Check current rating and capacitance charging inrush.
- **Whole-keyboard off:** switching the LED branch or the carrier's VSYS connection
  will not stop a module powered through its own USB socket. Depending on the
  selected module, coordinated regulator-enable and LED-power control can disable
  operation, but is not a complete VBUS disconnect. A true supply disconnect needs
  access upstream of the module's internal USB power connection, for example via
  a separately designed USB connector/daughterboard. RUN-to-GND is reset, not a
  full power switch.

### 7. The firmware directory is not yet a Vial-QMK port

`firmware/keyboard.json` lacks a `layouts.LAYOUT` definition, and there are no
default/vial keymaps, `vial.json`, keyboard UID, unlock combo, or Vial build rules.
The RGB layout repeats the same 22 matrix cells and marks every LED as modifier
(`flags: 1`) instead of ordinary key backlighting (`4`, with modifier flags as
appropriate). `key_matrix.csv` is also not correctly CSV-escaped: SW087's comma
legend shifts its matrix and coordinate fields.

After the hardware mapping is fixed, generate all definitions from one mapping,
use a proper CSV writer, and compile both default and Vial keymaps against a pinned
vial-qmk revision. Vial's keymap-level rules need `VIA_ENABLE = yes` and
`VIAL_ENABLE = yes`; RGB Matrix GUI support additionally needs
`VIALRGB_ENABLE = yes` and `"lighting": "vialrgb"` in `vial.json`. Use a real,
reachable two-key unlock combo and verify it on hardware. The RP2040 vendor/PIO
WS2812 driver is an appropriate choice; confirm timing against the purchased LED.

## Space use and hand-assembly recommendation

The top-right region above the numpad is a good controller location. The current
module centre is `(424.2375, 13.39)` mm, and its modeled body occupies roughly
`x=398.84–449.64`, `y=2.89–23.89` mm. Preserve this general region, but position the
actual USB-C receptacle mouth using the selected module's drawing, allowing for
the cable plug and case wall rather than trusting the current fictional outline.

**Move C1 out of the MCU region.** Its 8 mm body at `(412, 3.5)` overlaps the
module's body/header area and extends 0.5 mm beyond the top board edge. Its power
pad also violates clearance to a controller pad. A raised header is not sufficient
justification for a tall electrolytic in that location.

Reserve the unused area just left of the MCU, approximately `x=372–396`,
`y=0–25` mm, for the chosen edge-actuated through-hole switch and the compact
power/buffer circuit. These are proposed reservation bounds, not approved part
coordinates. Keep capacitor bodies and switch pads fully supported by the PCB,
provide iron access and actuator clearance, and check the complete plate/case
stack-up before fixing coordinates.

For the easiest reliable assembly:

- Use a specific USB-C controller module on soldered or socketed 2.54 mm headers,
  not a hand-soldered bare RP2040/QFN and custom USB front end.
- Use verified SOD-123 diode lands, 0805 passives, and a verified buffer footprint.
  A through-hole 74AHCT125 is an option if the reserved area and case height allow;
  unused gates must be terminated correctly.
- Put reference designators, cathode/LED orientation marks, power-switch states,
  and test points on accessible silkscreen. The generator currently hides all
  component reference fields.
- Avoid open vias in solder pads; they wick solder and complicate rework. Use
  thermal relief on through-hole ground/power pads.
- Start the LED chain near the MCU, then map its physical order in firmware. The
  current buffer-to-first-LED path totals about **779 mm**, detouring via the
  bottom edge; it is unnecessarily long. Keep the buffer/resistor/first LED close.
- The KLE's three separate lock-indicator decals have no dedicated hardware.
  Confirm whether per-key RGB indicators are sufficient or separate LEDs are wanted.
- Confirm plate-mounted versus PCB-mounted stabilizers. The DXF slot drawings are
  reference artwork only; PCB-mounted stabilizers would need real footprints/holes.
  Mounting holes and case support also remain unspecified.

## Release gates

1. Select the exact USB-C module, LED, power-switch function, and stabilizer type.
2. Validate 117 unique matrix cells, diode orientation, GPIO-to-module pin mapping,
   one RGB chain, and firmware/PCB agreement before routing.
3. Rebuild the schematic using meaningful input/output/power pin types. ERC must
   test the circuit, not merely find no conflicts among passive pins.
4. Complete routing with zero shorts, crossings, clearance errors, or unconnected
   items. Review warnings individually; do not weaken rules to hide failures.
5. Compile default and Vial firmware; validate every layout/LED coordinate and the
   security unlock keys. This review did not perform a firmware build.
6. Inspect a 1:1 mechanical print and the assembled stack-up, then bring up a
   prototype with current-limited power: module first, one key, one LED, then the
   complete matrix/chain. Test simultaneous keys, every LED, maximum allowed
   brightness, USB enumeration, suspend/resume, inrush, and the power switch.

## Reproducing the KiCad checks

Use absolute input paths so KiCad loads the project settings and schematic parity
correctly. The following commands write reports only; they do not save the board.
The output directory must already exist. Exit code 5 means violations were found.

```sh
mkdir -p /tmp/opencode/cleaver-review
kicad-cli sch erc --format json --severity-all --exit-code-violations -o /tmp/opencode/cleaver-review/erc.json "$(realpath kicad/Cleaver.kicad_sch)"
kicad-cli sch export netlist --format kicadxml -o /tmp/opencode/cleaver-review/netlist.xml "$(realpath kicad/Cleaver.kicad_sch)"
kicad-cli pcb drc --format json --schematic-parity --severity-all --exit-code-violations -o /tmp/opencode/cleaver-review/drc.json "$(realpath kicad/Cleaver.kicad_pcb)"
```

The reviewed PCB SHA-256 is
`7361ebc6f007ea8368e0441c3b22200e1f1a8a9985b5fccf38cea33399af72ba`;
the schematic is
`553fe6788f22c1e39bc4ba481d349ab94ba000498f3e2371060eb07bd0d16a01`.

### Reference documents

- [Raspberry Pi Pico datasheet](https://datasheets.raspberrypi.org/pico/pico-datasheet.pdf),
  mechanical specification and pinout, especially pins 36/38.
- [OPSCO SK6812MINI-E Rev. 02](https://cdn-shop.adafruit.com/product-files/4960/4960_SK6812MINI-E_REV02_EN.pdf),
  pages 4, 6, and 9. Use the datasheet for the exact purchased revision in the redesign.
- [KiCad SOD-123 footprint](https://github.com/KiCad/kicad-footprints/blob/master/Diode_SMD.pretty/D_SOD-123.kicad_mod)
  and [SOT-23-5 footprint](https://github.com/KiCad/kicad-footprints/blob/master/Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod).
- [Vial porting guide](https://get.vial.today/docs/porting-to-vial.html)
  and [RGB Matrix / VialRGB](https://get.vial.today/docs/lighting.html).
