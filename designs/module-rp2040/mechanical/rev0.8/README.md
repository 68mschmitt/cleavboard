# Revision 0.8 logo plate

Use **`Cleaver-top-plate-rev0.8.stl`** with the rev0.8 PCB and
[matching case](case/README.md). SVG and DXF cutting outlines are also supplied.

- 452.4375 × 147.6375 × **1.5 mm**; plate top **5 mm above PCB top**.
- 117 MX openings, seven 2u and one 6.25u Cherry-compatible plate-mount stabilizers.
- **16.4 mm square badge opening** at PCB `(227.6475,138.1125)` mm.
- Eleven Ø2.2 mm M2 holes; **H9 moved to (250,138) mm**.
- `stabilizer-fit-coupon-2u.stl` and `stabilizer-fit-coupon-6.25u.stl` retain the
  actual clips and M2 clearance for checking your printer/hardware.

The badge opening leaves a 1.325 mm front web. Avoid scaling the plate to adjust
fit, as it would move switch centers. Coupon-test hole/clip compensation first.
Use eleven 3.5 mm PCB-to-plate spacers from the case folder. Install plate-mount
stabilizers and their wires before assembling switches/plate/PCB.

The rev0.7 plate/base do not match the moved H9. All serialized STL openings,
PCB switch/mount positions and controller clearance are checked in
`validation.json`. Physical fit remains untested.

```sh
python3 -B designs/module-rp2040/source/generate_top_plate.py
python3 -B designs/module-rp2040/source/generate_case.py
```

[Badge dimensions, assembly and customization](../../LOGO.md).
