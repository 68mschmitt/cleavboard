# Cleaver-Embedded embedded-0.2 — completed implementation handoff

Finalized 2026-11-09 with KiCad **10.0.8**. All routing/cleanup jobs have completed.
The editable board was regenerated from the final routing archive and validated
again. This is an electrically checked prototype, **not fabrication released**.

## Final checks

| Check | Result |
| --- | --- |
| Schematic ERC, all configured severities | **0 violations** |
| PCB DRC, all configured severities/all track errors, zones refilled | **0 violations** |
| Unconnected items / schematic parity | **0 / 0** |
| Pin/package/power/matrix/LED/geometry assertions | **0 issues** |
| Actual SMD copper / paste on front | **0 / 0** |
| Bottom SMD copper pads | **1,363** |
| New controller bodies and courtyards checked | **34**, no overlaps |
| Controller capacitor/crystal ground-via proximity | **≤1.4142 mm**, 1.5 mm limit |
| Complete-copper archive round trip | **5,382 items → 5,382; 0 missing/extra** |
| Footprints, pad layers/geometry/nets and outline round trip | **Identical** |
| Independent parent default + Vial firmware builds | **Both PASS**; all 10 inputs unchanged |

Native reports are `validation/erc.json` and `validation/drc.json`. Exact current
PCB/schematic/project hashes are in `validation/validation.json`; archive and
round-trip hashes are in `validation/roundtrip.json`. The final manifest inventories
all deliverables and preserved parent firmware evidence.

## Implemented changes

- **One underside SMD assembly side:** RP2040, flash, crystal, regulator, USB-C,
  buttons and passives are B.Cu/B.Paste. Original composite switch footprints
  retain their mechanical geometry and F.Cu metadata, while their actual socket
  copper/paste and BOM assembly side remain bottom.
- All 117 switch/LED/diode positions and pad/hole geometry, 11 mounts, outline,
  matrix mapping and LED order are preserved. No diode was moved.
- MCU at (428,11), flash at (435,20), connector at (449,13) mm. USB still faces
  right. Connector and button bodies now project below the PCB; the case needs
  lower connector clearance and underside BOOTSEL/RESET access.
- Separate adjacent decouplers, explicit real controller courtyards/body checks,
  short ground returns and reserved In2 reference corridors beneath USB/clock.
- USB and crystal signal routes are hand-laid bottom copper with **zero signal
  vias**. QSPI and matrix fan-in use orderly octilinear escapes; clearance-aware
  shortening is applied across the board while preserving repeated key cells.
- Four ordinary masked **0.50/0.30 mm** ground vias are outside the QFN exposed
  copper/paste, connected with 0.4 mm spokes. No holes occupy the exposed pad;
  **filled/capped via-in-pad processing is no longer required**. Paste remains
  four 1.25 mm squares. Another 36 roomy routing vias were promoted to 0.50/0.30 mm.
- Protected TPS2553 branch (~353 mA nominal) and firmware **8/255** RGB cap remain.
  Firmware sources and electrical pin mapping are unchanged.

## Actual routing outcome

See [review/README.md](review/README.md) for actual before/after KiCad images,
body/courtyard overlay, all four layers, controller/fan-in crops and metrics.

- Segments **9,693 → 4,556**; degree-two bends **8,111 → 2,984**.
- Sub-0.2 mm segments **4,906 → 508**; vias **874 → 826**.
- USB total copper **54.172 → 34.857 mm**; XIN **12.297 → 5.659 mm**.
- Total board track length **20,197.980 → 20,324.962 mm (+0.63%)**: some matrix/
  debug paths lengthen with the physically separated underside placement. The
  improvement is substantially fewer bends, staircases and vias, plus shorter
  critical local nets; an overall length reduction is not claimed.

## Reproduce

Using KiCad's Python interpreter with Shapely/Pillow/pypdf, from this project:

```sh
python3 -B source/check.py
python3 -B source/archive.py
# Save the completed PCB outside the project before rebuilding.
python3 -B source/generate.py --route routing/Cleaver-Embedded.ses
python3 -B source/compare_roundtrip.py /path/to/completed-backup.kicad_pcb
python3 -B source/check.py
python3 -B source/export_pdf.py
python3 -B source/review.py Cleaver-Embedded.kicad_pcb after
python3 -B source/manifest.py
```

The actual round-trip backup is
`/tmp/opencode/cleaver-embedded/bottom-completed-before-roundtrip.kicad_pcb`.
Commands used `/usr/bin/python3 -B` with
`PYTHONPATH=/tmp/opencode/cleaver-embedded/python-deps`.
Normal regeneration imports complete copper and via metadata; historical 0.1
escape/repair scripts are not part of that workflow.

Editable project, complete/focused schematic PDFs, BOM, component data, local
libraries/models, references, provenance and routing archive are refreshed.
The original immutable baseline remains byte-identical to source commit
`8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad`.

## Firmware evidence and release blockers

Parent-owned evidence remains unchanged in `validation/firmware/`: Vial-QMK
`dd43959ae5c08d8a28d38a1acf7b04e86b14a344`, GCC 16.2.0, five strong keyboard hooks,
Vial/VialRGB linkage and EEPROM mapped base `0x103fe000`. The previously reported
independent interface check covered 1,363 assignments and all 117 matrix circuits;
the final local checker independently verifies preserved interfaces and geometry.

Release still requires resolution of the inherited LED-aperture tolerance
failure, factory DFM/actual four-layer stackup review, revised underside/case fit,
and assembled-board USB/power/functional testing. The five inherited ignored DRC
categories are listed in validation; no new ignored categories or individual
exclusions were introduced.

All implementation changes are confined to `designs/embedded-rp2040/`. Parent
firmware evidence and the root/legacy design were preserved. No commits were made.
