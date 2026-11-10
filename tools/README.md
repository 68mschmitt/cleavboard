# Repository-level checks

Run from the repository root with KiCad's Python environment where needed:

```sh
python3 -B tools/verify_legacy.py
python3 -B tools/verify_embedded_interface.py
```

- `verify_legacy.py` compares the original files with the pre-variant commit,
  translating moved paths with `repository_paths.py`. Later hardware/tooling
  changes are expected differences (exit 1); Git errors return exit 2. Local
  history, editor preferences, locks and caches are excluded.
- `verify_embedded_interface.py` reads the embedded PCB and its frozen revision
  0.4 baseline (`source/legacy-base.kicad_pcb`) and independently checks
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

## Artwork and design-specific tools

`add_tavi_artwork.py [--apply]` traces `assets/artwork/taviana/tavi-tac.png`
into the module and embedded projects' local footprints. See the
[artwork instructions](../assets/artwork/taviana/README.md).

Generators and design-specific tests live in each project's `source/` directory.
Run the module project's existing tests from the repository root:

```sh
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
python3 -B designs/module-rp2040/source/check_kicad.py
```

Use Python with KiCad's `pcbnew` and the dependencies described by each design.
