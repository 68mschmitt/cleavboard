# Revision 0.5 validation

**Electrical/layout checks pass, including complete copper connectivity.**
The archived routing was imported into a freshly regenerated board and checked
again. Physical fit, assembly, USB power measurements, and hardware operation
remain unverified; complete the prototype checks below before a production run.

The schematic and placement target the DWEII / VCC-GND YD-RP2040 USB-C module,
117 unique keys, and 117 reverse-mounted OPSCO SK6812MINI-E C5149201 LEDs. No physical
prototype has been assembled or tested by this agent.

## Checks recorded on 2026-11-10

| Check | Result |
| --- | --- |
| KiCad version | 10.0.8 |
| Schematic ERC, meaningful electrical pin types | 0 violations |
| Shared-design/geometry/router-boundary/model/assembly/routing unit tests | 29 passed (Shapely enabled) |
| Schematic/PCB net assignments | Pass |
| 8×16 matrix, 117 unique addresses | Pass |
| QMK and Vial matrix/RGB-order parity | Pass |
| YD module header position and pin numbering | Pass |
| Reverse-mount LED pad positions and 117 actual openings | Pass |
| Final routed-board DRC, all severities and all track errors, zones refilled | **0 violations** |
| Unconnected copper items | **0** |
| Schematic/PCB parity issues | **0** |
| Same-net via holes outside exposed SMD solder lands | Pass |
| Regeneration from archived `routing/Cleaver.ses` | Pass; fresh ERC/DRC/connectivity checks repeated |
| Factory assembly | 479 SMD placements, all bottom; socket origins corrected |
| Purchasing review | All 13 exact factory purchasing groups have positive JLCPCB SMT stock; dated evidence retained |
| Through-hole component pins / front paste pads | Only U1's 40 PTH pins / zero front paste pads |
| Mechanical mounting | 11 M2 holes, 6 mm copper-free hardware envelopes |
| Plate generation | Connected plate, matching holes, 7 × 2u + 1 × 6.25u stabilizers |
| Routed copper | 4,065 track segments and 670 vias; all 4,735 items preserved through regeneration |
| Bundled 3D models | 597 placements / 480 populated footprints; pads/holes/fiducials bare |
| `default` firmware build | Fresh clean revision 0.5 build passed; RP2040 UF2 validated |
| `vial` firmware build, including VialRGB | Fresh clean revision 0.5 build passed; RP2040 UF2 validated |

Firmware was freshly rebuilt on 2026-11-10, after target-specific clean commands,
with `make cleaver:default -j4` and `make cleaver:vial -j4`
against **vial-qmk `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`**, using
`arm-none-eabi-gcc 16.2.0`. The checked firmware includes secure Esc + main Enter
Vial unlock, VialRGB, lock-key indicators, the 8/255 brightness cap, and USB-aware
GP28 power control. Build success does not establish hardware operation.

## Recorded artifacts

- [`validation/erc.json`](validation/erc.json) and
  [`validation/drc.json`](validation/drc.json): the fresh KiCad reports.
- [`validation/validation.json`](validation/validation.json): checked PCB and
  schematic hashes and integration-check result.
- [`validation/manifest.json`](validation/manifest.json): SHA-256 hashes of the
  electrical files, active libraries/models, previews, firmware source, routing
  archive, checker, and tests; also firmware build provenance and UF2 hashes.
- [`routing/Cleaver.ses`](routing/Cleaver.ses): all accepted revision 0.5 copper,
  including the C5/TP1 connections and local ROW1 reroute. See `routing/README.md`.
- [`Cleaver.3dshapes/README.md`](Cleaver.3dshapes/README.md): model sources,
  licenses, and approximation limits; previews in [`previews/`](previews/).

