# Mechanical and reverse-LED implementation

## Retained carrier interface

- 452.4375 × 147.6375 mm outer board, 1.6 mm nominal thickness, four copper layers.
- All 117 switch centres, switch/socket pads and mechanical holes retained exactly.
- Eleven M2 clearance mounts at the original coordinates; 6 mm hardware cylinders
  retained as copper keepouts and independently checked against component bodies.
- Top YD-RP2040 body 53.34 × 22.86 mm; two 1×20 2.54 mm headers 17.78 mm apart.
  Controller position/orientation unchanged: USB-C faces the right board edge.
- Original plate-mount stabilizers and plate spacing apply: nominal plate top
  5.0 mm above PCB top, 1.5 mm plate, 3.5 mm between PCB and plate underside.
- The original controller notch remains necessary. The previous 10 mm top
  capacitor opening can remain empty or be closed. **No new plate/case cutout**
  is needed for the lighting circuit. The 117 PCB optical apertures do change.
- Provide at least **3 mm unobstructed space below the PCB**, including solder
  fillets/header tails. Socket bodies occupy about 1.8 mm; new support parts are
  low-profile 0805/1206/SOT-23 parts, conservatively reserve 2 mm including solder.
  Trim owner-installed header tails to this envelope. Never support the PCB on
  an SMD body. Original case geometry is an interface proposal, not a fit-tested
  case supplied by this project.

The current support bodies occupy the clear area left of the top module, roughly
X=376–397 mm and Y=3–24 mm, **all below the PCB**. Even though the module is on
top, no new support body is placed between its header rows. No radial capacitor
or tall through-hole electronic component is used.

## LED identity and aperture

**BrtLed BL-HZ333H-L21-TRE, JLCPCB C5123487** is the fitted reverse-mount white
LED. The manufacturer drawing is saved in `references/BL-HZ333H-L21-TRE.pdf`
(PDF page 2; tape orientation on PDF page 4). It specifies:

- two terminals: green dot/triangle denotes the **cathode**; our pad numbering
  is **1 cathode, 2 anode**;
- carrier 3.20 ±0.10 × 1.60 ±0.10 mm;
- raised lens length 1.40 ±0.05 mm; conservatively bound lens width by the whole
  package width (maximum 1.70 mm);
- total height 1.10 ±0.10 mm; separate substrate thickness is not dimensioned;
- recommended reflow lands 1.5 × 1.6 mm with a 2.0 mm inner gap;
- no dimensioned routed aperture: the **2.10 × 2.30 mm opening is our design**.

The underside-mounted carrier bridges the aperture; **only the lens enters the
board**, rather than forcing the whole 3.2 mm package through it. Even bounding
lens protrusion by the maximum entire package height (1.20 mm) keeps it below
a 1.6 mm board with −10% thickness tolerance (1.44 mm). Emitter centres stay at switch X,
switch Y+5.08 mm. Use switches/keycaps with a compatible translucent light path;
opaque housings are not made transparent by this design.

### Land changes and fabrication constraints

The exact footprint is `Cleaver-White:BL-HZ333H-L21-TRE_Reverse`:

- optical opening **2.10 × 2.30 mm** on Edge.Cuts;
- pad centres **X=±1.875 mm**, Y=0; pad size **1.35 × 1.60 mm**;
- pads start 1.20 mm from centre, giving **0.15 mm nominal copper-to-opening**;
- nominal ceramic/land overlap 1.60−1.20 = **0.40 mm** per end;
- inner land edge is a deliberate **0.20 mm setback** from the BrtLed suggested
  pattern; outer edge is 0.05 mm farther out. This retains the routed board's
  aperture clearance and is a **custom land pattern**, not the vendor pattern;
- cathode is the **left pad in PCB top-view coordinates**. The B.Silkscreen bar
  identifies that end. A bottom-view drawing mirrors it. Use the pad-orientation
  CSV rather than guessing orientation from a similar RGB package.

The 0.5 mm general copper-edge rule cannot be applied to these short reverse-LED
lands: it would leave only approximately 0.05 mm nominal ceramic overlap. The
project therefore has **one pad-scoped 0.1 mm edge-clearance rule**, limited to
the 117 LED footprints. All tracks, vias, other lands and the external board
edge retain the inherited rules. No DRC category is disabled to achieve this.

