# Revision 0.4 validation

**Electrical/layout checks pass, including complete copper connectivity.**
The archived routing was imported into a freshly regenerated board and checked
again. Physical fit, assembly, USB power measurements, and hardware operation
remain unverified; complete the prototype checks below before a production run.

The schematic and placement target the DWEII / VCC-GND YD-RP2040 USB-C module,
117 unique keys, and 117 reverse-mounted OPSCO SK6812MINI-E C5149201 LEDs. No physical
prototype has been assembled or tested by this agent.

## Checks recorded on 2026-11-08

| Check | Result |
| --- | --- |
| KiCad version | 10.0.8 |
| Schematic ERC, meaningful electrical pin types | 0 violations |
| Shared-design/geometry/router-boundary/model/assembly/routing unit tests | 25 passed (Shapely enabled) |
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
| Factory assembly | 478 SMD placements, all bottom; socket origins corrected |
| Mechanical mounting | 11 M2 holes, 6 mm copper-free hardware envelopes |
| Plate generation | Connected plate, matching holes, 7 × 2u + 1 × 6.25u stabilizers |
| Trace cleanup | 7,895 → 4,058 segments; sub-0.3 mm segments 2,835 → 575; 667 vias retained |
| Bundled 3D models | 597 placements / 480 populated footprints; pads/holes/fiducials bare |
| `default` firmware build | Previously succeeded; firmware unchanged in PCB revision 0.4 |
| `vial` firmware build, including VialRGB | Previously succeeded; firmware unchanged |

Firmware was built with `make cleaver:default -j4` and `make cleaver:vial -j4`
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
- [`routing/Cleaver.ses`](routing/Cleaver.ses): all accepted revision 0.4 copper,
  including the underside reroute. See `routing/README.md`.
- [`Cleaver.3dshapes/README.md`](Cleaver.3dshapes/README.md): model sources,
  licenses, and approximation limits; previews in [`previews/`](previews/).

Revision 0.4 changes placement, routing and mechanical features. It is not a
model-only change. The OPSCO purchasing part's pin numbering is aligned with
its catalog datasheet; physical LED signal locations and firmware remain the
same. The 100 nF and 1 µF purchasing capacitors are rated 50 V instead of the
previous 10 V minimum. All project electrical DRC rules remain in effect.

The manufacturing package and its independent SHA-256 manifest are under
[`../manufacturing/rev0.4/`](../manufacturing/rev0.4/). That package includes fresh
checks, exact purchasing BOM, bottom CPL, pad-orientation data, assembly drawing,
Gerbers, separate PTH/NPTH drills, and sourcing references. JLCPCB catalog support
is established for sockets/LEDs; order-specific stock and DFM acceptance are not.

The accepted routing cleanup replaces grid staircases and redundant pad-approach
jogs with straight/45-degree runs. Two 0.4 mm inner-layer LED-supply connections
restore continuity across regions separated by the refilled front power pour.
Pad/via locations, track widths, layer assignments and circuit mapping are
preserved. See `routing/cleanup.json` for before/after metrics and source hashes.

The build logs and UF2 outputs remain in the working environment under
`/tmp/opencode/cleaver-revision/` and `/tmp/opencode/cleaver-vial/`; they are not
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
The project comparison confirms that only netclass preferences were changed;
manufacturing minima, DRC/ERC severity settings, and exclusions remain unchanged.

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
   height on the assembled prototype. The MCU/capacitor plate openings and
   approximate models do not establish maximum-tolerance fit.
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
