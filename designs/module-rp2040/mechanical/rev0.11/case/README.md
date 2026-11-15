# Rev0.11 — PCB/plate cartridge and replaceable USB bezel

**Match the rev0.11 PCB, switch plate, base and cover.** The earlier PCB and
flat plate do not have this mounting arrangement.

## File folders

- **[test-prints/](test-prints/README.md)** — fit coupons, dummy PCB, measuring
  blank, controller support jig and gasket cutting-pattern reference.
- **[final-prints/](final-prints/README.md)** — installed case/plate parts, badge,
  USB bezel, socket shims and customization/cutting templates.

STL and matching STEP files are grouped together. Assembly CAD, reference
drawings, parameters and validation reports are alongside this guide.

## Mounting arrangement

| Sites | PCB hole | Printed support | Screw direction |
| --- | --- | --- | --- |
| H1–H12 | Ø7.0 mm NPTH | Ø6.0 mm base posts pass through PCB and stop at plate underside | M2 × 5 downward through plate |
| H13–H24 | Ø2.2 mm NPTH | Ø6.4 mm downward plate bosses stop on PCB top | M2 × 4 upward from PCB underside |

The plate remains **1.5 mm thick**, with its underside **3.5 mm above PCB top**.
The downward bosses incorporate short **2.5 mm inserts** and flared roots.
Each large PCB passage provides **0.5 mm radial clearance** around its base post.
The base posts support the plate directly; those screws do not clamp the PCB.
Plate-to-base holes are Ø2.8 mm for assembly tolerance. Three left/rear datum
tabs locate the plate, with extra clearance around the rest of its edge.

All 24 positions were selected against routed tracks, vias, pads, component
bodies, switch/stabilizer cutouts and hardware access. Existing tracks/vias
and electrical component positions are retained. Copper keepout diameters are
**8.0 mm** around pass-through holes and **6.4 mm** around attachment holes.

[Mounting plan](mounting-plan.svg) · [Sections](assembly-sections.svg) ·
[Exact PCB coordinates and drill sizes](../../../manufacturing/rev0.11/mounting-holes.csv)

## Print files and hardware

Installed parts are in **[final-prints/](final-prints/README.md)**:

- `Cleaver-case-base-rev0.11.stl`
- `Cleaver-case-top-cover-rev0.11.stl`
- **`Cleaver-switch-plate-rev0.11.stl`** — includes the downward bosses
- `USB-bezel-nominal.stl`, or fit a replacement using the blank in `test-prints/`
- `Logo-light-well.stl`, opaque
- `Logo-insert-blank.stl`, translucent, or a customized badge
- Controller socket shims as determined by measurement

The temporary `Controller-insertion-support-jig.stl` is in `test-prints/`.

STL files are individually bed-oriented. The plate and cover print exterior/top
face down; USB inserts print outer face down. STEP parts retain their PCB-frame
coordinates except for the desk-flat base; the complete STEP/FreeCAD assembly
positions everything correctly.

`Switch-plate-plan-reference.svg` / `.dxf` show the planar cutout geometry.
They are **not a complete fabrication definition** for the integral-boss plate.
Use its STL/STEP.

| Quantity | Hardware |
| ---: | --- |
| 12 | M2 × 5 socket-head screws, plate to base |
| 12 | M2 × 4 socket-head screws, PCB to plate |
| 12 | Insulating flat washers: **Ø5 outside, Ø2.2 inside, 0.3 mm thick** |
| 8 | M2 × 8 socket-head screws, cover from underneath |
| 20 | M2 heat-set inserts, approximately Ø3.2 × 4 mm: 12 base + 8 cover |
| 12 | **Short M2 inserts, approximately Ø3.2 × 2.5 mm**, downward plate bosses |
| 1 | 0.8 mm soft silicone-foam badge gasket, compressed to 0.6 mm |

