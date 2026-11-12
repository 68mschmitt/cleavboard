# Revision 0.6 — tilted case and separate top cover

**Two separate enclosure parts:** a flat-bottomed tray with **11 built-in PCB
standoffs**, and a removable key bezel. They fit the **452.4375 × 147.6375 mm**
rev0.6 module-RP2040 PCB and the [existing 1.5 mm switch plate](../README.md).
The rear is raised **5°**; the keys slope down towards the user.

## Files

| File | Use |
| --- | --- |
| [Base STL](Cleaver-case-base-rev0.6.stl) | Print once, flat floor on the bed |
| [Top cover STL](Cleaver-case-top-cover-rev0.6.stl) | Print once; already face-down on the bed |
| [3.5 mm spacer STL](PCB-to-plate-spacer-3.5mm.stl) | Print **11**, one per PCB/plate mounting axis |
| [USB/seat coupon base](USB-and-seat-fit-coupon-base.stl) + [cover](USB-and-seat-fit-coupon-cover.stl) | Test the actual rear-right case section first |
| [Assembly STEP](Cleaver-case-assembly-rev0.6.step) | All parts positioned together; reference PCB, plate, controller, capacitor and keycaps included |
| [FreeCAD assembly](Cleaver-case-assembly-rev0.6.FCStd) | Named solid parts; hide the cover/keycap references to inspect the interior |
| [Plan drawing](case-plan.svg) | Cover openings and labelled internal mounting bosses |
| [3D preview](assembly-preview.png) | Rendered tray and assembled enclosure; keycaps are simplified references |
| [Parameters](parameters.json) / [validation](validation.json) | Rebuild settings / measured geometry and checks |

Each printable part also has an identically named **STEP** file. The main base
is approximately **466 × 164 mm**: these are **full-size, unsplit** files, not
235 mm-bed sections. Allow additional bed space for a brim. Exact STL bounds are
recorded in `validation.json`.

## Fit and construction

- **0.25 mm clearance per side** around both PCB and plate; no global scaling.
  Both locate inside the same wall pocket. Eleven PCB bosses and eleven separate
  **Ø6 × 3.5 mm** plate spacers support the stack without loading sockets or SMD
  bodies. All PCB hardware stays inside the supplied **6 mm reserved envelopes**.
- Boss faces and their insert bores follow the PCB's **5° plane**, not the desk
  normal. Their centres match **H1–H11** in the saved rev0.6 PCB. The floor is
  horizontal and **2.8 mm** thick. There is **6 mm** clearance below the PCB at
  its front edge and more towards the rear, including the required **11 mm below
  the entire C5 capacitor envelope** at `(377, 6)` mm.
- The separate bezel is **not the switch-retaining plate**. It sits above that
  plate, covering the blank areas, mounting screws and controller. Its **12
  connected key-cluster openings** pass all **117 keycaps**, including the
  spacebar and tall numpad keys. Adjacent keys share apertures to avoid fragile
  inter-key webs. The apertures extend **0.15 mm beyond each KLE pitch envelope**;
  checks assume ordinary MX caps whose plan dimensions are pitch minus 1 mm.
- Cover underside: **8.4 mm above PCB top**; top: **10.8 mm**. This clears the
  approximate **7.64 mm direct-header controller envelope**. The underside
  locating lip has **0.25 mm lateral / 0.2 mm bottom clearance** in its rebate.
  Eight independent perimeter screws secure the cover, so removing it does not
  loosen the PCB or switch plate.
- **Right-side USB-C tunnel: 16 × 7.2 mm**, centred at PCB `Y=13.39 mm`,
  `Z=5.74 mm`. It cuts through both the tray and cover where necessary, with
  approximately **1.46 mm of roof** above it. Width is along PCB Y and height is
  normal to the PCB. This is a **cable-overmould opening**, not just an 8.95 mm
  connector-shell opening. Test your actual cable: shell height/projection and
  header stack are approximate in the supplier/reference model.
- BOOT/RESET access is by **removing the top cover**. No extra top openings expose
  the controller or unused PCB areas. This is a USB-only enclosure, not a battery
  compartment.

### Hardware

- **19 M2 heat-set inserts**, approximately **3.2 mm OD × 4 mm long**: 11 in the
  PCB bosses and 8 in the outer case rim. Printed pilot bores are **3.0 mm**;
  depth is **4.5 mm** at PCB bosses and **5.0 mm** at the cover screws.
  Insert brands differ: **test the coupon and change the bore parameter to suit
  the insert manufacturer's recommendation**. Do not force a larger insert into
  a 6 mm boss. Install square to the tilted mounting plane, not vertically.
