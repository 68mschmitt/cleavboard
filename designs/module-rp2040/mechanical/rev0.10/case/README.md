# Mechanical rev0.10 — underside-fastened, lower-profile case

For the **module-RP2040 rev0.9 PCB and rev0.9 switch plate**. Print the matching
rev0.10 base and cover. The printable base is approximately **466 × 175 mm**;
allow additional brim clearance.

## What changed

- **Eight bottom-access M2 screws** replace the visible top screws. Blind inserts
  sit in the cover, not the tray rim. No screw holes penetrate the cover exterior.
- **Rounded 12 × 6 mm cover pillars with 45° root ribs**, 1.4 mm minimum nominal
  plastic beside a Ø3.2 mm insert, and 2.9 mm of plastic above each pilot.
  Matching base pockets provide axial hard stops; tightening does not pull a
  thin unsupported bezel down onto a screw head.
- **Flat underside head seats** normal to the screw axes, with Ø4.6 mm access
  bores. The nominal edge material beside those bores is 1.95 mm, compared with
  about 0.4 mm beside the former top-head recesses.
- **Perimeter locating lip and rebate**, relieved around the new pillars.
  Nominal joint clearance is 0.25 mm per side. The joint aligns the halves and
  carries lateral loads.
- **Badge locating shoulders and a soft foam gasket** preload the existing
  flange/light-well stack against the switch plate. The opaque well stays
  0.8 mm above the PCB; the LEDs carry no mechanical load.
- **3° typing angle**, **2.2 mm floor**, **5.6 mm front underside-PCB allowance**
  and a **2 mm wide × 1.2 mm high front-edge bevel**.
- Width remains **465.94 mm**. Front and rear walls each extend another **2 mm**
  in PCB coordinates to support the new fasteners. The desk-flat base footprint
  is **465.94 × 174.26 mm**.

### Height comparison

CAD dimensions from the bare case bottom, with no feet. The home-row reference
is the A-key center with an illustrative keycap top at Z=20 mm above PCB.
Real keycap height depends on the caps used.

| Measurement | rev0.9 | rev0.10 | Reduction |
| --- | ---: | ---: | ---: |
| Outer front edge | 19.87 mm | 18.11 mm | 1.76 mm |
| Full-height bezel at front plate edge | 20.46 mm | 19.76 mm | 0.69 mm |
| Home-row PCB top | 16.62 mm | 13.14 mm | 3.48 mm |
| Home-row reference keycap top | 36.54 mm | 33.11 mm | 3.43 mm |
| Rear cover top | 34.61 mm | 28.37 mm | 6.24 mm |

[Profile comparison](height-comparison.svg) · [Plan](case-plan.svg) ·
[Section diagrams](assembly-sections.svg)

## Print and purchase

| Quantity | Part |
| ---: | --- |
| 1 | `Cleaver-case-base-rev0.10.stl` |
| 1 | `Cleaver-case-top-cover-rev0.10.stl` |
| 11 | `PCB-to-plate-spacer-3.5mm.stl` |
| 1 | `Logo-light-well.stl`, opaque |
| 1 | `Logo-insert-blank.stl`, translucent, or a customized badge |
| 1 | Existing [rev0.9 switch plate](../../rev0.9/README.md) |
| 11 | M2 × 10 PCB/plate screws |
| 8 | **M2 × 8 socket-head cover screws**, head diameter ≤3.8 mm, height ≤2 mm |
| 19 | M2 heat-set inserts, approximately Ø3.2 × 4 mm: eleven base, eight cover |
| 1 | **0.8 mm soft silicone-foam gasket**, 53.8 × 28.4 mm outside, 51.2 × 25.8 mm opening |
| As measured | Supplied 0.2–1.0 mm controller socket shims |

Cut the gasket using [`Logo-gasket-cut-template.svg`](Logo-gasket-cut-template.svg)
at **100% / actual size**, verifying the 53.8 mm outside width. The supplied
`Logo-gasket-cutting-pattern-0.8mm.stl`/STEP describe the **uncompressed cutting
pattern**, not a rigid part to install. Use readily compressible foam, not solid
PLA, PETG or stiff TPU. The nominal installed gap is 0.6 mm: 25% compression of
0.8 mm stock. Confirm the actual foam compresses without bowing the plate.
The assembled CAD shows the compressed gasket.

The cover screw grip is 4.5 mm, giving **3.5 mm nominal insert engagement**.
The Ø3.0 mm pilot is 4.5 mm deep, with 1 mm of tip clearance at the nominal
8 mm screw length. Install each 4 mm cover insert flush with its pillar's
underside end. Insert brand, knurl diameter and printer shrinkage must be
qualified on the coupons.

### Print setup

- STLs are bed-oriented: base floor-down, cover exterior-down, badge and well
  face-down. STEP parts retain their CAD coordinates; the full assembly is
  desk-flat. Mate coupon parts using their lips/stops, not their STL origins.
- Start with a 0.4 mm nozzle, 0.2 mm layers, **five perimeters**, at least
  five top/bottom layers, and local solid fill at the insert pillars and head
  seats. Inspect the sliced walls around the pilots before printing.
- The front bevel lifts only the outermost 2 mm of the face-down cover. Check
  first-layer/bridge behavior there. Small bores and internal pocket ceilings
  also need a slicer preview and coupon test.
- Use a dimensionally stable material and consistent settings for the coupons
  and full parts. Test inserts before committing to a full-width print.
- The shell joint is screw-fastened and releasable. The locating lip and badge
  shoulders are guides, not snap hooks.
