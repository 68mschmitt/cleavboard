# Cleaver-Embedded — embedded-0.2

Open **[Cleaver-Embedded.kicad_pro](Cleaver-Embedded.kicad_pro)** in KiCad 10.
This is a separate, editable project with a bare RP2040 and on-board USB-C.
The original Cleaver project is not its output directory or a build dependency.

**Implementation complete:** final ERC 0, DRC 0, unconnected 0, parity 0; complete
copper regeneration passed. See [the final handoff](HANDOFF.md) for exact results,
hashes, independent firmware evidence and remaining release blockers.

- [Complete schematic PDF](Cleaver-Embedded-schematic.pdf)
- [Controller/power schematic PDF](Cleaver-Embedded-controller.pdf), four focused review pages
- [BOM](BOM.csv), [firmware](firmware/README.md), [validation results](validation/validation.json)
- [Independent default/Vial firmware build evidence](validation/firmware/README.md)

**Prototype engineering design, not fabrication released.** Fresh ERC, DRC,
connectivity and parity results are recorded in `validation/`. In addition to
electrical checks, the inherited LED-aperture tolerance problem, factory DFM,
case fit and hardware testing must be resolved before release.
The project inherits KiCad's ignored missing-courtyard, footprint-filter/type,
off-centre-via and tuning-profile categories; the exact list is in the validation
JSON. All 34 new controller components have checked bottom courtyards and body
outlines; some inherited keyboard footprints lack courtyards. No individual DRC
exclusions are used.

## Preserved keyboard

117 MX hot-swap switches, 117 SK6812MINI-E reverse LEDs and capacitors, all key and
LED coordinates, 8×16 ROW2COL matrix addresses, chain order, 452.4375 × 147.6375 mm
outline, 11 M2 mounting axes and 6 mm mounting-hardware keepouts are inherited from
Cleaver revision 0.4. Unaffected routed copper comes from a local immutable
snapshot. The old YD-RP2040 footprint and manual raw-VBUS wire pad are absent from
the active schematic/PCB. No legacy generation command is needed.

Rows remain GP0–GP7; columns GP8–GP22 and GP26; RGB data GP27; LED enable GP28.
The TPS2553DBVR/75 kΩ branch (~353 mA nominal, approximately 311–401 mA bounds),
SN74LV1T125DBVR level translator, 330 Ω data resistor, default-off pull-downs,
117 local bypass capacitors and 470 µF switched-side bulk capacitor are retained.
**Brightness remains capped at 8/255. USB-C does not authorize higher LED power.**

## Embedded controller

| Function | Implementation |
| --- | --- |
| MCU | RP2040, QFN-56, 7×7 mm, 0.4 mm pitch, pad 57 = 3.2×3.2 mm exposed GND |
| Flash | Winbond **W25Q32JVSSIQ**, 32 Mbit / 4 MiB, **208-mil SOIC-8W 5.3×5.3 mm** |
| Clock | Abracon **ABM8-272-T3**, 12 MHz, 10 pF load; two 15 pF C0G caps and 1 kΩ XOUT series resistor |
| 3V3 | Diodes Inc. **AP2112K-3.3TRG1**, SOT-23-5; pin 1 VIN, 2 GND, 3 EN=VIN, 4 NC, 5 VOUT; 1 µF input/output |
| Core supply | RP2040 VREG_VOUT pin 45 → both DVDD pins 23/50; 1 µF VREG input/output plus 100 nF DVDD bypasses |
| Other decoupling | 100 nF on all six IOVDD pins, ADC_AVDD and USB_VDD; flash and ESD bypasses |
| USB | HRO **TYPE-C-31-M-12** USB2 receptacle; independent 5.1 kΩ CC1/CC2 pulldowns; A/B D+ and D− pairs joined |
| Protection | ST **USBLC6-2SC6**, SOT-23-6; 27 Ω series resistor on each MCU USB line |
| Boot/reset | BOOTSEL → 1 kΩ → QSPI_SS; 10 kΩ flash-select pullup; RESET shorts RUN to GND with 10 kΩ RUN pullup |
| Debug | TP10 SWCLK, TP11 SWDIO, TP12 GND, TP13 3V3 reference, TP14 1V1, TP15 RUN |

The USB receptacle supplies `RAW_USB_5V` directly. AP2112 powers the MCU and flash;
F1 feeds the retained protected LED branch. There is no module Vout diode or VBUS
jumper. USB is a USB2 full-speed device, with neither PD negotiation nor Type-C
high-current detection. Validate pre-configuration, configured and suspend current
on both A-to-C and C-to-C hosts. Do not externally power debug 3V3 while USB is
connected; TP13 is primarily the debugger's voltage reference.

## Layout, assembly and mechanical changes

**All SMD assembly is on the underside (B.Cu/B.Paste):** controller, USB-C,
buttons, passives, sockets and reverse LEDs. Composite switch footprints retain
their original F.Cu metadata and holes; their actual socket lands are on B.Cu.
The BOM reports these sockets as bottom assembly. Through-hole hardware and the
inherited radial bulk capacitor still require their own assembly operations.

