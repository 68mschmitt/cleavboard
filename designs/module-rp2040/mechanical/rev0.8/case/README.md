# Revision 0.8 illuminated-logo case

Print **`Cleaver-case-base-rev0.8.stl`**, **`Cleaver-case-top-cover-rev0.8.stl`**,
eleven **`PCB-to-plate-spacer-3.5mm.stl`**, one **`Logo-light-well.stl`** and one
**`Logo-insert-blank.stl`**. Use the [rev0.8 plate](../README.md) and PCB.

The new cover has a **16.4 mm square opening between the two front three-key
clusters**. A plate-supported opaque light well and flanged translucent badge
form a replaceable illuminated logo. **H9's base boss moved to (250,138) mm**.
The case retains its 5° typing angle, right-side USB-C tunnel and underside
controller-socket support ribs. The base needs roughly **466 × 164 mm plus brim**.

## Badge

[Full badge instructions and dimensions](../../../LOGO.md).
Print `Logo-fit-coupon-cover.stl`, `Logo-fit-coupon-plate.stl`, the well and the
insert first. The visible insert is **16 × 16 mm**, with a **1 mm diffuser face**
and hidden **19 mm flange**. Print the well opaque and the insert translucent.
`Logo-insert-template.scad` provides an editable two-color logo example.

The well drops into the plate, the insert rests on it, and the cover captures the
flange. To exchange artwork, remove the eight cover screws and lift the cover.
STLs are individually bed-oriented. STEP and `Cleaver-case-assembly-rev0.8.FCStd`
use assembled coordinates and include both badge parts.

## Controller, fasteners and fit

Use eleven M2×10 PCB/plate screws and eight M2×6 cover screws with nineteen M2
inserts (approximately Ø3.2 × 4 mm; nominal pilot Ø3.0 mm). USB and controller
geometry follow the [rev0.7 socket interface](../../rev0.7/case/README.md).
Print the `USB-and-seat-fit-coupon-*` pair to check the actual module, cable,
inserts and the two socket backstops. Supplied 0.2–1.0 mm shims let you set the
measured support gap to 0.1–0.3 mm. Mount the carrier in its base before inserting
the controller. C5 retains its 11 mm underside allowance.

`validation.json` records CAD intersections, four clear light paths, all 117
keycap sweeps, socket support clearances and watertight STL/STEP round trips.
Physical fit, material diffusion and light output have not yet been tested.

Regenerate with KiCad Python, FreeCAD, Shapely ≥2.1, NumPy, SciPy and Trimesh:

```sh
python3 -B designs/module-rp2040/source/generate_top_plate.py
python3 -B designs/module-rp2040/source/generate_case.py
```
