# Validation artifacts

Run `python3 -B source/check.py` from the project directory with KiCad 10's
Python interpreter. It exports the schematic netlist, runs ERC and DRC with all
configured severities, enables schematic parity and zone refill, then checks
pin assignments, packages, supplies, USB, boot/reset, matrix, LED order, firmware
pin declarations, retained geometry and the exposed-pad vias.

- `validation.json`: counts, assertions, source hashes, ignored rule categories
  and explicit release blockers.
- `erc.json`: native KiCad ERC report.
- `drc.json`: native KiCad DRC, unconnected-items and schematic-parity report.
- `netlist.xml`: exported authoritative schematic connectivity.
- `roundtrip.json`: completed-board versus regenerated-board comparison.
- `manifest.json`: SHA-256/size inventory of the final handoff, including parent
  firmware evidence, excluding editor lock/state files and the manifest itself.
  Refresh with `python3 -B source/manifest.py` after all other outputs are final.

PDF review artifacts come directly from the schematic through
`source/export_pdf.py`; the controller PDF contains four focused detail pages.
The script does not redraw or independently interpret the circuit.

Passing these checks is not a fabrication release. Missing courtyards and the
other inherited ignored categories are disclosed in `validation.json`. The
inherited LED-opening tolerance failure remains unresolved. Controlled-impedance
stackup, USB/clock layout review, factory assembly/DFM, case fit, current budget,
USB enumeration/suspend and physical keyboard operation require further review
or prototype measurements.

Independent firmware compilation and address verification passed in the parent
task: see [`firmware/README.md`](firmware/README.md), build logs, disassembly and
source/output hashes. Both default and Vial builds include all five strong
keyboard hooks; the Vial image links Vial/VialRGB, and both use EEPROM at mapped
address `0x103fe000`. Hardware persistence has not been tested. These results are
separate from this project's declarative firmware checks.