Socket-head screw envelopes are Ø3.8 × 2 mm. Plate-to-base engagement is 3.5 mm.
PCB-to-plate engagement is 2.1 mm with the specified washer; its blind pilot is
2.8 mm deep. Do not substitute the 4 mm inserts in the short plate bosses.

The base needs approximately **466 × 175 mm plus brim clearance**. Start with
five perimeters at a 0.4 mm nozzle, 0.2 mm layers and locally solid insert
bosses. Inspect the sliced short pilots, USB flange ears and front-edge bevel.
Use the same material and dimensional compensation for coupons and full parts.
Test heat-set pilot fit before printing the full plate.

## Assembly — the requested two-stage sequence

1. Install the twelve short inserts **flush with the bottoms of the downward
   plate bosses**. Install twelve long inserts in the tall base posts and eight
   in the cover pillars.
2. Fit the plate-mount stabilizers. Align the PCB beneath the plate, using a few
   switches as alignment aids if desired. Seat the PCB against the twelve
   downward bosses. Check all switch pins/socket alignment before tightening.
3. **From underneath the PCB**, install twelve M2 × 4 screws with the specified
   0.3 mm insulating washers into H13–H24. Tighten evenly until seated. The
   PCB and switch plate now form a removable cartridge.
4. If installing the controller on the bench, use the supplied support jig with
   its two rails directly beneath the **plastic bottoms of the two sockets**,
   17.78 mm apart. Check actual contact before pressing the module into place;
   the jig is temporary and does not stay in the case. Alternatively, insert
   the controller after seating the cartridge on the base's measured backstops.
5. **Lower the cartridge over the twelve base posts**, aligning H1–H12 with the
   Ø7 mm passages. Travel along the PCB normal, **3° from desk vertical**.
   Bring the plate against the left/rear locating tabs; it must sit on the post
   shoulders without forcing any PCB passage.
6. **From above the switch plate**, install twelve M2 × 5 screws into the tall
   posts. Screw heads remain clear of the conservative keycap sweeps. Fit the
   remaining switches/keycaps in the usual order, checking free travel.
7. Check socket backstop gaps and select shims for a measured **0.1–0.3 mm gap**,
   including adhesive. The existing
   [controller/header interface](../../../references/CONTROLLER-SOCKETS-0.7.md)
   still applies.
8. Measure and fit the USB bezel as described below. Install the badge well,
   badge and soft gasket; the well rests on the switch plate, 0.8 mm above PCB.
9. Lower the cosmetic cover. It captures the USB bezel ears and badge gasket.
   Support the assembly, then install eight M2 × 8 screws from underneath.
   Tighten only until the hard stops seat.

For PCB service, remove the cover and twelve plate-to-base screws, then lift
the cartridge along the PCB normal. The PCB-to-plate screws stay in place until
the cartridge is on the bench.

## Replaceable USB-C bezel

The case has a **larger receiver**, not a fixed final cable hole. The insert has:

- A **24 mm wide face**, extending from PCB Z=-2 to Z=10.8.
- A **28 mm wide internal flange**, guided by open-top slots in the tray.
- A flange stop at Z=-1 and ears captured by the cover at Z=8.4.
- Nominal 0.25 mm sliding clearance; the face sits flush with the outer wall.
- A nominal **16 × 7.2 mm opening**, centered at PCB **Y=13.39, Z=5.74 mm**.

With the cover removed, the insert lifts out while the PCB and MCU remain
installed. Closed, the cover stops upward movement and the flange/side rails
prevent inward or outward displacement under cable insertion.

### Measure after assembling the actual PCB and MCU

1. Seat the cartridge, controller and relevant socket shims.
2. Test the nominal insert with the **actual cable housing**, not just the metal
   USB shell. Use the closed blank to mark or measure a corrected opening.
