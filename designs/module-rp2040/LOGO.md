# Replaceable illuminated logo — rev0.8

One **16 mm square printed badge** sits between the front **M6–M8 / M9–M11**
clusters. Four controllable RGB LEDs illuminate it through aligned square
openings in the switch plate and case cover.

## Print and customize

Files are in [`mechanical/rev0.8/case/`](mechanical/rev0.8/case/README.md):

- **`Logo-insert-blank.stl`**: hollow, flanged translucent insert with a **1 mm
  diffuser face**. Print in translucent/natural or light-transmitting white
  material. Its visible face is 16 × 16 mm; the hidden retaining flange is 19 mm.
- **`Logo-light-well.stl`**: print opaque to contain light and support the insert.
  It rests on the plate and stops 0.8 mm above the PCB.
- **`Logo-insert-template.scad`**: editable badge with an example “C”. Replace
  `mark()` with your own centered artwork/SVG inside the **13 × 13 mm design area**.
  Export `mask` in opaque material and `diffuser` in translucent material, then
  load both as one multi-material object **at their shared origin**. The mask is
  0.4 mm thick. `blank` exports the plain insert. Keep the mechanical body/flange.
- **`Logo-fit-coupon-cover.stl` / `Logo-fit-coupon-plate.stl`**: actual sections
  of the new cover and plate for checking clearance before a full-size print.
- STEP files and the case FCStd assembly provide an alternative editable CAD
  starting point. STLs are already bed-oriented; STEP files retain assembly axes.

Print the light well and insert in their exported orientations. Place the well
through the plate opening, seat the badge on its flange, then fit the cover.
**To swap a badge, remove the eight cover screws and lift the cover.** The badge
and well then lift out; no adhesive or permanent fasteners are needed. The cover
captures the badge's flange, and the well prevents it falling toward the LEDs.
For the fit coupons, hold the cover underside **3.4 mm above the plate top** to
reproduce the real stack. Physical fit and illumination need a sample print.

## Mechanical interface

All PCB coordinates below use the upper-left origin, X right, Y toward the user.

| Feature | Dimension / location |
| --- | --- |
| Badge center | **(227.6475, 138.1125) mm**, midpoint between the two trios |
| Plate and cover openings | **16.4 × 16.4 mm** square |
| Insert body / locating sleeve | **16.0 × 16.0 mm**; 0.20 mm clearance per side |
| Hidden retaining flange | **19.0 × 19.0 × 0.8 mm** |
| Light-well bore | **14 × 14 mm** |
| Diffuser face | **1.0 mm**, top flush with the cover at Z=10.8 mm |
| Plate | Z=3.5–5.0 mm above PCB top |
| Light well | Z=0.8–7.4 mm; flange rests on the plate at Z=5.0 mm |
| Insert flange | Z=7.4–8.2 mm; 0.2 mm nominal clearance below cover |
| Cover | Z=8.4–10.8 mm |
| Plate material ahead of opening | **1.325 mm** |
| H9 PCB/plate hole and case boss | Moved from **(220,138)** to **(250,138) mm** |

The narrow front strip determines the square size. The PCB remains solid under
the badge except for the four **3.6 × 3.2 mm LED emitter apertures**. Use the new
PCB, plate, cover **and base together** because H9 moved. The flange and light
well clear the front locating lip, keys and mounting hardware.

## RGB and power

**LED118–LED121** are the same underside, reverse-mounted **SK6812MINI-E /
C5149201** as the keys. **C218–C221** provide individual 100 nF bypass capacitors.
LED centers are `(223.3975,135.6125)`, `(231.8975,135.6125)`,
`(231.8975,140.6125)`, `(223.3975,140.6125)` mm, in that order.

The chain appends to **LED112 (M6), the last key pixel**, using `RGB_117` through
`RGB_120`. Firmware indices **117–120** are non-key accent pixels; all existing
key indices 0–116 and the 117-key matrix retain their meaning. Power comes from
the existing protected **LED_5V** branch, with off-pad vias to the supply/ground
planes. No extra GPIO or external LED wiring is needed.

The badge follows the QMK/Vial **hue, saturation and brightness** controls as a
steady color while key effects run. VialRGB direct mode can address its four
pixels individually. Badge brightness has a **4× gain, capped at 32/255**;
keys remain capped at **8/255**. Zero brightness turns the badge off. The whole
LED supply still switches off before USB configuration, on suspend and RGB-off.

At 12 mA/color, the badge's maximum full-white color current is approximately
**18.1 mA**, plus its four LEDs' idle current. All key + badge color current is
approximately **150.2 mA**, plus all 121 LEDs' idle current. The existing
353 mA nominal branch limiter (311–401 mA calculated bounds) is retained;
actual brightness, diffusion, USB current and rail behavior await a prototype.
Use the **rev0.8 firmware** to drive all 121 pixels.

Sources: [`source/logo_interface.py`](source/logo_interface.py),
[`source/generate_case.py`](source/generate_case.py),
[`firmware/cleaver.c`](firmware/cleaver.c). See [validation](VALIDATION.md).
