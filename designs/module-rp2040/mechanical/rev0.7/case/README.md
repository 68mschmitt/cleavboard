# Revision 0.7 socket-support case

Use `Cleaver-case-base-rev0.7.stl` with
`Cleaver-case-top-cover-rev0.7.stl`; corresponding STEP files and
`Cleaver-case-assembly-rev0.7.FCStd` / `.step` are provided. Print eleven
`PCB-to-plate-spacer-3.5mm.stl` spacers. The full base needs approximately
**466 × 164 mm plus brim clearance**; it is not split for a small printer.

## Changes and fit

Two floor-connected ribs back the **underside Harwin controller sockets**.
Their faces follow the PCB's 5° plane and sit **0.70 mm below nominal 7.5 mm
socket bottoms**, clearing the drawing's full **7.0–8.0 mm** height range.
Select one supplied **0.2 / 0.4 / 0.6 / 0.8 / 1.0 mm shim** per rib as needed
for a **measured 0.1–0.3 mm gap**, including adhesive. Secure shims against
sliding; never preload a socket. They support insertion load without changing
the module height. Do not use the old base as if it had
these supports; support both sockets directly when mating outside this base.

The module's male-header **insulators seat on the carrier top**; the long posts
go through its NPTH holes. Use the specified 8.13 mm posts, not unverified
pre-headered module pins. USB remains right-facing at nominal Z=5.74 mm, in a
**16 × 7.2 mm** tunnel. The cover underside remains **8.4 mm above PCB top**;
CAD collision checks use a conservative 8.2 mm controller top envelope and
51.3 × 4.25 × 8.0 mm socket envelopes. C5 retains its 11 mm depth allowance.

The 11 Ø6 mm PCB bosses, 3.5 mm plate spacers, 0.25 mm edge clearances, 2.8 mm
floor, 19 M2 insert pockets and 117 keycap sweeps retain the previous design.
Use eleven M2×10 PCB/plate screws and eight M2×6 cover screws with the specified
M2 inserts (approximately Ø3.2 × 4 mm); test the 3.0 mm pilot holes first.

## Assembly and mandatory coupon test

1. **Print both `USB-and-seat-fit-coupon-*.stl` parts first.** They now include
   both socket backstops as well as H5, the USB tunnel and the cover seat.
2. Check the real sockets, carrier, male-header/module stack, USB cable and
   shim-adjusted support gap. Deburr/calibrate: do not force an interfering rib.
3. Fit the carrier into the base and support it before inserting U1. Press evenly
   near both header rows; do not apply full insertion force to an unsupported PCB.
4. Test electrical operation before closing the cover. Disconnect USB before
   removal; lift the module evenly, never lever it by the USB connector.

STLs are individually bed-oriented; STEP/FCStd use assembled coordinates. Print
the base floor-down and cover exterior-down as exported. Hardware/USB geometry,
socket retention, material strength and shrinkage have **not been physically
validated**. CAD interference checks are not a mechanical load certification.

Regenerate with KiCad Python, FreeCAD, Shapely ≥2.1, NumPy, SciPy and Trimesh:

```sh
python3 -B designs/module-rp2040/source/generate_top_plate.py
python3 -B designs/module-rp2040/source/generate_case.py
```

See `parameters.json`, `validation.json`, and the
[socket qualification](../../../references/CONTROLLER-SOCKETS-0.7.md).