Revision 0.5 replaces all 117 sockets with HanElectricity CPG151101S11-16 /
C41430893 and normalizes their bottom anchors without moving holes or lands.
C5 is now bottom SMD Nichicon PCF1A471MCL1GS / C3275369, and TP1 is a bare
bottom SMD wire pad. All other purchasing identities, LED pinout and firmware
are retained. See the [complete component review](references/COMPONENT-REVIEW.md).
All project electrical DRC rules remain in effect.

The manufacturing package and its independent SHA-256 manifest are under
[`../manufacturing/rev0.5/`](../manufacturing/rev0.5/). That package includes fresh
checks, exact purchasing BOM, bottom CPL, pad-orientation data, assembly drawing,
Gerbers and separate PTH/NPTH drills. Sourcing evidence is under `references/`.
All 13 selected factory groups had positive, purchasable SMT stock on 2026-11-10;
C5 had 103 pieces. Stock is not reserved and order-specific DFM is unverified.

The earlier routing cleanup is recorded in `routing/cleanup.json`. Revision 0.5
adds off-pad power/ground vias for C5 and the bottom TP1 pad, with a local ROW1
detour around the wider capacitor lands. Deterministically archived per-net
tracks/vias match exactly before and after fresh generator import.

The build logs, UF2 outputs and detailed build provenance are retained in
[`../manufacturing/rev0.5/firmware/`](../manufacturing/rev0.5/firmware/); they are not
required to regenerate the KiCad board. Hashes identify the supplied artifact
versions. Regeneration preserves the electrical/physical design, not necessarily
byte-identical KiCad UUIDs or compiler timestamps.

Run the read-only integration checker from the repository root:

```sh
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/check_kicad.py
```

The checker exports a fresh schematic netlist, verifies actual pad nets and
module/LED geometry, checks QMK/Vial/CSV mapping and local model coverage, runs
ERC, and runs DRC with zone refill, all track errors, schematic parity, and all
severities. It does not
save or alter the board. Success requires no violations and no unconnected items;
the supplied routed board passes those conditions.

The pre-existing project disables missing-courtyard, track-end-centering, tuning
profile, and footprint-filter/type checks. These settings were not relaxed to
accept routing. In particular, a clean electrical DRC is not a component-body or
case-fit guarantee; the physical prototype checks below are still required.
Comparison with the pre-edit project confirms only a stale `/MODULE_VOUT`
netclass assignment was removed; manufacturing minima, DRC/ERC severity settings,
and exclusions remain unchanged.

## Physical checks still required

1. Compare the actual module with a 1:1 print: body/header dimensions, numbering,
   USB-C plug access, and underside spacing. The published drawing/schematic is
   not proof that every seller revision matches.
2. Identify **raw USB VBUS before the module's diode** on the actual board and
   install the approved wire to TP1. Do not guess from a V1.1 reference designator
   when using a V1.3 module. Follow `README.md`.
3. Print the new stabilizer/switch fit coupon in `../mechanical/`, check clip fit
   with the actual plate-mount stabilizers, and confirm plate spacing. The case
   uses the 11 supplied M2 axes. Confirm LED polarity, lead overlap and emitter
   height on the assembled prototype. Reserve **11 mm clear underside case depth
   beneath C5**. The old top capacitor plate opening is unused; the MCU opening
   and approximate models do not establish maximum-tolerance fit.
4. Measure total USB current, the limited LED-branch current, pre-configuration
   and suspend current, startup behavior,
   and full-white rail ripple/voltage at the farthest LEDs at **8/255** brightness.
   The current limit is approximately 353 mA nominal, with 311–401 mA calculated
   bounds; the module draws additional current. Do not increase brightness without
   measurements. Check the 470 µF capacitor's polarity and installed height.
5. Test every key and multi-key chords, the complete RGB chain, Caps/Num/Scroll
   indicators, Vial unlock/remapping/persistence, USB suspend/resume, and both
   USB-A-to-C and C-to-C enumeration.

The historical revision 0.2 findings in `DESIGN_REVIEW.md` are not a substitute for
this revision's results. No autorouter timeout or “0 violations” router summary is
accepted as a fabrication check.
