# Revision 0.6 — print-ready top plate

For the matching **5° tilted case with a separate cosmetic key cover**, see
[`case/`](case/README.md). Its tray includes all 11 PCB bosses; print 11 of its
3.5 mm spacers to support this plate. The cosmetic cover does not replace this
switch/stabilizer plate.

**[Cleaver-top-plate-rev0.6.stl](Cleaver-top-plate-rev0.6.stl)** is the full-size,
single-piece switch plate for `../../Cleaver.kicad_pcb`, revision 0.6.

| STL | Size, mm | Purpose |
| --- | --- | --- |
| [Top plate](Cleaver-top-plate-rev0.6.stl) | 452.4375 × 147.6375 × 1.5 | Complete plate |
| [2u fit coupon](stabilizer-fit-coupon-2u.stl) | 40 × 24 × 1.5 | One switch, 2u stabilizer and M2 hole |
| [6.25u fit coupon](stabilizer-fit-coupon-6.25u.stl) | 120 × 24 × 1.5 | Spacebar switch, stabilizer and M2 hole |

## Included features

- **117 nominal 14 × 14 mm MX switch openings**, matched to the saved PCB centres.
- **Seven Cherry-compatible 2u plate-mount stabilizer sets**, 23.8 mm stem spacing:
  Backspace, main Enter, both Shifts, numpad Plus, numpad Enter and numpad Zero.
  The two tall numpad stabilizers are rotated 90°.
- **One 6.25u spacebar stabilizer set**, 100 mm stem spacing, with a centred switch.
  Cutouts include housing, latch and wire-installation clearances.
- **11 straight Ø2.2 mm M2 through-holes**, aligned with PCB holes H1–H11.
  [Hole coordinates](../mounting-holes.csv) and 6 mm screw/standoff envelopes
  are unchanged. No countersinks or printed threads are included.
- An open upper-right controller/USB notch. The obsolete top capacitor hole is
  omitted because revision 0.6's C5 is underneath the PCB.

Use **plate-mount stabilizers**, not PCB screw-in/clip-in types. This PCB has no
stabilizer mounting drills. Buy stabilizers matching the spacings above.

## Printing and assembly

Import in **millimetres at 100% scale**, flat on Z=0. The STL is not mirrored;
viewed from above, the controller notch is at the upper right. The full plate
needs a sufficiently large print bed, with additional room for any brim. It is
not split to fit a 235 mm bed; the existing split PCB mockup is not a top plate.

**Print the fit coupons first** with the intended switches and stabilizers.
The supplied STLs use nominal dimensions, without printer shrinkage or hole
compensation. Adjust local hole/contour compensation if needed, not the overall
scale, which would misalign the mounting holes and switches. Clip fit and plate
rigidity have not been physically tested. Support the large, thin plate with the
matching mounting hardware/case; do not thicken its clip edges indiscriminately.

The nominal assembly has the **plate top 5.0 mm above PCB top**, leaving a
**3.5 mm gap below this 1.5 mm plate**. Use separate spacers or case supports at
the mounting axes; the STLs do not include standoffs. Verify the stack with the
actual switches before choosing screws/spacers. Use low-profile screw heads and
keep hardware within the 6 mm reserved diameter; check keycap travel at each
mount. Do not let hardware clamp against sockets or SMD components.

Install the stabilizers and their wires before joining plate and PCB. Confirm
the actual RP2040-Plus/header/USB plug clearance. The case still needs **11 mm
clearance below the PCB at C5, (377, 6) mm**; that is independent of the top plate.

## Regeneration and recorded checks

With KiCad's `pcbnew`, Shapely >=2.1 / GEOS >=3.10, NumPy, SciPy and Trimesh installed:

```sh
python3 -B designs/module-rp2040/source/generate_top_plate.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_top_plate.py'
```

The generator reads but never writes the PCB. It checks its revision, outline,
all switch centres/rotations, all mounting pad centres/drills and controller body
clearance. Each serialized STL is checked for a single watertight body, consistent
winding, positive volume, correct dimensions and opening topology, and an XY
surface matching the intended cutouts. The plate has **128 enclosed through
openings** (117 key/stabilizer openings + 11 mounts), plus the open controller
notch. [validation.json](validation.json) records PCB/STL hashes and these checks;
it is not a physical fit certification. The [SVG](Cleaver-top-plate-rev0.6.svg)
is a matching 1:1 top-view cutting outline.

Historical revision 0.4 mechanical exports and `../Cleaver.stl` are left untouched.