- **11 M2 × 10 mm** screws through switch plate → 3.5 mm spacer → 1.6 mm PCB →
  boss insert. Nominal insert engagement is **3.4 mm**. Use heads/washers no larger
  than 6 mm OD and no taller than **2 mm** above the plate; check keycap travel.
- **8 M2 × 6 mm** cover screws, with heads up to **4.0 mm OD**. The cover has
  **Ø4.2 × 1.0 mm** flat-bottom head recesses, not conical countersinks. Nominal
  insertion is 4.6 mm, including the clearance below a 4 mm insert. Check actual
  screw lengths before tightening; do not bottom out or crush the printed cover.
- Optional stick-on rubber feet under the flat base. Feet are not modeled.

## Print, test, assemble

1. **Print both USB/seat coupons and one spacer first.** The coupons are actual
   rear-right sections containing H5, the USB opening, one cover screw, lip and
   PCB/plate edge pocket. Check them against the real PCB, plate, controller,
   cable and insert. Most of the PCB hangs outside this small test section:
   support it and keep it unpowered while checking fit.
2. Print at **100%, in millimetres**. Suggested starting point: PETG, 0.4 mm
   nozzle, 0.2 mm layers, 4–5 walls and 25–35% infill. Print spacers solid. The
   case's flat floor faces down; the cover STL already has its visible face down
   and locating lip up. Expect a short bridge at the USB notch/head pockets;
   enable local support only if needed. Do not auto-reorient the cover upright.
3. Correct local hole/contour compensation from the coupon; never rescale the
   whole enclosure. Remove elephant's foot from locating edges. A large print
   may warp; the nominal clearance does not guarantee a snug physical fit on an
   uncalibrated printer.
4. Install the inserts before electronics. Install the plate-mount stabilizers
   and switches in the **existing** plate. Lower the PCB onto the 11 bosses,
   add the 11 spacers, then the plate/switch assembly. Join switches to the
   hot-swap sockets squarely and fasten the 11 stack screws lightly.
5. Use **direct-soldered 2.54 mm male headers** for the Waveshare RP2040-Plus.
   Tall plug-in header sockets are **not** accommodated by default. Inspect C5,
   sockets, lead ends, USB insertion and full travel of every key before closing.
6. Seat the cover's locating lip and fit its 8 screws. The keycap openings allow
   vertical assembly around standard caps; remove caps first if your profile
   overhangs its nominal footprint. Verify every key, especially stabilized
   keys, moves freely through its entire travel.

## Rebuild and checks

Use Python with **FreeCAD Part/MeshPart**, KiCad `pcbnew`, Shapely >=2.1, NumPy,
SciPy and Trimesh. Optional Matplotlib adds the PNG preview. On Arch Linux the generator also searches
`/usr/lib/freecad/lib` for FreeCAD's Python modules. From the repository root:

```sh
python3 -B designs/module-rp2040/source/generate_case.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_case.py'
```

Edit `parameters.json` and regenerate to change fit/angle/insert/cable dimensions.
`--parameters FILE --output DIRECTORY` supports experimental exports elsewhere.
The FreeCAD file contains editable BRep solids and an **informational parameter
snapshot**, not a live parametric feature tree: change the JSON/Python source and
rerun to rebuild. Individual STL orientations are for printing, whereas STEP
parts/assembly retain CAD coordinates. Refer to the validation transforms when
repositioning STLs in CAD; do not stack the independently bed-normalized meshes.

The generator checks the saved PCB revision, thickness, outline, switch centres,
all 11 mounting drills, C5/controller positions, and the **actual existing plate
STL**. It tests tray/PCB/plate/cover interference, controller and C5 envelopes,
all keycap plan sweeps and the full USB tunnel. Serialized STL and STEP files are
reloaded: each printable part must be a single valid solid / watertight mesh
with consistent winding, positive volume and the expected size. Tests also
recover mounting-ring and bezel surfaces from the actual STL triangles.

**Not physically fit-tested.** The envelope checks are not supplier-qualified
models of every component, keycap, stabilizer or cable. Prototype fit, thermal
insert installation, screw engagement, print shrinkage, underside component
clearance and large-span rigidity must be checked on real hardware. The PCB,
routing, manufacturing exports and original switch plate are left unchanged.
