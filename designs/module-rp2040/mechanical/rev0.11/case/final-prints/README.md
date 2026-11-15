# Final installed parts

Use **STL** files in the slicer; matching **STEP** files are provided for CAD.

| Quantity | File | Notes |
| ---: | --- | --- |
| 1 | `Cleaver-case-base-rev0.11.stl` | Tall pass-through mounting posts |
| 1 | `Cleaver-case-top-cover-rev0.11.stl` | Bottom-fastened cosmetic cover |
| 1 | `Cleaver-switch-plate-rev0.11.stl` | Integral downward PCB mounting bosses |
| 1 | `USB-bezel-nominal.stl` | Use if the measured cable fit is correct; otherwise export a fitted replacement |
| 1 | `Logo-light-well.stl` | Opaque material |
| 1 | `Logo-insert-blank.stl` | Translucent material, or customize with `Logo-insert-template.scad` |
| As measured | `controller-socket-shim-*.stl` | Choose the needed thickness; do not install every supplied option |

**Templates:** `USB-bezel-template.scad` adjusts the cable opening.
`Logo-insert-template.scad` customizes the badge.
`Logo-gasket-cut-template.svg` is cut from **0.8 mm soft foam**, not printed as
a rigid installed part.

The `--usb-only` generator writes `USB-bezel-fitted.stl` and `.step` into
`final-prints/` beneath the chosen output directory.

Start with the [test prints](../test-prints/README.md), then follow the
[hardware and assembly guide](../README.md). Use the matching rev0.11 PCB.
