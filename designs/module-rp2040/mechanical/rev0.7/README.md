# Revision 0.7 mechanics

The switch/stabilizer plate retains rev0.6 geometry: **452.4375 × 147.6375 ×
1.5 mm**, 117 MX positions, seven 2u and one 6.25u Cherry-compatible **plate-mount**
stabilizers, 11 M2 holes and the existing controller notch. The revision-specific
STL/SVG and coupons are re-exported and checked against the new PCB.

- `Cleaver-top-plate-rev0.7.stl` / `.svg`: full-size, unsplit plate.
- `stabilizer-fit-coupon-2u.stl` and `stabilizer-fit-coupon-6.25u.stl`.
- [`case/`](case/README.md): revised base with controller-socket insertion supports,
  unchanged-height cover, spacers, STEP/FreeCAD assembly and USB/seat coupons.
- `validation.json`: source hashes, plate alignment and STL round-trip checks.

The existing rev0.6 plate can be reused; the **new case base is recommended**.
All physical fit, printer shrinkage, stabilizer clips and actual module/USB
geometry remain prototype checks. Keep the carrier's socket holes solder-free.
