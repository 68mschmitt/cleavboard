# Revision 0.9 validation — 2 × 1 inch illuminated badge

Recorded **2026-11-12 local / 2026-11-13 UTC**, using KiCad 10.0.8, FreeCAD 1.1.4,
Shapely 2.2.0 and Trimesh 5.2.0. The visible badge is **50.8 × 25.4 mm**, with
**51.2 × 25.8 mm** plate/cover openings. The plate and case front extend **8 mm**;
all key positions and the PCB outline are retained. H9 is now **(263,138) mm**.

| Check | Result |
| --- | --- |
| Unit / serialized mesh / CAD / firmware callback tests | **60 passed, none skipped** |
| Schematic ERC / routed PCB DRC, all severities | **0 / 0 violations** |
| Unconnected copper / schematic parity issues | **0 / 0** |
| Keys / RGB chain | **117 / 121**, with four badge emitters at 13 mm pitch |
| Factory assembly / local 3D coverage | **489 placements / 14 purchasing groups; 607 models / 490 footprints** |
| Serialized migration audit | All **5,356 pre-badge copper items** exactly retained; **172** replacement badge routing items |
| Footprints | All 511 identities, values, orientations and pad nets retained; only H9 and eight badge components move |
| Routed copper / project rules | **4,808 tracks / 720 vias**; project bytes unchanged |
| Complete-copper regeneration | Exact canonical match; fresh ERC/DRC/parity pass |
| Badge fit | Four clear optical paths; zero badge/PCB/plate/cover/base intersections; captive retention checked |
| Serialized visible face | **50.8 × 25.4 mm**, independently measured from the exported STL |
| Mechanical margins | **3.625 mm** plate front web; **0.9375 mm** flange-to-key-aperture clearance |
| Mesh exports | 14 case/badge/coupon/shim STLs plus plate and two stabilizer coupons; single watertight bodies |
| Firmware | Default and Vial target builds pass; UF2 headers/address ranges validated; no EEPROM overlap |

Evidence is in [`manufacturing/rev0.9/checks/`](manufacturing/rev0.9/checks/),
[`mechanical/rev0.9/`](mechanical/rev0.9/README.md) and
[`manufacturing/rev0.9/firmware/`](manufacturing/rev0.9/firmware/README.md).
USB device version is **0.9.0**; GPIO mapping, Vial UID/unlock, key LED indices
and the existing power/brightness limits are retained. Physical fit, diffusion
and hardware operation remain untested. [Badge dimensions and behavior](LOGO.md).

```sh
python3 -B designs/module-rp2040/source/check_kicad.py --reports designs/module-rp2040/manufacturing/rev0.9/checks
python3 -B designs/module-rp2040/source/check_routing_roundtrip.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
```

`upgrade_rev09_routing.py` records the one-time migration from explicit rev0.8
and rev0.7 backups. Normal regeneration uses the committed rev0.9 complete-copper
archive. Use the matching rev0.9 PCB, plate, base and cover together.

## Historical revision 0.8 — 16 mm square badge

Recorded **2026-11-12 local / 2026-11-13 UTC**, KiCad 10.0.8, FreeCAD 1.1.4,
Shapely 2.2.0 and Trimesh 5.2.0. This revision adds a four-pixel RGB badge,
matching plate/cover openings, printable light well/insert, and moves H9.

| Check | Result |
| --- | --- |
| Unit / serialized mesh / CAD / firmware callback tests | **59 passed, none skipped** |
| Schematic ERC / routed PCB DRC, all severities | **0 / 0 violations** |
| Unconnected copper / schematic parity issues | **0 / 0** |
| Keys / RGB chain | **117 / 121**; badge indices 117–120 |
| Factory assembly | **489 bottom SMT placements, 14 purchasing groups** |
| Local 3D coverage | **607 model instances / 490 modelled footprints** |
| Rev0.7 migration audit | All **5,356 existing copper items exactly retained**; 161 added |
| Footprint migration | 501 existing footprints/pad nets unchanged; H9 moved, LED112.4 feeds badge; eight new parts |
| Final routed copper | **4,793 tracks / 724 vias** |
| Project rules / exclusions | Unchanged |
| Complete-copper archive regeneration | Exact canonical match; regenerated ERC/DRC/parity pass |
| Badge geometry | Matching 16.4 mm plate/cover openings; 16 mm insert / 19 mm retaining flange |
| Mechanical fit | Four clear optical paths, zero badge/PCB/plate/cover intersections; captive retention checked |
| Mesh exports | 14 case/badge/coupon/shim STLs plus plate and two stabilizer coupons; single watertight bodies |
| Firmware | Default and Vial target builds pass; executable callback tests cover brightness/ranges/direct mode/USB gating |

