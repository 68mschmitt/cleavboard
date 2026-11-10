# Repository-level checks

Run from the repository root with KiCad's Python environment where needed:

```sh
python3 -B tools/verify_legacy.py
python3 -B tools/verify_embedded_interface.py
```

- `verify_legacy.py` compares the original tracked files with the pre-variant
  commit. It excludes the already-modified nested history repository and
  transient KiCad editor lockfiles.
- `verify_embedded_interface.py` reads both PCB files and independently checks
  the bare RP2040's power, QSPI and USB pinouts, USB-C pulldowns, regulator and
  ESD connections, all 117 switch/diode circuits, retained
  key-component positions, firmware matrix, and a fresh schematic netlist's pad
  assignments. It does not import either project's generator definitions.
  It also verifies that all SMD copper and stencil pads are on the underside,
  inspecting actual pad layers to handle composite switch/socket footprints.
- `inspect_routing.py BOARD [--baseline BEFORE] [--output REPORT.json]` reports
  trace length, vias, segment directions, bends, and SMD assembly sides directly
  from PCB geometry. It is read-only. Metrics complement visual review; a lower
  segment count alone does not establish a better route.

Both checks leave the KiCad design files untouched. The interface check needs
`pcbnew` and `kicad-cli`; its temporary exported netlist is removed afterward.
Use the embedded project's own validation command as well: schematic/PCB net
agreement does not establish that copper is fully routed or clear of shorts.
