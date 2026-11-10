# Cleaver PCB — revision 0.5

**Taviana Tactical artwork:** the active PCB includes a 34 mm-wide top-side logo.
Use the current [revision 0.5 fabrication files](manufacturing/rev0.5/).

117 MX hot-swap switches, 117 reverse-mount RGB LEDs, and the **DWEII / VCC-GND
YD-RP2040 4MB USB-C module** identified in your supplied manual. The keyboard is
USB-powered, with **no mechanical power switch** and no separate power supply.

Read [VALIDATION.md](VALIDATION.md) for the recorded checks and remaining prototype
tests. The old [DESIGN_REVIEW.md](DESIGN_REVIEW.md) describes revision 0.2, not this
replacement design. Electrical checks do not substitute for a physical prototype
or final plate/case checks.

**Revision 0.5 manufacturing:** all **479 factory-populated parts are underside
SMD**, including C5 and the HanElectricity hot-swap sockets. Only the MCU/headers
remain on top for owner soldering. TP1 is now a bare underside SMD wire pad.
There are 11 M2
mounting holes, five labelled underside probe pads and three bottom fiducials.
Use [`manufacturing/rev0.5/`](manufacturing/rev0.5/) for the purchasing BOM,
corrected socket placement data and fabrication package; use
[`mechanical/`](mechanical/) for the matching stabilizer/switch plate and
case mounting references. **Allow 11 mm clearance under C5**; the old case-depth
assumption no longer applies there. Older loose Gerbers and artwork exports are
not this revision. See the [complete live JLCPCB review](references/COMPONENT-REVIEW.md).

## Important: the approved USB power tap is required

The module's **pin 40 is Vout behind its small BAT54C diode**, not an unrestricted
USB 5 V supply. It is deliberately **unconnected** on this PCB. Do not power all
117 LEDs through that pin, VIN, 3V3, or a GPIO.

Add **one short insulated wire** from the module's **raw USB VBUS, before the
BAT54C diode**, to the underside SMD pad marked **TP1 / USB 5V TAP +** at `(446, 27)`
mm. Ground returns through the module's ordinary GND header pins; no second wire
is needed. Route the wire around the board edge and strain-relieve it to the case.
The single USB-C cable still powers everything.

On the published YD-RP2040 V1.1 schematic, raw USB VBUS is the USB-fed anode of D2
(BAT54C, pin 1); pin 3 is the diode-combined output, **not** the tap. Your listing
shows a V1.3 board, so **identify the raw VBUS point by continuity to the USB
connector's VBUS with power disconnected**, rather than trusting a reference
designator or a photo. A USB breakout makes this check easier. Then verify about
5 V relative to GND with the module alone powered. Disconnect power before
soldering the wire, insulate it, and provide strain relief. Do not attach to USB
data, CC, shell mounting tabs, or the diode's output. If the point cannot be
identified confidently, stop rather than bridging the diode or guessing.

LED power path:

```text
Module USB VBUS tap → TP1 → F1 (0.50 A PTC) → U3 (TPS2553) → LED_5V
Module GPIO28 → U3 enable (100 kΩ default-off pull-down)
Module GPIO27 → U2 level translator → R1 (330 Ω) → first LED DIN
```

- U3's **75 kΩ, 1%** current-limit resistor gives approximately **353 mA nominal**
  LED-branch current limiting (about **311–401 mA** using the datasheet bounds and
  resistor tolerance). This is separate from the module's own consumption.
- Firmware caps brightness at **8/255**. For 12 mA/colour LEDs, full-white colour
  current is approximately 132 mA at this setting, plus LED idle current and MCU
  consumption. Measure the actual total; a brightness setting or USB descriptor is
  not itself a current measurement. Do not raise the cap casually.
- RGB power stays off until USB is configured, and is removed on suspend and when
  RGB Matrix is disabled. R2 keeps it off during reset/bootloader operation.
- Every LED has its own 100 nF capacitor. C2 is 22 µF; **C5 is a low-impedance
  470 µF reservoir after the current limiter**, to supply coincident LED PWM pulses.
  It is not attached directly across USB at cable insertion. Fit its polarity
  correctly: pad 1 / `+` is positive, and the can's negative mark goes to pad 2.
- U2 is **SN74LV1T125DBVR**, not an arbitrary 74LVC/HC/AHCT substitute. Its
  reduced input thresholds translate 3.3 V data to the LED supply, and its input
  tolerates the GPIO while the LED supply is off.
- Do not connect a second external 5 V supply at TP1 while USB is connected. This
  design is for a tap from the same module's USB input, not power-source selection.

## Controller placement and pinout