Specify the finished aperture dimensions to **±0.05 mm in both axes**, aperture
registration to copper **±0.025 mm**, and **inside milling radius ≤0.25 mm**
(0.5 mm cutter or a qualified equivalent process). These are **explicit precision
fabrication requirements**, not assumed standard JLCPCB routing capability.
Nominal 0.15 mm copper-edge gap less 0.025 mm half-size error and 0.025 mm
registration leaves **0.10 mm**. The rectangular Edge.Cuts geometry represents
the aperture envelope; real cutter rounding must remain inside this allowance.

The worst-case lens envelope is **1.45 × 1.70 mm**. `source/check_replacements.py`
checks it against the minimum **2.05 × 2.25 mm** rounded aperture, with 0.25 mm
corner radius, ±0.10 mm placement, ±0.025 mm aperture registration, and angles
sampled every 0.1° across ±3°. Minimum computed lens-to-edge clearance is
**0.110 mm**. Minimum 3.1 mm carrier length and ±0.10 mm unrotated placement leave
**0.25 mm carrier overlap** per limiting land. This is substrate support, not a
guaranteed metallized contact area: the electrode notches and carrier thickness
are not sufficiently dimensioned for that claim. Stencil/reflow wetting of the
custom lands requires assembler review and a physical sample.

**Do not fabricate with an ordinary 2 mm cutter, substitute an RGB footprint,
or enlarge the opening indiscriminately.** A larger opening reduces the short
carrier's support and solder overlap. The assembler must approve the reduced
land length, aperture accuracy, stencil, reverse-mount pickup orientation and
MSL3 handling. If that process is unavailable, this exact PCB cannot be released
at that factory without redesign. The exact LED now has JLCPCB catalog code
**C5123487**, an Extended SMT component; global sourcing/consignment is no longer
the intended purchasing route.

## HanElectricity socket

All **SW001–SW117** use **CPG151101S11-16 / C41430893**, with local footprint
`Cleaver-White:HanElectricity_CPG151101S11-16`. Drawing:
`references/HanElectricity-CPG151101S11-16.pdf`. The PCB matches its recommended
two **3.00 mm holes**, **6.35 mm X / 2.54 mm Y** hole separation and
**2.55 × 2.50 mm** lands. In switch-centred top-view/down-Y coordinates:

| Feature | X, Y (mm) |
|---|---|
| Socket locating hole | −3.81, −2.54 |
| Socket locating hole | +2.54, −5.08 |
| Pad 1 / row | +6.29, −5.08 |
| Pad 2 / key diode | −7.56, −2.54 |
| CPL socket centre | −0.635, −3.81 |

The drawing specifies Ø2.90 ±0.05 mm locating bosses and Ø3.00 ±0.05 mm PCB
holes; at opposing tolerance limits this is line-to-line. Hole registration and
actual insertion fit should be checked with the purchased socket. Nominal body
height is about 1.85 mm; the 3 mm underside allowance is retained. Ratings are
12 V / 10 mA maximum and 100 mΩ maximum contact resistance, suitable for the
3.3 V, pull-up-limited key matrix (not a lighting-power path).

Independent checks use a conservative **15.10 × 6.14 mm** socket rectangle
(maximum full terminal/body dimensions plus ±0.10 mm placement) and a rotated,
tolerance-expanded LED envelope. Across all 234 replacements the closest checked
neighbor-body gap is **0.42 mm**. See `validation/replacements.json` for results
and assumptions. The socket's asymmetric holes/pads determine its orientation;
electrical nonpolarity does not make a 180° placement interchangeable.

## Assembly/fit checks

Use a sample of the exact LED, socket and intended switch to test one cell before
ordering the full board. Inspect lens entry, ceramic support, solder wetting,
polarity and optical transmission after reflow. All LED/resistor/diode/socket
pads have bottom paste; vias are outside their solder lands. The factory performs
one bottom SMT assembly operation. The owner then installs the top module headers
and mechanically clips in switches/stabilizers. USB receptacle projection and
header stack height must be checked against the actual module and existing case.