3. Record the required center in PCB coordinates, or measure the correction
   relative to the nominal opening:
   - **Positive Y offset moves toward the front/user.**
   - **Positive Z offset raises the hole normal to the PCB.**
   - `offset = measured center − nominal center`.
   Use the case/receiver's CAD datum or displacement from an installed nominal
   bezel, rather than re-zeroing on the physical PCB edge. This also captures
   cartridge seating and print errors. On the blank's face, its nominal rear
   edge is Y=2.5 and its bottom is Z=-2 mm; measure along the tilted PCB axes.
4. Choose opening width/height for the cable housing plus practical clearance.
   Leave at least **1 mm of material** at all outer face edges. The available
   upward adjustment is limited by the case height; the generator rejects an
   opening that breaks the frame.
5. Export **only a fitted insert**, for example:

```sh
python3 -B designs/module-rp2040/source/generate_cartridge_case.py \
  --usb-only --usb-y-offset 0.6 --usb-z-offset -0.4 \
  --usb-width 16 --usb-height 7.2 --output /tmp/opencode/cleaver-usb-fit
```

This writes `final-prints/USB-bezel-fitted.stl` and `.step` beneath the chosen
output directory, plus `USB-bezel-fitted.json` at its root. Alternatively, edit
`dy`, `dz`, `opening_w` and `opening_h` in
**[final-prints/USB-bezel-template.scad](final-prints/USB-bezel-template.scad)**.
Keep the face/flange interfaces.
`blank=true` exports a closed measuring/drilling blank. The template's in-plane
orientation differs by a rotation from the CAD STL, not a mirror.

## Coupons and prototype checks

The following coupons are in **[test-prints/](test-prints/README.md)**:

Each test piece has an embossed ID on an external tab: **A1–A3** mounting
stack, **B1–B3** USB receiver/blank, **C1–C2** cover fastener and **D1–D3**
badge fixtures/cutting aid. Match letters when fitting pieces together.
The [label key](test-prints/README.md#embossed-fit-set-labels) also identifies
the switch/stabilizer coupons and controller jig that fit purchased hardware.

- **`Cartridge-stack-coupon-{base,plate,dummy-PCB}`** contains actual H2 and H14.
  It exercises both hole families, the short insert, upward PCB screw/washer,
  pass-through clearance and downward plate screw. The dummy PCB is a printed
  1.6 mm fit gauge, not a circuit board or a substitute for a real-board trial.
- **`USB-bezel-fit-coupon-{base,cover}`** plus the full bezel checks sliding fit,
  the bottom stop, capture ears and straight cable passage. Fit it with the
  actual controller/header stack before choosing the final port position.
- **`Front-fastener-fit-coupon-{base,cover}`** checks the underside cover screw,
  insert, hard stop and joint.
- **`Logo-fit-coupon-cover`** and
  **`Logo-fit-coupon-plate-with-height-gauges`** test the well/badge/gasket at the
  correct 3.4 mm cover-to-plate gap.
- **2u and 6.25u stabilizer coupons** check clips and switch fit.

The badge gasket is **soft foam**, not a rigid printed spacer. Cut
[final-prints/Logo-gasket-cut-template.svg](final-prints/Logo-gasket-cut-template.svg)
at 100% scale; its outside is 53.8 × 28.4 mm and
opening 51.2 × 25.8 mm. The 0.8 mm STL is a cutting-pattern reference.

Record ten assembly/service cycles on the stack and cover coupons: no cracking,
rotating inserts, stripped threads, crushed plate/PCB seats or binding passages.
The USB insert should remain located during cable use and removable with the
cover off. Check badge rattle, plate bow, floor flatness and all key travel on
the full-size print. **Physical fit, preload and durability are not yet tested.**

## Regenerate and verify

```sh
python3 -B designs/module-rp2040/source/generate_cartridge_case.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
```

Requires KiCad `pcbnew`, FreeCAD, Shapely ≥2.1, NumPy, SciPy and Trimesh.
`parameters.json` is the editable input. FreeCAD contains assembled solids, not
an editable feature history. The [validation report](validation.json) records
source hashes, hardware fits, insertion paths, USB capture, key/optical paths,
single-solid STL checks and STEP round trips.
