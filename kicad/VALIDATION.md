# Revision 0.3 validation

**Electrical/layout checks pass, including complete copper connectivity.**
The archived routing was imported into a freshly regenerated board and checked
again. Physical fit, assembly, USB power measurements, and hardware operation
remain unverified; complete the prototype checks below before a production run.

The schematic and placement target the DWEII / VCC-GND YD-RP2040 USB-C module,
117 unique keys, and 117 reverse-mounted SK6812MINI-E Rev.02 LEDs. No physical
prototype has been assembled or tested by this agent.

## Checks recorded on 2026-11-08

| Check | Result |
| --- | --- |
| KiCad version | 10.0.8 |
| Schematic ERC, meaningful electrical pin types | 0 violations |
| Shared-design/geometry/router-boundary unit tests | 11 passed |
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
| `default` firmware build | Succeeded |
| `vial` firmware build, including VialRGB | Succeeded |

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
  electrical files, active libraries, firmware source, routing archive, checker,
  and tests; also the firmware build provenance and UF2 hashes.
- [`routing/Cleaver.ses`](routing/Cleaver.ses): the accepted routing, including
  the ten final completion connections. See `routing/README.md`.

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
module/LED geometry, checks QMK/Vial/CSV mapping, runs ERC, and runs DRC with
zone refill, all track errors, schematic parity, and all severities. It does not
save or alter the board. Success requires no violations and no unconnected items;
the supplied routed board passes those conditions.

The pre-existing project disables missing-courtyard, track-end-centering, tuning
profile, and footprint-filter/type checks. These settings were not relaxed to
accept routing. In particular, a clean electrical DRC is not a component-body or
case-fit guarantee; the hand-assembly/prototype checks below are still required.
The project comparison confirms that only netclass preferences were changed;
manufacturing minima, DRC/ERC severity settings, and exclusions remain unchanged.

## Physical checks still required

1. Compare the actual module with a 1:1 print: body/header dimensions, numbering,
   USB-C plug access, and underside spacing. The published drawing/schematic is
   not proof that every seller revision matches.
2. Identify **raw USB VBUS before the module's diode** on the actual board and
   install the approved wire to TP1. Do not guess from a V1.1 reference designator
   when using a V1.3 module. Follow `README.md`.
3. Fit one switch/socket/diode/LED/capacitor cell to the supplied plate. Confirm
   LED polarity, lead overlap, emitter height, and hand-soldering access. Use
   plate-mounted stabilizers; case-specific holes are not defined.
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