The module uses two 20-pin, 2.54 mm-pitch headers **17.78 mm apart**. Its body is
**53.34 × 22.86 mm**, based on the YD manufacturer's mechanical drawing. It sits
top-right, USB-C facing the right edge. The body ends at the board edge and the
receptacle mouth can project slightly past it. Use headers/sockets with sufficient
underside clearance, and confirm the actual purchased board against a 1:1 print.

This is **not a Pico symbol or an alternating-numbered 2×20 connector**:

| Module pin | YD-RP2040 function | Carrier use |
| --- | --- | --- |
| 35 | GP29 | Unconnected/spare |
| 36 | 3V3_OUT | Unconnected |
| 37 | GP23 / onboard RGB | Unconnected |
| 38 | GND | Ground plane |
| 39 | VIN | Unconnected |
| 40 | Diode-protected Vout | Unconnected |

The module's BOOT and RESET buttons remain accessible in the upper-right area.
No separate USB connector or USB data traces are required on the carrier.

## Matrix, RGB order, and assembly

The electrical matrix is **8×16 ROW2COL**, with 117 unique populated cells:

| Function | GPIOs |
| --- | --- |
| Rows 0–7 | GP0–GP7 |
| Columns 0–15 | GP8–GP22, GP26 |
| RGB data | GP27 |
| RGB power enable | GP28 |

Logical rows are banks of 16 switches in KLE order, **not** the seven physical
key rows. This avoids the old duplicate addresses without adding an expander.
Vial still displays the original physical layout. Every switch goes from its row
through the switch to the diode anode; the cathode connects to the column.

- Diodes are **1N4148W, SOD-123**, using normal **pad 1 = cathode, pad 2 = anode**
  numbering. Match the diode's stripe to the footprint's cathode mark.
  Diodes sit 8.25 mm above switch centres, improving body clearance to sockets.
  These and all other SMD parts are factory-assembled underneath.
- LEDs use the **OPSCO SK6812MINI-E / C5149201 catalog pinout**:
  **1=GND, 2=DIN, 3=VDD, 4=DOUT**. This renumbers the older Rev.02 sheet's pins
  without changing physical net positions. Do not substitute MINI/EA/5050
  packages based only on a similar name.
- LEDs and their 0805 bypass capacitors are on **B.Cu**, with emitters facing
  through the **3.6 × 3.2 mm PCB openings toward the switches**. These are real
  Edge.Cuts, not reference artwork. Mounting pads are outside the opening and
  retain at least 0.5 mm nominal edge clearance.
  From the **top/emitter side**, pad 3 is upper-left, pad 4 lower-left, pad 1
  lower-right, and pad 2 upper-right. The ground-corner mark is on the back.
  Check this orientation on one LED before assembling the entire chain.
  Specify an internal milling-corner radius **no larger than 0.5 mm** (prefer
  0.4 mm) for these small openings; a default 2 mm-diameter cutter will not fit
  the LED's square corners. Confirm the fabricator's aperture tolerances.
- The chain begins at the function-row Pause key near the MCU circuitry, runs
  left across that row, and then snakes across subsequent physical rows. Firmware
  entries are in **actual chain order**, not switch-reference order.
- `firmware/key_matrix.csv` gives switch, matrix cell, position, and RGB index.
  `manufacturing/BOM.csv` lists exact references, values, board side, and placement coordinates.
  SWxxx, Dxxx, and LEDxxx refer to the same physical key; C101 belongs to SW001.
  Each SW footprint is a **B.Cu HanElectricity CPG151101S11-16 / C41430893 socket**.
  The switch plugs in from above. Its origin is still the switch centre; use the
  revision-specific factory CPL for the actual socket placement centre. The owner
  provides two 1×20 headers (and optional mating sockets) and
  the insulated USB tap wire.
- Caps/Num/Scroll lock are indicated using their **own keys' RGB LEDs**. The three
  decorative KLE circles above the numpad do not represent additional components
hidden beneath the MCU.

The four-layer stack uses In1.Cu as ground return, with explicit ground vias
outside solder pads. A **switched LED_5V pour on F.Cu** and off-pad power vias
feed each LED and bypass capacitor, avoiding a narrow, serial supply chain.
Signals use F.Cu/In2.Cu/B.Cu. Preferred track widths are
0.3 mm for signals and 0.6 mm for power; manufacturing minima remain 0.2 mm track,
0.2 mm clearance, 0.5 mm copper-to-edge, and the existing project hole rules.
Ordinary through-vias are used; filled/capped via-in-pad fabrication is not needed.