The four logo pixels use the existing protected LED_5V branch. Key brightness
stays at 8/255; badge pixels have a 4× gain capped at 32/255, approximately
18.1 mA maximum full-white color current plus their idle current. GPIO mapping,
Vial UID/unlock and key pixel indices are retained; USB device version is 0.8.0.
See [badge dimensions and operating behavior](LOGO.md).

Use [`manufacturing/rev0.8/`](manufacturing/rev0.8/README.md),
[`mechanical/rev0.8/`](mechanical/rev0.8/README.md), and
[`manufacturing/rev0.8/firmware/`](manufacturing/rev0.8/firmware/README.md).
Fresh build logs, UF2 validation and exact input/output hashes accompany both
firmware images. Builds use vial-qmk
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344` and arm-none-eabi-gcc 16.2.0.

Reproduce with the commands under **Evidence and reproduction** below, using
the **rev0.8** complete-copper archive. The independent migration check takes a
saved rev0.7 PCB and its adjacent project file:

```sh
python3 -B designs/module-rp2040/source/check_rev08_migration.py /path/to/rev07/Cleaver.kicad_pcb
```

**Physical fit, diffusion/brightness and hardware operation remain untested.**
The supplied logo coupons exercise the actual openings and captive stack before
printing the large case. Use the new base/plate together: H9 is now `(250,138)`.

## Historical revision 0.7 record — bottom-entry controller sockets

Recorded **2026-11-12 local / 2026-11-13 UTC**, KiCad **10.0.8**. Electrical,
layout, regeneration and CAD checks pass. **Engineering/prototype handoff only**:
supplier DFM/placement acceptance and physical mating/operation remain unverified.

## Results

| Check | Result |
| --- | --- |
| Unit tests, including Shapely, socket and CAD checks | **55 passed, none skipped** |
| Schematic ERC, all severities | **0 violations** |
| PCB DRC, all track errors, refilled zones | **0 violations** |
| Unconnected copper / schematic parity issues | **0 / 0** |
| U1.40 → J2.1 → RAW_USB_5V → F1 → U3 → LED_5V | Pass; routed copper |
| All 40 module pins → J1/J2 mapping and NPTH entries | Pass; J2 is reversed |
| Independent firmware GPIO-to-Waveshare-header check | Pass |
| 8x16 ROW2COL matrix / unique keys / RGB LEDs | 8x16 / 117 / 117 |
| Vial layout, UID, VID/PID, secure unlock, VialRGB | Pass |
| Complete-copper archive regeneration | Exact canonical match, **4,652 tracks + 704 vias**, 0.0001 mm archive resolution |
| Rev0.6 migration audit | **500 non-controller footprints unchanged**; copper outside controller area unchanged within 0.0002 mm |
| Project fabrication minima, severities and exclusions | Unchanged |
| Factory assembly | **481 bottom SMT placements, 14 purchasing groups** |
| JLCPCB PnP catalog-angle corrections | **U2: 90° counterclockwise; SW001–SW117: 180°**, already applied in CPL; PCB unchanged |
| Plated through-hole component pads / front paste pads | **0 / 0** |
| Controller entries | **40 × Ø1.00 mm unnumbered, net-free NPTH** |
| SMD via holes outside exposed solder lands | Pass |
| Local 3D coverage | **599 instances across 482 modelled footprints** |
| Socket/header depth budget, full 7–8 mm socket range | **1.60 mm minimum past contact; 0.18 mm minimum before far end** |
| Plate, case, USB/seat coupons and socket-support shims | CAD interference checks and serialized mesh checks pass; 10 case/shim STLs plus plate/2 stabilizer coupons |
| Default / Vial firmware | Sources unchanged; compatible rev0.6 builds retained, not rebuilt for this mechanical revision |

Revision 0.7 replaces direct-soldered U1 pads with **two Harwin M20-7862042 /
C5379059 underside sockets**. U1 is off-board in the schematic and a pad-free,
excluded visual reference on the PCB. The 40 entry holes retain their positions;
separate SMT lands and off-pad vias provide electrical connections. Adapted
1.02 × 1.80 mm lands retain 0.30 mm nominal hole clearance without weakening rules.
The local routing migration retains **4,670 original copper item identities**;
its audit region is PCB XY `[398, 0, 452.4375, 29]` mm. Ground access formerly
provided by U1's plated barrels is now routed to real ground vias.

The entry positions, 117 switch centres, matrix GPIOs, GP27 RGB data, GP28
LED enable, and RGB chain are retained. Vial identity/unlock are retained;
firmware explicitly keeps EEPROM within the first 2MB. The USB device version
deliberately remains **0.6.0**. TP1 remains a bare VBUS test pad; no tap wire is needed.

Use **bare Waveshare SKU 20290** with **Samtec TSW-120-14-G-S**: 8.13 mm gold
posts downward, 2.79 mm tails soldered only to the module. **Pre-headered SKU
20808 is not qualified.** The new case base includes backstop ribs and five
selectable shim thicknesses for a measured 0.1–0.3 mm gap without preload.
The controller's nominal top envelope remains 7.64 mm; CAD checks 8.2 mm below
the 8.4 mm cover. The old plate is reusable; the old base lacks insertion supports.

## Retained rev0.6 firmware build evidence

Previously built in a fresh checkout of **vial-qmk
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344`**, with its pinned submodules and
**arm-none-eabi-gcc 16.2.0**:

