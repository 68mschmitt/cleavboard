# Design and verification provenance

Revision `white-0.1`, 2026-11-10. This is the isolated monochrome derivative of
the repository's rev0.4 YD-RP2040 carrier, implemented under this directory.

## Frozen inputs and editable outputs

- `source/base-rev04.kicad_pcb` freezes the original carrier geometry and routed
  matrix. `source/layout.json` freezes key positions, matrix assignments and module
  pin definitions. Historical RGB fields in that input are not active circuitry.
- `source/generate.py` selects the inherited switches, diodes and module, creates
  the monochrome circuitry and generates the local symbols, schematic and PCB.
- The 117 switch/socket and diode pad geometries, 40 module pads, 11 mounting
  holes and outer outline are independently compared with the frozen board.
- The local footprint library retains the inherited CC BY-SA 4.0 notice in
  `Cleaver-White.pretty/LICENSE.md`. Inherited footprint geometry is attributed
  to the Cleaver carrier library and its upstream notices; newly drawn LED and
  MOSFET footprints are provided under the same library license. Manufacturer
  reference documents retain their original ownership.

## Routing history and restoration

The inherited matrix routing was retained. `source/fanout.py` created repeating
short LED/resistor fanouts; `source/route.py` and `source/grid_route.cpp` completed
the new controller connections using conservative obstacle-aware grid routing.
Filled F.Cu distributes LED supply, In1.Cu is GND, and In2.Cu distributes the
switched LED return alongside retained matrix copper. No simulated illustration
is substituted for actual routing in the review images.

`source/archive_routing.py` records **all** final tracks/vias in
`source/complete.ses`. Its coordinates have 0.0001mm resolution. Normal generation
restores that archive and refills zones. `--placement` is a deliberate routing
reset for development, not the standard rebuild path. Temporary routing binaries
and work files are unnecessary to open, edit, restore, check or export the design.

`validation/routing-roundtrip.json` records the before/after geometric comparison
at the archive resolution: **3,384 tracks/vias retained, zero added or missing**.
Schematic presentation and corrected F1 purchasing
text can change without changing the archived copper geometry.

To repeat this comparison, save the current board outside the project before
running the normal generator, then run:

```sh
$PY -B designs/single-color-devboard/source/compare_routing.py \
  /path/to/saved-before.kicad_pcb \
  designs/single-color-devboard/Cleaver-White.kicad_pcb \
  designs/single-color-devboard/validation/routing-roundtrip.json
```

## Evidence and limits

Catalog substitution: all 117 sockets are now HanElectricity CPG151101S11-16 /
C41430893 and all 117 LEDs BrtLed BL-HZ333H-L21-TRE / C5123487. The original
socket holes/lands and custom LED lands/apertures are retained after the new
datasheet comparisons. Exact KiCad identities, purchasing fields and model
assignments were updated; original key legends survive in the `Key` field.
`source/sourcing.py` supplies purchasing identities to generation/export;
`source/check_replacements.py` independently transcribes vendor dimensions for
envelope/polarity checks. `validation/replacements.json` records the results and
unverified manufacturing assumptions. The LED visualization now uses a 1.10 mm
total envelope; the socket visualization remains an explicitly documented proxy.

- KiCad 10.0.8 `source/check.py`: ERC, exhaustive DRC, unconnected and schematic
  parity checks after zone refill, plus geometry, circuit and assembly assertions.
  `validation/validation.json` binds results to the checked design hashes.
- `source/export.py`: genuine KiCad schematic PDFs and copper/assembly plots,
  fabrication files, exact BOM and bottom-side CPL with socket-centroid offsets.
- `source/check_exports.py`: independent reference/count, centroid, pad/net,
  firmware-hash and fabrication-archive checks; report in
  `validation/exports.json`.
- `manufacturing/SHA256.json` identifies exported fabrication files and their
  source board. `SHA256.json` at project root covers the complete handoff except
  itself and transient KiCad UI/cache files.
- `firmware/build/provenance.json` records pinned upstream source, toolchain,
  commands, source hashes and UF2 hashes for both successful builds.

Review images were inspected for repeating key-cell arrangement and controller
routing. Schematic detail pages were also inspected; matrix symbols were spaced
vertically to eliminate overlapping net labels. All numerical power estimates
are calculations. No physical LED, module, case or assembled-board tests were
performed. Remaining qualification is explicitly listed in `POWER.md`,
`MECHANICAL.md` and `manufacturing/README.md`.

Use the generation/check/export commands in `README.md`, followed by
`source/check_exports.py`, for a refreshed deliverable. Refresh the root manifest
after documentation or firmware changes with `source/manifest.py`.
