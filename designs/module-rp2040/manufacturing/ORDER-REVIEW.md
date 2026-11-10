# Cleaver rev0.4 — first-order review

This is the recorded revision 0.4 review. Paths below refer to its original
checkout; see the [path migration guide](../../../docs/REPOSITORY.md#path-migration).
The original root ZIP is now in [archive/](archive/README.md), and the current
module manufacturing package is [rev0.5/](rev0.5/README.md).

Reviewed 2026-11-08 for **5 fabricated PCBs, 2 assembled underneath, 3 bare**.

## Verdict

**Ready to submit for a JLCPCB engineering quote; not yet ready to release to
manufacturing.** Electrical checks and the revision-specific exports pass. The
LED-window tolerance stack needs resolution, and JLCPCB must register the actual
parts against the placement data and confirm stock/process acceptance.

### 1. Resolve LED-window fit before fabrication

Affected: all 117 LEDs; `kicad/Cleaver.pretty/MINI_E.kicad_mod:14` and
`rev0.4/README.md:24–26,58–71`.

The opening is **3.6 × 3.2 mm**, drawn with square corners. The catalog-linked
OPSCO SK6812MINI-E-012 B/2 document, pages 4–5, specifies a **3.2 × 2.8 mm** body
and an otherwise-unspecified dimensional tolerance of **±0.1 mm**. JLCPCB
publishes **±0.2 mm for non-plated slots** and does not manufacture perfectly
square internal corners.

The existing instruction “internal radius ≤0.5 mm, preferably 0.4 mm” addresses
nominal fit but does **not** establish worst-case fit:

| Case | Opening | LED body | Straight-side gap, each side |
| --- | --- | --- | --- |
| Nominal | 3.6 × 3.2 | 3.2 × 2.8 | 0.20 mm |
| Small opening / large body | 3.4 × 3.0 | 3.3 × 2.9 | 0.05 mm |

For equal side gaps, a square body corner inside a rounded aperture needs at
least `radius × (1 − 1/√2)` clearance: **0.146 mm at R0.5**, or **0.117 mm at
R0.4**. The tolerance-extreme case fails even with perfect centering, before
allowing placement/registration error. Even ±0.1 mm opening-size tolerance leaves
only 0.10 mm per side for a maximum-size body. This is a tolerance risk, not a
claim that nominal LEDs cannot fit or that every board will fail.

**Required resolution:** obtain an explicit finished-aperture size, corner
profile and placement tolerance accepted by JLCPCB for the actual LED body, or
revise the windows with suitable clearance/corner relief and regenerate the
package. Do not simply enlarge every window: the present LED lands have only
**0.55 mm nominal clearance to the straight window edge** against the project's
0.5 mm copper-to-edge rule. Nominal lead-to-land overlap is approximately
**0.59 mm**, which also needs assembly-process acceptance.

The lenses must face through the PCB toward the switches. JLCPCB's catalog
classifies C5149201 as **Standard Only, High assembly difficulty, MSL 5a**.
Confirm reverse-mount placement, support/retention and reflow, including the
large board's support fixture. An ordinary surface-mounted LED preview alone
does not establish the correct process.

### 2. Confirm catalog rotations and parts before assembly release

Affected: `rev0.4/CPL-JLCPCB.csv`, `rev0.4/pad-orientation-reference.csv`.

All **478 CPL rows are bottom-side, rotation 0°**. The positions and physical pad
mapping agree with the PCB, including the socket origin correction. These angles
have **not** been validated in an actual JLCPCB order preview against JLC's
library zero-angle conventions. There is no basis to change them blindly.

Review the imported positions and polarities against the pad table and request
JLC's **Confirm Parts Placement** service. In the supplied bottom-view drawing
(horizontal mirror of PCB top view, same top edge):

- LED GND/chamfered lead **1 is lower-left**; VDD **3 upper-right**, DIN **2
  upper-left**, DOUT **4 lower-right**. Emitters face away from this bottom view.
- Diode cathode **1 is right**, matching the stripe mark.
- U2/U3 pin **1 is lower-right**. U2 uses the three-pin bank on the right.
- Socket pad **1 is left/up**, pad **2 right/down**; its plastic contact openings
  must register with the two 3 mm NPTHs. SW references purchase sockets, not
  switches. Corrected socket center is switch X −0.635 mm, PCB Y −3.81 mm.

CPL coordinates use the **top-view lower-left origin, X right, Y up**. Do not
mirror bottom-side X coordinates again.

The catalog confirms SMT assembly support for Kailh **C2803348** and OPSCO
**C5149201**, both Standard Only. Reserve **234 of each plus JLC's required
attrition**, and verify all 12 BOM groups are selected. Order-specific available
stock, minimum purchase quantities and lead times remain unconfirmed. Catalog
listings and LCSC stock are not a reservation for this order.

### 3. Use the complete revision-specific fabrication archive

**Do not upload the root `Cleaver-gerbers.zip`: it contains no PTH or NPTH drill
files.** The loose files under `kicad/` are not the audited handoff.

Upload these together from `manufacturing/rev0.4/`:

1. `Cleaver-rev0.4-fabrication.zip`
2. `BOM-JLCPCB.csv`
3. `CPL-JLCPCB.csv`

Provide `README.md`, `assembly-bottom.svg`, `pad-orientation-reference.csv` and
`fiducials.csv` for engineering review, together with this review's LED-fit issue.
The BOM quantities are **per assembled board**; do not multiply the CSV by 2 or 5.

## Verified results

| Check performed in this review | Result |
| --- | --- |
| Fresh KiCad 10.0.8 ERC | 0 violations |
| Fresh DRC, refilled zones, all severities/all track errors | 0 violations |
| DRC of saved zones used by the fabrication exports | 0 violations; 0 unconnected items; 0 parity issues |
| Unconnected items / schematic parity | 0 / 0 |
| Tests, including Shapely routing tests | 25 passed, 0 skipped |
| Manufacturing SHA256 manifest | All 33 entries match |
| Fabrication ZIP vs unpacked fabrication directory | All entries match |
| Independent re-export of 11 Gerbers and 2 drill files | Matches package, excluding timestamps |
| BOM / CPL | 12 groups, 478 unique placements, identical reference sets |
| CPL and pad-coordinate table vs current PCB | Exact match |
| Assembly sides / paste | All populated SMD pads on bottom; front paste Gerber empty |
| Matrix / RGB chain / firmware mapping | 117 unique 8×16 cells; 117 LEDs; parity passes |
| Module header / LED physical pad numbering | Pass |
| TI U2/U3 pin functions vs datasheets | Match circuit and footprint numbering |
| Minimum actual trace width / via drill | 0.20 mm / 0.30 mm |
| Via diameters | 0.60 and 0.70 mm; ordinary through-vias |
| Fabrication drills | 710 PTH, including 667 vias; 596 NPTH, including 11 mounts |
| Internal LED windows | 117 real Edge.Cuts openings |
| Firmware provenance | Current source hash and both existing UF2 hashes match recorded successful builds |

The firmware was not rebuilt in this review; the unchanged source matches the
recorded default/Vial builds at vial-qmk commit
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344`.

There are **no individual DRC exclusions**, but missing-courtyard checking is
disabled and **all 500 footprints lack courtyards**. DRC therefore does not prove
body spacing. A separate conservative nominal SMD-envelope check found no
component collisions, no overhang beyond the finished outline and no conflict
with the 6 mm mounting-hardware envelopes. The closest repeated nominal spacing
is approximately **0.365 mm between socket and diode**. This is a nominal
screen, not a maximum-tolerance mechanical fit test.

Power review: the 75 kΩ, 1% TPS2553 setting calculates to **353 mA nominal,
311–401 mA bounds** for the LED branch. The 8/255 brightness cap gives about
132 mA nominal color-channel average plus about 70 mA typical LED idle current,
before MCU consumption. The 470 µF reservoir is downstream of the limiter;
GP28/R2 keep the branch off until enabled. Actual startup, PWM rail ripple,
total USB current and suspend behavior still require the prototype.

## Exact order settings after resolving the release conditions

| Setting | Selection |
| --- | --- |
| PCB quantity | **5 total** |
| PCBA quantity | **2 of those 5**; return remaining **3 bare** |
| PCBA service / side | **Standard / Bottom only** |
| Delivery format | Single-board design; factory-added tooling rails |
| Finished size | **452.4375 × 147.6375 mm** |
| Layers | **4**, F.Cu / In1.Cu / In2.Cu / B.Cu |
| Material / thickness | FR4 / **1.6 mm** |
| Copper | **1 oz outer**, standard inner copper |
| Stackup | JLC standard four-layer stackup; no controlled impedance |
| Finish / mask / legend | **ENIG / green / white** |
| Vias | Tented; no filled/capped via-in-pad process required |
| Tooling | Factory-added 5 mm rails along the two long edges, tooling holes and required fiducials |
| Depanelization | Select/request rail removal; return finished boards |
| Assembly scope | 478 underside SMD parts per assembled board; no top/THT assembly or programming |

JLC's current published Standard single-board limit is **460 × 500 mm**, with
assembly quantity starting at **2**. The finished board fits. With the requested
long-edge rails, the nominal handling rectangle is **452.4375 × 157.6375 mm**;
JLC must confirm its final tooling/transport arrangement. Do not turn this into a
multi-board customer panel: JLC's published panel limits differ from single-board
limits. Boards normally ship with rails unless removal is requested.

The finished board area is **667.97 cm²**, exceeding JLC's published **650 cm²**
large-size assembly surcharge threshold. Include that surcharge and tooling in
the quote; no binding price was obtained.

The `.gbrjob` contains default metadata (`Finish: None`, 35 µm inner copper and
0.48 mm dielectric sections), while the handoff specifies ENIG and the factory's
standard stackup. Explicitly set the order options above and clarify that the
default job metadata is not a custom stackup requirement. Its reported outline
bounding box also includes the 0.05 mm outline stroke; use the finished dimensions
above, measured at the Edge.Cuts centerline.

## Owner assembly and first bring-up

For the two assembled boards, separately provide **2 YD-RP2040 modules, 4 × 1×20
headers, 2 Panasonic EEU-FR1A471 capacitors and 2 raw-USB tap wires**, plus switches,
plate-mount stabilizers, keycaps, plates and cases. Optional mating header sockets
need their own height allowance. C5 and the controller mount on top.

Verify the actual YD module's header fit and USB-C access on a 1:1 print, and
identify its raw USB VBUS point before the BAT54C diode. Carrier pin 40 is
intentionally unused. Without the TP1 tap, the RGB rail has no input power.

After owner assembly: check polarity/shorts, bring up with current-limited power,
test every key and chords, every LED, full-white current and far-end rail ripple
at the existing brightness cap, USB suspend/resume, USB-A-to-C/C-to-C, and Vial
unlock/remapping/persistence. Use the matching `mechanical/` plate and **plate-mount
stabilizers**. These measurements establish prototype operation.

## Message for JLCPCB engineering

> Please quote Cleaver rev0.4: fabricate 5 PCBs total, assemble the bottom-side
> BOM on exactly 2, and return 2 assembled plus 3 bare boards. Four layers,
> 452.4375 × 147.6375 mm finished, 1.6 mm FR4, standard stackup, 1 oz outer copper,
> standard inner copper, green soldermask, white silkscreen, ENIG. Each assembled
> board has 478 SMD placements, including 117 Kailh C2803348 sockets and 117 OPSCO
> C5149201 reverse-mount LEDs. Please confirm stock, attrition and lead time.
> The LEDs face through 117 openings toward the opposite/top side. Current
> openings are 3.6 × 3.2 mm; please resolve their finished dimensions, corner
> radius and placement tolerance against a 3.3 × 2.9 mm maximum LED body. Our
> review finds that ordinary ±0.2 mm milling with R0.5 does not guarantee fit.
> Please confirm lead overlap, reverse-mount retention/reflow and MSL 5a handling.
> Verify socket, LED, diode and IC orientation against the supplied pad-coordinate
> table; CPL is top-view XY, bottom placement, with corrected socket centers.
> Add suitable long-edge tooling rails/holes and support fixtures, and return
> depanelized boards. No through-hole assembly, top-side paste or programming.
> Please include the large-board surcharge and tooling costs. Resolve the LED
> fit/process questions with us before releasing fabrication.

No quote request, file upload, stock reservation or order was submitted by this
review.

## Evidence and reproducibility

Fresh local reports and independent exports: `/tmp/opencode/cleaver-order-review/`.
The first test invocation skipped four Shapely-dependent tests; rerunning with
the existing dependency directory enabled all 25:

```sh
python3 -B scripts/check_kicad.py --reports /tmp/opencode/cleaver-order-review
PYTHONPATH=/tmp/opencode/cleaver-assembly/python python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

Reviewed PCB SHA-256:
`7b83a48035d38c427af6c47ff20fb311b552b90ad182bab0faea532f9db61585`.
Reviewed fabrication ZIP SHA-256:
`98ef27cab35ebc6be01d31606a1856bfab1bc2208e6c2cfe4ac334a0db0c1854`.

Sources checked:

- [JLCPCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- [JLCPCB fabrication capabilities and slot tolerances](https://jlcpcb.com/capabilities/)
- [JLCPCB five fabricated / two assembled ordering example](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- [JLCPCB assembly charges](https://jlcpcb.com/help/article/pcb-assembly-price)
- [Kailh C2803348](https://jlcpcb.com/partdetail/Kailh-CPG151101S11/C2803348)
- [OPSCO C5149201](https://jlcpcb.com/partdetail/SK6812MINI-E/C5149201)
- [OPSCO catalog-linked datasheet](https://datasheet.lcsc.com/datasheet/pdf/0907a34a701b4aef568078003f6e9eae.pdf),
  reviewed from the existing `/tmp/opencode/cleaver-assembly/C5149201.pdf` cache
  because fresh PDF retrieval returned HTTP 403. Cover B/2, 2025-11-22; SHA-256
  `d78c60d7a163c7fdb69db78a2fccf0faa8104532fdee0b0472736aaeac427cc7`.
- [TI TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
- [TI SN74LV1T125 datasheet](https://www.ti.com/lit/ds/symlink/sn74lv1t125.pdf)