The RP2040 is at (428, 11) mm; flash at (435, 20) mm; USB-C at (449, 13) mm.
Coordinates are the normal top-view board frame. The flipped connector still
faces **right**; its fabrication outline extends about 0.52 mm past the board
edge and its axis is 0.39 mm above the old module's axis in plan view.
The connector body now projects approximately **3.16 mm below** the PCB.
BOOTSEL/RESET require **underside access** and about 2.5 mm component clearance;
the flash is roughly 2 mm high. The case needs a lower connector opening and
bottom access/clearance for these parts. Existing plate geometry and mounting
axes are retained; confirm the revised vertical envelope against the actual case.
Decouplers occupy separate adjacent bottom-side footprints rather than opposing
the MCU on the other face. Each controller capacitor ground pad and both crystal
ground pads have a ground via within 1.5 mm, with local bottom copper returns.
The final distances are recorded in `validation/local-ground.json`.

This is a four-layer design. The keyboard retains its ground plane and LED-power
pour; local front and In2 ground regions replace LED power beneath the new
controller. USB and crystal signal paths are hand-laid entirely on B.Cu, with no
signal vias. The router reserves 0.65 mm ground-reference corridors on adjacent
In2 beneath those traces. Local GPIO/power crossings use other In2 areas and
In1 escapes. Actual reference-plane thickness, impedance and return paths still
need stackup review. Electrical connectivity is not signal-integrity qualification.

**Factory reflow assembly is required for RP2040.** The fine-pitch escape region
uses a 0.127 mm minimum track/clearance, 0.20 mm finished drill and 0.40 mm via
land; other new routing commonly uses 0.15 mm or wider. Four ordinary 0.30 mm
drill / 0.50 mm land ground vias are **outside the exposed copper/paste area**,
connected by short 0.4 mm bottom spokes. There are no holes in the exposed pad;
filled/capped QFN via-in-pad processing is no longer required. The QFN paste is
divided into four 1.25 mm squares. Masked vias are not used as a substitute for
moving holes out of solderable exposed-pad copper.
Specify these capabilities and the actual stackup to the fabricator; generic
default two-layer manufacturing settings are unsuitable.

### Routing review

See [before/after review](review/README.md) for actual KiCad copper-layer exports,
controller crops and measured changes. The repeated key cells are retained;
controller/fan-in routing is rebuilt with octilinear paths, and clearance-aware
shortening is applied across the keyboard. Plots hide zone fills in a disposable
copy to make traces visible; the validated PCB retains filled zones.

### Inherited LED opening issue

The 117 original **3.6×3.2 mm square LED openings** are deliberately preserved.
The LED body is nominally 3.2×2.8 mm with ±0.1 mm tolerance. With ±0.2 mm routed
slot tolerance and R0.4/R0.5 internal corners, extreme-fit combinations can fail.
This is the issue recorded in the legacy `manufacturing/ORDER-REVIEW.md`; DRC does
not verify it. Obtain a tolerance-qualified opening/tooling agreement and fit
coupon before fabrication release. This project does not claim to fix it.

## Reproduce and verify

Use a Python interpreter with KiCad 10's `pcbnew`; the generator also needs
Shapely 2. These commands operate exclusively in this project:

```sh
cd designs/embedded-rp2040
python3 -B source/check.py
python3 -B source/generate.py --route routing/Cleaver-Embedded.ses
python3 -B source/check.py
python3 -B source/export_pdf.py
```

The normal rebuild imports the complete-copper archive and refills zones.
`source/legacy-base.kicad_pcb` and `source/legacy-data.json` are read-only inputs
copied from revision 0.4, not the original project. `source/generate.py --placement`
deliberately resets this project's PCB to partially routed placement and exports
`routing/placement.dsn`; use that only when restarting routing. Firmware is
maintained separately and is not overwritten by PCB regeneration.

PDF export alone:

```sh
kicad-cli sch export pdf -o Cleaver-Embedded-schematic.pdf Cleaver-Embedded.kicad_sch
```

`source/export_pdf.py` also makes four controller-only pages using `pypdf`: MCU
and decoupling, flash/clock/boot/reset, USB-C/ESD/regulator, and LED power/buffer. The
schematic source is authoritative; PDF crops are review artifacts, not a second
electrical design. `source/route.py`/`grid_route.cpp` are optional routing-development
tools (Pillow required); the saved archive is the normal reproducible route.
No script imports the legacy generator or writes to root `kicad/`, `scripts/`,
`mechanical/` or `manufacturing/`.

## Reference and license notes

See [PROVENANCE.md](PROVENANCE.md) for baseline identity, attribution, license
scope and the absence of a blanket repository-wide license grant.

See [references/README.md](references/README.md) for datasheet pin/package evidence.
Local symbols explicitly model MCU power, inputs, bidirectional GPIO, regulator
output, buffer output and LED direction. No-connect markers are confined to
unused GPIO/SBU/FAULT/NC pins. The local symbol/footprint tables use `${KIPRJMOD}`.
Existing switch/LED models and their licenses are copied in `Cleaver.3dshapes/`;
several new packages (including RP2040, flash, crystal and USB-C) do not yet have
bundled 3D models. KiCad footprint copies
retain upstream geometry; the RP2040, 0402 and button footprints are dimensioned
local definitions. No 3D view is a tolerance or assembly sign-off.
