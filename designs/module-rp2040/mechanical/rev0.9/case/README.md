# Rev0.9 — case with 2 × 1 inch illuminated logo

The visible removable badge is **50.8 mm wide × 25.4 mm tall**. The front bezel,
plate and tray are **8 mm deeper** to accommodate it, retaining all 117 key
positions, the 5° typing angle and right-side USB-C opening. H9 moves to
**(263,138) mm**. Use the rev0.9 PCB, [plate](../README.md), base and cover together.

[Assembled showcase and reproduction](renderings/README.md).

Print one each:

- `Cleaver-case-base-rev0.9.stl`
- `Cleaver-case-top-cover-rev0.9.stl`
- `Logo-light-well.stl` in opaque material
- `Logo-insert-blank.stl` in translucent material

Also print eleven `PCB-to-plate-spacer-3.5mm.stl`. The unsplit case requires
approximately **466 × 172 mm plus brim clearance**.

## Badge

The matching plate/cover openings are **51.2 × 25.8 mm**. The insert's hidden
**53.8 × 28.4 × 0.8 mm flange** is captured beneath the cover. Its **1 mm diffuser**
is flush with the cover top. The opaque light well rests on the plate, 0.8 mm
above the PCB. Four RGB emitters illuminate the badge.

`Logo-insert-template.scad` provides an editable sample “C” and separate mask /
diffuser exports for two-color printing. [Dimensions and customization](../../../LOGO.md).
Print `Logo-fit-coupon-cover.stl`, `Logo-fit-coupon-plate.stl`, the well and insert
first. Hold the cover underside 3.4 mm above the plate top for the coupon assembly.

Remove the eight cover screws and lift the cover to exchange the insert; no
adhesive is required. STLs are individually bed-oriented; STEP and
`Cleaver-case-assembly-rev0.9.FCStd` preserve assembled coordinates.

## Fasteners and controller fit

Use eleven M2×10 PCB/plate screws, eight M2×6 cover screws and nineteen M2 inserts
(approximately Ø3.2 × 4 mm; nominal pilot Ø3.0 mm). The USB fit coupon, underside
socket backstops and 0.2–1.0 mm shims follow the
[rev0.7 controller interface](../../rev0.7/case/README.md). Mount the carrier in the
base before inserting the controller. C5 retains its 11 mm underside allowance.

`validation.json` records CAD intersections, four clear optical paths, all 117
keycap sweeps, socket clearances, STL/STEP round trips and exact source hashes.
Physical fit, diffusion and light output remain untested.