```sh
make cleaver:default -j4
make cleaver:vial -j4
```

Both UF2 images start at `0x10000000`; the Vial image ends at `0x1000da00`,
well below the EEPROM region. The builds include GP28 USB-aware power control,
the 8/255 brightness ceiling, lock-key indicators and secure Esc + main Enter
unlock. Logs, images, exact input hashes and provenance are in
[`manufacturing/rev0.6/firmware/`](manufacturing/rev0.6/firmware/).

## Evidence and reproduction

- [`manufacturing/rev0.7/checks/`](manufacturing/rev0.7/checks/): fresh ERC/DRC,
  netlist, interface, migration, tests and isolated regeneration evidence.
- [`manufacturing/rev0.7/`](manufacturing/rev0.7/): fabrication ZIP, BOM/CPL,
  assembly drawing, pin/land orientation references, separate NPTH/PTH drills
  and SHA-256 manifest (paths relative to the design directory).
- [`validation/`](validation/): **historical rev0.6** recorded evidence, retained.
- [`routing/Cleaver.ses`](routing/Cleaver.ses): checked complete-copper archive.
- [`references/RP2040-Plus.md`](references/RP2040-Plus.md): vendor pinout,
  VBUS circuit and nominal geometry review with archived source documents.
- [`references/CONTROLLER-SOCKETS-0.7.md`](references/CONTROLLER-SOCKETS-0.7.md):
  archived supplier drawings, mating-depth budget, dated JLC stock and open gates.
- [`mechanical/rev0.7/`](mechanical/rev0.7/): matched plate, revised case,
  coupons, shims and hash-linked CAD/STL validation.
- [`previews/`](previews/): populated KiCad renderings. Module connector/package
  details are approximations; see the local model README.

From the repository root, with KiCad Python, Shapely ≥2.1, NumPy, SciPy,
Trimesh and FreeCAD (used: Python 3.14, FreeCAD 1.1.4, Shapely 2.2):

```sh
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
python3 -B designs/module-rp2040/source/check_kicad.py
python3 -B designs/module-rp2040/source/check_routing_roundtrip.py
```

To regenerate the current design intentionally, import the matching **revision 0.8** archive:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --ses designs/module-rp2040/routing/Cleaver.ses
python3 -B designs/module-rp2040/source/check_kicad.py
```

The fresh generated board and in-place migrated board were compared by their
deterministic complete-copper archives and matched exactly. Both pass fresh
all-severity ERC/DRC and parity checks. Round-trip generation also confirms
unchanged firmware contents. The read-only check uses a temporary project copy.

## Prototype checks

Confirm the actual module/header stack and USB plug/case access against a 1:1
print. The smaller module fits inside the existing controller plate opening;
its USB-side PCB edge is 1.17 mm inside the carrier edge. Leave the battery
connector unused for USB-only operation. Allow 11 mm free depth below C5.

**Before any production order:** obtain JLC engineering approval for the adapted
lands/stencil, NPTH drill/registration tolerances, pickup/placement of the long
socket bodies, reverse-LED milling, and the actual BOM/CPL preview. Catalog
availability is not approval. Measure insertion alignment, contact/retention,
module height, USB fit and shimmed backstop gaps on samples. Neither the mixed
Harwin/Samtec pair nor printed support strength has been physically qualified.

Test all keys/chords, RGB chain, lock indicators, Vial unlock/remapping and
persistence, suspend/resume and USB-A-to-C/C-to-C enumeration. Measure USB
startup/suspend/full-white current and LED rail ripple at the retained 8/255
ceiling. The TPS2553 branch limit remains approximately 353 mA nominal
(311–401 mA calculated bounds), plus module consumption. No physical prototype
has been tested as part of this change.