The power/buffer circuit and bulk capacitor occupy the empty region **left of
the MCU**, rather than overlapping its body or headers. C5 is a bottom-mounted
**Nichicon PCF1A471MCL1GS / C3275369**, 470 µF/10 V SMD polymer, Ø10 mm and
10 mm maximum height, centred at `(377, 6)` mm. Allow **11 mm free case depth
below the PCB at C5**. The old top capacitor plate opening can remain unused.

**Mechanical interface:** switch centres and board outline are retained. The
new plate in `mechanical/` includes matching M2 holes and Cherry-style
**plate-mount stabilizers**: seven 2u sets and one 6.25u spacebar set. Do not use
PCB-mount stabilizers. The custom printed case uses the supplied hole-coordinate
table and 6 mm screw/standoff envelopes. See the mechanical README for nominal
plate spacing, clip thickness, controller/capacitor openings and a fit coupon.

## Populated 3D view

Open **Cleaver.kicad_pcb → View → 3D Viewer (Alt+3)**. The project includes local
models for **all 480 component footprints**, including front-side MX switches,
back-side sockets, LEDs/passives, and a simplified YD-RP2040 with headers/USB-C.
No extra model-library installation is needed. Flip the view with **F** to see
the underside. TP1–TP6, mounting holes and fiducials intentionally have no models.

- [Top-side preview](previews/Cleaver-top.png)
- [Bottom-side preview](previews/Cleaver-bottom.png)
- [Model coverage, approximations, licensing, and STEP export](Cleaver.3dshapes/README.md)

The module/header stack and some package details are approximations; keycaps,
plate, stabilizers, and case are not modeled. These views do not replace the
physical fit checks above. Model assignments are preserved by the generator.

## Vial-QMK firmware

Ready-to-flash revision 0.5 builds and instructions are in
[`manufacturing/rev0.5/firmware/`](manufacturing/rev0.5/firmware/).

Copy `firmware/` to `keyboards/cleaver/` in a **vial-qmk** checkout. From that
checkout run:

```sh
make cleaver:default
make cleaver:vial
```

The Vial keymap includes its own UID, physical `vial.json`, VIA/Vial/VialRGB rules,
and a secure **Esc + main Enter** unlock combination. No insecure-unlock option is
enabled. The RP2040 vendor/PIO WS2812 driver uses GRB data and explicit timings.
The module's onboard RGB LED is not included in the keyboard's 117-LED chain.
Default macro-key assignments can be changed in Vial.

Build provenance and the tested vial-qmk commit belong in [VALIDATION.md](VALIDATION.md).
Compiled firmware has not been exercised on a physical keyboard by this agent.

## Regeneration and checks

`source/design.py` is the shared source for schematic, PCB nets, matrix, RGB
order, and firmware. The PCB receives pad nets from **KiCad's exported schematic
netlist**. Regeneration preserves project settings except for the explicit power
netclass and the preferred 0.3 mm signal width; it does not weaken DRC minima.

Run the following commands from the repository root with KiCad's Python environment.

Generate a fresh **unrouted** placement and DSN only when deliberately restarting
routing:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --placement-only
```

Import a matching routed Specctra session:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --ses designs/module-rp2040/routing/Cleaver.ses
python3 -B designs/module-rp2040/source/check_kicad.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
```

See `routing/README.md` for the autorouter invocation. The DSN preparation carries
KiCad's edge clearances and power widths into the router; a router reporting
“0 violations” is **not** a substitute for KiCad DRC after session import.

## Hardware sources

- [Your supplied module manual and listing photographs](https://manuals.plus/asin/B0CG9BY48X).
- [YD-RP2040 manufacturer drawing, pinout, and schematic mirror](https://github.com/initdc/YD-RP2040).
  The listing photo is V1.3; the available schematic is V1.1. Verify the USB tap on
  the actual board as described above.
- [OPSCO C5149201 datasheet](https://datasheet.lcsc.com/datasheet/pdf/0907a34a701b4aef568078003f6e9eae.pdf).
  Physical reverse-mount signal orientation also agrees with the
  [established MX MINI-E footprint](https://github.com/ebastler/kicad-keyboard-parts.pretty/blob/master/MX_SK6812MINI-E.kicad_mod).
- [SN74LV1T125](https://www.ti.com/lit/ds/symlink/sn74lv1t125.pdf),
  [TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf), and
  [Nichicon PCF capacitor specification](references/Nichicon-PCF.pdf).
- [Exact-part JLCPCB review and socket compatibility](references/COMPONENT-REVIEW.md).

Bring up the prototype on current-limited USB power: check supply polarity/shorts,
test the module and one key first, then one LED, all 117 keys (including chords),
the complete RGB chain, maximum allowed full-white current/rail ripple,
suspend/resume, and USB-A-to-C plus C-to-C enumeration. Keep the brightness cap
until those measurements pass.