- No tall feet are required by this design. If adding non-slip pads, use thin,
  equal-thickness pads clear of access holes and add their **exposed thickness**
  to all desk-height measurements.

## Fit coupons

1. **`Front-fastener-fit-coupon-{base,cover}`**: actual front screw pillar, blind
   insert, flat head seat, hard stop, joint and beveled edge. Install one insert
   and one M2 × 8 screw. The cover must seat before tightening and the screw
   must clamp without bottoming out.
2. **`USB-and-seat-fit-coupon-{base,cover,plate}`**: actual rear-right interface,
   H5 PCB boss, one cover fastener, socket backstops and USB opening. Use a
   3.5 mm spacer and the actual PCB/module/cable to verify the installed stack.
   The section includes only H5: support the rest of the full PCB during fitting.
3. **`Logo-fit-coupon-cover`** and
   **`Logo-fit-coupon-plate-with-height-gauges`**: fit the full-size well,
   badge and foam gasket. Integral gauge rails hold the cover underside exactly
   **3.4 mm above the plate top** when fully seated. Hold it gently against
   those stops while checking rattle and preload. The gauge rails are a fixture,
   not additions to the full switch plate.
4. **`Lower-profile-section-{base,cover}`**: matching left-wall sections. Align
   the lip and seat to assess the new lengthwise profile before a full print.
5. The existing [2u and 6.25u stabilizer coupons](../../rev0.9/README.md) remain
   applicable. Qualify actual switch/stabilizer clips and keycaps.

**Do not drill the blind insert pilots through the exterior.** If tuning a
pilot diameter, change the parameter and reprint the coupon. More perimeters
complement the stronger geometry; they are not a substitute for sufficient
wall thickness.

## Assembly

1. Heat-set eleven inserts into the PCB bosses in the base and eight into the
   cover pillars. Keep the cover inserts flush at the pillar ends so the plastic
   axial stops, rather than proud inserts, establish the joint height.
2. Mount the PCB on all eleven bosses. Fit the eleven 3.5 mm spacers, rev0.9
   plate and eleven M2 × 10 screws using the established switch/plate procedure.
3. Measure the controller socket/backstop gaps and select shims to leave
   **0.1–0.3 mm**, including adhesive. Install the carrier in the base before
   inserting the controller. Follow the
   [socket interface instructions](../../rev0.7/case/README.md).
4. Place the opaque well through the plate's badge opening. Its flange sits on
   the plate at Z=5.0, and its bottom stops at Z=0.8 above PCB.
5. Seat the badge flange on the well at Z=7.4. Its flange top is Z=8.2.
   Lay the foam frame flat on the flange, outside the visible badge face.
6. Lower the cover. Its side/front shoulders locate the well/flange; the badge
   face enters the cover aperture. The gasket sits in the cover's 0.4 mm recess
   and compresses between Z=8.2 and Z=8.8. The badge's diffuser is flush at
   Z=10.8. Nothing should need to be forced past a shoulder.
7. Hold the halves together and support the assembly in a padded cradle that
   does not load keycaps. Insert eight M2 × 8 screws from underneath.
   **Screw axes follow the PCB normal: 3° from desk vertical**, not straight up
   relative to the desk. Use a straight slim driver shaft ≤4.4 mm diameter.
8. Tighten in alternating positions only until the halves seat and the screws
   are snug. Extra torque does not improve alignment or badge retention.
   Check USB fit, all keys/stabilizers, badge rattle and case rocking.

For service, unplug USB, support the halves, remove the eight underside screws,
and lift the cover. The gasket, badge and well lift out without adhesive or
releasing fragile tabs. Use a plastic pick at the gasket/flange if needed.

## Validation and prototype acceptance

[`validation.json`](validation.json) records PCB/plate input hashes, generator
hashes, CAD interference checks, hardware/driver access, hard-stop material,
all 117 actual cover/keycap sweeps, four optical paths, controller/socket/USB
clearance, height comparisons, and STEP/STL round trips. All exported printable
parts must be single, watertight positive-volume solids.

**Physical fit and durability remain to be tested.** Record the following
against a sample printed with the intended material/settings:

| Check | Acceptance |
| --- | --- |
| Fastener durability | Ten open/close cycles on both fastener coupons: no cracks, stripped/rotating inserts, crushed seats or pullout |
| Joint seating | Stops meet without forcing; uniform seam; no top screw holes |
| Badge retention | With cover seated, no audible rattle during normal handling, no visible rocking or plate bow; still removable for service |
| Height | Measure front edge and A-key top; compare like-for-like caps and feet with rev0.9 |
| Hardware fit | All eleven PCB mounts align; actual USB cable fits; controller sockets have measured support gaps |
| Key function | All 117 keys travel/return freely; every stabilized key clears through full travel |
| Full-size print | Flat floor, no rocking or visibly bowed bezel; no unacceptable floor flex in normal typing |

These are prototype acceptance checks, not already completed physical results.

## Reproduce

Use Python with KiCad `pcbnew`, FreeCAD, Shapely ≥2.1, NumPy, SciPy and Trimesh:

```sh
python3 -B designs/module-rp2040/source/generate_case_service.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_case*.py'
```

Optional flags: `--parameters FILE.json --output DIRECTORY`.
`parameters.json` inherits the older generator's parameter schema; the old
top-head recess and tray-cover-insert parameters are retained for shared
validation compatibility but do not create top screws in this revision.
Use `underside_head_bore_mm` and `blind_insert_depth_mm` for the new fastening
features. Edit parameters and regenerate: FreeCAD properties are an informational
snapshot, not a parametric feature tree.
