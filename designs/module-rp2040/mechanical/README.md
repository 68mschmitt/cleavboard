# Cleaver — case and plate interface

## Revision 0.6 enclosure

[Case and removable top cover](rev0.6/case/README.md): a **5° rear-raised tray**
with 11 matching PCB standoffs, separate key-cluster bezel, right-side USB-C
opening and 3.5 mm plate spacers. Includes printable STLs, STEP/FreeCAD assembly,
an actual-size USB/seat fit coupon and adjustable fit parameters. These full-size
parts need approximately a **466 × 164 mm** bed plus brim allowance; physical
fit testing is still required.

## Print-ready revision 0.6 top plate

Use **[Cleaver-top-plate-rev0.6.stl](rev0.6/Cleaver-top-plate-rev0.6.stl)** for the
current PCB: 117 MX switch openings, seven 2u and one 6.25u plate-mount stabilizer
sets, and all 11 matching M2 through-holes. It is **452.4375 × 147.6375 × 1.5 mm**.
[Printing/assembly instructions and fit-test STLs](rev0.6/README.md) include both
stabilizer sizes. The rev0.6 plate omits the unused top capacitor hole; the
historical references below remain unchanged.

## Historical references and PCB compatibility

**Revision 0.6 PCB:** switch centres, outline and mounting holes are compatible,
but C5 is now underneath at `(377, 6)` mm. Provide **11 mm clear case depth below
the PCB there** for its 10 mm maximum-height SMD can. The old top capacitor
opening may remain unused. The Waveshare RP2040-Plus is **51 x 21 mm**, inside
the existing controller opening, with the same header centres. Its USB-side
PCB edge is 1.17 mm inside the carrier edge; verify actual USB plug/case access.
TP1 is a bare underside VBUS test pad; no tap wire is required. These historical
rev0.4 mockups do not represent the current capacitor or test-pad geometry.

These plate and mounting references remain compatible with revision 0.6 as
described above; the printed PCB mockups record revision 0.4. The original supplied plate remains
in its original directory as an input/reference; it does not include these mounts.

For a full-size printed PCB mockup, use the four interlocking STL sections in
[`pcb-fit-model/`](pcb-fit-model/README.md). Each fits a 235 × 235 mm bed; joined
together they reproduce the board outline, mechanical holes and 1.6 mm thickness.

## Mounting

- **11 × 2.2 mm non-plated holes for M2 hardware**, shared by PCB and plate.
- `mounting-holes.csv`: authoritative coordinates, PCB **top view**, origin at
  upper-left, X right, Y down, millimetres.
- A **6 mm diameter cylinder** around each axis is reserved for screw heads,
  washers and case/plate standoffs. All PCB copper layers exclude this area.
  Keep the actual hardware within this envelope; do not countersink the PCB.
- `mounting-reference.scad` provides axes and standoff envelopes for importing
  into a custom case. Its Y coordinate is negative toward the keyboard front,
  matching ordinary CAD coordinates. PCB top Z=0; PCB underside Z=-1.6 mm.
- Use separate case-to-PCB and PCB-to-plate spacers, or an equivalent printed
  support structure. Choose screw lengths to suit your case and insert depth.
  Do not clamp the board against sockets, leads or SMD bodies.

## Plate and stabilizers

`Cleaver-plate.svg`, `.dxf`, and `.scad` describe the same connected plate:

- 117 MX switch openings, nominally 14 × 14 mm.
- **Seven Cherry-style 2u plate-mount stabilizers**: Backspace, main Enter,
  both Shifts, numpad Plus, numpad Enter, and numpad Zero.
- **One 6.25u plate-mount stabilizer** for Space; centred switch, 100 mm between
  stabilizer stems. The 2u stabilizers use 23.8 mm between stems; the two tall
  numpad keys rotate the stabilizer assembly 90°.
- Retention details and a wire-installation slot, rather than the original
  plate's simple stabilizer-body clearance rectangles.
- An open upper-right notch for the top-mounted controller/USB connector and
  a 10 mm opening over the top-mounted 8 mm bulk capacitor.

Buy **plate-mount**, not PCB screw-in/clip-in stabilizers. These mounts do not
require additional stabilizer drill holes in the PCB. Install stabilizers/wires
in the plate before joining it to the PCB. All SMD parts are below the PCB, so
the top-side stabilizer wire travel is unobstructed.

Nominal MX stack: plate **top 5.0 mm above PCB top**, plate thickness **1.5 mm**,
giving **3.5 mm between PCB top and plate underside**. Confirm with the actual
switch and stabilizer set before fixing printed case spacer heights. The 1.5 mm
thickness is important at the retaining clips; a thick printed plate needs
locally thin clip ledges and reinforcement outside switch/stabilizer envelopes.

`stabilizer-fit-coupon.svg/.dxf` is a small combined switch/2u-stabilizer cutout
to extrude to 1.5 mm and test-print before printing the whole plate. Nominal
drawings include no printer shrinkage or laser kerf compensation. Adjust those
in the fabrication process based on the coupon, not by scaling the entire plate
(which would misalign the switches and mounting holes).

SVG: Y down. DXF/OpenSCAD: Y up, same upper-left datum. DXF coordinates are mm;
explicitly choose millimetres if your importer ignores the unit header.

## Sources and regeneration

The practical Cherry-compatible cutout dimensions are documented by
[swill/kad, `DrawCherryStab`](https://github.com/swill/kad/blob/master/key.go)
and the [author's explanation](https://github.com/swill/kad/issues/14).
The generator constructs the geometric union of switch, housing, latch and
wire openings from these dimensions. This is not a claim of fit testing with
every third-party stabilizer brand.

Install Shapely >=2 in a Python environment, then run:

```sh
python3 -B designs/module-rp2040/source/generate_mechanical.py
```

Generation asserts a single connected, valid plate, eight stabilized keys,
and no screw-head envelope overlapping a plate opening. `validation.json`
records the generated dimensions. Case rigidity and printed clip fit require
the chosen material/printer and physical coupon.
